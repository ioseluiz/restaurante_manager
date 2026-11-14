"""E2E de inventario: compra -> recepción (stock + WAC + Kardex) -> ventas diarias -> reabrir día ->
conteo -> abastecimiento. Los valores esperados están calculados a mano (ver docs/calculos.md)."""
import pytest

from app.controllers.abastecimiento_controller import AbastecimientoController
from app.controllers.kardex_controller import KardexController
from app.views.modulos.conteo_inventario import _registrar_ajuste_kardex

import escenario_e2e as E

approx = pytest.approx


def _stock(db, insumo_id):
    return db.fetch_one("SELECT stock_actual FROM insumos WHERE id=?", (insumo_id,))[0]


def _costo(db, insumo_id):
    return db.fetch_one("SELECT costo_unitario FROM insumos WHERE id=?", (insumo_id,))[0]


def _invariante_kardex(db, esc):
    """stock_actual = stock inicial + Σ movimientos, para cada insumo."""
    for iid, stock in db.fetch_all("SELECT id, stock_actual FROM insumos"):
        movs = db.fetch_one("SELECT COALESCE(SUM(cantidad),0) FROM movimientos_inventario WHERE insumo_id=?",
                            (iid,))[0]
        assert stock == approx(esc.stock_inicial.get(iid, 0.0) + movs), f"insumo {iid}"


def test_recepcion_sube_stock_y_recalcula_promedio_ponderado(db, esc, recibir):
    recibir(db, esc.compra)

    # Arroz: 5 000 g a 0.0010 + 2 sacos × 10 000 g a 0.0012 = 25 000 g a (5 + 24) / 25 000
    assert _stock(db, esc.arroz) == approx(25000)
    assert _costo(db, esc.arroz) == approx(0.00116)
    # Sin stock previo: el costo es el de entrada
    assert (_stock(db, esc.pollo), _costo(db, esc.pollo)) == (approx(15000), approx(0.004))
    assert (_stock(db, esc.tomate), _costo(db, esc.tomate)) == (approx(4000), approx(0.0015))
    assert (_stock(db, esc.aceite), _costo(db, esc.aceite)) == (approx(2000), approx(0.004))
    assert (_stock(db, esc.envase), _costo(db, esc.envase)) == (approx(50), approx(0.20))
    assert (_stock(db, esc.soda), _costo(db, esc.soda)) == (approx(24), approx(0.50))

    assert db.fetch_one("SELECT estado FROM compras WHERE id=?", (esc.compra,))[0] == "RECIBIDO"
    assert db.fetch_one("SELECT COUNT(*) FROM movimientos_inventario WHERE tipo_movimiento='COMPRA'")[0] == 6
    _invariante_kardex(db, esc)


def test_recepcion_no_se_aplica_dos_veces(db, esc, recibir, sin_dialogos):
    from app.views.modulos.compras_crud import RecepcionDialog

    recibir(db, esc.compra)
    RecepcionDialog(db, esc.compra)._aplicar()
    assert _stock(db, esc.arroz) == approx(25000)
    assert db.fetch_one("SELECT COUNT(*) FROM movimientos_inventario")[0] == 6


def test_ventas_diarias_descuentan_receta_explotada_y_reabrir_lo_revierte(db, esc, recibir):
    recibir(db, esc.compra)
    rid = E.dia_ventas(db, E.FECHA_VENTA, [(esc.p1, 10), (esc.p2, 20)])
    k = KardexController(db)

    res = k.procesar_ventas_diarias(rid)
    # Por porción — P1: Pollo 200, Arroz 150, Tomate 50×1200/1000 = 60, Aceite 50×100/1000 = 5
    #               P2 (tanda × 400/4000): Arroz 150, Pollo 200, Aceite 20
    # Consumo: Pollo 10×200 + 20×200 = 6 000 · Arroz 1 500 + 3 000 = 4 500 · Tomate 600 · Aceite 50 + 400 = 450
    assert res["movimientos"] == 4 and res["sin_receta"] == [] and res["negativos"] == []
    esperado = {esc.pollo: 9000, esc.arroz: 20500, esc.tomate: 3400, esc.aceite: 1550}
    for iid, stock in esperado.items():
        assert _stock(db, iid) == approx(stock)
    _invariante_kardex(db, esc)

    assert k.revertir_ventas_diarias(rid) == 4
    assert _stock(db, esc.pollo) == approx(15000) and _stock(db, esc.arroz) == approx(25000)

    k.procesar_ventas_diarias(rid)
    for iid, stock in esperado.items():
        assert _stock(db, iid) == approx(stock)
    with pytest.raises(ValueError):
        k.procesar_ventas_diarias(rid)
    _invariante_kardex(db, esc)


def test_ventas_diarias_descuentan_empaques_segun_pct_para_llevar(db, esc, recibir):
    """H10: los empaques del plato (no pasan por la caja) se descuentan con el % de platos para llevar.
    Bebidas y acompañamientos no: la caja los registra como líneas propias con su receta."""
    recibir(db, esc.compra)
    db.execute_query("UPDATE costeo_config SET valor='40' WHERE clave='pct_platos_llevar'")
    k = KardexController(db)
    rid = E.dia_ventas(db, E.FECHA_VENTA, [(esc.p1, 10), (esc.p2, 20)])
    k.procesar_ventas_diarias(rid)
    # P1 lleva envase solo para llevar: 10 × 40 % = 4 -> 50 - 4
    assert _stock(db, esc.envase) == approx(46)
    assert _stock(db, esc.soda) == approx(24)
    assert _stock(db, esc.pollo) == approx(9000)
    _invariante_kardex(db, esc)
    k.revertir_ventas_diarias(rid)
    assert _stock(db, esc.envase) == approx(50)


def test_sin_pct_para_llevar_no_se_descuentan_empaques(db, esc, recibir):
    recibir(db, esc.compra)
    KardexController(db).procesar_ventas_diarias(E.dia_ventas(db, E.FECHA_VENTA, [(esc.p1, 10)]))
    assert _stock(db, esc.envase) == approx(50)


def test_conteo_ajusta_por_diferencia(db, esc, recibir):
    recibir(db, esc.compra)
    KardexController(db).procesar_ventas_diarias(E.dia_ventas(db, E.FECHA_VENTA, [(esc.p1, 10), (esc.p2, 20)]))
    # Teórico 20 500 g, contado 20 400 g -> ajuste de -100 g
    _registrar_ajuste_kardex(db, esc.arroz, 20400 - _stock(db, esc.arroz), 1, "merma")
    assert _stock(db, esc.arroz) == approx(20400)
    mov = db.fetch_one("SELECT cantidad, stock_anterior, stock_nuevo FROM movimientos_inventario "
                       "WHERE tipo_movimiento='AJUSTE_INVENTARIO'")
    assert mov == (approx(-100), approx(20500), approx(20400))
    _invariante_kardex(db, esc)


def test_abastecimiento_envio_y_anulacion(db, esc, recibir):
    recibir(db, esc.compra)
    ctrl = AbastecimientoController(db)
    res = ctrl.registrar("2026-05-11", esc.suc_centro, esc.suc_norte, [(esc.pollo, 1000, esc.g)])
    assert res["efecto"] == "SALIDA"
    assert _stock(db, esc.pollo) == approx(14000)
    ctrl.anular(res["id"])
    assert _stock(db, esc.pollo) == approx(15000)
    _invariante_kardex(db, esc)


def test_promedio_ponderado_con_stock_negativo(db, esc, recibir):
    # H5: se vendieron 1 000 g de pollo antes de recibir: stock -1 000 g con costo anterior 0.004
    db.execute_query("UPDATE insumos SET stock_actual=-1000, costo_unitario=0.004 WHERE id=?", (esc.pollo,))
    esc.stock_inicial[esc.pollo] = -1000.0
    cid = E.compra(db, esc.proveedor, [(esc.p_pollo, 1, 30.00)])  # 5 000 g a 0.006
    recibir(db, cid)
    # Sin stock real que promediar, el costo es el de la compra (antes daba 0.0065)
    assert _costo(db, esc.pollo) == approx(0.006)
    assert _stock(db, esc.pollo) == approx(4000)
    _invariante_kardex(db, esc)


def test_recepcion_es_atomica(db, esc, monkeypatch):
    # H15: si falla una línea a mitad, no queda nada aplicado y la compra sigue PENDIENTE
    original = KardexController._aplicar
    llamadas = []

    def _falla_en_la_segunda(self, *a, **k):
        llamadas.append(1)
        if len(llamadas) == 2:
            raise RuntimeError("falla simulada")
        return original(self, *a, **k)

    monkeypatch.setattr(KardexController, "_aplicar", _falla_en_la_segunda)
    detalles = [r[0] for r in db.fetch_all("SELECT id FROM detalle_compras WHERE compra_id=?", (esc.compra,))]
    with pytest.raises(RuntimeError):
        KardexController(db).recibir_compra(esc.compra, {d: 1 for d in detalles})
    assert _stock(db, esc.arroz) == approx(5000) and _costo(db, esc.arroz) == approx(0.0010)
    assert db.fetch_one("SELECT COUNT(*) FROM movimientos_inventario")[0] == 0
    assert db.fetch_one("SELECT estado FROM compras WHERE id=?", (esc.compra,))[0] == "PENDIENTE"


def test_recepcion_parcial(db, esc):
    # Llega 1 de los 2 sacos de arroz y nada de lo demás
    det_arroz = db.fetch_one("SELECT id FROM detalle_compras WHERE compra_id=? AND presentacion_id=?",
                             (esc.compra, esc.p_arroz))[0]
    KardexController(db).recibir_compra(esc.compra, {det_arroz: 1})
    # (5 000 × 0.0010 + 10 000 × 0.0012) / 15 000, guardado con 6 decimales
    assert _stock(db, esc.arroz) == approx(15000)
    assert _costo(db, esc.arroz) == approx(17 / 15000, abs=1e-6)
    assert _stock(db, esc.pollo) == 0
    with pytest.raises(ValueError):
        KardexController(db).recibir_compra(esc.compra, {det_arroz: 1})

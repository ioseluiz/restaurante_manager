import pytest

from app.controllers.kardex_controller import KardexController
from app.database.connection import DatabaseManager


@pytest.fixture
def db(tmp_path):
    return DatabaseManager(str(tmp_path / "t.db"))


def _g(db):
    return db.execute_query("INSERT INTO unidades_medida (nombre, abreviatura) VALUES ('Gramo','g')").lastrowid


def _insumo(db, nombre, g, stock):
    return db.execute_query(
        "INSERT INTO insumos (nombre, unidad_base_id, stock_actual) VALUES (?,?,?)", (nombre, g, stock)
    ).lastrowid


def _plato(db, codigo, nombre, **extra):
    iid = db.execute_query(
        "INSERT INTO menu_items (codigo, nombre, precio_venta) VALUES (?,?,5)", (codigo, nombre)
    ).lastrowid
    for k, v in extra.items():
        db.execute_query(f"UPDATE menu_items SET {k}=? WHERE id=?", (v, iid))
    return iid


def _receta(db, plato, insumo, cant):
    db.execute_query(
        "INSERT INTO recetas (menu_item_id, insumo_id, cantidad_necesaria) VALUES (?,?,?)", (plato, insumo, cant)
    )


def _dia(db, ventas, fecha="2026-05-10", procesado=0):
    rid = db.execute_query(
        "INSERT INTO registro_ventas_diarias (fecha, inventario_descontado) VALUES (?,?)", (fecha, procesado)
    ).lastrowid
    for plato, cant in ventas:
        db.execute_query(
            "INSERT INTO detalle_ventas_diarias (registro_diario_id, menu_item_id, cantidad) VALUES (?,?,?)",
            (rid, plato, cant),
        )
    return rid


def _stock(db, insumo):
    return db.fetch_one("SELECT stock_actual FROM insumos WHERE id=?", (insumo,))[0]


def test_descuenta_por_receta_y_suma_por_insumo(db):
    g = _g(db)
    carne, sal = _insumo(db, "Carne", g, 10000), _insumo(db, "Sal", g, 500)
    a, b = _plato(db, "1", "Bistec"), _plato(db, "2", "Lomo")
    _receta(db, a, carne, 200); _receta(db, a, sal, 5)
    _receta(db, b, carne, 300)
    rid = _dia(db, [(a, 10), (b, 4)])
    r = KardexController(db).procesar_ventas_diarias(rid)
    assert _stock(db, carne) == pytest.approx(10000 - 10 * 200 - 4 * 300)
    assert _stock(db, sal) == pytest.approx(500 - 50)
    assert r["movimientos"] == 2 and r["sin_receta"] == [] and r["negativos"] == []
    # un solo movimiento VENTA por insumo, con referencia al registro del día
    filas = db.fetch_all("SELECT insumo_id, tipo_movimiento, referencia_id FROM movimientos_inventario "
                         "ORDER BY insumo_id")
    assert sorted(filas) == sorted([(carne, "VENTA", rid), (sal, "VENTA", rid)])
    assert db.fetch_one("SELECT inventario_descontado FROM registro_ventas_diarias WHERE id=?", (rid,))[0] == 1


def test_receta_por_tanda_y_subreceta(db):
    g = _g(db)
    carne, ajo = _insumo(db, "Carne", g, 10000), _insumo(db, "Ajo", g, 1000)
    chimi = _plato(db, "#205", "Chimichurri", es_componente=1, rendimiento=400, unidad_rendimiento_id=g)
    _receta(db, chimi, ajo, 100)                                       # 0.25 g de ajo por g de chimichurri
    lomo = _plato(db, "30", "Lomo", rendimiento=2000, unidad_rendimiento_id=g,
                  porcion_servida=200, unidad_porcion_id=g)            # factor 0.1
    _receta(db, lomo, carne, 2000)
    db.execute_query("INSERT INTO receta_componentes (menu_item_id, componente_id, cantidad, unidad_id) "
                     "VALUES (?,?,?,?)", (lomo, chimi, 570, g))
    rid = _dia(db, [(lomo, 5)])
    KardexController(db).procesar_ventas_diarias(rid)
    assert _stock(db, carne) == pytest.approx(10000 - 5 * 200)
    assert _stock(db, ajo) == pytest.approx(1000 - 5 * (570 * 0.1 * 100 / 400))


def test_no_se_puede_procesar_dos_veces(db):
    g = _g(db)
    carne = _insumo(db, "Carne", g, 1000)
    a = _plato(db, "1", "Bistec"); _receta(db, a, carne, 100)
    rid = _dia(db, [(a, 1)])
    k = KardexController(db)
    k.procesar_ventas_diarias(rid)
    with pytest.raises(ValueError):
        k.procesar_ventas_diarias(rid)
    assert _stock(db, carne) == pytest.approx(900)


def test_avisa_platos_sin_receta_e_insumos_negativos(db):
    g = _g(db)
    carne = _insumo(db, "Carne", g, 100)
    a, sin = _plato(db, "1", "Bistec"), _plato(db, "2", "Soda")
    _receta(db, a, carne, 100)
    rid = _dia(db, [(a, 3), (sin, 5)])
    r = KardexController(db).procesar_ventas_diarias(rid)
    assert r["sin_receta"] == ["Soda"] and r["negativos"] == ["Carne"]
    assert _stock(db, carne) == pytest.approx(-200)


def test_reabrir_repone_exactamente_y_permite_reprocesar(db):
    g = _g(db)
    carne = _insumo(db, "Carne", g, 1000)
    a = _plato(db, "1", "Bistec"); _receta(db, a, carne, 100)
    rid = _dia(db, [(a, 4)])
    k = KardexController(db)
    k.procesar_ventas_diarias(rid)
    assert _stock(db, carne) == pytest.approx(600)
    assert k.revertir_ventas_diarias(rid) == 1
    assert _stock(db, carne) == pytest.approx(1000)
    assert db.fetch_one("SELECT inventario_descontado FROM registro_ventas_diarias WHERE id=?", (rid,))[0] == 0
    # se corrige la cantidad y se reprocesa; revertir de nuevo repone solo lo último
    db.execute_query("UPDATE detalle_ventas_diarias SET cantidad=6 WHERE registro_diario_id=?", (rid,))
    k.procesar_ventas_diarias(rid)
    assert _stock(db, carne) == pytest.approx(400)
    k.revertir_ventas_diarias(rid)
    assert _stock(db, carne) == pytest.approx(1000)
    tipos = [t for (t,) in db.fetch_all("SELECT tipo_movimiento FROM movimientos_inventario ORDER BY id")]
    assert tipos == ["VENTA", "REVERSO_VENTA", "VENTA", "REVERSO_VENTA"]


def test_dia_marcado_por_la_simulacion_antigua_solo_pierde_la_marca(db):
    g = _g(db)
    carne = _insumo(db, "Carne", g, 1000)
    a = _plato(db, "1", "Bistec"); _receta(db, a, carne, 100)
    rid = _dia(db, [(a, 4)], procesado=1)          # marcado sin movimientos
    assert KardexController(db).revertir_ventas_diarias(rid) == 0
    assert _stock(db, carne) == pytest.approx(1000)
    assert db.fetch_one("SELECT inventario_descontado FROM registro_ventas_diarias WHERE id=?", (rid,))[0] == 0


def test_revertir_un_dia_no_procesado_es_error(db):
    rid = _dia(db, [])
    with pytest.raises(ValueError):
        KardexController(db).revertir_ventas_diarias(rid)

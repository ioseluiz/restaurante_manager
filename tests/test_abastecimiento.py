import pytest

from app.controllers.abastecimiento_controller import AbastecimientoController
from app.database.connection import DatabaseManager


@pytest.fixture
def ctx(tmp_path):
    db = DatabaseManager(str(tmp_path / "t.db"))
    g = db.execute_query("INSERT INTO unidades_medida (nombre, abreviatura) VALUES ('Gramo','g')").lastrowid
    suc = lambda n, local=0: db.execute_query(
        "INSERT INTO sucursales (nombre, es_principal) VALUES (?,?)", (n, local)).lastrowid
    aqui, otra, tercera = suc("Central", 1), suc("Local A"), suc("Local B")
    carne = db.execute_query("INSERT INTO insumos (nombre, unidad_base_id, stock_actual, costo_unitario) "
                             "VALUES ('Carne',?,1000,0.01)", (g,)).lastrowid
    return db, AbastecimientoController(db), g, aqui, otra, tercera, carne


def _stock(db, i):
    return db.fetch_one("SELECT stock_actual FROM insumos WHERE id=?", (i,))[0]


def _tipos(db):
    return [t for (t,) in db.fetch_all("SELECT tipo_movimiento FROM movimientos_inventario ORDER BY id")]


def test_enviar_resta_y_registra_en_el_kardex(ctx):
    db, c, g, aqui, otra, _t, carne = ctx
    r = c.registrar("2026-05-01", aqui, otra, [(carne, 300, g)])
    assert r["efecto"] == "SALIDA" and r["negativos"] == []
    assert _stock(db, carne) == pytest.approx(700)
    fila = db.fetch_one("SELECT tipo_movimiento, cantidad, referencia_id, observacion FROM movimientos_inventario")
    assert fila == ("TRASLADO_SALIDA", -300.0, r["id"], "Traslado a Local A")


def test_recibir_suma_sin_cambiar_el_costo(ctx):
    db, c, g, aqui, otra, _t, carne = ctx
    r = c.registrar("2026-05-01", otra, aqui, [(carne, 200, g)])
    assert r["efecto"] == "ENTRADA" and _stock(db, carne) == pytest.approx(1200)
    assert _tipos(db) == ["TRASLADO_ENTRADA"]
    assert db.fetch_one("SELECT costo_unitario FROM insumos WHERE id=?", (carne,))[0] == pytest.approx(0.01)


def test_un_traslado_que_no_involucra_a_esta_sucursal_se_rechaza(ctx):
    db, c, g, aqui, otra, tercera, carne = ctx
    with pytest.raises(ValueError, match="no involucra"):
        c.registrar("2026-05-01", otra, tercera, [(carne, 10, g)])
    assert db.fetch_one("SELECT COUNT(*) FROM abastecimiento_interno")[0] == 0
    assert _stock(db, carne) == pytest.approx(1000)


def test_sin_sucursal_local_configurada_pide_configurarla(ctx):
    db, c, g, aqui, otra, _t, carne = ctx
    db.execute_query("UPDATE sucursales SET es_principal = 0")
    with pytest.raises(ValueError, match="marcada"):
        c.registrar("2026-05-01", aqui, otra, [(carne, 10, g)])
    assert c.sucursal_local() is None and c.efecto(aqui, otra) is None


def test_validaciones_basicas(ctx):
    db, c, g, aqui, otra, _t, carne = ctx
    with pytest.raises(ValueError):
        c.registrar("2026-05-01", aqui, aqui, [(carne, 1, g)])
    with pytest.raises(ValueError):
        c.registrar("2026-05-01", aqui, otra, [])
    with pytest.raises(ValueError):
        c.registrar("2026-05-01", aqui, otra, [(carne, 0, g)])


def test_avisa_stock_insuficiente_pero_permite_continuar(ctx):
    db, c, g, aqui, otra, _t, carne = ctx
    assert c.revisar_stock(aqui, otra, [(carne, 1500, g)]) == [("Carne", 1000.0, 1500.0)]
    assert c.revisar_stock(otra, aqui, [(carne, 1500, g)]) == []          # recibir nunca falta stock
    r = c.registrar("2026-05-01", aqui, otra, [(carne, 1500, g)])
    assert r["negativos"] == ["Carne"] and _stock(db, carne) == pytest.approx(-500)


def test_anular_repone_y_no_borra_el_registro(ctx):
    db, c, g, aqui, otra, _t, carne = ctx
    r = c.registrar("2026-05-01", aqui, otra, [(carne, 300, g)])
    assert c.anular(r["id"]) == 1
    assert _stock(db, carne) == pytest.approx(1000)
    assert _tipos(db) == ["TRASLADO_SALIDA", "REVERSO_TRASLADO"]
    est = db.fetch_one("SELECT estado, anulado_en FROM abastecimiento_interno WHERE id=?", (r["id"],))
    assert est[0] == "ANULADO" and est[1] is not None
    with pytest.raises(ValueError, match="ya está anulado"):
        c.anular(r["id"])


def test_anular_una_entrada_resta(ctx):
    db, c, g, aqui, otra, _t, carne = ctx
    r = c.registrar("2026-05-01", otra, aqui, [(carne, 200, g)])
    c.anular(r["id"])
    assert _stock(db, carne) == pytest.approx(1000)


def test_anular_un_traslado_de_la_version_anterior_sin_movimientos(ctx):
    db, c, g, aqui, otra, _t, carne = ctx
    # lo que dejaba la versión anterior: registro + detalle + stock ya modificado, sin Kardex
    aid = db.execute_query("INSERT INTO abastecimiento_interno (fecha, sucursal_origen_id, sucursal_destino_id) "
                           "VALUES ('2026-04-01', ?, ?)", (aqui, otra)).lastrowid
    db.execute_query("INSERT INTO detalle_abastecimiento (abastecimiento_id, insumo_id, cantidad, unidad_id) "
                     "VALUES (?,?,?,?)", (aid, carne, 100, g))
    db.execute_query("UPDATE insumos SET stock_actual = 900 WHERE id=?", (carne,))
    assert c.anular(aid) == 1
    assert _stock(db, carne) == pytest.approx(1000)
    assert _tipos(db) == ["REVERSO_TRASLADO"]


def test_listado_y_detalle(ctx):
    db, c, g, aqui, otra, tercera, carne = ctx
    c.registrar("2026-05-01", aqui, otra, [(carne, 300, g)])
    c.registrar("2026-05-02", otra, aqui, [(carne, 50, g)])
    filas = c.listar()
    assert [(f[2], f[3], f[4], f[5]) for f in filas] == [
        ("Local A", "Central", "ENTRADA", "COMPLETADO"), ("Central", "Local A", "SALIDA", "COMPLETADO")]
    assert c.detalle(filas[1][0]) == [("Carne", 300.0, "g")]

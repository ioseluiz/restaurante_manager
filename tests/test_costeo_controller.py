import pytest

from app.controllers.costeo_controller import CosteoController, margen, precio_sugerido
from app.database.connection import DatabaseManager


@pytest.fixture
def db(tmp_path):
    return DatabaseManager(str(tmp_path / "t.db"))


def _unidad(db, nombre, abrev):
    return db.execute_query(
        "INSERT INTO unidades_medida (nombre, abreviatura) VALUES (?,?)", (nombre, abrev)
    ).lastrowid


def _insumo(db, nombre, unidad_id, costo):
    return db.execute_query(
        "INSERT INTO insumos (nombre, unidad_base_id, costo_unitario) VALUES (?,?,?)",
        (nombre, unidad_id, costo),
    ).lastrowid


def _item(db, codigo, nombre, precio=0.0, **extra):
    iid = db.execute_query(
        "INSERT INTO menu_items (codigo, nombre, precio_venta) VALUES (?,?,?)",
        (codigo, nombre, precio),
    ).lastrowid
    for k, v in extra.items():
        db.execute_query(f"UPDATE menu_items SET {k} = ? WHERE id = ?", (v, iid))
    return iid


def _receta(db, item, insumo, cant, unidad=None):
    db.execute_query(
        "INSERT INTO recetas (menu_item_id, insumo_id, cantidad_necesaria, unidad_id) VALUES (?,?,?,?)",
        (item, insumo, cant, unidad),
    )


@pytest.fixture
def base(db):
    g, kg = _unidad(db, "Gramo", "g"), _unidad(db, "Kilogramo", "kg")
    return db, g, kg


def test_receta_por_porcion_sin_rendimiento_no_cambia(base):
    db, g, _ = base
    pollo = _insumo(db, "Pollo", g, 0.01)
    plato = _item(db, "1", "Pollo frito", 5.0)
    _receta(db, plato, pollo, 300)
    c = CosteoController(db)
    assert c.factor_por_porcion(plato) == 1.0
    assert c.costo_ingredientes(plato)["total"] == pytest.approx(3.0)


def test_receta_por_tanda_costo_por_porcion(base):
    db, g, _ = base
    carne = _insumo(db, "Carne", g, 0.01)
    salsa = _insumo(db, "Salsa", g, 0.002)
    # tanda: 2000 g carne + 1000 g salsa = 22; rinde 3000 g; se sirven 200 g
    plato = _item(db, "30", "Lomo", 6.0, rendimiento=3000, unidad_rendimiento_id=g,
                  porcion_servida=200, unidad_porcion_id=g)
    _receta(db, plato, carne, 2000)
    _receta(db, plato, salsa, 1000)
    c = CosteoController(db)
    assert c.costo_tanda(plato)["total"] == pytest.approx(22.0)
    assert c.factor_por_porcion(plato) == pytest.approx(200 / 3000)
    assert c.costo_ingredientes(plato)["total"] == pytest.approx(22.0 * 200 / 3000)


def test_conversion_unidades_kg_a_g(base):
    db, g, kg = base
    harina = _insumo(db, "Harina", g, 0.004)
    plato = _item(db, "2", "Pan")
    _receta(db, plato, harina, 0.5, unidad=kg)  # 0.5 kg = 500 g
    assert CosteoController(db).costo_ingredientes(plato)["total"] == pytest.approx(2.0)


def test_subreceta_costo_por_unidad_y_uso_en_plato(base):
    db, g, _ = base
    ajo = _insumo(db, "Ajo", g, 0.01)
    aceite = _insumo(db, "Aceite", g, 0.005)
    # chimichurri: 100 g ajo + 300 g aceite = 2.5, rinde 400 g => 0.00625/g
    chimi = _item(db, "#205", "Chimichurri", 0, es_componente=1, rendimiento=400,
                  unidad_rendimiento_id=g)
    _receta(db, chimi, ajo, 100)
    _receta(db, chimi, aceite, 300)
    pollo = _insumo(db, "Pollo", g, 0.01)
    plato = _item(db, "1", "Combo 1", 8.0)
    _receta(db, plato, pollo, 200)  # 2.0
    db.execute_query(
        "INSERT INTO receta_componentes (menu_item_id, componente_id, cantidad, unidad_id) VALUES (?,?,?,?)",
        (plato, chimi, 57, g),
    )
    c = CosteoController(db)
    assert c.costo_por_unidad_componente(chimi)[0] == pytest.approx(0.00625)
    assert c.costo_ingredientes(plato)["total"] == pytest.approx(2.0 + 57 * 0.00625)


def test_ciclo_de_subrecetas_no_cuelga(base):
    db, g, _ = base
    a = _item(db, "A", "A", es_componente=1, rendimiento=1, unidad_rendimiento_id=g)
    b = _item(db, "B", "B", es_componente=1, rendimiento=1, unidad_rendimiento_id=g)
    for x, y in ((a, b), (b, a)):
        db.execute_query(
            "INSERT INTO receta_componentes (menu_item_id, componente_id, cantidad, unidad_id) VALUES (?,?,?,?)",
            (x, y, 1, g),
        )
    r = CosteoController(db).costo_plato(a)
    assert any("Ciclo" in adv for adv in r["advertencias"])


def test_insumo_sin_costo_y_sin_receta_generan_advertencias(base):
    db, g, _ = base
    sal = _insumo(db, "Sal", g, 0)
    plato = _item(db, "3", "Sopa")
    vacio = _item(db, "4", "Vacio")
    _receta(db, plato, sal, 5)
    c = CosteoController(db)
    assert any("sin costo" in a for a in c.costo_plato(plato)["advertencias"])
    assert "Sin receta" in c.costo_plato(vacio)["advertencias"]


def test_extras_por_canal_y_total_con_indirecto(base):
    db, g, _ = base
    arroz_i = _insumo(db, "Arroz", g, 0.002)
    caja_i = _insumo(db, "Fiambrera", g, 0.25)
    pollo_i = _insumo(db, "Pollo", g, 0.01)
    arroz = _item(db, "#99", "Arroz", es_componente=1)
    caja = _item(db, "#E1", "Fiambrera", es_componente=1)
    plato = _item(db, "5", "Arroz con pollo", 6.0)
    _receta(db, arroz, arroz_i, 100)  # 0.20
    _receta(db, caja, caja_i, 1)      # 0.25
    _receta(db, plato, pollo_i, 300)  # 3.00
    for comp, tipo, canal in ((arroz, "ACOMPANAMIENTO", "AMBOS"), (caja, "EMPAQUE", "LLEVAR")):
        db.execute_query(
            "INSERT INTO plato_extras (menu_item_id, componente_id, cantidad_porciones, tipo, canal) VALUES (?,?,?,?,?)",
            (plato, comp, 1, tipo, canal),
        )
    c = CosteoController(db)
    local = c.costo_plato(plato, "LOCAL", indirecto=0.5)
    llevar = c.costo_plato(plato, "LLEVAR", indirecto=0.5)
    assert local["empaque"] == 0 and local["total"] == pytest.approx(3.0 + 0.2 + 0.5)
    assert llevar["empaque"] == pytest.approx(0.25)
    assert llevar["total"] == pytest.approx(3.0 + 0.2 + 0.25 + 0.5)
    # 30% ganancia local: precio = costo / 0.7
    assert local["precio_sugerido"] == pytest.approx(3.7 / 0.7)
    # canal LLEVAR usa pct_ganancia_pedidosya = 50 => costo / 0.5
    assert llevar["precio_sugerido"] == pytest.approx(3.95 / 0.5)


def test_fuente_costo_promedio_vs_vigente(base):
    db, g, _ = base
    ins = _insumo(db, "Papa", g, 0.02)  # WAC
    pid = db.execute_query(
        "INSERT INTO presentaciones_compra (insumo_id, nombre, cantidad_contenido, precio_compra, costo_unitario_calculado) "
        "VALUES (?,?,?,?,?)", (ins, "Saco", 1000, 10.0, 0.01)).lastrowid
    assert pid
    c = CosteoController(db)
    assert c.costo_unitario_insumo(ins)[0] == pytest.approx(0.01)  # VIGENTE por defecto
    db.execute_query("UPDATE costeo_config SET valor='PROMEDIO' WHERE clave='fuente_costo_insumo'")
    c.limpiar_cache()
    assert c.costo_unitario_insumo(ins)[0] == pytest.approx(0.02)


def test_pool_indirectos_usa_promedio_configurado_sin_ventas(db):
    r = CosteoController(db).pool_indirectos(5, 2026)
    assert r["fuente_platos"] == "promedio configurado"
    assert r["platos"] == 198 * 30
    assert r["por_plato"] == 0.0


def test_precio_sugerido_y_margen():
    assert precio_sugerido(0.75, 25) == pytest.approx(1.0)
    assert precio_sugerido(1, 100) is None
    m, fc, mp = margen(5.0, 2.0)
    assert (m, fc, mp) == (3.0, 40.0, 60.0)
    assert margen(0, 2.0) == (None, None, None)


# ---------------------------------------------------------------- regresión
# Los consumidores legados de `recetas` deben aplicar el factor tanda->porción.
def _venta(db, item, cantidad, fecha="2026-05-10"):
    rid = db.execute_query(
        "INSERT INTO registro_ventas_diarias (fecha) VALUES (?)", (fecha,)).lastrowid
    db.execute_query(
        "INSERT INTO detalle_ventas_diarias (registro_diario_id, menu_item_id, cantidad) VALUES (?,?,?)",
        (rid, item, cantidad))


def test_rentabilidad_costo_teorico_respeta_tanda(base):
    from app.controllers.rentabilidad_controller import RentabilidadController
    db, g, _ = base
    carne = _insumo(db, "Carne", g, 0.01)
    porcion = _item(db, "1", "Por porcion", 5.0)
    _receta(db, porcion, carne, 200)                       # 2.00 por plato
    tanda = _item(db, "2", "Por tanda", 5.0, rendimiento=2000, unidad_rendimiento_id=g,
                  porcion_servida=200, unidad_porcion_id=g)
    _receta(db, tanda, carne, 2000)                        # 20.00 la tanda => 2.00 por plato
    _venta(db, porcion, 10)
    _venta(db, tanda, 10, "2026-05-11")
    assert RentabilidadController(db).costo_teorico_mes(2026, 5) == pytest.approx(40.0)


def test_vista_explotada_aplica_tanda_y_subrecetas(base):
    db, g, _ = base
    ajo = _insumo(db, "Ajo", g, 0.01)
    aceite = _insumo(db, "Aceite", g, 0.005)
    carne = _insumo(db, "Carne", g, 0.01)
    # chimichurri: 100 g ajo + 300 g aceite, rinde 400 g
    chimi = _item(db, "#205", "Chimichurri", 0, es_componente=1, rendimiento=400, unidad_rendimiento_id=g)
    _receta(db, chimi, ajo, 100)
    _receta(db, chimi, aceite, 300)
    # lomo por tanda: 2000 g carne rinde 2000, porción 200 (=> factor 0.1) + 57 g chimichurri por tanda
    lomo = _item(db, "30", "Lomo", 6.0, rendimiento=2000, unidad_rendimiento_id=g,
                 porcion_servida=200, unidad_porcion_id=g)
    _receta(db, lomo, carne, 2000)
    db.execute_query(
        "INSERT INTO receta_componentes (menu_item_id, componente_id, cantidad, unidad_id) VALUES (?,?,?,?)",
        (lomo, chimi, 570, g))
    filas = dict(db.fetch_all(
        "SELECT insumo_id, cantidad_necesaria FROM v_recetas_explotadas WHERE menu_item_id = ?", (lomo,)))
    assert filas[carne] == pytest.approx(200.0)                  # 2000 * 0.1
    assert filas[ajo] == pytest.approx(570 * 0.1 * 100 / 400)    # 14.25 g
    assert filas[aceite] == pytest.approx(570 * 0.1 * 300 / 400)  # 42.75 g
    # coherencia con el costo calculado en Python
    costo_sql = sum(cant * CosteoController(db).costo_unitario_insumo(i)[0] for i, cant in filas.items())
    assert costo_sql == pytest.approx(CosteoController(db).costo_ingredientes(lomo)["total"])


def test_vista_explotada_no_cuelga_con_ciclos(base):
    db, g, _ = base
    x = _insumo(db, "X", g, 1)
    a = _item(db, "A", "A", es_componente=1, rendimiento=1, unidad_rendimiento_id=g)
    b = _item(db, "B", "B", es_componente=1, rendimiento=1, unidad_rendimiento_id=g)
    _receta(db, a, x, 1)
    for u, v in ((a, b), (b, a)):
        db.execute_query(
            "INSERT INTO receta_componentes (menu_item_id, componente_id, cantidad, unidad_id) VALUES (?,?,?,?)",
            (u, v, 1, g))
    assert db.fetch_all("SELECT * FROM v_recetas_explotadas WHERE menu_item_id = ?", (a,))

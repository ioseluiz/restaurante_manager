import os

import pytest

from app.controllers.costeo_controller import CosteoController
from app.database.connection import DatabaseManager
from app.utils.importar_costeo_excel import clave_palabras, importar, norm

EXCEL_CLIENTE = "D:/italos/PLANILLA_COSTO_PLATOS/COSTEO DE  PLATOS Y SUS INSUMOS.xlsx"


@pytest.fixture
def db(tmp_path):
    return DatabaseManager(str(tmp_path / "t.db"))


def _excel(tmp_path, filas):
    """filas: (cat, nombre, cod, cod_ins, insumo, cant, unidad, costo, J, K, L, M)"""
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "PLATOS CODIGOS Y RECETAS "
    ws.append(["CATEGORIA", "MENU", "CODIGO", "INSUMO CODIGO", "INSUMO", "CANT", "U", "COSTO UNI",
               "SUB", "TOTAL", "COST X U", "CANT SERVIDA", "U2", "TOTAL CS"])
    for cat, nom, cod, cins, ins, cant, u, costo, j, k, l, m in filas:
        ws.append([cat, nom, cod, cins, ins, cant, u, costo, None, j, k, l, m, None])
    ruta = str(tmp_path / "costeo.xlsx")
    wb.save(ruta)
    return ruta


def _demo(tmp_path):
    # chimichurri (componente): 100 g ajo + 300 g aceite = 2.5, rinde 400 g
    # lomo (por tanda): 2000 g carne + 570 g de chimichurri, rinde 2570, porción 200 g
    return _excel(tmp_path, [
        ("complementos", "chimichurri", "#205", "#V002", "Ajo", 100, "g", 0.01, 2.5, 2.5 / 400, None, None),
        ("complementos", "chimichurri", "#205", "#IC001", "Aceite", 300, "g", 0.005, None, None, None, None),
        ("baño maria", "lomo", "# 30", "#C014", "Carne", 2000, "g", 0.01, 25.0, 25.0 / 2570, 200, "g"),
        ("baño maria", "lomo", "# 30", "#205", "chimichurri", 570, "g", None, None, None, None, None),
    ])


def _unidad_g(db):
    return db.execute_query("INSERT INTO unidades_medida (nombre, abreviatura) VALUES ('Gramo','g')").lastrowid


def test_norm_y_clave_palabras():
    assert norm("  Baño   María ") == "bano maria"
    assert clave_palabras("consome pollo") == clave_palabras("Consome De Pollo")


def test_dry_run_no_guarda_nada(db, tmp_path):
    r = importar(db, _demo(tmp_path), dry_run=True, crear_insumos=True)
    assert r.recetas_importadas == 2 and r.dry_run
    for t in ("menu_items", "insumos", "recetas", "receta_componentes"):
        assert db.fetch_one(f"SELECT COUNT(*) FROM {t}")[0] == 0


def test_importa_tanda_componente_y_costo(db, tmp_path):
    r = importar(db, _demo(tmp_path), dry_run=False, crear_insumos=True, completar_costos=True)
    assert r.recetas_importadas == 2 and r.insumos_creados == 3
    lomo = db.fetch_one("SELECT id, rendimiento, porcion_servida, es_componente, categoria_costeo "
                        "FROM menu_items WHERE nombre='lomo'")
    assert lomo[1] == pytest.approx(2570) and lomo[2] == 200 and lomo[3] == 0 and lomo[4] == "plato"
    chimi = db.fetch_one("SELECT id, codigo, es_componente, rendimiento FROM menu_items WHERE nombre='chimichurri'")
    assert chimi[1] == "#205" and chimi[2] == 1 and chimi[3] == pytest.approx(400)
    assert db.fetch_one("SELECT cantidad FROM receta_componentes WHERE menu_item_id=? AND componente_id=?",
                        (lomo[0], chimi[0]))[0] == 570
    esperado = (2000 * 0.01 + 570 * (2.5 / 400)) * 200 / 2570
    assert CosteoController(db).costo_ingredientes(lomo[0])["total"] == pytest.approx(esperado)
    # la vista explotada (compras/stock) ve los insumos de la sub-receta
    ajo = db.fetch_one("SELECT id FROM insumos WHERE nombre='Ajo'")[0]
    cant = db.fetch_one("SELECT cantidad_necesaria FROM v_recetas_explotadas WHERE menu_item_id=? AND insumo_id=?",
                        (lomo[0], ajo))[0]
    assert cant == pytest.approx(570 * (200 / 2570) * 100 / 400)


def test_insumo_sin_resolver_bloquea_la_receta(db, tmp_path):
    r = importar(db, _demo(tmp_path), dry_run=False, crear_insumos=False)
    assert r.recetas_importadas == 0
    assert any(n == "ERROR" and "Ajo" in m for n, _, m in r.problemas)
    assert db.fetch_one("SELECT COUNT(*) FROM recetas")[0] == 0  # nunca a medias


def test_no_sobrescribe_salvo_reemplazar(db, tmp_path):
    ruta = _demo(tmp_path)
    importar(db, ruta, dry_run=False, crear_insumos=True)
    db.execute_query("UPDATE recetas SET cantidad_necesaria = 1 WHERE insumo_id = "
                     "(SELECT id FROM insumos WHERE nombre='Carne')")
    r2 = importar(db, ruta, dry_run=False, crear_insumos=True)
    assert r2.recetas_importadas == 0 and r2.recetas_omitidas == 2
    q = ("SELECT cantidad_necesaria FROM recetas r JOIN insumos i ON i.id=r.insumo_id WHERE i.nombre='Carne'")
    assert db.fetch_one(q)[0] == 1
    r3 = importar(db, ruta, dry_run=False, crear_insumos=True, reemplazar=True)
    assert r3.recetas_importadas == 2
    assert db.fetch_one(q)[0] == 2000


def test_insumo_existente_por_mismas_palabras_y_costo_completado(db, tmp_path):
    g = _unidad_g(db)
    db.execute_query("INSERT INTO insumos (nombre, unidad_base_id, costo_unitario) VALUES ('Consome De Pollo', ?, 0)", (g,))
    ruta = _excel(tmp_path, [("baño maria", "sopa", "# 1", None, "consome pollo", 10, "g", 0.02, 1.0, 0.1, 100, "g")])
    r = importar(db, ruta, dry_run=False, crear_insumos=True, completar_costos=True)
    assert r.insumos_creados == 0 and r.costos_completados == 1
    assert db.fetch_one("SELECT costo_unitario FROM insumos")[0] == pytest.approx(0.02)


def test_abreviatura_no_se_duplica_pero_nombre_mas_especifico_si_se_crea(db, tmp_path):
    g = _unidad_g(db)
    db.execute_query("INSERT INTO insumos (nombre, unidad_base_id) VALUES ('Aceite Veg', ?)", (g,))
    ruta = _excel(tmp_path, [("baño maria", "arroz", "# 1", None, "aceite", 10, "g", 0.02, None, None, None, None),
                             ("baño maria", "pasta", "# 2", None, "Aceite Veg roja", 10, "g", 0.02, None, None, None, None)])
    r = importar(db, ruta, dry_run=False, crear_insumos=True)
    assert r.insumos_creados == 1  # «Aceite Veg roja» es más específico => otro producto
    assert any(n == "ERROR" and "abreviatura" in m for n, _, m in r.problemas)  # «aceite» requiere decisión


def test_codigo_repetido_es_conflicto(db, tmp_path):
    ruta = _excel(tmp_path, [("bebidas", "chicha a", "# 305", None, "Agua", 1, "ml", 0.001, None, None, None, None),
                             ("bebidas", "chicha b", "# 305", None, "Agua", 1, "ml", 0.001, None, None, None, None)])
    r = importar(db, ruta, dry_run=False, crear_insumos=True)
    assert any(n == "ERROR" and "305" in m for n, _, m in r.problemas)
    assert db.fetch_one("SELECT COUNT(*) FROM menu_items")[0] == 1


@pytest.mark.skipif(not os.path.exists(EXCEL_CLIENTE), reason="Excel del cliente no disponible")
def test_golden_excel_del_cliente(db):
    """Con los costos del propio Excel, los platos sin referencias cruzadas coinciden con sus valores cacheados."""
    import openpyxl
    r = importar(db, EXCEL_CLIENTE, dry_run=False, crear_insumos=True, completar_costos=True)
    assert r.recetas_importadas >= 45
    ws = openpyxl.load_workbook(EXCEL_CLIENTE, data_only=True)["PLATOS CODIGOS Y RECETAS "]
    c = CosteoController(db)
    for nombre, celda in (("arroz con pollo", "N107"), ("mondongo", "N226"), ("pernil", "N79"),
                          ("yuca frita", "N365"), ("patacones", "N367")):
        mid = db.fetch_one("SELECT id FROM menu_items WHERE lower(nombre) LIKE ?", (nombre + "%",))[0]
        assert c.costo_ingredientes(mid)["total"] == pytest.approx(ws[celda].value, rel=0.005), nombre

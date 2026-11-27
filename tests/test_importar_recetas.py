"""Importación de recetas desde la plantilla estándar (app/utils/importar_recetas.py)."""
import openpyxl
import pytest

from app.controllers.costeo_controller import CosteoController
from app.database.connection import DatabaseManager
from app.utils.importar_recetas import (clave_singular, convertir_cantidad, exportar_reporte, importar,
                                        importar_insumos_faltantes)
from app.utils.plantilla_recetas import (LineaPlantilla as L, PlatoPlantilla as P, RecetaPlantilla as R,
                                         generar_plantilla, leer_plantilla)

approx = pytest.approx


@pytest.fixture
def db(tmp_path):
    d = DatabaseManager(str(tmp_path / "r.db"))
    u = {}
    for nombre, abrev in (("Gramo", "g"), ("Mililitro", "ml"), ("Libra", "lb")):
        u[abrev] = d.execute_query("INSERT INTO unidades_medida (nombre, abreviatura) VALUES (?,?)",
                                   (nombre, abrev)).lastrowid
    for cod, nombre, uni, costo, gml in (("G001", "Arroz", "g", 0.002, None), ("V002", "Ajo", "g", 0.01, 0.6),
                                         ("V018", "Cebolla", "g", 0.004, None), ("IC002", "Agua", "ml", 0.0, 1.0),
                                         (None, "Pollo", "lb", 2.0, None)):
        d.execute_query("INSERT INTO insumos (codigo, nombre, unidad_base_id, costo_unitario, gramos_por_ml) "
                        "VALUES (?,?,?,?,?)", (cod, nombre, u[uni], costo, gml))
    d.execute_query("INSERT INTO menu_items (codigo, nombre, precio_venta) VALUES ('38', 'Arroz combinado', 4.5)")
    d.u = u
    yield d
    d.conn.close()


def _plantilla(db, tmp_path, recetas, nombre="p.xlsx"):
    ruta = str(tmp_path / nombre)
    generar_plantilla(db, ruta, recetas)
    return ruta


def _ins(db, nombre):
    return db.fetch_one("SELECT id FROM insumos WHERE nombre=?", (nombre,))[0]


def _item(db, codigo):
    return db.fetch_one("SELECT id, nombre, precio_venta, rendimiento, porcion_servida, es_componente "
                        "FROM menu_items WHERE codigo=?", (codigo,))


def test_convertir_cantidad():
    assert convertir_cantidad(2, "lb", "g")[0] == approx(907.184)
    assert convertir_cantidad(1, "L", "ml")[0] == approx(1000)
    assert convertir_cantidad(100, "ml", "g", gramos_por_ml=0.5)[0] == approx(50)
    assert convertir_cantidad(100, "ml", "g") == (None, "falta «Gramos por ml»")
    assert convertir_cantidad(1, "und", "g")[0] is None


def test_plantilla_ida_y_vuelta(db, tmp_path):
    rec = R(0, "38", "Arroz de combinación", "PLATO", 4000, "g", "nota",
            [L(0, "G001", "Arroz", 5, "lb"), L(0, "200", "Guizos", 750, "ml", "obs")],
            [P(0, "38", "Arroz combinado", 287, "g"), P(0, "78", "Arroz eco", 190, "g")])
    leida = leer_plantilla(_plantilla(db, tmp_path, [rec]))
    assert not leida.errores
    r = leida.recetas[0]
    assert (r.codigo, r.nombre, r.tipo, r.rendimiento, r.unidad_rend) == ("38", "Arroz de combinación", "PLATO", 4000, "g")
    assert [(ln.codigo, ln.ingrediente, ln.cantidad, ln.unidad) for ln in r.lineas] == [
        ("G001", "Arroz", 5, "lb"), ("200", "Guizos", 750, "ml")]
    assert [(p.codigo, p.porcion) for p in r.platos] == [("38", 287), ("78", 190)]
    wb = openpyxl.load_workbook(str(tmp_path / "p.xlsx"))
    assert {"Instrucciones", "Recetas", "Ingredientes", "Platos", "Insumos", "Unidades"} <= set(wb.sheetnames)


def test_un_plato_es_la_tanda_y_convierte_a_la_unidad_del_insumo(db, tmp_path):
    rec = R(0, "38", "Arroz", "PLATO", 3000, "g", "",
            [L(0, "G001", "Arroz", 2, "lb"), L(0, "V002", "ajo", 50, "ml"), L(0, "", "Pollo", 500, "g")],
            [P(0, "38", "", 300, "g")])
    res = importar(db, _plantilla(db, tmp_path, [rec]), dry_run=False)
    assert res.importadas == 1 and res.bloqueadas == 0, res.texto()
    pid, nombre, precio, rend, porcion, comp = _item(db, "38")
    assert (nombre, precio, rend, porcion, comp) == ("Arroz combinado", 4.5, 3000, 300, 0)  # se respeta lo del menú
    lineas = dict(db.fetch_all("SELECT insumo_id, cantidad_necesaria FROM recetas WHERE menu_item_id=?", (pid,)))
    assert lineas[_ins(db, "Arroz")] == approx(907.184)          # 2 lb -> g
    assert lineas[_ins(db, "Ajo")] == approx(30)                 # 50 ml × 0.6 g/ml
    assert lineas[_ins(db, "Pollo")] == approx(500 / 453.592)    # g -> lb (unidad del insumo)
    # El costeo lo lee igual: porción = 1/10 de la tanda
    costo = CosteoController(db).costo_ingredientes(pid)["total"]
    assert costo == approx((907.184 * 0.002 + 30 * 0.01 + 500 / 453.592 * 2.0) / 10)


def test_varios_platos_comparten_la_tanda_con_porciones_distintas(db, tmp_path):
    rec = R(0, "38", "Arroz de combinación", "PLATO", 1000, "g", "", [L(0, "G001", "Arroz", 1000, "g")],
            [P(0, "38", "", 300, "g"), P(0, "78", "Arroz eco", 150, "g")])
    res = importar(db, _plantilla(db, tmp_path, [rec]), dry_run=False)
    assert res.importadas == 1 and res.platos_creados == 1, res.texto()
    tanda = _item(db, "R38")
    assert tanda[5] == 1 and tanda[3] == 1000 and "tanda" in tanda[1]
    c = CosteoController(db)
    assert c.costo_plato(_item(db, "38")[0])["ingredientes"] == approx(300 * 0.002)
    assert c.costo_plato(_item(db, "78")[0])["ingredientes"] == approx(150 * 0.002)
    assert _item(db, "78")[2] == 0  # creado con precio 0
    # Kardex/presupuesto (vista explotada) ven el insumo por plato
    q = db.fetch_one("SELECT cantidad_necesaria FROM v_recetas_explotadas WHERE menu_item_id=?", (_item(db, "78")[0],))
    assert q[0] == approx(150)


def test_subreceta_del_archivo_se_usa_por_codigo(db, tmp_path):
    guiso = R(0, "200", "Guizos", "SUB-RECETA", 1000, "ml", "", [L(0, "V018", "Cebolla", 400, "g"),
                                                                 L(0, "IC002", "Agua", 600, "ml")])
    plato = R(0, "46", "Pollo guisado", "PLATO", 2000, "g", "", [L(0, "", "Pollo", 3, "lb"),
                                                                 L(0, "200", "guizos", 250, "ml")],
              [P(0, "46", "Pollo guisado", 250, "g")])
    res = importar(db, _plantilla(db, tmp_path, [plato, guiso]), dry_run=False)
    assert res.importadas == 2 and res.bloqueadas == 0, res.texto()
    guiso_id = _item(db, "#200")[0]
    comp = db.fetch_one("SELECT componente_id, cantidad FROM receta_componentes WHERE menu_item_id=?",
                        (_item(db, "46")[0],))
    assert comp == (guiso_id, 250)


def test_insumo_faltante_bloquea_y_se_lista(db, tmp_path):
    rec = R(0, "36", "Filete de pescado", "PLATO", 2000, "g", "",
            [L(0, "M004", "Filete de pescado", 5, "lb"), L(0, "", "Limón", 63, "ml"), L(0, "G001", "Arroz", 100, "g")],
            [P(0, "36", "Filete", 136, "g")])
    ruta = _plantilla(db, tmp_path, [rec])
    res = importar(db, ruta, dry_run=False)
    assert res.importadas == 0 and res.bloqueadas == 1
    assert _item(db, "36") is None  # nunca a medias: ni siquiera se crea el plato
    assert {f["nombre"]: (f["codigo"], f["unidad"]) for f in res.faltantes.values()} == {
        "Filete de pescado": ("M004", "g"), "Limón": ("", "ml")}
    reporte = exportar_reporte(res, str(tmp_path / "reporte.xlsx"))
    hoja = openpyxl.load_workbook(reporte)["Insumos faltantes"]
    assert hoja.cell(2, 2).value == "Filete de pescado" and "36 Filete de pescado" in hoja.cell(2, 6).value

    # Se completan y se importan; luego la receta entra
    wb = openpyxl.load_workbook(reporte)
    wb["Insumos faltantes"].cell(3, 4, 1.0)  # limón: 1 g por ml
    wb.save(reporte)
    creados, _msgs = importar_insumos_faltantes(db, reporte)
    assert creados == 2
    assert db.fetch_one("SELECT codigo FROM insumos WHERE nombre='Filete de pescado'")[0] == "M004"
    res2 = importar(db, ruta, dry_run=False)
    assert res2.importadas == 1, res2.texto()
    assert importar_insumos_faltantes(db, reporte)[0] == 0  # no duplica


def test_codigo_y_nombre_distintos_avisa_y_usa_el_codigo(db, tmp_path):
    rec = R(0, "38", "Arroz", "PLATO", 1000, "g", "", [L(0, "V002", "Culantro", 10, "g")], [P(0, "38", "", 100, "g")])
    res = importar(db, _plantilla(db, tmp_path, [rec]), dry_run=False)
    assert res.importadas == 1
    assert any("V002" in m and "Ajo" in m for n, _r, _f, m in res.problemas if n == "AVISO")
    assert db.fetch_one("SELECT insumo_id FROM recetas")[0] == _ins(db, "Ajo")


def test_volumen_sin_factor_bloquea(db, tmp_path):
    rec = R(0, "38", "Arroz", "PLATO", 1000, "g", "", [L(0, "", "Cebolla", 200, "ml")], [P(0, "38", "", 100, "g")])
    res = importar(db, _plantilla(db, tmp_path, [rec]))
    assert res.bloqueadas == 1 and any("Gramos por ml" in m for _n, _r, _f, m in res.problemas)


def test_sin_rendimiento_queda_pendiente(db, tmp_path):
    rec = R(0, "38", "Arroz", "PLATO", None, "", "", [L(0, "G001", "Arroz", 1, "lb")], [P(0, "38", "", 100, "g")])
    res = importar(db, _plantilla(db, tmp_path, [rec]), dry_run=False)
    assert res.pendientes == 1 and res.importadas == 0
    assert db.fetch_one("SELECT COUNT(*) FROM recetas")[0] == 0


def test_subreceta_inexistente_bloquea(db, tmp_path):
    rec = R(0, "38", "Arroz", "PLATO", 1000, "g", "", [L(0, "203", "Salsa espesor", 60, "ml")],
            [P(0, "38", "", 100, "g")])
    res = importar(db, _plantilla(db, tmp_path, [rec]))
    assert res.bloqueadas == 1 and any("203" in m for _n, _r, _f, m in res.problemas)


def test_modos_nuevas_y_actualizar(db, tmp_path):
    pid = _item(db, "38")[0]
    db.execute_query("INSERT INTO recetas (menu_item_id, insumo_id, cantidad_necesaria) VALUES (?,?,99)",
                     (pid, _ins(db, "Arroz")))
    rec = R(0, "38", "Arroz", "PLATO", 1000, "g", "", [L(0, "G001", "Arroz", 500, "g")], [P(0, "38", "", 100, "g")])
    ruta = _plantilla(db, tmp_path, [rec])

    res = importar(db, ruta, dry_run=False, modo="NUEVAS")
    assert res.omitidas == 1
    assert db.fetch_one("SELECT cantidad_necesaria FROM recetas WHERE menu_item_id=?", (pid,))[0] == 99

    for _ in range(2):  # idempotente
        res = importar(db, ruta, dry_run=False, modo="ACTUALIZAR")
        assert res.actualizadas == 1
        assert db.fetch_all("SELECT cantidad_necesaria FROM recetas WHERE menu_item_id=?", (pid,)) == [(500,)]


def test_simulacion_no_guarda_nada(db, tmp_path):
    antes = db.fetch_one("SELECT (SELECT COUNT(*) FROM recetas) + (SELECT COUNT(*) FROM menu_items) "
                         "+ (SELECT COUNT(*) FROM unidades_medida)")[0]
    rec = R(0, "99", "Nuevo", "PLATO", 2, "kg", "", [L(0, "G001", "Arroz", 1, "kg")], [P(0, "99", "Nuevo", 200, "g")])
    res = importar(db, _plantilla(db, tmp_path, [rec]), dry_run=True)
    assert res.importadas == 1 and res.platos_creados == 1 and res.unidades_creadas == 1
    despues = db.fetch_one("SELECT (SELECT COUNT(*) FROM recetas) + (SELECT COUNT(*) FROM menu_items) "
                           "+ (SELECT COUNT(*) FROM unidades_medida)")[0]
    assert antes == despues


def test_archivo_que_no_es_la_plantilla(db, tmp_path):
    ruta = str(tmp_path / "otro.xlsx")
    openpyxl.Workbook().save(ruta)
    with pytest.raises(ValueError, match="plantilla"):
        importar(db, ruta)


def test_nombres_en_plural_encuentran_el_insumo(db, tmp_path):
    assert clave_singular("Cebollas") == clave_singular("cebolla")
    assert clave_singular("limones") == clave_singular("Limón")
    rec = R(0, "38", "Arroz", "PLATO", 1000, "g", "", [L(0, "", "Cebollas", 100, "g")], [P(0, "38", "", 100, "g")])
    res = importar(db, _plantilla(db, tmp_path, [rec]), dry_run=False)
    assert res.importadas == 1, res.texto()
    assert db.fetch_one("SELECT insumo_id FROM recetas")[0] == _ins(db, "Cebolla")

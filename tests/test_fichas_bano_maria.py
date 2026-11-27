"""Convertidor de las fichas «Baño María» del cliente a la plantilla estándar."""
import openpyxl
import pytest

from app.database.connection import DatabaseManager
from app.utils.fichas_bano_maria import convertir_a_plantilla, leer_fichas, limpiar_nombre, unidad_estandar
from app.utils.plantilla_recetas import leer_plantilla

ENCABEZADO = ["INGREDIENTES", "   CANT RECETA /         U", None, None, "PORCION", "CANTIDAD   / U"]


def _ficha_a(ws, col=2, nombre="Arroz de combinacion", platos=(("#38", None), ("#78", None)), eco=True):
    """Formato estándar. `col` = columna del «CODIGO :» (la de «carne guisada» está corrida a la C)."""
    ws.cell(3, col, "CODIGO :")
    ws.cell(3, col + 1, nombre)
    for i, (cod, etiqueta) in enumerate(platos):
        ws.cell(4 + i, col, cod)
        if etiqueta:
            ws.cell(4 + i, col + 1, etiqueta)
    for j, t in enumerate(ENCABEZADO):
        if t:
            ws.cell(6, col + 1 + j, t)
    filas = [("#G001", "Arroz ", 5, "lb"), ("#V002", "Ajo", 30, "ml"), (None, "2 mazorca", "4.69", "lbs"),
             ("#200", "guizos", 750, "ml"), (None, None, 63, "ml")]
    for i, (cod, nom, cant, uni) in enumerate(filas):
        r = 7 + i
        ws.cell(r, col, cod)
        ws.cell(r, col + 1, nom)
        ws.cell(r, col + 2, cant)
        ws.cell(r, col + 3, uni)
    ws.cell(7, col + 5, "servida")
    ws.cell(7, col + 6, 287)
    ws.cell(7, col + 7, "g ")
    if eco:
        ws.cell(8, col + 5, "servida eco")
        ws.cell(8, col + 6, 190)
        ws.cell(8, col + 7, "g ")


def _ficha_b(ws):
    """Plantilla copiada: códigos viejos, cantidad en la columna del nombre, «g» para valores en kg."""
    ws.cell(3, 2, "CODIGO :")
    ws.cell(3, 3, "Chuleta en Salsa")
    ws.cell(4, 2, "#46")
    ws.cell(4, 3, 2.144)
    ws.cell(4, 4, "kg")
    ws.cell(5, 2, "#79")
    for j, t in enumerate(ENCABEZADO):
        if t:
            ws.cell(6, 3 + j, t)
    for i, (cod, cant, nom, uni) in enumerate([("#V001", 2.144, "Chuleta", "g"), ("Bist", 0.8, "Consome de Res", "g"),
                                               ("#V017", 29.5, "Caldo de Pollo", "g"), ("#IC002", None, None, "g")]):
        ws.cell(7 + i, 2, cod)
        ws.cell(7 + i, 3, cant)
        ws.cell(7 + i, 4, nom)
        ws.cell(7 + i, 5, uni)
    ws.cell(7, 7, "servida")
    ws.cell(7, 8, 292)
    ws.cell(7, 9, "g")


@pytest.fixture
def archivo(tmp_path):
    wb = openpyxl.Workbook()
    _ficha_a(wb.active)
    wb.active.title = "arroz de combinacion"
    _ficha_a(wb.create_sheet("carne guisada"), col=3, nombre="carne guisada", platos=(), eco=False)
    _ficha_a(wb.create_sheet("sopa de carne"), nombre="sopa de carne", platos=(("#69", None), ("#70", "con arroz")),
             eco=False)
    _ficha_b(wb.create_sheet("Chuleta en Salsa "))
    wb.create_sheet("Hoja2")
    ruta = str(tmp_path / "fichas.xlsx")
    wb.save(ruta)
    return ruta


def test_unidades_y_nombres():
    assert [unidad_estandar(u) for u in ("lbs", "L", "Kg", "gal", "u", "")] == ["lb", "l", "kg", "gal", "und", ""]
    assert limpiar_nombre("2 mazorca")[0] == "Mazorca" and "2 mazorca" in limpiar_nombre("2 mazorca")[1]
    assert limpiar_nombre("16 tazas de agua")[0] == "Agua"
    assert limpiar_nombre("4 tazas de agua de")[0] == "Agua"
    assert limpiar_nombre("Ajo ") == ("Ajo", "")


def test_formato_estandar(archivo):
    fichas, resumen = leer_fichas(archivo)
    assert [f.formato for f in fichas] == ["A", "A", "A", "B", "VACIA"]
    arroz = fichas[0].receta
    assert (arroz.codigo, arroz.nombre, arroz.tipo, arroz.rendimiento) == ("38", "Arroz de combinacion", "PLATO", None)
    assert [(p.codigo, p.porcion, p.unidad) for p in arroz.platos] == [("38", 287, "g"), ("78", 190, "g")]
    assert [(ln.codigo, ln.ingrediente, ln.cantidad, ln.unidad) for ln in arroz.lineas] == [
        ("G001", "Arroz", 5, "lb"), ("V002", "Ajo", 30, "ml"), ("", "Mazorca", 4.69, "lb"),
        ("200", "Guizos", 750, "ml"), ("", "", 63, "ml")]
    assert "2 mazorca" in arroz.lineas[2].observacion
    assert "Falta el ingrediente" in arroz.lineas[4].observacion
    assert "Rendimiento tanda" in arroz.revision[0]
    assert "Hoja2" in "\n".join(resumen)


def test_columna_corrida_y_sin_codigo_de_plato(archivo):
    carne = leer_fichas(archivo)[0][1].receta
    assert carne.lineas[0].ingrediente == "Arroz" and carne.platos == []
    assert carne.codigo.startswith("F-CARNE")
    assert any("código de plato" in r for r in carne.revision)


def test_variante_con_arroz(archivo):
    sopa = leer_fichas(archivo)[0][2].receta
    assert [(p.codigo, p.nombre, p.porcion) for p in sopa.platos] == [
        ("69", "sopa de carne", 287), ("70", "sopa de carne con arroz", 287)]
    assert "con arroz" in sopa.platos[1].observacion


def test_formato_b_ignora_codigos_y_queda_pendiente(archivo):
    chuleta = leer_fichas(archivo)[0][3].receta
    assert chuleta.platos == [] and chuleta.rendimiento is None
    assert [(ln.codigo, ln.ingrediente, ln.cantidad) for ln in chuleta.lineas] == [
        ("", "Chuleta", 2.144), ("", "Consome de Res", 0.8), ("", "Caldo de Pollo", 29.5)]
    assert "kg" in chuleta.lineas[1].observacion
    texto = "\n".join(chuleta.revision)
    assert "formato distinto" in texto and "2.144 kg" in texto


def test_convertir_genera_una_plantilla_importable(archivo, tmp_path):
    db = DatabaseManager(str(tmp_path / "x.db"))
    salida = str(tmp_path / "plantilla.xlsx")
    convertir_a_plantilla(archivo, salida, db)
    wb = openpyxl.load_workbook(salida)
    assert wb.sheetnames[:2] == ["Instrucciones", "Revisión"]
    leida = leer_plantilla(salida)
    assert not leida.errores
    assert [r.codigo for r in leida.recetas] == ["38", "F-CARNE-GUISADA", "69", "F-CHULETA-EN-SALSA"]
    assert leida.recetas[0].platos[1].porcion == 190
    db.conn.close()

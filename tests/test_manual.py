import importlib.util
import os

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _cargar_generador():
    spec = importlib.util.spec_from_file_location("generar_manual", os.path.join(RAIZ, "generar_manual.py"))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_el_manual_se_genera_desde_la_ayuda(tmp_path):
    gm = _cargar_generador()
    salida = gm.generar(str(tmp_path / "manual.pdf"))
    with open(salida, "rb") as f:
        contenido = f.read()
    assert contenido.startswith(b"%PDF")
    assert len(contenido) > 50_000, "el PDF es sospechosamente pequeño"


def test_markdown_convierte_tablas_listas_y_avisos():
    gm = _cargar_generador()
    md = (
        "# Tema de prueba\n\nTexto con **negrita** y [enlace](ayuda:ventas).\n\n"
        "| A | B |\n|---|---|\n| 1 | 2 |\n\n"
        "1. Paso uno\n2. Paso dos\n   - subpaso\n\n"
        "> **Importante:** cuidado.\n"
    )
    flow = gm.markdown_a_flowables(md, "prueba")
    tipos = [type(f).__name__ for f in flow]
    assert "Table" in tipos                      # banner + tabla + caja
    assert sum(1 for t in tipos if t == "Paragraph") >= 4  # párrafo + 3 viñetas


def test_el_manual_publicado_esta_actualizado_con_la_ayuda():
    """Si se edita cualquier tema de assets/ayuda sin regenerar el PDF, esta prueba falla."""
    gm = _cargar_generador()
    ruta = os.path.join(RAIZ, gm.ARCHIVO_HUELLA)
    assert os.path.exists(ruta), "falta la huella del manual: ejecute `python generar_manual.py`"
    with open(ruta, encoding="utf-8") as f:
        guardada = f.read().strip()
    assert guardada == gm.huella_ayuda(), (
        "La ayuda cambió pero el manual PDF no se regeneró. Ejecute: python generar_manual.py"
    )

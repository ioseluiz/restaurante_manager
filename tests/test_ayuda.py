import os
import re

from app.utils import ayuda

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CLAVES = {c for c, _ in ayuda.TEMAS}


def test_todos_los_temas_tienen_archivo_con_contenido():
    for clave in CLAVES:
        assert ayuda.existe(clave), f"falta assets/ayuda/{clave}.md"
        texto = ayuda.leer(clave)
        assert texto.lstrip().startswith("# "), f"{clave}: debe empezar con un título #"
        assert len(texto) > 400, f"{clave}: ayuda demasiado corta"


def test_no_hay_archivos_de_ayuda_huerfanos():
    carpeta = os.path.join(RAIZ, "assets", "ayuda")
    en_disco = {f[:-3] for f in os.listdir(carpeta) if f.endswith(".md")}
    assert en_disco == CLAVES, f"sin registrar en TEMAS: {en_disco - CLAVES}; sin archivo: {CLAVES - en_disco}"


def test_los_enlaces_internos_apuntan_a_temas_existentes():
    for clave in CLAVES:
        for destino in re.findall(r"\(ayuda:([a-z_]+)\)", ayuda.leer(clave)):
            assert destino in CLAVES, f"{clave}.md enlaza a un tema inexistente: {destino}"


def test_cada_modulo_del_menu_lateral_tiene_ayuda():
    """Si se agrega un módulo a MainWindow.load_module, debe agregarse su ayuda (F1)."""
    with open(os.path.join(RAIZ, "app", "views", "main_window.py"), encoding="utf-8") as f:
        claves_modulos = set(re.findall(r'load_module\(\s*"([a-z_]+)"', f.read()))
    assert claves_modulos, "no se encontraron módulos"
    faltan = claves_modulos - CLAVES
    assert not faltan, f"módulos sin tema de ayuda: {faltan}"


def test_busqueda_sin_distinguir_tildes_ni_mayusculas():
    assert "planilla" in ayuda.buscar("PLANILLA")
    assert "conteo" in ayuda.buscar("FÍSICAMENTE")            # el texto dice «físicamente»
    assert "conteo" in ayuda.buscar("fisicamente")
    assert ayuda.buscar("zzzpalabranoexistente") == []
    assert len(ayuda.buscar("")) == len(CLAVES)


def test_tema_inexistente_devuelve_aviso_en_vez_de_fallar():
    assert "Todavía no hay ayuda" in ayuda.leer("no_existe")

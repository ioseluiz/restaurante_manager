# [FILE: app/utils/ayuda.py]
"""Contenido de la ayuda en pantalla: un archivo Markdown por módulo en assets/ayuda/.

La clave de cada tema es la misma que usa MainWindow.load_module (p. ej. "ventas"), de modo que
F1 abre la ayuda del módulo que el usuario tiene a la vista. Para agregar/editar ayuda basta con
modificar el .md (y, si es un módulo nuevo, agregarlo a TEMAS). No requiere tocar los .spec porque
la carpeta assets ya se empaqueta completa.
"""

import os
import sys
import unicodedata

# (clave, título en el índice) — en el orden del menú lateral.
TEMAS = [
    ("general", "Primeros pasos y navegación"),
    ("dashboard", "Panel de Control"),
    ("ventas", "Ventas"),
    ("compras", "Compras"),
    ("inventario", "Inventario"),
    ("conteo", "Toma de Inventario"),
    ("insumos", "Catálogo de Insumos"),
    ("etiquetas", "Etiquetas y Códigos"),
    ("recetas", "Recetas (Fichas)"),
    ("menu", "Menú"),
    ("presupuestos", "Presupuestos"),
    ("consolidados", "Consolidados"),
    ("rentabilidad", "Rentabilidad"),
    ("costo_platos", "Costo de Platos"),
    ("grafico_precios", "Análisis de Precios"),
    ("planilla", "Planilla"),
    ("unidades", "Unidades de Medida"),
    ("sucursales", "Sucursales"),
    ("usuarios", "Usuarios"),
]
_TITULOS = dict(TEMAS)
TEMA_POR_DEFECTO = "general"


def _base():
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def ruta_tema(clave):
    return os.path.join(_base(), "assets", "ayuda", f"{clave}.md")


def titulo(clave):
    return _TITULOS.get(clave, clave)


def existe(clave):
    return os.path.isfile(ruta_tema(clave))


def leer(clave):
    """Markdown del tema, o un texto de aviso si el archivo no está disponible."""
    try:
        with open(ruta_tema(clave), encoding="utf-8") as f:
            return f.read()
    except OSError:
        return (f"# {titulo(clave)}\n\nTodavía no hay ayuda escrita para esta sección.\n\n"
                "Consulte la [guía de primeros pasos](ayuda:general).")


def _plano(s):
    """Minúsculas y sin acentos, para buscar sin importar tildes."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return s.lower()


def buscar(texto):
    """Claves de los temas cuyo título o contenido contienen TODAS las palabras buscadas."""
    palabras = _plano(texto).split()
    if not palabras:
        return [c for c, _ in TEMAS]
    out = []
    for clave, tit in TEMAS:
        haystack = _plano(tit + " " + leer(clave))
        if all(p in haystack for p in palabras):
            out.append(clave)
    return out

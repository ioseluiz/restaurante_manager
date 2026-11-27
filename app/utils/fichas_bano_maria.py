"""Convierte las fichas de recetas del cliente (una receta por hoja, p. ej. «BAÑO MARIA 1 recetas de ITALOS
ATRIO.xlsx») a la plantilla estándar (app/utils/plantilla_recetas.py), con observaciones de lo que hay que revisar.

Formato de cada hoja (se ubica por los rótulos, no por posición fija):

    CODIGO :   <nombre de la receta>
    #38                                   <- códigos de plato del POS (el 2.º suele ser la versión «eco»
    #78        [con arroz]                   o «con arroz»)
               INGREDIENTES | CANT RECETA / U |        | PORCION      | CANTIDAD / U
    #V002      Ajo          | 30   | ml       |        | servida      | 287 | g
    #200       guizos       | 750  | ml       |        | servida eco  | 190 | g

Formato B: algunas hojas se armaron copiando una plantilla y quedaron con la cantidad en la columna del nombre,
los códigos viejos de la plantilla y unidades «g» para valores en kg. Se detectan, se ignoran sus códigos y se
dejan PENDIENTES (sin rendimiento) para que se revisen.

Las fichas no traen el rendimiento total de la tanda: queda vacío (obligatorio) y la receta va a «Revisión».
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.utils.codigo_insumo import normalizar_codigo_insumo
from app.utils.importar_costeo_excel import norm
from app.utils.plantilla_recetas import LineaPlantilla, PlatoPlantilla, RecetaPlantilla, a_numero, codigo_texto

_ALIAS_UNIDAD = {"lbs": "lb", "libra": "lb", "libras": "lb", "l": "l", "lt": "l", "lts": "l", "litro": "l",
                 "litros": "l", "gr": "g", "grs": "g", "gramos": "g", "kgs": "kg", "kilo": "kg", "kilos": "kg",
                 "gal": "gal", "galon": "gal", "galones": "gal", "u": "und", "un": "und", "unidad": "und",
                 "unidades": "und", "ml": "ml", "g": "g", "kg": "kg", "lb": "lb", "oz": "oz", "und": "und"}
_CANTIDAD_EN_NOMBRE = re.compile(r"^\s*(\d+(?:[.,]\d+)?|un|una|dos|tres)\s+(?:(?:tazas?|cdas?|cucharadas?)\s+de\s+)?",
                                 re.IGNORECASE)


def unidad_estandar(texto):
    """'lbs' -> 'lb', 'L' -> 'l'. Cadena vacía si no hay unidad; el texto tal cual si no se reconoce."""
    t = norm(texto)
    return _ALIAS_UNIDAD.get(t, t)


def limpiar_nombre(nombre):
    """('2 mazorca' -> 'mazorca', observación) · ('16 tazas de agua' -> 'agua', …) · ('Ajo ' -> 'Ajo', '')."""
    original = re.sub(r"\s+", " ", str(nombre or "")).strip()
    limpio = _CANTIDAD_EN_NOMBRE.sub("", original).strip()
    limpio = re.sub(r"\s+de$", "", limpio).strip()  # «4 tazas de agua de» -> «agua»
    if limpio and limpio != original:
        return limpio[:1].upper() + limpio[1:], f"El nombre decía «{original}»: revise que la cantidad sea la de la tanda"
    return (original[:1].upper() + original[1:]) if original else "", ""


@dataclass
class FichaLeida:
    hoja: str
    receta: RecetaPlantilla | None
    formato: str            # "A", "B" o "VACIA"
    avisos: list = field(default_factory=list)


def _buscar(ws, predicado, filas=None):
    for row in ws.iter_rows(min_row=1, max_row=filas or ws.max_row):
        for c in row:
            if isinstance(c.value, str) and predicado(norm(c.value)):
                return c.row, c.column
    return None


def leer_ficha(ws):
    v = lambda r, c: ws.cell(r, c).value if r >= 1 and c >= 1 else None  # noqa: E731
    pos_cod = _buscar(ws, lambda t: t.startswith("codigo"))
    pos_ing = _buscar(ws, lambda t: t == "ingredientes")
    if not pos_cod or not pos_ing:
        return FichaLeida(ws.title, None, "VACIA", ["Hoja sin ficha de receta (se omite)"])
    r0, c0 = pos_cod
    rh, ci = pos_ing
    nombre = re.sub(r"\s+", " ", str(v(r0, c0 + 1) or ws.title)).strip()
    pos_por = _buscar(ws, lambda t: t == "porcion")
    cp = pos_por[1] if pos_por else ci + 4

    # Códigos de plato (debajo de «CODIGO :», antes del encabezado de ingredientes)
    platos_cod = []
    for r in range(r0 + 1, rh):
        cod = v(r, c0)
        if isinstance(cod, str) and re.fullmatch(r"#\s*\d+", cod.strip()):
            platos_cod.append((codigo_texto(cod), str(v(r, c0 + 1) or "").strip() if isinstance(v(r, c0 + 1), str) else ""))

    # Porciones («servida», «servida eco») en la columna PORCION
    porciones = []
    for r in range(rh + 1, ws.max_row + 1):
        etiqueta = v(r, cp)
        if isinstance(etiqueta, str) and norm(etiqueta).startswith("servida"):
            porciones.append((norm(etiqueta), a_numero(v(r, cp + 1)), unidad_estandar(v(r, cp + 2)) or "g"))

    # Líneas
    filas = []
    for r in range(rh + 1, ws.max_row + 1):
        cod, nom, cant, uni = v(r, ci - 1), v(r, ci), v(r, ci + 1), v(r, ci + 2)
        extra = v(r, ci + 3)
        if (nom is None or str(nom).strip() == "") and a_numero(cant) is None:
            continue
        filas.append((r, cod, nom, cant, uni, extra))

    # Formato B: la cantidad está en la columna del nombre y el nombre en la de cantidad
    invertidas = sum(1 for _r, _c, nom, cant, _u, _e in filas
                     if a_numero(nom) is not None and isinstance(cant, str) and a_numero(cant) is None)
    formato = "B" if filas and invertidas >= max(1, len(filas) // 2) else "A"

    rec = RecetaPlantilla(0, "", nombre, "PLATO", None, "", "")
    ficha = FichaLeida(ws.title, rec, formato)
    if formato == "B":
        total, u_total, nota = a_numero(v(r0 + 1, c0 + 1)), unidad_estandar(v(r0 + 1, c0 + 2)), v(r0 + 1, c0 + 3)
        rec.revision.append("Ficha con formato distinto (plantilla copiada): los códigos de insumo y de plato son "
                            "los de otra receta y se ignoraron; las unidades dicen «g» pero muchos valores parecen kg. "
                            "Revise cada cantidad y unidad.")
        if total:
            rec.revision.append(f"La ficha indica {total:g} {u_total or ''} en total"
                                + (f" ({nota})" if isinstance(nota, str) and nota.strip() else "")
                                + ": si es el rendimiento de la tanda, cópielo en «Rendimiento tanda».")
        platos_cod = []
        rec.revision.append("Indique en la hoja «Platos» el código del POS y la porción de este plato.")

    for r, cod, nom, cant, uni, extra in filas:
        if formato == "B":
            cod, nom, cant = None, cant, nom
        n_cant = a_numero(cant)
        nombre_ln, obs = limpiar_nombre(nom)
        observaciones = [obs] if obs else []
        if isinstance(cant, str) and n_cant is not None:
            pass  # número guardado como texto: se convierte sin aviso
        if not nombre_ln:
            observaciones.append("Falta el ingrediente: complete el nombre o borre la fila")
        if n_cant is None:
            observaciones.append("Falta la cantidad")
        u = unidad_estandar(uni)
        if not u:
            observaciones.append("Falta la unidad")
        if formato == "B" and u == "g" and n_cant is not None and n_cant < 5:
            observaciones.append(f"¿{n_cant:g} g o {n_cant:g} kg? Revise la unidad")
        if isinstance(extra, str) and extra.strip() and not norm(extra).startswith("servida"):
            observaciones.append(f"Nota de la ficha: {extra.strip()}")
        codigo = ""
        if cod is not None and str(cod).strip():
            codigo = normalizar_codigo_insumo(cod)
            if not re.fullmatch(r"[A-Z]{1,3}\d{2,4}|\d{3,}", codigo):
                observaciones.append(f"Código «{cod}» no reconocido (se ignoró)")
                codigo = ""
        rec.lineas.append(LineaPlantilla(r, codigo, nombre_ln, n_cant, u, "; ".join(observaciones)))

    # Platos y porciones
    normal = next((p for p in porciones if p[0] == "servida"), porciones[0] if porciones else None)
    eco = next((p for p in porciones if "eco" in p[0]), None)
    for i, (cod, etiqueta) in enumerate(platos_cod):
        p = eco if (i > 0 and eco) else normal
        obs = ""
        if i > 0 and not eco:
            obs = (f"Variante «{etiqueta}»: la porción es la de la ficha; agregue aparte lo que lleva de más"
                   if etiqueta else "Segundo código sin porción propia en la ficha: confirme la porción")
        nombre_plato = nombre + (f" {etiqueta}" if etiqueta else (" eco" if i > 0 and eco else ""))
        rec.platos.append(PlatoPlantilla(0, cod, nombre_plato, p[1] if p else None, p[2] if p else "g", obs))
    if formato == "A" and not platos_cod:
        rec.revision.append("La ficha no trae código de plato: indique en la hoja «Platos» el código del POS "
                            "y la porción (o cambie el tipo a SUB-RECETA si se usa dentro de otras recetas).")
    if formato == "A" and normal and normal[1] is None:
        rec.revision.append("La ficha no indica la porción servida.")

    rec.revision.insert(0, "Complete «Rendimiento tanda»: cuánto sale en total de la tanda (la ficha no lo indica).")
    for ln in rec.lineas:
        if ln.observacion:
            rec.revision.append(f"Ingrediente «{ln.ingrediente or '(sin nombre)'}» (fila {ln.fila} de la ficha): "
                                f"{ln.observacion}")
    return ficha


def leer_fichas(ruta):
    """Lee todas las hojas. Devuelve (fichas, resumen) con códigos de receta únicos asignados."""
    import openpyxl

    wb = openpyxl.load_workbook(ruta, data_only=True)
    fichas = [leer_ficha(ws) for ws in wb.worksheets]
    usados, vistos = set(), {}
    for f in fichas:
        rec = f.receta
        if rec is None:
            continue
        base = rec.platos[0].codigo if rec.platos else "F-" + re.sub(r"[^A-Z0-9]+", "-", norm(rec.nombre).upper())[:20]
        cod, n = base, 2
        while cod in usados:
            cod, n = f"{base}-{n}", n + 1
        usados.add(cod)
        rec.codigo = cod
        clave = norm(rec.nombre)
        if clave in vistos:
            rec.revision.append(f"Hay otra ficha con el mismo nombre (hoja «{vistos[clave]}»): "
                                "conserve una sola o cámbiele el nombre.")
        else:
            vistos[clave] = f.hoja
    validas = [f for f in fichas if f.receta]
    resumen = [
        f"Archivo convertido: {len(fichas)} hojas, {len(validas)} recetas "
        f"({sum(f.formato == 'A' for f in validas)} con formato estándar, "
        f"{sum(f.formato == 'B' for f in validas)} con formato distinto que hay que revisar a fondo).",
        "Ninguna ficha trae el rendimiento total de la tanda: complételo en la hoja «Recetas» (columna amarilla).",
        "Las filas amarillas de «Ingredientes» y «Platos» tienen observaciones.",
    ] + [f"Hoja «{f.hoja}»: {'; '.join(f.avisos)}" for f in fichas if f.receta is None]
    return fichas, resumen


def convertir_a_plantilla(ruta_fichas, ruta_salida, db):
    """Lee las fichas y escribe la plantilla prellenada. Devuelve (fichas, resumen)."""
    from app.utils.plantilla_recetas import generar_plantilla

    fichas, resumen = leer_fichas(ruta_fichas)
    generar_plantilla(db, ruta_salida, [f.receta for f in fichas if f.receta], resumen)
    return fichas, resumen

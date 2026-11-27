"""Plantilla estándar para cargar recetas desde Excel (generar vacía o prellenada, y leerla).

Hojas:
  - Instrucciones
  - Recetas       una fila por tanda o sub-receta: código, nombre, tipo, rendimiento de la tanda y su unidad
  - Ingredientes  líneas de cada receta: insumo (por código o nombre) o sub-receta (código numérico), cantidad
                  de la TANDA y unidad
  - Platos        platos del menú (código del POS) que se sirven de una receta, con su porción: así un plato
                  normal y su versión «eco» comparten la misma tanda con porciones distintas
  - Insumos       (referencia) el catálogo de la app
  - Unidades      (referencia) las unidades de la app
  - Revisión      (solo si viene del convertidor de fichas) lo que hay que completar o corregir

La importación está en app/utils/importar_recetas.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.utils.importar_costeo_excel import norm

TIPOS = ("PLATO", "SUB-RECETA")

# (clave interna, encabezado, ancho, obligatorio)
COLS_RECETAS = [
    ("codigo", "Código receta", 14, True), ("nombre", "Nombre", 34, True), ("tipo", "Tipo", 13, True),
    ("rendimiento", "Rendimiento tanda", 18, True), ("unidad_rend", "Unidad rendimiento", 18, True),
    ("notas", "Notas", 60, False),
]
COLS_INGREDIENTES = [
    ("receta", "Código receta", 14, True), ("codigo", "Código insumo / sub-receta", 22, False),
    ("ingrediente", "Ingrediente", 34, True), ("cantidad", "Cantidad", 12, True), ("unidad", "Unidad", 10, True),
    ("observacion", "Observación", 60, False),
]
COLS_PLATOS = [
    ("codigo", "Código plato (POS)", 18, True), ("nombre", "Nombre plato", 34, False),
    ("receta", "Código receta", 14, True), ("porcion", "Porción", 12, True), ("unidad", "Unidad porción", 15, True),
    ("observacion", "Observación", 50, False),
]

INSTRUCCIONES = [
    "PLANTILLA PARA CARGAR RECETAS — Italos Manager",
    "",
    "1. Hoja «Recetas»: una fila por receta (tanda). Tipo PLATO = se sirve como plato; SUB-RECETA = se usa dentro",
    "   de otras recetas (guisos, salsas, arroz…). Su código es numérico (200, 203…) y así se la cita en Ingredientes.",
    "   «Rendimiento tanda» = cuánto sale en total de la tanda (p. ej. 4500 g). Es OBLIGATORIO: sin él no se puede",
    "   calcular la porción y la receta queda PENDIENTE (no se importa).",
    "2. Hoja «Ingredientes»: las cantidades son las de la TANDA completa. En «Código insumo / sub-receta» ponga el",
    "   código del insumo (V002, IC005…; vea la hoja «Insumos») o el código numérico de una sub-receta. Si no hay",
    "   código se busca por el nombre.",
    "   Unidades: g, kg, lb, oz, ml, l, gal, und. Si mide en ml algo que el insumo lleva en gramos (cebolla picada…),",
    "   el insumo debe tener «Gramos por ml» en Catálogo de Insumos.",
    "3. Hoja «Platos»: cada plato del menú (código del POS) que se sirve de la receta, con su porción (p. ej. 287 g).",
    "   Un plato normal y su versión eco pueden usar la misma receta con porciones distintas.",
    "4. En la app: Costo de Platos → Recetas de costeo → Importar recetas → Simular (no guarda) → revisar → Importar.",
    "   «Solo nuevas» no toca las recetas que ya existen; «Actualizar existentes» reemplaza las del archivo.",
    "   Nunca se borra nada que no esté en el archivo.",
    "5. Si falta un insumo, la receta no se importa y el reporte trae la hoja «Insumos faltantes»: complétela y",
    "   use «Importar insumos faltantes…» para crearlos; luego vuelva a importar las recetas.",
]


@dataclass
class LineaPlantilla:
    fila: int
    codigo: str
    ingrediente: str
    cantidad: float | None
    unidad: str
    observacion: str = ""


@dataclass
class PlatoPlantilla:
    fila: int
    codigo: str
    nombre: str
    porcion: float | None
    unidad: str
    observacion: str = ""


@dataclass
class RecetaPlantilla:
    fila: int
    codigo: str
    nombre: str
    tipo: str
    rendimiento: float | None
    unidad_rend: str
    notas: str = ""
    lineas: list = field(default_factory=list)
    platos: list = field(default_factory=list)
    revision: list = field(default_factory=list)  # pendientes que anota el convertidor de fichas


@dataclass
class Plantilla:
    recetas: list = field(default_factory=list)
    errores: list = field(default_factory=list)  # (hoja, fila, mensaje): problemas de forma del archivo


def a_numero(valor):
    """Número desde celda: acepta '4.69', '4,69' y '1,234.5'. None si no es número."""
    if isinstance(valor, bool) or valor is None:
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    t = str(valor).strip().replace(" ", "")
    if not t:
        return None
    if t.count(",") == 1 and "." not in t:
        t = t.replace(",", ".")
    else:
        t = t.replace(",", "")
    try:
        return float(t)
    except ValueError:
        return None


def codigo_texto(valor):
    """Código de receta/plato como texto: 38.0 -> '38', '#38 ' -> '38'."""
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    return str(valor or "").strip().lstrip("#").strip()


# ----------------------------------------------------------------------------- generar
def generar_plantilla(db, ruta, recetas=None, resumen=None):
    """Escribe la plantilla en `ruta`. `recetas` (lista de RecetaPlantilla) la prellena; `resumen` (líneas de
    texto) va al inicio de la hoja Revisión."""
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation

    rojo, gris = PatternFill("solid", fgColor="A20F22"), PatternFill("solid", fgColor="555555")
    blanco = Font(color="FFFFFF", bold=True)
    amarillo = PatternFill("solid", fgColor="FFF4CC")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Instrucciones"
    for i, linea in enumerate(INSTRUCCIONES, 1):
        ws.cell(i, 1, linea).font = Font(bold=(i == 1), size=13 if i == 1 else 11)
    ws.column_dimensions["A"].width = 120

    def hoja(nombre, cols):
        h = wb.create_sheet(nombre)
        for c, (_k, titulo, ancho, oblig) in enumerate(cols, 1):
            cel = h.cell(1, c, titulo + (" *" if oblig else ""))
            cel.fill, cel.font = (rojo if oblig else gris), blanco
            cel.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            h.column_dimensions[openpyxl.utils.get_column_letter(c)].width = ancho
        h.freeze_panes = "A2"
        return h

    unidades = [a for (a,) in db.fetch_all("SELECT abreviatura FROM unidades_medida ORDER BY abreviatura")]
    for estandar in ("g", "kg", "lb", "oz", "ml", "l", "gal", "und"):
        if estandar not in [norm(u) for u in unidades]:
            unidades.append(estandar)

    h_rec = hoja("Recetas", COLS_RECETAS)
    h_ing = hoja("Ingredientes", COLS_INGREDIENTES)
    h_pla = hoja("Platos", COLS_PLATOS)

    h_uni = wb.create_sheet("Unidades")
    h_uni.cell(1, 1, "Unidad").font = Font(bold=True)
    for i, u in enumerate(unidades, 2):
        h_uni.cell(i, 1, u)
    rango_unidades = f"Unidades!$A$2:$A${len(unidades) + 1}"

    for h, col in ((h_rec, "E"), (h_ing, "E"), (h_pla, "E")):
        dv = DataValidation(type="list", formula1=rango_unidades, allow_blank=True,
                            error="Elija una unidad de la hoja «Unidades».", showErrorMessage=False)
        h.add_data_validation(dv)
        dv.add(f"{col}2:{col}2000")
    dv_tipo = DataValidation(type="list", formula1='"PLATO,SUB-RECETA"', allow_blank=True)
    h_rec.add_data_validation(dv_tipo)
    dv_tipo.add("C2:C2000")

    h_ins = hoja("Insumos", [("codigo", "Código", 12, False), ("nombre", "Nombre", 40, False),
                             ("unidad", "Unidad base", 12, False), ("gml", "Gramos por ml", 14, False)])
    for i, (cod, nom, uni, gml) in enumerate(db.fetch_all(
            "SELECT i.codigo, i.nombre, u.abreviatura, i.gramos_por_ml FROM insumos i "
            "LEFT JOIN unidades_medida u ON u.id = i.unidad_base_id ORDER BY i.nombre"), 2):
        for c, v in enumerate((cod, nom, uni, gml), 1):
            h_ins.cell(i, c, v)

    fila_rec, fila_ing, fila_pla = 2, 2, 2
    for rec in recetas or []:
        for c, v in enumerate((rec.codigo, rec.nombre, rec.tipo, rec.rendimiento, rec.unidad_rend, rec.notas), 1):
            h_rec.cell(fila_rec, c, v)
        if rec.rendimiento is None:
            h_rec.cell(fila_rec, 4).fill = amarillo
        fila_rec += 1
        for ln in rec.lineas:
            for c, v in enumerate((rec.codigo, ln.codigo, ln.ingrediente, ln.cantidad, ln.unidad, ln.observacion), 1):
                h_ing.cell(fila_ing, c, v)
            if ln.observacion:
                for c in range(1, 7):
                    h_ing.cell(fila_ing, c).fill = amarillo
            fila_ing += 1
        for pl in rec.platos:
            for c, v in enumerate((pl.codigo, pl.nombre, rec.codigo, pl.porcion, pl.unidad, pl.observacion), 1):
                h_pla.cell(fila_pla, c, v)
            if pl.observacion or pl.porcion is None:
                for c in range(1, 7):
                    h_pla.cell(fila_pla, c).fill = amarillo
            fila_pla += 1

    if recetas is not None and (resumen or any(r.revision for r in recetas)):
        h_rev = hoja("Revisión", [("receta", "Código receta", 14, False), ("nombre", "Receta", 34, False),
                                  ("pendiente", "Qué revisar o completar", 110, False)])
        f = 2
        for linea in resumen or []:
            h_rev.cell(f, 3, linea).font = Font(bold=True)
            f += 1
        if resumen:
            f += 1
        for rec in recetas:
            for p in rec.revision:
                h_rev.cell(f, 1, rec.codigo)
                h_rev.cell(f, 2, rec.nombre)
                h_rev.cell(f, 3, p)
                f += 1
        wb.move_sheet("Revisión", offset=-(len(wb.sheetnames) - 2))  # justo después de Instrucciones

    wb.save(ruta)
    return ruta


# ----------------------------------------------------------------------------- leer
def _mapa_columnas(ws, cols, errores):
    """{clave: número de columna} según los encabezados de la fila 1 (tolera orden distinto y el « *»)."""
    titulos = {norm(str(c.value or "").replace("*", "")): c.column for c in ws[1] if c.value}
    mapa = {}
    for clave, titulo, _ancho, oblig in cols:
        col = titulos.get(norm(titulo))
        if col is None and oblig:
            errores.append((ws.title, 1, f"Falta la columna «{titulo}»"))
        mapa[clave] = col
    return mapa


def _filas(ws, cols, errores):
    mapa = _mapa_columnas(ws, cols, errores)
    for r in range(2, ws.max_row + 1):
        fila = {k: (ws.cell(r, c).value if c else None) for k, c in mapa.items()}
        if all(v is None or str(v).strip() == "" for v in fila.values()):
            continue
        yield r, fila


def _texto(v):
    return str(v).strip() if v is not None else ""


def leer_plantilla(ruta):
    """Lee la plantilla y devuelve Plantilla(recetas, errores). No valida contra la base de datos."""
    import openpyxl

    wb = openpyxl.load_workbook(ruta, data_only=True)
    res = Plantilla()
    hojas = {norm(n): wb[n] for n in wb.sheetnames}
    faltan = [n for n in ("Recetas", "Ingredientes", "Platos") if norm(n) not in hojas]
    if faltan:
        raise ValueError("El archivo no tiene el formato de la plantilla de recetas (faltan las hojas: "
                         + ", ".join(faltan) + "). Descargue la plantilla desde la app.")

    por_codigo = {}
    for r, f in _filas(hojas["recetas"], COLS_RECETAS, res.errores):
        cod = codigo_texto(f["codigo"])
        if not cod:
            res.errores.append(("Recetas", r, "Fila sin «Código receta»"))
            continue
        if cod in por_codigo:
            res.errores.append(("Recetas", r, f"El código de receta {cod} está repetido (fila {por_codigo[cod].fila})"))
            continue
        tipo = norm(f["tipo"]).upper().replace(" ", "-") or "PLATO"
        tipo = "SUB-RECETA" if tipo.startswith("SUB") else tipo
        if tipo not in TIPOS:
            res.errores.append(("Recetas", r, f"Tipo «{f['tipo']}» no válido (use PLATO o SUB-RECETA)"))
            tipo = "PLATO"
        rec = RecetaPlantilla(r, cod, _texto(f["nombre"]), tipo, a_numero(f["rendimiento"]),
                              _texto(f["unidad_rend"]), _texto(f["notas"]))
        por_codigo[cod] = rec
        res.recetas.append(rec)

    for r, f in _filas(hojas["ingredientes"], COLS_INGREDIENTES, res.errores):
        rec = por_codigo.get(codigo_texto(f["receta"]))
        if rec is None:
            res.errores.append(("Ingredientes", r, f"La receta «{_texto(f['receta'])}» no está en la hoja Recetas"))
            continue
        rec.lineas.append(LineaPlantilla(r, codigo_texto(f["codigo"]), _texto(f["ingrediente"]),
                                         a_numero(f["cantidad"]), _texto(f["unidad"]), _texto(f["observacion"])))

    for r, f in _filas(hojas["platos"], COLS_PLATOS, res.errores):
        rec = por_codigo.get(codigo_texto(f["receta"]))
        if rec is None:
            res.errores.append(("Platos", r, f"La receta «{_texto(f['receta'])}» no está en la hoja Recetas"))
            continue
        rec.platos.append(PlatoPlantilla(r, codigo_texto(f["codigo"]), _texto(f["nombre"]),
                                         a_numero(f["porcion"]), _texto(f["unidad"]), _texto(f["observacion"])))
    return res

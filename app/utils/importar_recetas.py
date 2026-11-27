"""Importa recetas desde la plantilla estándar (app/utils/plantilla_recetas.py) al módulo Costo de platos.

Reglas (decididas con el usuario):
  - Rendimiento de la tanda OBLIGATORIO: sin él la receta queda PENDIENTE y no se importa.
  - Insumos: se buscan por código (insumos.codigo) y luego por nombre. Si no existe, la receta NO se importa
    (nunca a medias) y el insumo va a la hoja «Insumos faltantes» del reporte.
  - Las cantidades se guardan convertidas a la unidad base del insumo (la vista v_recetas_explotadas, que usan
    Kardex y presupuestos, no convierte). Volumen <-> masa usa insumos.gramos_por_ml; si falta, se bloquea.
  - Una receta con un solo plato: el plato es la tanda (rendimiento + porción en menu_items). Con varios platos
    (normal / eco): la tanda se crea como sub-receta «R<código>» y cada plato lleva su porción de ella.
  - modo NUEVAS no toca recetas que ya tienen líneas; ACTUALIZAR reemplaza solo las del archivo. Nunca se
    borra nada que no esté en el archivo. Todo en una transacción; dry_run=True hace rollback.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.controllers.costeo_controller import _UNIDADES_ESTANDAR
from app.utils.codigo_insumo import es_codigo_subreceta, normalizar_codigo_insumo
from app.utils.fichas_bano_maria import unidad_estandar
from app.utils.importar_costeo_excel import clave_palabras, norm
from app.utils.plantilla_recetas import leer_plantilla

_NOMBRE_UNIDAD = {"g": "Gramo", "kg": "Kilogramo", "lb": "Libra", "oz": "Onza", "ml": "Mililitro",
                  "l": "Litro", "gal": "Galón", "und": "Unidad"}
_FAMILIA = dict(_UNIDADES_ESTANDAR, l=("vol", 1000.0))


def clave_singular(nombre):
    """Clave de nombre tolerante a plurales y orden: «2 Cebollas» y «cebolla» -> misma clave."""
    palabras = []
    for w in clave_palabras(nombre).split():
        if len(w) > 4 and w.endswith("es") and w[-3] not in "aeiou":
            w = w[:-2]          # «limones» -> «limon»
        elif len(w) > 3 and w.endswith("s"):
            w = w[:-1]          # «cebollas» -> «cebolla»
        palabras.append(w)
    return " ".join(sorted(palabras))


def convertir_cantidad(cantidad, u_origen, u_destino, gramos_por_ml=None):
    """(cantidad convertida, None) o (None, motivo). Volumen <-> masa solo con gramos_por_ml."""
    o, d = unidad_estandar(u_origen), unidad_estandar(u_destino)
    if o == d:
        return cantidad, None
    fo, fd = _FAMILIA.get(o), _FAMILIA.get(d)
    if not fo or not fd:
        return None, f"no se puede convertir «{o}» a «{d}»"
    base = cantidad * fo[1]  # en g o ml
    if fo[0] != fd[0]:
        if not gramos_por_ml:
            return None, "falta «Gramos por ml»"
        base = base * gramos_por_ml if fo[0] == "vol" else base / gramos_por_ml
    return base / fd[1], None


@dataclass
class Resultado:
    dry_run: bool = True
    modo: str = "NUEVAS"
    importadas: int = 0
    actualizadas: int = 0
    omitidas: int = 0
    pendientes: int = 0
    bloqueadas: int = 0
    platos_creados: int = 0
    unidades_creadas: int = 0
    lineas: int = 0
    problemas: list = field(default_factory=list)   # (nivel, receta, fila, mensaje)
    faltantes: dict = field(default_factory=dict)   # nombre norm -> {codigo, nombre, unidad, recetas, veces}

    def agregar(self, nivel, receta, fila, mensaje):
        self.problemas.append((nivel, receta, fila, mensaje))

    def texto(self):
        cab = "SIMULACIÓN (no se guardó nada)" if self.dry_run else "IMPORTACIÓN REALIZADA"
        modo = "solo recetas nuevas" if self.modo == "NUEVAS" else "actualizar existentes"
        out = [cab, "=" * len(cab), f"Modo: {modo}",
               f"Importadas: {self.importadas}   actualizadas: {self.actualizadas}   ya existían (omitidas): "
               f"{self.omitidas}",
               f"Pendientes (sin rendimiento): {self.pendientes}   bloqueadas por errores: {self.bloqueadas}",
               f"Platos creados: {self.platos_creados}   unidades creadas: {self.unidades_creadas}   "
               f"líneas: {self.lineas}"]
        if self.faltantes:
            out += ["", f"INSUMOS FALTANTES ({len(self.faltantes)}) — créelos y vuelva a importar "
                        "(«Guardar reporte…» trae la hoja para «Importar insumos faltantes…»)"]
            out += [f"  • {f['nombre']}" + (f" [{f['codigo']}]" if f["codigo"] else "")
                    + f" — usado en {len(f['recetas'])} receta(s)" for f in self.faltantes.values()]
        for nivel, titulo in (("ERROR", "BLOQUEA LA RECETA"), ("PENDIENTE", "PENDIENTES"), ("AVISO", "AVISOS"),
                              ("INFO", "INFORMACIÓN")):
            items = [p for p in self.problemas if p[0] == nivel]
            if items:
                out += ["", f"{titulo} ({len(items)})"]
                out += [f"  • [{r}]" + (f" fila {f}:" if f else "") + f" {m}" for _n, r, f, m in items]
        return "\n".join(out)


def importar(db, ruta, dry_run=True, modo="NUEVAS"):
    plantilla = leer_plantilla(ruta)
    res = Resultado(dry_run=dry_run, modo=modo)
    for hoja, fila, msg in plantilla.errores:
        res.agregar("ERROR", f"hoja {hoja}", fila, msg)
    cur = db.conn.cursor()
    try:
        _Importador(cur, res, modo).ejecutar(plantilla.recetas)
        db.conn.rollback() if dry_run else db.conn.commit()
    except Exception:
        db.conn.rollback()
        raise
    return res


class _Importador:
    def __init__(self, cur, res, modo):
        self.cur, self.res, self.modo = cur, res, modo
        self.unidades = {}  # abreviatura estándar -> (id, abreviatura en la BD)
        for uid, abrev in cur.execute("SELECT id, abreviatura FROM unidades_medida ORDER BY id"):
            self.unidades.setdefault(unidad_estandar(abrev), uid)
        self.abrev_por_id = {uid: a for a, uid in self.unidades.items()}
        self.ins_codigo, self.ins_nombre, self.ins_palabras, self.ins_singular = {}, {}, {}, {}
        for iid, cod, nombre, ub, gml in cur.execute(
                "SELECT id, codigo, nombre, unidad_base_id, gramos_por_ml FROM insumos"):
            info = (iid, nombre, ub, gml)
            if cod:
                self.ins_codigo[normalizar_codigo_insumo(cod)] = info
            self.ins_nombre.setdefault(norm(nombre), info)
            self.ins_palabras.setdefault(clave_palabras(nombre), info)
            self.ins_singular.setdefault(clave_singular(nombre), info)
        self.subrecetas = {}  # código numérico -> id de menu_items (de la BD o importada en esta corrida)

    # -------------------------------------------------------------- utilidades
    def _abrev(self, unidad_id):
        if unidad_id not in self.abrev_por_id:
            r = self.cur.execute("SELECT abreviatura FROM unidades_medida WHERE id=?", (unidad_id,)).fetchone()
            self.abrev_por_id[unidad_id] = unidad_estandar(r[0]) if r else ""
        return self.abrev_por_id[unidad_id]

    def _unidad_id(self, abrev):
        """Id de la unidad (la crea si es estándar y no existe). None si no se reconoce."""
        a = unidad_estandar(abrev)
        if a in self.unidades:
            return self.unidades[a]
        if a not in _NOMBRE_UNIDAD:
            return None
        self.cur.execute("INSERT INTO unidades_medida (nombre, abreviatura) VALUES (?,?)", (_NOMBRE_UNIDAD[a], a))
        self.unidades[a] = self.cur.lastrowid
        self.abrev_por_id[self.cur.lastrowid] = a
        self.res.unidades_creadas += 1
        return self.unidades[a]

    def _item_por_codigo(self, codigo, componente=None):
        filtro = "" if componente is None else f" AND COALESCE(es_componente,0) = {1 if componente else 0}"
        r = self.cur.execute(f"SELECT id FROM menu_items WHERE codigo IN (?, ?){filtro} ORDER BY id LIMIT 1",
                             (codigo, f"#{codigo}")).fetchone()
        return r[0] if r else None

    def _tiene_receta(self, item_id):
        return self.cur.execute(
            "SELECT (SELECT COUNT(*) FROM recetas WHERE menu_item_id=?) + "
            "(SELECT COUNT(*) FROM receta_componentes WHERE menu_item_id=?)", (item_id, item_id)).fetchone()[0] > 0

    def _borrar_receta(self, item_id):
        self.cur.execute("DELETE FROM recetas WHERE menu_item_id=?", (item_id,))
        self.cur.execute("DELETE FROM receta_componentes WHERE menu_item_id=?", (item_id,))

    def _crear_item(self, codigo, nombre, componente, categoria):
        self.cur.execute(
            "INSERT INTO menu_items (codigo, nombre, precio_venta, es_preparado, es_componente, categoria_costeo) "
            "VALUES (?,?,0,1,?,?)", (codigo, nombre, 1 if componente else 0, categoria))
        return self.cur.lastrowid

    def _faltante(self, ln, receta):
        clave = norm(ln.ingrediente)
        f = self.res.faltantes.setdefault(clave, {"codigo": ln.codigo, "nombre": ln.ingrediente,
                                                 "unidad": "", "recetas": [], "veces": 0})
        fam = _FAMILIA.get(unidad_estandar(ln.unidad))
        f["unidad"] = f["unidad"] or ("g" if fam and fam[0] == "masa" else "ml" if fam else unidad_estandar(ln.unidad))
        f["codigo"] = f["codigo"] or ln.codigo
        if receta not in f["recetas"]:
            f["recetas"].append(receta)
        f["veces"] += 1

    # -------------------------------------------------------------- ejecución
    def ejecutar(self, recetas):
        # Sub-recetas primero: las demás las citan por código
        for rec in sorted(recetas, key=lambda r: r.tipo != "SUB-RECETA"):
            self._receta(rec)

    def _resolver_insumo(self, ln, ambito):
        info = self.ins_codigo.get(normalizar_codigo_insumo(ln.codigo)) if ln.codigo else None
        por_nombre = (self.ins_nombre.get(norm(ln.ingrediente)) or self.ins_palabras.get(clave_palabras(ln.ingrediente))
                      or self.ins_singular.get(clave_singular(ln.ingrediente)))
        if info:
            if por_nombre is not info and norm(info[1]) != norm(ln.ingrediente):
                self.res.agregar("AVISO", ambito, ln.fila, f"El código {ln.codigo} es «{info[1]}» en la app pero el "
                                 f"archivo dice «{ln.ingrediente}»: se usó «{info[1]}» (por código)")
            return info
        if por_nombre and ln.codigo:
            self.res.agregar("AVISO", ambito, ln.fila, f"«{por_nombre[1]}» se encontró por nombre; el código "
                             f"{ln.codigo} no lo tiene ningún insumo (puede asignárselo en Catálogo de Insumos)")
        return por_nombre

    def _receta(self, rec):
        ambito = f"{rec.codigo} {rec.nombre}".strip()
        errores = []

        def error(fila, msg):
            errores.append((fila, msg))

        if not rec.nombre:
            error(rec.fila, "Falta el nombre de la receta")
        if rec.rendimiento is None or rec.rendimiento <= 0:
            self.res.pendientes += 1
            self.res.agregar("PENDIENTE", ambito, rec.fila, "Sin «Rendimiento tanda»: no se importa hasta completarlo")
            return
        u_rend = self._unidad_id(rec.unidad_rend) if rec.unidad_rend else None
        if not u_rend:
            error(rec.fila, f"Unidad de rendimiento «{rec.unidad_rend}» no válida")
        if not rec.lineas:
            error(rec.fila, "La receta no tiene ingredientes")
        if rec.tipo == "PLATO" and not rec.platos:
            error(rec.fila, "Indique en la hoja «Platos» al menos un plato (código del POS) con su porción")

        # Ingredientes -> {insumo_id: cantidad en base} y {componente_id: (cantidad, unidad_id)}
        insumos, comps = {}, {}
        for ln in rec.lineas:
            if not ln.ingrediente:
                error(ln.fila, "Línea sin ingrediente")
                continue
            if ln.cantidad is None or ln.cantidad <= 0:
                error(ln.fila, f"«{ln.ingrediente}» sin cantidad")
                continue
            if not ln.unidad:
                error(ln.fila, f"«{ln.ingrediente}» sin unidad")
                continue
            if ln.codigo and es_codigo_subreceta(ln.codigo):
                cid = self.subrecetas.get(ln.codigo) or self._item_por_codigo(ln.codigo)
                if not cid:
                    error(ln.fila, f"La sub-receta {ln.codigo} «{ln.ingrediente}» no existe en la app ni se importó "
                                   "en este archivo")
                    continue
                u_comp = self.cur.execute("SELECT unidad_rendimiento_id FROM menu_items WHERE id=?",
                                          (cid,)).fetchone()[0]
                if u_comp:
                    q, motivo = convertir_cantidad(ln.cantidad, ln.unidad, self._abrev(u_comp))
                    if q is None and motivo.startswith("falta"):
                        q, _ = convertir_cantidad(ln.cantidad, ln.unidad, self._abrev(u_comp), gramos_por_ml=1.0)
                        self.res.agregar("AVISO", ambito, ln.fila, f"Sub-receta «{ln.ingrediente}»: se tomó 1 ml = 1 g "
                                         f"({ln.unidad} → {self._abrev(u_comp)})")
                    if q is None:
                        error(ln.fila, f"Sub-receta «{ln.ingrediente}»: {motivo}")
                        continue
                else:
                    q, u_comp = ln.cantidad, self._unidad_id(ln.unidad)
                prev = comps.get(cid, (0.0, u_comp))[0]
                comps[cid] = (prev + q, u_comp)
                continue
            info = self._resolver_insumo(ln, ambito)
            if info is None:
                self._faltante(ln, ambito)
                error(ln.fila, f"Insumo no encontrado: «{ln.ingrediente}»" + (f" [{ln.codigo}]" if ln.codigo else ""))
                continue
            iid, nombre, ub, gml = info
            q, motivo = convertir_cantidad(ln.cantidad, ln.unidad, self._abrev(ub), gml)
            if q is None:
                error(ln.fila, f"«{nombre}» ({ln.cantidad:g} {ln.unidad} → {self._abrev(ub)}): {motivo}"
                      + (" — defínalo en Catálogo de Insumos" if motivo.startswith("falta") else ""))
                continue
            insumos[iid] = insumos.get(iid, 0.0) + q

        # Platos: porción convertida a la unidad del rendimiento
        platos = []
        for pl in rec.platos if rec.tipo == "PLATO" else []:
            if not pl.codigo:
                error(pl.fila, "Plato sin código")
                continue
            if pl.porcion is None or pl.porcion <= 0 or not pl.unidad:
                error(pl.fila, f"Plato {pl.codigo}: falta la porción o su unidad")
                continue
            q, motivo = (convertir_cantidad(pl.porcion, pl.unidad, rec.unidad_rend) if u_rend else (None, ""))
            if q is None and motivo.startswith("falta"):
                q, _ = convertir_cantidad(pl.porcion, pl.unidad, rec.unidad_rend, gramos_por_ml=1.0)
                self.res.agregar("AVISO", ambito, pl.fila, f"Plato {pl.codigo}: porción en {pl.unidad} y rendimiento en "
                                 f"{rec.unidad_rend}; se tomó 1 ml = 1 g")
            if q is None:
                if u_rend:
                    error(pl.fila, f"Plato {pl.codigo}: {motivo}")
                continue
            platos.append((pl, q))
        if rec.tipo == "SUB-RECETA" and rec.platos:
            self.res.agregar("AVISO", ambito, rec.fila, "Las sub-recetas no llevan platos: se ignoró la hoja Platos")

        if errores:
            self.res.bloqueadas += 1
            for fila, msg in errores:
                self.res.agregar("ERROR", ambito, fila, msg)
            return

        # ---- destino: quién lleva la tanda
        if rec.tipo == "SUB-RECETA":
            codigo_tanda, es_comp = f"#{rec.codigo}", True
        elif len(platos) == 1:
            codigo_tanda, es_comp = None, False
        else:
            codigo_tanda, es_comp = f"R{rec.codigo}", True

        items_platos = []
        for pl, q in platos:
            pid = self._item_por_codigo(pl.codigo, componente=False)
            if pid is None:
                r = self.cur.execute("SELECT id FROM menu_items WHERE lower(trim(nombre)) = lower(trim(?)) "
                                     "AND COALESCE(es_componente,0)=0", (pl.nombre or rec.nombre,)).fetchone()
                pid = r[0] if r else None
            items_platos.append((pl, q, pid))

        tanda_id = None
        if codigo_tanda:
            r = self.cur.execute("SELECT id FROM menu_items WHERE codigo=?", (codigo_tanda,)).fetchone()
            tanda_id = r[0] if r else None
            if tanda_id is None and rec.tipo == "SUB-RECETA":
                tanda_id = self._item_por_codigo(rec.codigo, componente=True)  # «200» o «#200»

        existentes = [i for i in [tanda_id] + [p[2] for p in items_platos] if i and self._tiene_receta(i)]
        if existentes and self.modo == "NUEVAS":
            self.res.omitidas += 1
            self.res.agregar("INFO", ambito, rec.fila, "Ya tiene receta en la app: se omite (use «Actualizar existentes»)")
            if rec.tipo == "SUB-RECETA" and tanda_id:
                self.subrecetas[rec.codigo] = tanda_id
            return

        # ---- escribir
        for i in existentes:
            self._borrar_receta(i)
        if codigo_tanda:
            if tanda_id is None:
                tanda_id = self._crear_item(codigo_tanda, rec.nombre if rec.tipo == "SUB-RECETA"
                                            else f"{rec.nombre} (tanda)", True, "componente")
            self._escribir_lineas(tanda_id, insumos, comps)
            self.cur.execute("UPDATE menu_items SET rendimiento=?, unidad_rendimiento_id=?, porcion_servida=NULL, "
                             "unidad_porcion_id=NULL, es_componente=1 WHERE id=?", (rec.rendimiento, u_rend, tanda_id))
            if rec.tipo == "SUB-RECETA":
                self.subrecetas[rec.codigo] = tanda_id
        for pl, q, pid in items_platos:
            if pid is None:
                pid = self._crear_item(pl.codigo, pl.nombre or rec.nombre, False, "plato")
                self.res.platos_creados += 1
                self.res.agregar("AVISO", ambito, pl.fila, f"Plato {pl.codigo} «{pl.nombre or rec.nombre}» no existía en "
                                 "el Menú: se creó con precio 0 (complete el precio)")
            if tanda_id:  # varios platos: cada uno lleva su porción de la tanda
                self.cur.execute("INSERT INTO receta_componentes (menu_item_id, componente_id, cantidad, unidad_id) "
                                 "VALUES (?,?,?,?)", (pid, tanda_id, q, u_rend))
                self.cur.execute("UPDATE menu_items SET rendimiento=NULL, unidad_rendimiento_id=NULL, "
                                 "porcion_servida=NULL, unidad_porcion_id=NULL WHERE id=?", (pid,))
            else:          # un solo plato: el plato es la tanda
                self._escribir_lineas(pid, insumos, comps)
                self.cur.execute("UPDATE menu_items SET rendimiento=?, unidad_rendimiento_id=?, porcion_servida=?, "
                                 "unidad_porcion_id=? WHERE id=?", (rec.rendimiento, u_rend, q, u_rend, pid))
        if existentes:
            self.res.actualizadas += 1
        else:
            self.res.importadas += 1
        self.res.lineas += len(insumos) + len(comps)

    def _escribir_lineas(self, item_id, insumos, comps):
        for iid, q in insumos.items():
            ub = self.cur.execute("SELECT unidad_base_id FROM insumos WHERE id=?", (iid,)).fetchone()[0]
            self.cur.execute("INSERT INTO recetas (menu_item_id, insumo_id, cantidad_necesaria, unidad_id) "
                             "VALUES (?,?,?,?)", (item_id, iid, q, ub))
        for cid, (q, uid) in comps.items():
            self.cur.execute("INSERT INTO receta_componentes (menu_item_id, componente_id, cantidad, unidad_id) "
                             "VALUES (?,?,?,?)", (item_id, cid, q, uid))


# ----------------------------------------------------------------------------- reporte
def exportar_reporte(res, ruta):
    """Excel con Resumen, Problemas e Insumos faltantes (esta última se puede completar e importar)."""
    import openpyxl
    from openpyxl.styles import Font, PatternFill

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Resumen"
    for i, linea in enumerate(res.texto().split("\n")[:7], 1):
        ws.cell(i, 1, linea)
    ws.column_dimensions["A"].width = 110
    cab = Font(color="FFFFFF", bold=True)
    rojo = PatternFill("solid", fgColor="A20F22")

    hp = wb.create_sheet("Problemas")
    for c, t in enumerate(("Nivel", "Receta", "Fila", "Mensaje"), 1):
        hp.cell(1, c, t).font, hp.cell(1, c).fill = cab, rojo
    for r, (nivel, receta, fila, msg) in enumerate(res.problemas, 2):
        for c, v in enumerate((nivel, receta, fila, msg), 1):
            hp.cell(r, c, v)
    for col, ancho in zip("ABCD", (11, 34, 7, 110)):
        hp.column_dimensions[col].width = ancho

    hf = wb.create_sheet("Insumos faltantes")
    titulos = ("Código", "Nombre *", "Unidad base *", "Gramos por ml", "Categoría", "Usado en", "Veces")
    for c, t in enumerate(titulos, 1):
        hf.cell(1, c, t).font, hf.cell(1, c).fill = cab, rojo
    for r, f in enumerate(res.faltantes.values(), 2):
        for c, v in enumerate((f["codigo"], f["nombre"], f["unidad"], None, None,
                               "; ".join(f["recetas"]), f["veces"]), 1):
            hf.cell(r, c, v)
    for col, ancho in zip("ABCDEFG", (10, 32, 14, 14, 18, 70, 7)):
        hf.column_dimensions[col].width = ancho
    wb.save(ruta)
    return ruta


def importar_insumos_faltantes(db, ruta):
    """Crea los insumos de la hoja «Insumos faltantes» (revisada). No toca los que ya existen.

    Devuelve (creados, mensajes)."""
    import openpyxl

    wb = openpyxl.load_workbook(ruta, data_only=True)
    hoja = next((wb[n] for n in wb.sheetnames if norm(n) == "insumos faltantes"), None)
    if hoja is None:
        raise ValueError("El archivo no tiene la hoja «Insumos faltantes» (use el reporte de la importación).")
    titulos = {norm(str(c.value or "").replace("*", "")): c.column for c in hoja[1] if c.value}
    col = lambda nombre: titulos.get(norm(nombre))  # noqa: E731
    cur = db.conn.cursor()
    unidades = {}
    for uid, abrev in cur.execute("SELECT id, abreviatura FROM unidades_medida ORDER BY id"):
        unidades.setdefault(unidad_estandar(abrev), uid)
    categorias = {norm(n): i for i, n in cur.execute("SELECT id, nombre FROM categorias_insumos")}
    creados, mensajes = 0, []
    try:
        for r in range(2, hoja.max_row + 1):
            v = lambda nombre: hoja.cell(r, col(nombre)).value if col(nombre) else None  # noqa: E731
            nombre = str(v("Nombre") or "").strip()
            if not nombre:
                continue
            codigo = normalizar_codigo_insumo(v("Código")) or None
            u = unidad_estandar(v("Unidad base"))
            if codigo and cur.execute("SELECT 1 FROM insumos WHERE codigo=?", (codigo,)).fetchone():
                mensajes.append(f"Fila {r}: ya existe un insumo con código {codigo}; no se creó «{nombre}»")
                continue
            if cur.execute("SELECT 1 FROM insumos WHERE lower(trim(nombre)) = lower(trim(?))", (nombre,)).fetchone():
                mensajes.append(f"Fila {r}: «{nombre}» ya existe; no se creó")
                continue
            if u not in unidades:
                if u not in _NOMBRE_UNIDAD:
                    mensajes.append(f"Fila {r}: unidad «{v('Unidad base')}» no válida para «{nombre}»")
                    continue
                cur.execute("INSERT INTO unidades_medida (nombre, abreviatura) VALUES (?,?)", (_NOMBRE_UNIDAD[u], u))
                unidades[u] = cur.lastrowid
            gml = v("Gramos por ml")
            gml = float(gml) if isinstance(gml, (int, float)) and gml > 0 else None
            cat = categorias.get(norm(v("Categoría"))) if v("Categoría") else None
            cur.execute("INSERT INTO insumos (nombre, unidad_base_id, categoria_id, codigo, gramos_por_ml) "
                        "VALUES (?,?,?,?,?)", (nombre[:1].upper() + nombre[1:], unidades[u], cat, codigo, gml))
            creados += 1
        db.conn.commit()
    except Exception:
        db.conn.rollback()
        raise
    mensajes.insert(0, f"Insumos creados: {creados}. Complete su presentación de compra y precio en Catálogo "
                       "de Insumos para que tengan costo.")
    return creados, mensajes

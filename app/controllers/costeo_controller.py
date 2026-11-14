# [FILE: app/controllers/costeo_controller.py]
"""Costo de platos: receta (por porción o por tanda) + sub-recetas + acompañamientos
+ indirectos por plato vendido + precio sugerido.

Convención de recetas (ver connection._migrate_costeo_platos):
  - menu_items.rendimiento NULL  => `recetas.cantidad_necesaria` es por PORCIÓN.
  - menu_items.rendimiento = R   => es por TANDA; costo/porción = costo_tanda * porcion/R.
La vista no calcula: todo pasa por CosteoController.
"""

# Respaldo cuando conversiones_unidades no tiene el par: abreviatura -> (familia, factor a base)
_UNIDADES_ESTANDAR = {
    "g": ("masa", 1.0), "gr": ("masa", 1.0), "kg": ("masa", 1000.0),
    "lb": ("masa", 453.592), "oz": ("masa", 28.3495),
    "ml": ("vol", 1.0), "l": ("vol", 1000.0), "lt": ("vol", 1000.0),
    "gal": ("vol", 3785.41),
}

from app.database.costeo_sql import SQL_FACTOR_PORCION  # noqa: F401  (reexport)

CANALES = ("LOCAL", "LLEVAR")
TIPOS_EXTRA = ("ACOMPANAMIENTO", "BEBIDA", "EMPAQUE")


def precio_sugerido(costo, pct_ganancia):
    """costo / (1 - pct/100). None si el porcentaje no es válido (>=100)."""
    try:
        pct = float(pct_ganancia)
    except (TypeError, ValueError):
        return None
    if pct >= 100:
        return None
    return float(costo) / (1.0 - pct / 100.0)


def margen(precio_venta, costo):
    """(margen_$, food_cost_%, margen_%) contra el precio de venta actual."""
    precio = float(precio_venta or 0)
    costo = float(costo or 0)
    if precio <= 0:
        return (None, None, None)
    return (precio - costo, costo / precio * 100.0, (precio - costo) / precio * 100.0)


class CosteoController:
    def __init__(self, db):
        self.db = db
        self._cache_unidad = {}
        self._cache_costo_insumo = {}
        self._cache_unitario = {}

    def limpiar_cache(self):
        self._cache_unidad.clear()
        self._cache_costo_insumo.clear()
        self._cache_unitario.clear()

    # ---------------------------------------------------------------- config
    def config(self, clave, defecto=None):
        row = self.db.fetch_one("SELECT valor FROM costeo_config WHERE clave = ?", (clave,))
        return row[0] if row else defecto

    def config_float(self, clave, defecto=0.0):
        try:
            return float(self.config(clave, defecto))
        except (TypeError, ValueError):
            return float(defecto)

    # ------------------------------------------------------------- unidades
    def _abrev(self, unidad_id):
        if unidad_id not in self._cache_unidad:
            row = self.db.fetch_one(
                "SELECT abreviatura FROM unidades_medida WHERE id = ?", (unidad_id,))
            self._cache_unidad[unidad_id] = str(row[0]).strip().lower() if row else ""
        return self._cache_unidad[unidad_id]

    def convertir(self, cantidad, unidad_origen_id, unidad_destino_id):
        """Convierte `cantidad` entre unidades. None si no hay conversión posible.
        Sin unidad en origen o destino, o iguales, devuelve la cantidad tal cual."""
        if not unidad_origen_id or not unidad_destino_id or unidad_origen_id == unidad_destino_id:
            return cantidad
        row = self.db.fetch_one(
            "SELECT factor_conversion FROM conversiones_unidades "
            "WHERE unidad_origen_id = ? AND unidad_destino_id = ?",
            (unidad_origen_id, unidad_destino_id))
        if row and row[0]:
            return cantidad * row[0]
        o = _UNIDADES_ESTANDAR.get(self._abrev(unidad_origen_id))
        d = _UNIDADES_ESTANDAR.get(self._abrev(unidad_destino_id))
        if o and d and o[0] == d[0]:
            return cantidad * o[1] / d[1]
        return None

    # ---------------------------------------------------------------- insumos
    def costo_unitario_insumo(self, insumo_id):
        """(costo por unidad base, sin_costo). Según config fuente_costo_insumo:
        VIGENTE = presentación vigente (fallback promedio); PROMEDIO = WAC (fallback presentación)."""
        if insumo_id in self._cache_costo_insumo:
            return self._cache_costo_insumo[insumo_id]
        pres = self.db.fetch_one(
            "SELECT costo_unitario_calculado FROM presentaciones_compra "
            "WHERE insumo_id = ? AND costo_unitario_calculado > 0 ORDER BY id LIMIT 1",
            (insumo_id,))
        wac = self.db.fetch_one("SELECT costo_unitario FROM insumos WHERE id = ?", (insumo_id,))
        c_pres = float(pres[0]) if pres and pres[0] else 0.0
        c_wac = float(wac[0]) if wac and wac[0] else 0.0
        orden = (c_wac, c_pres) if self.config("fuente_costo_insumo") == "PROMEDIO" else (c_pres, c_wac)
        costo = next((c for c in orden if c > 0), 0.0)
        res = (costo, costo <= 0)
        self._cache_costo_insumo[insumo_id] = res
        return res

    # --------------------------------------------------------- receta / plato
    def _item(self, menu_item_id):
        return self.db.fetch_one(
            "SELECT id, codigo, nombre, precio_venta, categoria_costeo, es_componente, "
            "rendimiento, unidad_rendimiento_id, porcion_servida, unidad_porcion_id "
            "FROM menu_items WHERE id = ?", (menu_item_id,))

    def factor_por_porcion(self, menu_item_id):
        """Único punto que interpreta rendimiento/porción: multiplica el costo (o la
        cantidad de insumo) de la receta para obtener lo de UNA porción. 1.0 si la
        receta ya es por porción (rendimiento NULL)."""
        it = self._item(menu_item_id)
        return self._factor(it) if it else 1.0

    def _factor(self, it):
        rend, u_rend, porcion, u_por = it[6], it[7], it[8], it[9]
        if not rend or rend <= 0 or not porcion or porcion <= 0:
            return 1.0
        por = self.convertir(porcion, u_por, u_rend)
        return (por if por is not None else porcion) / rend

    def costo_tanda(self, menu_item_id, _pila=None):
        """Costo de la receta completa (tanda o porción según rendimiento).
        Devuelve {total, lineas[], advertencias[]}."""
        pila = set(_pila or ())
        res = {"total": 0.0, "lineas": [], "advertencias": []}
        if menu_item_id in pila:
            res["advertencias"].append("Ciclo de sub-recetas detectado")
            return res
        pila.add(menu_item_id)

        for _rid, ins_id, nombre, cant, unid_id, base_id in self.db.fetch_all(
            "SELECT r.id, r.insumo_id, i.nombre, r.cantidad_necesaria, r.unidad_id, i.unidad_base_id "
            "FROM recetas r JOIN insumos i ON i.id = r.insumo_id WHERE r.menu_item_id = ?",
            (menu_item_id,)):
            cant = float(cant or 0)
            costo_u, sin_costo = self.costo_unitario_insumo(ins_id)
            en_base = self.convertir(cant, unid_id, base_id)
            if en_base is None:
                res["advertencias"].append(f"Sin conversión de unidad para '{nombre}'")
                en_base = cant
            if sin_costo:
                res["advertencias"].append(f"Insumo sin costo: {nombre}")
            if cant <= 0:
                res["advertencias"].append(f"Cantidad vacía: {nombre}")
            sub = en_base * costo_u
            res["total"] += sub
            res["lineas"].append({"tipo": "INSUMO", "nombre": nombre, "cantidad": cant,
                                  "unidad_id": unid_id or base_id, "costo_unitario": costo_u,
                                  "subtotal": sub})

        for comp_id, nombre, cant, unid_id in self.db.fetch_all(
            "SELECT rc.componente_id, m.nombre, rc.cantidad, rc.unidad_id "
            "FROM receta_componentes rc JOIN menu_items m ON m.id = rc.componente_id "
            "WHERE rc.menu_item_id = ?", (menu_item_id,)):
            cant = float(cant or 0)
            costo_u, adv = self._costo_por_unidad(comp_id, pila)
            res["advertencias"].extend(f"{nombre}: {a}" for a in adv)
            comp = self._item(comp_id)
            en_base = self.convertir(cant, unid_id, comp[7] if comp else None)
            if en_base is None:
                res["advertencias"].append(f"Sin conversión de unidad para '{nombre}'")
                en_base = cant
            sub = en_base * costo_u
            res["total"] += sub
            res["lineas"].append({"tipo": "COMPONENTE", "nombre": nombre, "cantidad": cant,
                                  "unidad_id": unid_id, "costo_unitario": costo_u, "subtotal": sub})

        if not res["lineas"]:
            res["advertencias"].append("Sin receta")
        return res

    def _costo_por_unidad(self, menu_item_id, pila):
        """Costo por unidad de rendimiento de un componente (chimichurri = $/g)."""
        it = self._item(menu_item_id)
        if not it:
            return 0.0, ["Componente inexistente"]
        t = self.costo_tanda(menu_item_id, pila)
        adv = list(t["advertencias"])
        rend = it[6]
        if not rend or rend <= 0:
            adv.append("Sin rendimiento definido: se toma el costo total como costo por unidad")
            return t["total"], adv
        return t["total"] / rend, adv

    def costo_por_unidad_componente(self, menu_item_id):
        if menu_item_id not in self._cache_unitario:
            self._cache_unitario[menu_item_id] = self._costo_por_unidad(menu_item_id, set())
        return self._cache_unitario[menu_item_id]

    def costo_ingredientes(self, menu_item_id):
        """Costo de ingredientes de UNA porción: {total, lineas, advertencias}."""
        it = self._item(menu_item_id)
        t = self.costo_tanda(menu_item_id)
        f = self._factor(it) if it else 1.0
        t["total"] *= f
        for ln in t["lineas"]:
            ln["subtotal"] *= f
        return t

    def costo_extras(self, menu_item_id, canal="LOCAL"):
        """Acompañamientos/bebida/empaque del plato para el canal. {tipo: costo, 'lineas', 'advertencias'}"""
        out = {t: 0.0 for t in TIPOS_EXTRA}
        out["lineas"], out["advertencias"] = [], []
        for comp_id, nombre, cant, tipo, cnl in self.db.fetch_all(
            "SELECT e.componente_id, m.nombre, e.cantidad_porciones, e.tipo, e.canal "
            "FROM plato_extras e JOIN menu_items m ON m.id = e.componente_id "
            "WHERE e.menu_item_id = ?", (menu_item_id,)):
            if cnl not in ("AMBOS", canal):
                continue
            c = self.costo_ingredientes(comp_id)
            sub = c["total"] * float(cant or 0)
            out[tipo] += sub
            out["lineas"].append({"tipo": tipo, "nombre": nombre, "cantidad": cant, "subtotal": sub})
            out["advertencias"].extend(f"{nombre}: {a}" for a in c["advertencias"])
        return out

    def costo_plato(self, menu_item_id, canal="LOCAL", indirecto=0.0):
        """Desglose completo del costo de producir UN plato en el canal indicado."""
        it = self._item(menu_item_id)
        ing = self.costo_ingredientes(menu_item_id)
        ext = self.costo_extras(menu_item_id, canal)
        total = ing["total"] + sum(ext[t] for t in TIPOS_EXTRA) + float(indirecto or 0)
        precio = it[3] if it else 0.0
        m, fc, mp = margen(precio, total)
        pct_key = "pct_ganancia_pedidosya" if canal == "LLEVAR" else "pct_ganancia_local"
        return {
            "menu_item_id": menu_item_id, "codigo": it[1] if it else "", "nombre": it[2] if it else "",
            "categoria": it[4] if it else None, "canal": canal,
            "ingredientes": ing["total"], "acompanamientos": ext["ACOMPANAMIENTO"],
            "bebida": ext["BEBIDA"], "empaque": ext["EMPAQUE"], "indirecto": float(indirecto or 0),
            "total": total, "precio_venta": precio, "margen": m, "food_cost_pct": fc, "margen_pct": mp,
            "precio_sugerido": precio_sugerido(total, self.config_float(pct_key)),
            "lineas": ing["lineas"] + ext["lineas"],
            "advertencias": ing["advertencias"] + ext["advertencias"],
        }

    def listar_platos(self):
        """Ítems vendibles (no componentes) con receta o categoría de costeo."""
        return self.db.fetch_all(
            "SELECT id FROM menu_items WHERE COALESCE(es_componente,0) = 0 ORDER BY categoria_costeo, nombre")

    # -------------------------------------------------------------- indirectos
    def pool_indirectos(self, mes, anio):
        """Indirectos por plato = (gastos fijos + planilla del mes) / platos vendidos.
        Fuente de platos: ventas diarias -> reporte POS -> platos_dia_default * dias_mes."""
        from app.utils.gastos_reales import calcular_planilla_real_mes, ejecutado_gastos_mes

        gastos = ejecutado_gastos_mes(self.db, mes, anio)
        if self.config("base_indirectos") == "PRESUPUESTO":
            fila = self.db.fetch_all(
                "SELECT d.concepto, SUM(d.monto) FROM detalle_presupuesto_gastos d "
                "JOIN presupuestos p ON p.id = d.presupuesto_id WHERE p.mes = ? AND p.anio = ? "
                "GROUP BY d.concepto", (int(mes), int(anio)))
            gastos = {c: float(m or 0) for c, m in fila}
        total_gastos = sum(gastos.values())
        planilla = float(calcular_planilla_real_mes(self.db, mes, anio) or 0)

        mes_p, anio_s = f"{int(mes):02d}", str(int(anio))
        row = self.db.fetch_one(
            "SELECT SUM(d.cantidad) FROM detalle_ventas_diarias d "
            "JOIN registro_ventas_diarias r ON r.id = d.registro_diario_id "
            "WHERE strftime('%m', r.fecha) = ? AND strftime('%Y', r.fecha) = ?", (mes_p, anio_s))
        platos, fuente = (row[0] if row and row[0] else 0), "ventas diarias"
        if not platos:
            row = self.db.fetch_one(
                "SELECT SUM(d.cantidad) FROM detalle_reportes_ventas d "
                "JOIN reportes_ventas r ON r.id = d.reporte_id WHERE r.mes = ? AND r.anio = ?",
                (int(mes), int(anio)))
            platos, fuente = (row[0] if row and row[0] else 0), "reporte POS"
        if not platos:
            platos = self.config_float("platos_dia_default", 198) * self.config_float("dias_mes", 30)
            fuente = "promedio configurado"

        total = total_gastos + planilla
        return {"gastos": gastos, "total_gastos": total_gastos, "planilla": planilla,
                "total": total, "platos": float(platos), "fuente_platos": fuente,
                "por_plato": total / platos if platos else 0.0}

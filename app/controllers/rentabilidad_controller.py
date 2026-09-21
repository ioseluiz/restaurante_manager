# [FILE: app/controllers/rentabilidad_controller.py]
"""
Controlador de Rentabilidad.

Calcula el Estado de Resultados (P&L) mensual y anual del restaurante a partir
de los datos ya capturados por el sistema. Es lógica pura (sin UI) para poder
reutilizarse desde la vista de Rentabilidad y desde el Dashboard.

Modelo de cálculo (todo agrupado por strftime('%Y-%m', fecha)):

  INGRESOS
    Ventas Netas .............. SUM(diario_ventas.total_ventas)

  COSTO DE VENTAS (doble base)
    Real (caja) ............... pagos_efectivo: costo_viveres + costo_carnes + desayunos
    Teórico (recetas) ......... SUM(ventas por plato × costo de receta)
                                fallback: SUM(detalle_reportes_ventas.total_costo) del POS
    Merma / Desviación ........ Real − Teórico

  UTILIDAD BRUTA .............. Ventas − Costo Real

  GASTOS OPERATIVOS (base caja, canales de pago disjuntos → sin doble conteo)
    pagos_efectivo (categorías): planilla, gastos_propietarios, honorarios,
        reparaciones_mantenimiento, atencion_empleados, combustible,
        medicamentos, otros
    cheques ................... SUM(chequera.monto)
    yappy ..................... SUM(transacciones_yappy.monto)
    tarjetas .................. SUM(transacciones_tarjeta.monto WHERE tipo='COMPRA')

  UTILIDAD NETA .............. Utilidad Bruta − Gastos Operativos

NOTA: la tabla `compras`/`detalle_compras` NO se suma aquí (se pagaría por uno
de los canales anteriores y duplicaría el gasto); se expone solo como referencia
informativa en la vista.
"""

import datetime


# --- Categorías consideradas COSTO DE VENTAS (base caja) --------------------
# Se dejan como constante para poder reclasificar fácilmente si el cliente lo pide.
COGS_COLS = ["costo_viveres", "costo_carnes", "desayunos"]

# --- Categorías de GASTOS OPERATIVOS provenientes de pagos_efectivo ---------
GASTO_OP_COLS = [
    "planilla",
    "gastos_propietarios",
    "honorarios",
    "reparaciones_mantenimiento",
    "atencion_empleados",
    "combustible",
    "medicamentos",
    "otros",
]

# Etiquetas legibles para la UI (categorías de pagos_efectivo + canales de pago)
ETIQUETAS_GASTOS = {
    "planilla": "Planilla",
    "gastos_propietarios": "Gastos Propietarios",
    "honorarios": "Honorarios",
    "reparaciones_mantenimiento": "Reparaciones y Mantenimiento",
    "atencion_empleados": "Atención a Empleados",
    "combustible": "Combustible",
    "medicamentos": "Medicamentos",
    "otros": "Otros (Efectivo)",
    "cheques": "Gastos por Cheque",
    "yappy": "Gastos por Yappy",
    "tarjetas": "Gastos por Tarjeta",
}

ETIQUETAS_COGS = {
    "costo_viveres": "Costo de Víveres",
    "costo_carnes": "Costo de Carnes",
    "desayunos": "Desayunos",
}

_DATE_FMTS = (
    "%Y-%m-%d",   # ISO  2025-03-01
    "%d/%m/%Y",   # Latin  01/03/2025
    "%d-%m-%Y",   # 01-03-2025
    "%m/%d/%Y",   # US  03/01/2025
    "%Y/%m/%d",   # 2025/03/01
    "%d/%m/%y",   # 01/03/25
)


def _parse_mes(date_str):
    """Devuelve 'YYYY-MM' a partir de una fecha en cualquier formato común, o None."""
    if not date_str:
        return None
    s = str(date_str).strip()
    for fmt in _DATE_FMTS:
        try:
            return datetime.datetime.strptime(s, fmt).strftime("%Y-%m")
        except ValueError:
            continue
    return None


def _pct(parte, total):
    """Porcentaje seguro de `parte` sobre `total` (0 si total es 0)."""
    if not total:
        return 0.0
    return (parte / total) * 100.0


class RentabilidadController:
    def __init__(self, db_manager):
        self.db = db_manager

    # ------------------------------------------------------------------
    # Bloques de datos individuales
    # ------------------------------------------------------------------
    def _ventas_mes(self, mes_key):
        row = self.db.fetch_one(
            "SELECT COALESCE(SUM(total_ventas), 0) FROM diario_ventas "
            "WHERE strftime('%Y-%m', fecha) = ?",
            (mes_key,),
        )
        return float(row[0] or 0.0)

    def _pagos_efectivo_mes(self, mes_key):
        """Devuelve un dict {columna: total} con TODAS las categorías de pagos_efectivo."""
        cols = COGS_COLS + GASTO_OP_COLS
        sql = "SELECT " + ", ".join(f"COALESCE(SUM({c}), 0)" for c in cols)
        sql += " FROM pagos_efectivo WHERE strftime('%Y-%m', fecha) = ?"
        row = self.db.fetch_one(sql, (mes_key,)) or [0] * len(cols)
        return {c: float(v or 0.0) for c, v in zip(cols, row)}

    def _gasto_cheques_mes(self, mes_key):
        row = self.db.fetch_one(
            "SELECT COALESCE(SUM(monto), 0) FROM chequera "
            "WHERE strftime('%Y-%m', fecha) = ?",
            (mes_key,),
        )
        return float(row[0] or 0.0)

    def _gasto_yappy_mes(self, mes_key):
        row = self.db.fetch_one(
            "SELECT COALESCE(SUM(monto), 0) FROM transacciones_yappy "
            "WHERE strftime('%Y-%m', fecha) = ?",
            (mes_key,),
        )
        return float(row[0] or 0.0)

    def _gasto_tarjetas_mes(self, mes_key):
        row = self.db.fetch_one(
            "SELECT COALESCE(SUM(monto), 0) FROM transacciones_tarjeta "
            "WHERE tipo_transaccion = 'COMPRA' AND strftime('%Y-%m', fecha) = ?",
            (mes_key,),
        )
        return float(row[0] or 0.0)

    # ------------------------------------------------------------------
    # Costo teórico por recetas (con fallback a reportes del POS)
    # ------------------------------------------------------------------
    def costo_teorico_mes(self, anio, mes):
        """
        Costo teórico de los platos vendidos en el mes:
            Σ (cantidad vendida × costo de la receta)
        donde costo de la receta = Σ (cantidad_necesaria × insumos.costo_unitario).

        Devuelve un float, o None si no hay datos suficientes (ni ventas por
        plato con receta, ni reportes del POS con costo).
        """
        mes_key = f"{anio:04d}-{mes:02d}"

        row = self.db.fetch_one(
            """
            SELECT COALESCE(SUM(d.cantidad * rc.costo_receta), 0)
            FROM detalle_ventas_diarias d
            JOIN registro_ventas_diarias r ON d.registro_diario_id = r.id
            JOIN (
                SELECT rec.menu_item_id,
                       SUM(rec.cantidad_necesaria * i.costo_unitario) AS costo_receta
                FROM v_recetas_explotadas rec
                JOIN insumos i ON rec.insumo_id = i.id
                GROUP BY rec.menu_item_id
            ) rc ON rc.menu_item_id = d.menu_item_id
            WHERE strftime('%Y-%m', r.fecha) = ?
            """,
            (mes_key,),
        )
        val = float(row[0] or 0.0)
        if val > 0:
            return val

        # Fallback: costo reportado por el POS para ese mes
        return self._costo_pos_mes(anio, mes)

    def _costo_pos_mes(self, anio, mes):
        """SUM(detalle_reportes_ventas.total_costo) de los reportes cuyo período
        cae en el mes indicado. Devuelve float o None si no hay reportes."""
        mes_key = f"{anio:04d}-{mes:02d}"
        filas = self.db.fetch_all(
            """
            SELECT rv.fecha_inicio_periodo, COALESCE(SUM(drv.total_costo), 0)
            FROM reportes_ventas rv
            JOIN detalle_reportes_ventas drv ON drv.reporte_id = rv.id
            WHERE rv.fecha_inicio_periodo IS NOT NULL
              AND rv.fecha_inicio_periodo != ''
            GROUP BY rv.id
            """
        )
        total = 0.0
        encontrado = False
        for fecha_str, costo in filas:
            if _parse_mes(fecha_str) == mes_key:
                total += float(costo or 0.0)
                encontrado = True
        return total if encontrado else None

    # ------------------------------------------------------------------
    # Estado de Resultados mensual
    # ------------------------------------------------------------------
    def pyl_mensual(self, anio, mes):
        """
        Devuelve un dict con el Estado de Resultados del mes:
          {
            'anio', 'mes', 'mes_key',
            'ventas',
            'costo_real', 'costo_teorico' (float|None), 'merma' (float|None),
            'utilidad_bruta', 'margen_bruto',
            'cogs_desglose'  {col: monto},
            'gastos'         {clave: monto},   # incluye categorías + canales
            'total_gastos',
            'utilidad_neta', 'margen_neto',
            'pct'            {clave: % sobre ventas para cada renglón},
          }
        """
        mes_key = f"{anio:04d}-{mes:02d}"

        ventas = self._ventas_mes(mes_key)
        pe = self._pagos_efectivo_mes(mes_key)

        cogs_desglose = {c: pe[c] for c in COGS_COLS}
        costo_real = sum(cogs_desglose.values())

        costo_teorico = self.costo_teorico_mes(anio, mes)
        merma = (costo_real - costo_teorico) if costo_teorico is not None else None

        utilidad_bruta = ventas - costo_real

        gastos = {c: pe[c] for c in GASTO_OP_COLS}
        gastos["cheques"] = self._gasto_cheques_mes(mes_key)
        gastos["yappy"] = self._gasto_yappy_mes(mes_key)
        gastos["tarjetas"] = self._gasto_tarjetas_mes(mes_key)
        total_gastos = sum(gastos.values())

        utilidad_neta = utilidad_bruta - total_gastos

        # Porcentajes sobre ventas por renglón
        pct = {
            "ventas": 100.0 if ventas else 0.0,
            "costo_real": _pct(costo_real, ventas),
            "utilidad_bruta": _pct(utilidad_bruta, ventas),
            "total_gastos": _pct(total_gastos, ventas),
            "utilidad_neta": _pct(utilidad_neta, ventas),
        }
        if costo_teorico is not None:
            pct["costo_teorico"] = _pct(costo_teorico, ventas)
            pct["merma"] = _pct(merma, ventas)
        for c in COGS_COLS:
            pct[c] = _pct(cogs_desglose[c], ventas)
        for k, v in gastos.items():
            pct[k] = _pct(v, ventas)

        return {
            "anio": anio,
            "mes": mes,
            "mes_key": mes_key,
            "ventas": ventas,
            "costo_real": costo_real,
            "costo_teorico": costo_teorico,
            "merma": merma,
            "cogs_desglose": cogs_desglose,
            "utilidad_bruta": utilidad_bruta,
            "margen_bruto": _pct(utilidad_bruta, ventas),
            "gastos": gastos,
            "total_gastos": total_gastos,
            "utilidad_neta": utilidad_neta,
            "margen_neto": _pct(utilidad_neta, ventas),
            "pct": pct,
        }

    # ------------------------------------------------------------------
    # Comparativo anual (12 meses)
    # ------------------------------------------------------------------
    def matriz_anual(self, anio):
        """
        Devuelve una lista de 13 dicts: 12 meses (Ene–Dic) + un renglón 'total'.
        Cada dict trae ventas, costo_real, utilidad_bruta, total_gastos,
        utilidad_neta y margen_neto.
        """
        filas = []
        acc = {
            "ventas": 0.0,
            "costo_real": 0.0,
            "utilidad_bruta": 0.0,
            "total_gastos": 0.0,
            "utilidad_neta": 0.0,
        }
        for m in range(1, 13):
            pyl = self.pyl_mensual(anio, m)
            fila = {
                "mes": m,
                "ventas": pyl["ventas"],
                "costo_real": pyl["costo_real"],
                "utilidad_bruta": pyl["utilidad_bruta"],
                "total_gastos": pyl["total_gastos"],
                "utilidad_neta": pyl["utilidad_neta"],
                "margen_neto": pyl["margen_neto"],
            }
            for k in acc:
                acc[k] += fila[k]
            filas.append(fila)

        total = dict(acc)
        total["mes"] = "total"
        total["margen_neto"] = _pct(acc["utilidad_neta"], acc["ventas"])
        filas.append(total)
        return filas

    # ------------------------------------------------------------------
    # Variaciones vs mes anterior y vs mismo mes del año anterior
    # ------------------------------------------------------------------
    def deltas(self, anio, mes):
        """
        Compara el mes (anio, mes) contra el mes anterior y contra el mismo mes
        del año anterior. Devuelve dict con Δ absoluto y % para ventas,
        utilidad_bruta y utilidad_neta.
        """
        actual = self.pyl_mensual(anio, mes)

        prev_anio, prev_mes = (anio, mes - 1) if mes > 1 else (anio - 1, 12)
        mes_anterior = self.pyl_mensual(prev_anio, prev_mes)
        anio_anterior = self.pyl_mensual(anio - 1, mes)

        def _delta(base):
            out = {}
            for campo in ("ventas", "utilidad_bruta", "utilidad_neta"):
                abs_d = actual[campo] - base[campo]
                out[campo] = {"abs": abs_d, "pct": _pct(abs_d, abs(base[campo]))}
            return out

        return {
            "actual": actual,
            "vs_mes_anterior": _delta(mes_anterior),
            "vs_anio_anterior": _delta(anio_anterior),
            "ref_mes_anterior": mes_anterior,
            "ref_anio_anterior": anio_anterior,
        }

    # ------------------------------------------------------------------
    # Compras itemizadas por categoría (solo referencia informativa)
    # ------------------------------------------------------------------
    def compras_por_categoria_mes(self, anio, mes):
        """
        Total de compras registradas en el mes, agrupado por categoría de insumo.
        Se usa SOLO como referencia (no se suma al P&L para evitar doble conteo).
        Agrupa por compras.fecha_compra si existe, si no por fecha_registro.
        """
        mes_key = f"{anio:04d}-{mes:02d}"
        return self.db.fetch_all(
            """
            SELECT COALESCE(cat.nombre, 'Sin categoría') AS categoria,
                   COALESCE(SUM(dc.subtotal), 0) AS total
            FROM detalle_compras dc
            JOIN compras c              ON dc.compra_id = c.id
            JOIN presentaciones_compra p ON dc.presentacion_id = p.id
            JOIN insumos ins            ON p.insumo_id = ins.id
            LEFT JOIN categorias_insumos cat ON ins.categoria_id = cat.id
            WHERE strftime('%Y-%m',
                    COALESCE(NULLIF(c.fecha_compra, ''), c.fecha_registro)) = ?
            GROUP BY categoria
            ORDER BY total DESC
            """,
            (mes_key,),
        )

    # ------------------------------------------------------------------
    # Utilidades varias
    # ------------------------------------------------------------------
    def anios_disponibles(self):
        """Años con datos (de ventas o gastos), de más reciente a más antiguo.
        Siempre incluye el año en curso."""
        anios = set()
        for tabla, col in (
            ("diario_ventas", "fecha"),
            ("pagos_efectivo", "fecha"),
            ("chequera", "fecha"),
        ):
            try:
                for (a,) in self.db.fetch_all(
                    f"SELECT DISTINCT strftime('%Y', {col}) FROM {tabla} "
                    f"WHERE {col} IS NOT NULL"
                ):
                    if a:
                        anios.add(int(a))
            except Exception:
                pass
        anios.add(datetime.date.today().year)
        return sorted(anios, reverse=True)

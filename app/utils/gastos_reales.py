# [FILE: app/utils/gastos_reales.py]
"""Costos reales del mes (planilla y gastos por tipo). Sin dependencias de Qt;
usados por Presupuestos y por el módulo Costo de platos."""
from app.utils.calculo_planilla import cargar_config, cargar_isr_tramos, calcular_costo_empleado


def calcular_planilla_real_mes(db, mes, anio):
    """Costo real de planilla ejecutado en el mes/año: suma los períodos de pago
    cuya fecha de inicio cae en ese mes, con el costo COMPLETO del módulo Planilla
    (bruto + aportes patronales + riesgo profesional + provisiones)."""
    mes_p = f"{int(mes):02d}"
    anio_s = str(int(anio))
    periodos = db.fetch_all(
        "SELECT id FROM periodos_pago "
        "WHERE strftime('%m', fecha_inicio) = ? AND strftime('%Y', fecha_inicio) = ?",
        (mes_p, anio_s),
    )
    if not periodos:
        return 0.0
    recargos, pcts = cargar_config(db)
    ctx = (recargos, pcts, cargar_isr_tramos(db))
    ids = [str(p[0]) for p in periodos]
    placeholders = ",".join(["?"] * len(ids))
    rows = db.fetch_all(
        f"""SELECT e.salario_hora, h.horas_regulares, h.horas_festivos, h.horas_domingos,
                   h.horas_extra_diurnas, h.horas_extra_nocturnas,
                   COALESCE(e.tipo_contrato, 'INDEFINIDO')
            FROM horas_empleado h
            JOIN empleados e ON e.id = h.empleado_id
            WHERE h.periodo_id IN ({placeholders})""",
        tuple(ids),
    )
    total = 0.0
    for sal, h_reg, h_fest, h_dom, h_exd, h_exn, contrato in rows:
        costo = calcular_costo_empleado(
            db, sal,
            {
                "horas_regulares": h_reg, "horas_festivos": h_fest,
                "horas_domingos": h_dom, "horas_extra_diurnas": h_exd,
                "horas_extra_nocturnas": h_exn,
            },
            tipo_contrato=contrato, ctx=ctx,
        )
        total += costo["costo_total_completo"]
    return total


def ejecutado_gastos_mes(db, mes, anio):
    """Suma los egresos de consolidados (cheques, tarjeta, Yappy, efectivo) del
    mes/año, agrupados por 'tipo_gasto'. Devuelve {concepto: monto_ejecutado}."""
    mes_p = f"{int(mes):02d}"
    anio_s = str(int(anio))
    resultado = {}

    def _acumular(query):
        for concepto, monto in db.fetch_all(query, (mes_p, anio_s)):
            if not concepto:
                continue
            resultado[concepto] = resultado.get(concepto, 0.0) + float(monto or 0)

    base = (
        "strftime('%m', fecha) = ? AND strftime('%Y', fecha) = ? "
        "AND tipo_gasto IS NOT NULL AND TRIM(tipo_gasto) <> ''"
    )
    _acumular(f"SELECT tipo_gasto, SUM(monto) FROM chequera WHERE {base} GROUP BY tipo_gasto")
    _acumular(
        f"SELECT tipo_gasto, SUM(monto) FROM transacciones_tarjeta "
        f"WHERE {base} AND tipo_transaccion = 'COMPRA' GROUP BY tipo_gasto"
    )
    _acumular(f"SELECT tipo_gasto, SUM(monto) FROM transacciones_yappy WHERE {base} GROUP BY tipo_gasto")

    # Pagos en efectivo: el tipo de gasto se etiqueta por línea del desglose.
    for concepto, monto in db.fetch_all(
        "SELECT d.tipo_gasto, SUM(d.monto) "
        "FROM detalle_pagos_efectivo d "
        "JOIN pagos_efectivo p ON p.id = d.pago_efectivo_id "
        "WHERE strftime('%m', p.fecha) = ? AND strftime('%Y', p.fecha) = ? "
        "AND d.tipo_gasto IS NOT NULL AND TRIM(d.tipo_gasto) <> '' "
        "GROUP BY d.tipo_gasto",
        (mes_p, anio_s),
    ):
        if concepto:
            resultado[concepto] = resultado.get(concepto, 0.0) + float(monto or 0)
    return resultado

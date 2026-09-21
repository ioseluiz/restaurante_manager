"""Cálculo de planilla — fuente única de verdad.

Reúne la fórmula de nómina (salario bruto por recargos, deducciones del
colaborador y aportes patronales) para que tanto el módulo de Planilla como
el bloque de planilla del Presupuesto calculen exactamente igual.

Las deducciones específicas de un período (vales, deducciones "otras") NO se
incluyen aquí: son propias del cierre de nómina real, no de una proyección de
presupuesto. El módulo de Planilla las suma aparte sobre este resultado base.
"""

# Recargos por defecto (multiplicador sobre el salario/hora)
DEFAULT_RECARGOS = {
    "regulares":       1.00,
    "festivos":        2.50,
    "domingos":        1.50,
    "extra_diurnas":   1.25,
    "extra_nocturnas": 1.50,
}

# Porcentajes de deducción por defecto (en %)
DEFAULT_DEDUCCIONES_PCT = {
    "seguro_social_colaborador":       9.75,
    "seguro_social_empleador":        12.25,
    "seguro_educativo_colaborador":    1.25,
    "seguro_educativo_empleador":      1.50,
    # Cargas patronales y provisiones (Panamá) — configurables
    "riesgos_profesionales_empleador": 2.10,
    "provision_decimo":                8.33,
    "provision_vacaciones":            8.33,
    "provision_prima_antiguedad":      1.92,
}

# Tabla de ISR por defecto (DGI personas naturales): (desde, hasta, tasa, cuota_fija).
# hasta = None significa "sin límite superior".
DEFAULT_ISR_TRAMOS = [
    (0.0,      11000.0,  0.00,     0.00),
    (11000.0,  50000.0,  0.15,     0.00),
    (50000.0,  None,     0.25,  5850.00),
]

# Períodos de pago por año por defecto (quincenal). Se usa para anualizar la
# base del ISR cuando el llamador no calcula el factor desde las fechas.
DEFAULT_FACTOR_ANUAL = 24.0


def cargar_config(db):
    """Lee recargos y porcentajes de deducción desde la base de datos,
    cayendo a los valores por defecto si algún registro falta.

    Devuelve (recargos: dict, pcts: dict) listos para pasar a calcular_costo.
    """
    recargos = dict(DEFAULT_RECARGOS)
    try:
        for tipo, _nombre, recargo in db.fetch_all(
            "SELECT tipo_hora, nombre_display, recargo FROM planilla_config_recargos", ()
        ):
            if tipo:
                recargos[tipo] = float(recargo or 0)
    except Exception:
        pass

    pcts = dict(DEFAULT_DEDUCCIONES_PCT)
    try:
        for concepto, _nombre, porcentaje, _aplica in db.fetch_all(
            "SELECT concepto, nombre_display, porcentaje, aplica_a FROM planilla_config_deducciones", ()
        ):
            if concepto:
                pcts[concepto] = float(porcentaje or 0)
    except Exception:
        pass

    return recargos, pcts


def cargar_isr_tramos(db):
    """Lee la tabla progresiva de ISR desde la base de datos, cayendo a
    DEFAULT_ISR_TRAMOS si no hay registros. Devuelve lista de
    (desde, hasta|None, tasa, cuota_fija)."""
    try:
        rows = db.fetch_all(
            "SELECT desde, hasta, tasa, cuota_fija FROM planilla_isr_tramos ORDER BY orden, desde", ()
        )
        tramos = [
            (float(d or 0), (float(h) if h is not None else None),
             float(t or 0), float(c or 0))
            for d, h, t, c in rows
        ]
        if tramos:
            return tramos
    except Exception:
        pass
    return list(DEFAULT_ISR_TRAMOS)


def calcular_isr(base_anual, tramos):
    """Impuesto sobre la renta ANUAL para una base gravable anual, según los
    tramos (desde, hasta|None, tasa, cuota_fija). Retorna 0 si cae en el
    tramo exento."""
    base = float(base_anual or 0)
    if base <= 0:
        return 0.0
    for desde, hasta, tasa, cuota in tramos:
        if base > desde and (hasta is None or base <= hasta):
            return cuota + (base - desde) * tasa
    return 0.0


def calcular_costo(salario_hora, horas, recargos, pcts):
    """Calcula el costo de nómina de un empleado.

    Parámetros:
      salario_hora: salario por hora (float)
      horas: dict con horas_regulares, horas_festivos, horas_domingos,
             horas_extra_diurnas, horas_extra_nocturnas (faltantes = 0)
      recargos: dict de multiplicadores (ver cargar_config)
      pcts: dict de porcentajes de deducción en % (ver cargar_config)

    Devuelve un dict con:
      salario_bruto     — pago bruto del empleado
      deducciones_colab — seguro social + educativo del colaborador
      costo_patronal    — seguro social + educativo del empleador
      costo_total       — bruto + costo_patronal (costo real para la empresa)
    """
    sal = float(salario_hora or 0)

    def h(clave):
        return float(horas.get(clave, 0) or 0)

    bruto = (
        h("horas_regulares")       * sal * recargos.get("regulares",       1.00) +
        h("horas_festivos")        * sal * recargos.get("festivos",        2.50) +
        h("horas_domingos")        * sal * recargos.get("domingos",        1.50) +
        h("horas_extra_diurnas")   * sal * recargos.get("extra_diurnas",   1.25) +
        h("horas_extra_nocturnas") * sal * recargos.get("extra_nocturnas", 1.50)
    )

    pct_ss_c = pcts.get("seguro_social_colaborador",    9.75) / 100
    pct_se_c = pcts.get("seguro_educativo_colaborador", 1.25) / 100
    pct_ss_e = pcts.get("seguro_social_empleador",     12.25) / 100
    pct_se_e = pcts.get("seguro_educativo_empleador",   1.50) / 100

    deducciones_colab = bruto * (pct_ss_c + pct_se_c)
    costo_patronal    = bruto * (pct_ss_e + pct_se_e)
    costo_total       = bruto + costo_patronal

    return {
        "salario_bruto":     bruto,
        "deducciones_colab": deducciones_colab,
        "costo_patronal":    costo_patronal,
        "costo_total":       costo_total,
    }


def calcular_costo_completo(salario_hora, horas, recargos, pcts,
                            tipo_contrato="INDEFINIDO", tramos_isr=None,
                            factor_anual=DEFAULT_FACTOR_ANUAL):
    """Costo laboral REAL para la empresa (Panamá), incluyendo cargas
    patronales adicionales y provisiones laborales.

    Envuelve calcular_costo() y añade:
      riesgos_prof         — aporte patronal de riesgos profesionales
      provision_decimo     — provisión del décimo tercer mes (XIII)
      provision_vacaciones — provisión de vacaciones
      provision_prima      — provisión prima de antigüedad (solo INDEFINIDO)
      provisiones_total    — suma de las tres provisiones
      isr                  — retención de ISR del colaborador (por período)
      costo_patronal_total — SS + SE + riesgos profesionales (empleador)
      costo_total_completo — bruto + costo_patronal_total + provisiones_total

    El ISR se estima anualizando la base del período por `factor_anual`
    (períodos de pago al año) y prorrateando el impuesto anual de vuelta.
    Mantiene todas las claves de calcular_costo() para compatibilidad.
    """
    base = calcular_costo(salario_hora, horas, recargos, pcts)
    bruto = base["salario_bruto"]

    pct_riesgos = pcts.get("riesgos_profesionales_empleador", 0.0) / 100
    pct_decimo  = pcts.get("provision_decimo",                0.0) / 100
    pct_vac     = pcts.get("provision_vacaciones",            0.0) / 100
    pct_prima   = pcts.get("provision_prima_antiguedad",      0.0) / 100

    es_indefinido = str(tipo_contrato or "").strip().upper() == "INDEFINIDO"

    riesgos     = bruto * pct_riesgos
    prov_decimo = bruto * pct_decimo
    prov_vac    = bruto * pct_vac
    prov_prima  = bruto * pct_prima if es_indefinido else 0.0
    provisiones = prov_decimo + prov_vac + prov_prima

    tramos = tramos_isr if tramos_isr is not None else list(DEFAULT_ISR_TRAMOS)
    factor = float(factor_anual or 0)
    if factor > 0:
        isr = calcular_isr(bruto * factor, tramos) / factor
    else:
        isr = 0.0

    costo_patronal_total = base["costo_patronal"] + riesgos
    costo_total_completo = bruto + costo_patronal_total + provisiones

    result = dict(base)
    result.update({
        "riesgos_prof":         riesgos,
        "provision_decimo":     prov_decimo,
        "provision_vacaciones": prov_vac,
        "provision_prima":      prov_prima,
        "provisiones_total":    provisiones,
        "isr":                  isr,
        "costo_patronal_total": costo_patronal_total,
        "costo_total_completo": costo_total_completo,
    })
    return result


def calcular_costo_empleado(db, salario_hora, horas, empleado_id=None, tipo_contrato=None, ctx=None):
    """Costo laboral COMPLETO de un empleado (misma regla del Resumen de Planilla).

    Es la fuente única para el bloque de planilla del Presupuesto, el ejecutado del Control
    Presupuestal y los indirectos de Costo de Platos: bruto + Seguro Social/Educativo patronales
    + riesgo profesional + provisiones laborales (la prima de antigüedad solo si el contrato es
    INDEFINIDO). `ctx` = (recargos, pcts, tramos_isr) permite reutilizar la configuración al
    calcular muchas filas. El ISR no forma parte del costo (es deducción del colaborador).
    """
    if ctx is None:
        recargos, pcts = cargar_config(db)
        ctx = (recargos, pcts, cargar_isr_tramos(db))
    recargos, pcts, tramos = ctx
    if not tipo_contrato and empleado_id:
        try:
            row = db.fetch_one("SELECT tipo_contrato FROM empleados WHERE id=?", (empleado_id,))
            tipo_contrato = row[0] if row else None
        except Exception:
            tipo_contrato = None
    return calcular_costo_completo(
        salario_hora, horas, recargos, pcts,
        tipo_contrato=tipo_contrato or "INDEFINIDO", tramos_isr=tramos)

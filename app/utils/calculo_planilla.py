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
    "seguro_social_colaborador":   9.75,
    "seguro_social_empleador":    12.25,
    "seguro_educativo_colaborador": 1.25,
    "seguro_educativo_empleador":   1.50,
}


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

"""E2E de Planilla: costo laboral completo (Panamá), planilla real del mes e ISR."""
import pytest

from app.utils.calculo_planilla import (
    DEFAULT_ISR_TRAMOS, calcular_costo_completo, calcular_costo_empleado, calcular_isr, cargar_config,
)
from app.utils.gastos_reales import calcular_planilla_real_mes

import escenario_e2e as E

approx = pytest.approx


def test_costo_completo_empleado_indefinido(db, esc):
    # Ana, $4.00/h: 88 regulares + 8 domingo ×1.5 + 4 extra diurnas ×1.25 = 352 + 48 + 20 = 420
    c = calcular_costo_empleado(db, 4.00, {"horas_regulares": 88, "horas_domingos": 8,
                                           "horas_extra_diurnas": 4}, empleado_id=esc.ana)
    assert c["salario_bruto"] == approx(420)
    assert c["deducciones_colab"] == approx(420 * 0.11)          # SS 9.75 % + SE 1.25 %
    assert c["costo_patronal"] == approx(57.75)                    # SS 12.25 % + SE 1.50 %
    assert c["riesgos_prof"] == approx(8.82)                       # 2.10 %
    assert c["provision_decimo"] == approx(34.986)                 # 8.33 %
    assert c["provision_vacaciones"] == approx(34.986)             # 8.33 %
    assert c["provision_prima"] == approx(8.064)                   # 1.92 %, solo INDEFINIDO
    assert c["costo_patronal_total"] == approx(66.57)
    assert c["costo_total_completo"] == approx(564.606)
    assert c["isr"] == 0                                           # 420 × 24 = 10 080 < 11 000


def test_costo_completo_empleado_definido_sin_prima(db, esc):
    c = calcular_costo_empleado(db, 3.00, {"horas_regulares": 96}, empleado_id=esc.luis)
    assert c["salario_bruto"] == approx(288)
    assert c["provision_prima"] == 0
    # 288 + 39.60 (13.75 %) + 6.048 (2.10 %) + 2 × 23.9904 (8.33 %)
    assert c["costo_total_completo"] == approx(381.6288)


def test_planilla_real_del_mes(db, esc):
    assert calcular_planilla_real_mes(db, E.MES, E.ANIO) == approx(564.606 + 381.6288)
    assert calcular_planilla_real_mes(db, 6, E.ANIO) == 0


def test_periodo_que_cruza_de_mes_se_imputa_al_mes_de_inicio(db, esc):
    """Caracterización (H6): un período del 25/05 al 08/06 cuenta entero para mayo."""
    pid = db.execute_query("INSERT INTO periodos_pago (nombre, fecha_inicio, fecha_fin) "
                           "VALUES ('cruce','2026-05-25','2026-06-08')").lastrowid
    db.execute_query("INSERT INTO horas_empleado (empleado_id, periodo_id, horas_regulares) VALUES (?,?,96)",
                     (esc.luis, pid))
    assert calcular_planilla_real_mes(db, E.MES, E.ANIO) == approx(946.2348 + 381.6288)
    assert calcular_planilla_real_mes(db, 6, E.ANIO) == 0


@pytest.mark.parametrize("base, esperado", [
    (11000, 0.0),
    (11001, 0.15),
    (50000, 5850.0),
    (50001, 5850.25),
    (0, 0.0),
])
def test_isr_en_los_bordes_de_los_tramos(base, esperado):
    assert calcular_isr(base, DEFAULT_ISR_TRAMOS) == approx(esperado)


def test_isr_por_periodo_anualiza_por_24(db):
    recargos, pcts = cargar_config(db)
    # $20/h × 88 h = 1 760 por quincena -> 42 240 al año -> (42 240 - 11 000) × 15 % = 4 686 -> /24
    c = calcular_costo_completo(20, {"horas_regulares": 88}, recargos, pcts)
    assert c["isr"] == approx(4686 / 24)

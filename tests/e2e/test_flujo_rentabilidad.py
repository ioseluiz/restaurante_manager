"""E2E de Rentabilidad: estado de resultados de mayo 2026, matriz anual, variaciones y costo teórico."""
import pytest

from app.controllers.costeo_controller import CosteoController
from app.controllers.kardex_controller import KardexController
from app.controllers.rentabilidad_controller import RentabilidadController

import escenario_e2e as E

approx = pytest.approx

# Costo teórico = ingredientes de Costo de Platos (precio vigente): P1 1.09 · P2 1.06
TEORICO_MAYO = 10 * 1.09 + 20 * 1.06  # 32.10
# Referencia con extras (canal local): P2 suma la soda -> 10 × 1.09 + 20 × 1.56
TEORICO_CON_EXTRAS = 10 * 1.09 + 20 * 1.56  # 42.10


@pytest.fixture
def mayo(db, esc, recibir):
    recibir(db, esc.compra)
    KardexController(db).procesar_ventas_diarias(E.dia_ventas(db, E.FECHA_VENTA, [(esc.p1, 10), (esc.p2, 20)]))
    return esc


def test_estado_de_resultados_mensual(db, mayo):
    pyl = RentabilidadController(db).pyl_mensual(E.ANIO, E.MES)
    # Ventas = 20 + 30 + 40 + 50 + 60.5 + 1 (sobrante) - 0.5 (faltante)
    assert pyl["ventas"] == approx(201)
    # Costo real (efectivo): víveres 120 + carnes 100
    assert pyl["costo_real"] == approx(220)
    assert pyl["costo_teorico"] == approx(TEORICO_MAYO)
    assert pyl["merma"] == approx(220 - TEORICO_MAYO)
    assert pyl["costo_teorico_con_extras"] == approx(TEORICO_CON_EXTRAS)
    assert pyl["utilidad_bruta"] == approx(-19)
    # Gastos: planilla en efectivo 900 + otros 50 + cheques 1 100 + Yappy 150 + tarjeta (solo COMPRA) 60
    assert pyl["gastos"]["planilla"] == approx(900)
    assert pyl["gastos"]["cheques"] == approx(1100)
    assert pyl["gastos"]["tarjetas"] == approx(60)
    assert pyl["total_gastos"] == approx(2260)
    assert pyl["utilidad_neta"] == approx(-2279)
    assert pyl["margen_neto"] == approx(-2279 / 201 * 100)


def test_matriz_anual_y_variaciones(db, mayo):
    ctrl = RentabilidadController(db)
    filas = ctrl.matriz_anual(E.ANIO)
    assert len(filas) == 13
    assert filas[4]["ventas"] == approx(201) and filas[3]["ventas"] == 0
    assert filas[12]["mes"] == "total" and filas[12]["utilidad_neta"] == approx(-2279)

    d = ctrl.deltas(E.ANIO, E.MES)
    assert d["vs_mes_anterior"]["ventas"]["abs"] == approx(201)
    assert d["vs_mes_anterior"]["ventas"]["pct"] == 0  # abril sin ventas: % no definido -> 0


def test_costo_real_y_gastos_por_canal_de_pago(db, mayo):
    """Caracterización (H8): el costo de ventas real solo sale de las columnas de efectivo. El cheque de
    $300 a «Carnes del Istmo» va a gastos operativos y la planilla es la pagada en efectivo ($900), no el
    costo del módulo Planilla ($946.23). Requiere confirmar con el cliente/contadora."""
    pyl = RentabilidadController(db).pyl_mensual(E.ANIO, E.MES)
    assert pyl["costo_real"] == approx(220)
    assert pyl["gastos"]["cheques"] == approx(800 + 300)
    assert pyl["gastos"]["planilla"] == approx(900)


def test_costo_teorico_usa_el_motor_de_costo_de_platos(db, mayo):
    """H1: el teórico usa CosteoController (misma fuente de costo y conversión que Costo de Platos), sin los
    extras del plato; el teórico con extras queda como referencia."""
    c = CosteoController(db)
    ctrl = RentabilidadController(db)
    assert ctrl.costo_teorico_mes(E.ANIO, E.MES) == approx(
        10 * c.costo_ingredientes(mayo.p1)["total"] + 20 * c.costo_ingredientes(mayo.p2)["total"])
    assert ctrl.costo_teorico_con_extras_mes(E.ANIO, E.MES) == approx(
        10 * c.costo_plato(mayo.p1)["total"] + 20 * c.costo_plato(mayo.p2)["total"])
    # Con «costo promedio» en Parámetros, el teórico sigue al inventario: P1 1.084 (arroz a 0.00116), P2 1.054
    db.execute_query("UPDATE costeo_config SET valor='PROMEDIO' WHERE clave='fuente_costo_insumo'")
    assert ctrl.costo_teorico_mes(E.ANIO, E.MES) == approx(10 * 1.084 + 20 * 1.054, abs=1e-4)
    assert ctrl.costo_teorico_con_extras_mes(E.ANIO, 7) is None

"""E2E de Costo de platos: tanda + sub-receta + extras por canal, precio sugerido, margen e indirectos."""
import pytest

from app.controllers.costeo_controller import CosteoController, precio_sugerido

import escenario_e2e as E

approx = pytest.approx

# Planilla real de mayo (ver test_flujo_planilla): Ana 564.606 + Luis 381.6288
PLANILLA_MAYO = 946.2348
# Gastos etiquetados de mayo: Alquiler 800 (cheque) + Internet 60 (tarjeta) + Luz 150 (Yappy) + Gas 50 (efectivo)
GASTOS_MAYO = {"Alquiler": 800.0, "Internet / Teléfono": 60.0, "Luz (electricidad)": 150.0, "Gas": 50.0}


def test_costo_por_porcion_con_subreceta_y_extras_por_canal(db, esc):
    c = CosteoController(db)
    # Salsa: (1 200 g × 0.0015 + 100 ml × 0.004) / 1 000 g = 0.0022 $/g
    assert c.costo_por_unidad_componente(esc.salsa)[0] == approx(0.0022)

    # P1: Pollo 200×0.004 = 0.80 + Arroz 150×0.0012 = 0.18 + Salsa 50×0.0022 = 0.11 -> 1.09
    local = c.costo_plato(esc.p1, "LOCAL")
    assert local["ingredientes"] == approx(1.09)
    assert local["empaque"] == 0 and local["total"] == approx(1.09)
    assert local["advertencias"] == []
    llevar = c.costo_plato(esc.p1, "LLEVAR")
    assert llevar["empaque"] == approx(0.20) and llevar["total"] == approx(1.29)

    # P2 por tanda: (1 500×0.0012 + 2 000×0.004 + 200×0.004) = 10.60 × 400/4 000 = 1.06; + soda 0.50
    p2 = c.costo_plato(esc.p2, "LOCAL")
    assert p2["ingredientes"] == approx(1.06) and p2["bebida"] == approx(0.50)
    assert p2["total"] == approx(1.56)
    assert c.costo_plato(esc.p2, "LLEVAR")["total"] == approx(1.56)


def test_precio_sugerido_y_margen(db, esc):
    c = CosteoController(db)
    local = c.costo_plato(esc.p1, "LOCAL")
    # 30 % local: 1.09 / 0.70 · 50 % Pedidos Ya: 1.29 / 0.50
    assert local["precio_sugerido"] == approx(1.09 / 0.70)
    assert c.costo_plato(esc.p1, "LLEVAR")["precio_sugerido"] == approx(2.58)
    # Margen contra el precio de $6.00
    assert local["margen"] == approx(4.91)
    assert local["food_cost_pct"] == approx(1.09 / 6 * 100)
    assert local["margen_pct"] == approx(4.91 / 6 * 100)
    # Con indirecto de $2.00 por plato
    assert c.costo_plato(esc.p1, "LOCAL", indirecto=2.0)["total"] == approx(3.09)
    assert precio_sugerido(10, 100) is None


def test_fuente_promedio_usa_el_costo_ponderado(db, esc, recibir):
    recibir(db, esc.compra)  # Arroz queda a 0.00116 $/g
    db.execute_query("UPDATE costeo_config SET valor='PROMEDIO' WHERE clave='fuente_costo_insumo'")
    # 0.80 + 150×0.00116 = 0.174 + 0.11
    assert CosteoController(db).costo_plato(esc.p1)["ingredientes"] == approx(1.084)


def test_presentacion_preferida(db, esc, sin_dialogos):
    """H2: con varias presentaciones se usa la marcada como preferida; sin ninguna, la primera creada."""
    from app.views.modulos.insumos_crud import PresentacionDialog

    saco25 = E.presentacion(db, esc.arroz, "Saco 25 kg", 25000, 25.00)  # 0.0010 $/g, creada después
    assert CosteoController(db).costo_unitario_insumo(esc.arroz)[0] == approx(0.0012)

    dlg = PresentacionDialog(db, presentacion_id=saco25)
    dlg.chk_preferida.setChecked(True)
    dlg.guardar()
    assert CosteoController(db).costo_unitario_insumo(esc.arroz)[0] == approx(0.0010)

    # Marcar el saco de 10 kg desmarca el de 25 kg: una sola preferida por insumo
    dlg = PresentacionDialog(db, presentacion_id=esc.p_arroz)
    assert not dlg.chk_preferida.isChecked()
    dlg.chk_preferida.setChecked(True)
    dlg.guardar()
    assert db.fetch_all("SELECT id FROM presentaciones_compra WHERE insumo_id=? AND es_preferida=1",
                        (esc.arroz,)) == [(esc.p_arroz,)]


def test_indirectos_por_plato_con_ventas_diarias(db, esc):
    E.dia_ventas(db, E.FECHA_VENTA, [(esc.p1, 10), (esc.p2, 20)])
    pool = CosteoController(db).pool_indirectos(E.MES, E.ANIO)
    assert pool["gastos"] == {k: approx(v) for k, v in GASTOS_MAYO.items()}
    assert pool["planilla"] == approx(PLANILLA_MAYO)
    assert pool["platos"] == 30 and pool["fuente_platos"] == "ventas diarias"
    # (1 060 + 946.2348) / 30
    assert pool["por_plato"] == approx((1060 + PLANILLA_MAYO) / 30)


def test_indirectos_sin_ventas_usa_promedio_configurado(db, esc):
    pool = CosteoController(db).pool_indirectos(E.MES, E.ANIO)
    assert pool["fuente_platos"] == "promedio configurado"
    assert pool["platos"] == 198 * 30
    assert pool["por_plato"] == approx((1060 + PLANILLA_MAYO) / 5940)


def test_indirectos_con_reporte_pos_cargado(db, esc):
    # H9: sin ventas diarias, los platos salen del reporte del POS que cubre el mes
    ok, _ = db.guardar_reporte_mensual(
        {"desde": "01/05/2026", "hasta": "31/05/2026", "pct_sugerido": 10},
        [{"code": "P1", "desc": "Pollo con arroz", "day": "Lunes", "qty": 400, "total_venta": 2400}])
    assert ok
    pool = CosteoController(db).pool_indirectos(E.MES, E.ANIO)
    assert pool["fuente_platos"] == "reporte POS" and pool["platos"] == approx(400)
    assert CosteoController(db).pool_indirectos(7, E.ANIO)["fuente_platos"] == "promedio configurado"


def test_indirectos_con_reporte_pos_de_varios_meses(db, esc):
    # 01/04–31/05 = 61 días con 610 platos -> 10 por día × 31 días de mayo
    db.guardar_reporte_mensual(
        {"desde": "01/04/2026", "hasta": "31/05/2026", "pct_sugerido": 10},
        [{"code": "P1", "desc": "Pollo con arroz", "day": "Lunes", "qty": 610, "total_venta": 0}])
    assert CosteoController(db).pool_indirectos(E.MES, E.ANIO)["platos"] == approx(310)


def test_indirectos_base_presupuesto_usa_gastos_presupuestados_y_planilla_real(db, esc):
    """H7 (decisión): con base PRESUPUESTO los gastos fijos salen del presupuesto y la planilla sigue siendo
    la real; la opción se llama «Gastos fijos del presupuesto del mes (planilla real)»."""
    pid = db.execute_query("INSERT INTO presupuestos (numero, mes, anio) VALUES (1, ?, ?)",
                           (E.MES, E.ANIO)).lastrowid
    db.execute_query("INSERT INTO detalle_presupuesto_gastos (presupuesto_id, concepto, monto) "
                     "VALUES (?, 'Alquiler', 1000)", (pid,))
    db.execute_query("INSERT INTO detalle_presupuesto_planilla (presupuesto_id, empleado_nombre, costo_total) "
                     "VALUES (?, 'Ana', 1200)", (pid,))
    db.execute_query("UPDATE costeo_config SET valor='PRESUPUESTO' WHERE clave='base_indirectos'")
    pool = CosteoController(db).pool_indirectos(E.MES, E.ANIO)
    assert pool["total_gastos"] == approx(1000)
    assert pool["planilla"] == approx(PLANILLA_MAYO)


def test_bebida_y_empaque_opcionales(db, esc):
    """El cliente elige si la bebida y el empaque entran en el costo; se informan igual como referencia."""
    c = CosteoController(db)
    # P2 lleva soda 0.50 (bebida): sin ella el costo es solo la porción de la tanda
    sin_bebida = c.costo_plato(esc.p2, "LOCAL", incluir_bebida=False)
    assert sin_bebida["total"] == approx(1.06) and sin_bebida["bebida"] == approx(0.50)
    assert not sin_bebida["incluye_bebida"] and sin_bebida["precio_sugerido"] == approx(1.06 / 0.70)
    assert [ln["incluido"] for ln in sin_bebida["lineas"] if ln["tipo"] == "BEBIDA"] == [False]
    # P1 para llevar: sin empaque baja exactamente el envase (0.20)
    sin_empaque = c.costo_plato(esc.p1, "LLEVAR", incluir_empaque=False)
    assert sin_empaque["total"] == approx(1.09) and sin_empaque["empaque"] == approx(0.20)
    assert sin_empaque["precio_sugerido"] == approx(1.09 / 0.50)
    # Por defecto, todo incluido (como antes)
    assert c.costo_plato(esc.p2, "LOCAL")["incluye_bebida"] is True


def test_las_opciones_no_cambian_rentabilidad_ni_inventario(db, esc, sin_dialogos):
    from app.controllers.kardex_controller import KardexController
    from app.controllers.rentabilidad_controller import RentabilidadController

    E.dia_ventas(db, E.FECHA_VENTA, [(esc.p1, 10), (esc.p2, 20)])
    antes = RentabilidadController(db).pyl_mensual(E.ANIO, E.MES)["costo_teorico_con_extras"]
    for clave in ("incluir_bebida", "incluir_empaque"):
        db.execute_query("UPDATE costeo_config SET valor='0' WHERE clave=?", (clave,))
    assert RentabilidadController(db).pyl_mensual(E.ANIO, E.MES)["costo_teorico_con_extras"] == approx(antes)
    db.execute_query("UPDATE costeo_config SET valor='50' WHERE clave='pct_platos_llevar'")
    reg = db.fetch_one("SELECT id FROM registro_ventas_diarias")[0]
    KardexController(db).procesar_ventas_diarias(reg)
    # 10 P1 × 50 % para llevar = 5 envases descontados aunque el empaque no entre en el costo
    assert db.fetch_one("SELECT stock_actual FROM insumos WHERE id=?", (esc.envase,))[0] == approx(-5)

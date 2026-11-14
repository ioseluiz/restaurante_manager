"""E2E de Presupuestos: reporte POS -> recetas -> presentaciones, recálculo, bloques de planilla y gastos
y control presupuestado vs. ejecutado. Usa los diálogos reales (Qt sin pantalla)."""
import pytest

import escenario_e2e as E

approx = pytest.approx

# Reporte POS de abril con 10 % sugerido. Promedio por día de la semana:
#   P1: lunes 2 + martes 3 = 5 por semana · P2: lunes 4 por semana
FILAS_POS = [
    ("P1", "Pollo con arroz", "Lunes", 8, 2, 48, 0),
    ("P1", "Pollo con arroz", "Martes", 12, 3, 72, 0),
    ("P2", "Arroz con pollo", "Lunes", 16, 4, 88, 0),
]


def _generar(db, reporte_ids, mes=E.MES, anio=E.ANIO):
    from app.views.modulos.presupuestos import CrearPresupuestoDialog
    from PyQt5.QtCore import Qt

    dlg = CrearPresupuestoDialog(db)
    dlg.cmb_mes.setCurrentText(str(mes))
    dlg.spin_anio.setValue(anio)
    for i in range(dlg.list_reportes.count()):
        item = dlg.list_reportes.item(i)
        if item.data(Qt.UserRole) in reporte_ids:
            item.setCheckState(Qt.Checked)
    dlg.generar_presupuesto()
    assert dlg.nuevo_presupuesto_id
    return dlg.nuevo_presupuesto_id


def _detalle(db, pid):
    return {r[0]: (r[1], r[2]) for r in db.fetch_all(
        "SELECT insumo_nombre, cantidad_requerida, monto_estimado FROM detalle_presupuestos "
        "WHERE presupuesto_id=?", (pid,))}


def _ver(db, pid):
    from app.views.modulos.presupuestos import VerPresupuestoDialog

    num, mes, anio, desc, monto = db.fetch_one(
        "SELECT numero, mes, anio, descripcion, monto_total FROM presupuestos WHERE id=?", (pid,))
    return VerPresupuestoDialog(db, pid, num, mes, anio, desc, monto)


def test_generar_presupuesto_de_compras(db, esc, sin_dialogos):
    rep = E.reporte_pos(db, 10, FILAS_POS)
    pid = _generar(db, [rep])
    # Platos/mes = semanal × 4: P1 20, P2 16. Requerido × 1.10:
    #   Pollo (200×20 + 200×16) × 1.1 = 7 920 g -> 1.58 cajas de 5 kg -> 2 × $20
    #   Arroz (150×20 + 150×16) × 1.1 = 5 940 g -> 1 saco × $12
    #   Tomate 60×20 × 1.1 = 1 320 g -> 1 caja × $3 · Aceite (5×20 + 20×16) × 1.1 = 462 ml -> 1 × $4
    assert _detalle(db, pid) == {
        "Pollo": (2, approx(40.0)), "Arroz": (1, approx(12.0)),
        "Tomate": (1, approx(3.0)), "Aceite": (1, approx(4.0)),
    }
    assert db.fetch_one("SELECT monto_total FROM presupuestos WHERE id=?", (pid,))[0] == approx(59.0)


def test_presupuesto_usa_la_presentacion_preferida(db, esc, sin_dialogos):
    # H2: caja de pollo de 10 kg a $38 marcada como preferida -> 7 920 g = 1 caja × $38
    caja10 = E.presentacion(db, esc.pollo, "Caja 10 kg", 10000, 38.00)
    db.execute_query("UPDATE presentaciones_compra SET es_preferida=1 WHERE id=?", (caja10,))
    pid = _generar(db, [E.reporte_pos(db, 10, FILAS_POS)])
    assert _detalle(db, pid)["Pollo"] == (1, approx(38.0))
    _ver(db, pid).recalcular_automatico(confirmar=False)
    assert _detalle(db, pid)["Pollo"] == (1, approx(38.0))


def test_recalcular_da_lo_mismo_que_generar(db, esc, sin_dialogos):
    pid = _generar(db, [E.reporte_pos(db, 10, FILAS_POS)])
    antes = _detalle(db, pid)
    _ver(db, pid).recalcular_automatico(confirmar=False)
    assert _detalle(db, pid) == antes
    assert db.fetch_one("SELECT monto_total FROM presupuestos WHERE id=?", (pid,))[0] == approx(59.0)


def test_dos_reportes_se_promedian(db, esc, sin_dialogos):
    # Un plato que no aparece en un reporte vendió 0 esa vez: el promedio divide entre 2
    r1 = E.reporte_pos(db, 10, [("P2", "Arroz con pollo", "Lunes", 40, 10, 0, 0)])
    r2 = E.reporte_pos(db, 10, [("P1", "Pollo con arroz", "Lunes", 4, 1, 0, 0)])
    pid = _generar(db, [r1, r2])
    # P2: 10/2 × 4 = 20 platos -> Arroz 150×20×1.1 = 3 300 + P1: 0.5×4 = 2 platos -> 150×2×1.1 = 330
    det = db.fetch_one("SELECT detalle_calculo FROM detalle_presupuestos WHERE presupuesto_id=? "
                       "AND insumo_nombre='Arroz'", (pid,))[0]
    assert "3630.00 g" in det


def test_presupuesto_proyecta_cuatro_semanas_por_mes(db, esc, sin_dialogos):
    """Caracterización (H4): el mes se proyecta como 4 semanas, igual que en los Excel del cliente
    (`=B13*4`). Un mes real tiene ≈4.33 semanas: con 52/12 saldrían 433 platos y 20 cajas."""
    rep = E.reporte_pos(db, 10, [("P1", "Pollo con arroz", "Lunes", 400, 100, 0, 0)])
    pid = _generar(db, [rep])
    # 100 × 4 = 400 platos -> Pollo 200 × 400 × 1.1 = 88 000 g -> 17.6 -> 18 cajas
    assert _detalle(db, pid)["Pollo"][0] == 18


def test_presupuesto_incluye_empaques_para_llevar(db, esc, sin_dialogos):
    """H10: con 40 % para llevar, P1 (20 platos/mes) necesita 20 × 1.1 × 40 % = 8.8 envases -> 1 paquete de 50.
    La soda no se agrega: la caja la vende como línea propia y entra por su propio código."""
    db.execute_query("UPDATE costeo_config SET valor='40' WHERE clave='pct_platos_llevar'")
    pid = _generar(db, [E.reporte_pos(db, 10, FILAS_POS)])
    det = _detalle(db, pid)
    assert det["Envase"] == (1, approx(10.0))
    assert "Soda" not in det
    html = db.fetch_one("SELECT detalle_calculo FROM detalle_presupuestos WHERE presupuesto_id=? "
                        "AND insumo_nombre='Envase'", (pid,))[0]
    assert "empaque para llevar (40 % de los platos)" in html and "8.80 und" in html
    _ver(db, pid).recalcular_automatico(confirmar=False)
    assert _detalle(db, pid) == det


def test_bloques_de_planilla_y_gastos(db, esc, sin_dialogos):
    from app.views.modulos.presupuestos import (
        _guardar_fila_planilla, recalcular_total_gastos, recalcular_total_planilla,
    )

    pid = _generar(db, [E.reporte_pos(db, 10, FILAS_POS)])
    _guardar_fila_planilla(db, pid, {"empleado_id": esc.ana, "empleado_nombre": "Ana Pérez", "salario_hora": 4.0,
                                     "horas_regulares": 88, "horas_domingos": 8, "horas_extra_diurnas": 4})
    assert recalcular_total_planilla(db, pid) == approx(564.606)
    for concepto, monto in (("Alquiler", 800), ("Luz (electricidad)", 140)):
        db.execute_query("INSERT INTO detalle_presupuesto_gastos (presupuesto_id, concepto, monto) VALUES (?,?,?)",
                         (pid, concepto, monto))
    assert recalcular_total_gastos(db, pid) == approx(940)
    # Los tres bloques quedan separados
    assert db.fetch_one("SELECT monto_total, monto_planilla, monto_gastos FROM presupuestos WHERE id=?", (pid,)) \
        == (approx(59.0), approx(564.606), approx(940))


def _arbol(dlg):
    """{CATEGORÍA: (presupuestado, ejecutado)} de la primera fila de cada categoría del control."""
    out = {}
    for i in range(dlg.tree.topLevelItemCount()):
        it = dlg.tree.topLevelItem(i)
        num = lambda s: float(s.replace("$", "").replace(",", ""))  # noqa: E731
        out[it.text(0)] = (num(it.text(1)), num(it.text(2)))
    return out


def _control(db, pid):
    from app.views.modulos.presupuestos import ControlPresupuestoDialog

    db.execute_query("UPDATE compras SET presupuesto_id=? WHERE id=?", (pid, 1))
    for concepto, monto in (("Alquiler", 800), ("Luz (electricidad)", 140)):
        db.execute_query("INSERT INTO detalle_presupuesto_gastos (presupuesto_id, concepto, monto) VALUES (?,?,?)",
                         (pid, concepto, monto))
    return ControlPresupuestoDialog(db, pid, 1, E.MES, E.ANIO)


def test_control_presupuestado_vs_ejecutado(db, esc, sin_dialogos):
    pid = _generar(db, [E.reporte_pos(db, 10, FILAS_POS)])
    arbol = _arbol(_control(db, pid))
    # Compras vinculadas (aún PENDIENTE): Arroz 24, Pollo 60, Tomate 6, Aceite 8 (Víveres/Carnes) + Envase 10
    # y Soda 12 (sin categoría); presupuestado: Pollo 40 / Arroz 12 + Tomate 3 + Aceite 4
    assert arbol["CARNES"] == (approx(40), approx(60))
    assert arbol["VÍVERES"] == (approx(19), approx(38))
    assert arbol["SIN CATEGORÍA"] == (approx(0), approx(22))
    assert arbol["PLANILLA"] == (approx(0), approx(946.23))
    # Gastos: presupuestado 940; ejecutado Alquiler 800 + Internet 60 + Luz 150 + Gas 50
    assert arbol["GASTOS FIJOS"] == (approx(940), approx(1060))


def test_control_muestra_saldo_global(db, esc, sin_dialogos):
    pid = _generar(db, [E.reporte_pos(db, 10, FILAS_POS)])
    dlg = _control(db, pid)
    texto = dlg.lbl_resumen.text()
    # Presupuestado 59 + 0 + 940 = 999 · ejecutado 120 + 946.23 + 1 060 = 2 126.23
    assert "$999.00" in texto and "$2,126.23" in texto
    assert "-$1,127.23 (Alerta de Exceso)" in texto

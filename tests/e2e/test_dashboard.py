"""Panel de Control: navegar a meses anteriores con las tarjetas, el top de platos y el gráfico."""
import datetime

import escenario_e2e as E


def _ir_a(panel, anio, mes):
    while panel._mes > (anio, mes):
        panel._mover_mes(-1)
    assert panel._mes == (anio, mes)


def test_panel_muestra_un_mes_anterior(db, esc, sin_dialogos):
    from app.views.dashboard import DashboardView

    E.dia_ventas(db, E.FECHA_VENTA, [(esc.p1, 10), (esc.p2, 20)])
    panel = DashboardView(db)
    hoy = datetime.date.today()
    assert panel._mes == (hoy.year, hoy.month)
    assert not panel.btn_mes_sig.isEnabled() and not panel.btn_mes_actual.isEnabled()

    _ir_a(panel, E.ANIO, E.MES)
    assert panel.lbl_badge.text() == "MAYO 2026"
    assert panel.card_mes.lbl_value.text() == "$ 201.00"
    assert panel.card_mes.lbl_sub.text() == "Mayo 2026"
    top = panel.tbl_platos["table"]
    assert [(top.item(r, 0).text(), top.item(r, 1).text()) for r in range(top.rowCount())] == [
        ("Arroz con pollo", "20"), ("Pollo con arroz", "10")]
    assert panel.btn_mes_sig.isEnabled() and panel.btn_mes_actual.isEnabled()

    # El mes anterior no tiene ventas; «Mes actual» vuelve al de hoy
    panel._mover_mes(-1)
    assert panel.card_mes.lbl_value.text() == "$ 0.00" and panel.tbl_platos["table"].rowCount() == 0
    panel._ir_mes_actual()
    assert panel._mes == (hoy.year, hoy.month)
    panel._mover_mes(1)  # no pasa del mes actual
    assert panel._mes == (hoy.year, hoy.month)

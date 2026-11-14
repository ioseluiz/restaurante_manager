"""E2E de la carga del reporte del POS con el CSV real del cliente (si está en el repositorio)."""
from pathlib import Path

import pytest

from app.controllers.report_parser import ReportParser

CSV = Path(__file__).resolve().parents[2] / "assets" / "datos_presupuesto_2025" / \
    "REPORTE EJEMPLO PROM DE VENTAS X PLATO ITALOS (2).csv"

pytestmark = pytest.mark.skipif(not CSV.exists(), reason="CSV del cliente no disponible")


@pytest.fixture(scope="module")
def reporte():
    meta, recs, err = ReportParser.parse_csv(str(CSV))
    assert err is None
    return meta, recs


def test_lee_metadatos_y_filas(reporte):
    meta, recs = reporte
    assert meta == {"desde": "01/09/2025", "hasta": "07/11/2025", "pct_sugerido": 12.16}
    assert len(recs) == 606 and len({r["code"] for r in recs}) == 115
    assert sum(r["total_venta"] for r in recs) == pytest.approx(100899.98)
    # Prom/Med = cantidad / 9 semanas en todas las filas
    assert all(r["prom"] > 0 for r in recs)
    assert all(round(r["qty"] / r["prom"]) == 9 for r in recs)


def test_guardar_y_usar_en_presupuesto(db, reporte):
    meta, recs = reporte
    ok, _ = db.guardar_reporte_mensual(meta, recs)
    assert ok
    assert db.fetch_one("SELECT COUNT(*), SUM(promedio_medida) > 0 FROM detalle_reportes_ventas") == (606, 1)


def test_estimado_por_medida(reporte):
    # H13: la vista previa mostraba Estim/Med en 0
    meta, recs = reporte
    r = recs[0]  # #IC002 jueves: Prom .22 · Estim .25 (= .22 × 1.1216)
    assert float(r["estim_med"]) == pytest.approx(0.25)
    # En todas las filas, Estim = Prom × (1 + % sugerido), con el redondeo a 2 decimales del POS
    factor = 1 + meta["pct_sugerido"] / 100
    assert all(abs(float(x["estim_med"]) - x["prom"] * factor) <= 0.02 for x in recs)

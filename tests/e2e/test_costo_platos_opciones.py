"""Vista Costo por plato: casillas «Incluir bebida» e «Incluir empaque» (se recuerdan; solo cambian el costo)."""
import pytest

approx = pytest.approx


def _fila(vista, codigo):
    t = vista.tbl_costos
    for r in range(t.rowCount()):
        if t.item(r, 1).text() == codigo:
            return {c: t.item(r, c) for c in range(t.columnCount())}
    raise AssertionError(codigo)


def test_casillas_bebida_y_empaque(db, esc, sin_dialogos):
    from app.views.modulos.costo_platos import CostoPlatosView

    vista = CostoPlatosView(db)
    vista.chk_indirectos.setChecked(False)
    assert vista.chk_bebida.isChecked() and vista.chk_empaque.isChecked()

    vista.cmb_canal.setCurrentIndex(vista.cmb_canal.findData("LLEVAR"))
    assert _fila(vista, "P1")[8]._v == approx(1.29)
    vista.chk_empaque.setChecked(False)
    fila = _fila(vista, "P1")
    assert fila[8]._v == approx(1.09)                   # total sin envase
    assert fila[6]._v == approx(0.20) and fila[6].toolTip() == "No incluido en el costo"
    assert db.fetch_one("SELECT valor FROM costeo_config WHERE clave='incluir_empaque'")[0] == "0"

    vista.cmb_canal.setCurrentIndex(vista.cmb_canal.findData("LOCAL"))
    vista.chk_bebida.setChecked(False)
    assert _fila(vista, "P2")[8]._v == approx(1.06)     # sin la soda

    # Se recuerda al volver a abrir el módulo
    otra = CostoPlatosView(db)
    assert not otra.chk_bebida.isChecked() and not otra.chk_empaque.isChecked()

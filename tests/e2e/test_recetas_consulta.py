"""Recetas (Fichas) como consulta: tipo de receta, sub-recetas, cantidades por porción y permisos."""
import pytest

from app.views.modulos.recetas_crud import (SIN_RECETA, TIPO_PORCION, TIPO_SUBRECETA, TIPO_TANDA, TIPO_USA_TANDA,
                                            RecetaDetalleDialog, RecetasCRUD, tipo_receta)

approx = pytest.approx


def _filas(vista):
    t = vista.table
    return {t.item(r, 1).text(): (t.item(r, 3).text(), t.item(r, 4).text()) for r in range(t.rowCount())}


def test_tipo_receta():
    assert tipo_receta(0, None, 0, 0) == SIN_RECETA
    assert tipo_receta(0, None, 2, 0) == TIPO_PORCION
    assert tipo_receta(0, 1000, 2, 1) == TIPO_TANDA
    assert tipo_receta(0, None, 0, 1) == TIPO_USA_TANDA
    assert tipo_receta(1, 500, 2, 0) == TIPO_SUBRECETA


def test_lista_cuenta_subrecetas_y_oculta_componentes(db, esc, sin_dialogos):
    # Plato que solo usa una tanda compartida: antes salía «Sin receta»
    pid = db.execute_query("INSERT INTO menu_items (codigo, nombre, precio_venta, es_preparado) "
                           "VALUES ('78', 'Plato eco', 3, 1)").lastrowid
    db.execute_query("INSERT INTO receta_componentes (menu_item_id, componente_id, cantidad) VALUES (?,?,30)",
                     (pid, esc.salsa))
    vista = RecetasCRUD(db)
    filas = _filas(vista)
    assert filas["78"] == (TIPO_USA_TANDA, "0 insumo(s) + 1 sub-receta(s)")
    assert filas["P2"][0] == TIPO_TANDA and filas["P1"][0] in (TIPO_PORCION, TIPO_TANDA)
    assert "#SALSA" not in filas and "SALSA" not in "".join(filas)  # componentes ocultos por defecto
    vista.chk_internas.setChecked(True)
    assert any(t == TIPO_SUBRECETA for t, _ in _filas(vista).values())


def test_detalle_por_tanda_muestra_cantidad_por_porcion(db, esc, sin_dialogos):
    dlg = RecetaDetalleDialog(db, esc.p2, "Arroz con pollo")
    assert "por tanda" in dlg.lbl_resumen.text().lower() and "porciones" in dlg.lbl_resumen.text()
    t = dlg.tbl_lineas
    lineas = {t.item(r, 1).text(): (t.item(r, 2).data(0x0100), t.item(r, 3).data(0x0100)) for r in range(t.rowCount())}
    from app.controllers.costeo_controller import CosteoController
    f = CosteoController(db).factor_por_porcion(esc.p2)
    assert f < 1
    for tanda, porcion in lineas.values():
        assert porcion == approx(tanda * f)
    # La tabla de inventario coincide con la vista explotada (lo que descuentan las ventas)
    expl = dict(db.fetch_all("SELECT i.nombre, v.cantidad_necesaria FROM v_recetas_explotadas v "
                             "JOIN insumos i ON i.id = v.insumo_id WHERE v.menu_item_id=?", (esc.p2,)))
    inv = {dlg.tbl_inventario.item(r, 0).text(): dlg.tbl_inventario.item(r, 1).data(0x0100)
           for r in range(dlg.tbl_inventario.rowCount())}
    assert inv == approx(expl)


def test_editar_solo_para_quien_ve_costo_de_platos(db, esc, sin_dialogos):
    vista = RecetasCRUD(db)
    for rol, puede in (("admin", True), ("gerente", True), ("empleado", False)):
        vista.set_rol(rol)
        assert vista.puede_editar is puede
        dlg = RecetaDetalleDialog(db, esc.p1, "P1", vista.puede_editar)
        assert dlg.btn_editar.isHidden() is not puede

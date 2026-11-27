"""Interfaz: diálogo «Importar recetas» y campos Código / Gramos por ml del Catálogo de Insumos."""
from app.utils.plantilla_recetas import LineaPlantilla, PlatoPlantilla, RecetaPlantilla, generar_plantilla


def test_insumo_guarda_codigo_normalizado_y_rechaza_repetidos(db, esc, sin_dialogos):
    from app.views.modulos.insumos_crud import InsumoDialog

    dlg = InsumoDialog(db, insumo_id=esc.arroz)
    dlg.txt_codigo.setText(" #g001 ")
    dlg.sp_g_ml.setValue(0.85)
    dlg.guardar()
    assert db.fetch_one("SELECT codigo, gramos_por_ml FROM insumos WHERE id=?", (esc.arroz,)) == ("G001", 0.85)

    otro = InsumoDialog(db, insumo_id=esc.pollo)
    otro.txt_codigo.setText("G001")
    otro.guardar()
    assert db.fetch_one("SELECT codigo FROM insumos WHERE id=?", (esc.pollo,))[0] is None
    assert any(m[1] == "Código repetido" for m in sin_dialogos)


def test_dialogo_simula_e_importa(db, esc, sin_dialogos, tmp_path):
    from app.views.importar_recetas_dialog import ImportarRecetasDialog

    ruta = str(tmp_path / "plantilla.xlsx")
    rec = RecetaPlantilla(0, "90", "Arroz blanco", "PLATO", 2000, "g", "",
                          [LineaPlantilla(0, "", "Arroz", 1000, "g"), LineaPlantilla(0, "", "Azafrán", 2, "g")],
                          [PlatoPlantilla(0, "90", "Arroz blanco", 200, "g")])
    generar_plantilla(db, ruta, [rec])
    dlg = ImportarRecetasDialog(db)
    dlg.txt_ruta.setText(ruta)
    dlg._ejecutar(True)
    texto = dlg.txt_reporte.toPlainText()
    assert "SIMULACIÓN" in texto and "Azafrán" in texto and "INSUMOS FALTANTES (1)" in texto
    assert dlg.btn_reporte.isEnabled()

    generar_plantilla(db, ruta, [RecetaPlantilla(0, "90", "Arroz blanco", "PLATO", 2000, "g", "",
                                                 [LineaPlantilla(0, "", "Arroz", 1000, "g")],
                                                 [PlatoPlantilla(0, "90", "Arroz blanco", 200, "g")])])
    dlg._ejecutar(False)
    assert "IMPORTACIÓN REALIZADA" in dlg.txt_reporte.toPlainText()
    assert db.fetch_one("SELECT rendimiento, porcion_servida FROM menu_items WHERE codigo='90'") == (2000, 200)

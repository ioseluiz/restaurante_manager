import csv
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt

class ExportarMesDialog(QDialog):
    def __init__(self, parent=None, meses=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Mes para Exportar")
        self.setMinimumWidth(300)
        self.mes_seleccionado = None
        
        layout = QVBoxLayout()
        
        lbl = QLabel("Seleccione el mes a exportar:")
        layout.addWidget(lbl)
        
        self.combo_meses = QComboBox()
        self.combo_meses.addItem("Todos")
        if meses:
            for mes in sorted(meses, reverse=True):
                self.combo_meses.addItem(mes)
        layout.addWidget(self.combo_meses)
        
        btn_layout = QHBoxLayout()
        btn_exportar = QPushButton("Exportar")
        btn_exportar.setProperty("class", "btn-success")
        btn_exportar.clicked.connect(self.aceptar)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_exportar)
        btn_layout.addWidget(btn_cancelar)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
    def aceptar(self):
        self.mes_seleccionado = self.combo_meses.currentText()
        self.accept()

def exportar_tabla_por_mes(parent, table, nombre_archivo_default, date_col_idx):
    meses_set = set()
    for row in range(table.rowCount()):
        item = table.item(row, date_col_idx)
        if item:
            fecha_texto = item.text()
            if len(fecha_texto) >= 7:
                mes = fecha_texto[:7]
                # Try to ensure it resembles YYYY-MM
                if mes[4] == '-':
                    meses_set.add(mes)
                
    dlg = ExportarMesDialog(parent, list(meses_set))
    if dlg.exec_():
        mes_elegido = dlg.mes_seleccionado
        
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getSaveFileName(parent, "Exportar a CSV", nombre_archivo_default, "CSV Files (*.csv);;All Files (*)", options=options)
        if fileName:
            try:
                with open(fileName, mode='w', newline='', encoding='utf-8-sig') as file:
                    writer = csv.writer(file)
                    
                    # Escribir encabezados
                    headers = [table.horizontalHeaderItem(col).text() for col in range(table.columnCount()) if not table.isColumnHidden(col)]
                    writer.writerow(headers)

                    # Escribir datos
                    for row in range(table.rowCount()):
                        item_fecha = table.item(row, date_col_idx)
                        if item_fecha:
                            fecha_texto = item_fecha.text()
                            if mes_elegido != "Todos" and not fecha_texto.startswith(mes_elegido):
                                continue # Omitir filas que no coinciden con el mes
                                
                        row_data = []
                        for col in range(table.columnCount()):
                            if not table.isColumnHidden(col):
                                item = table.item(row, col)
                                row_data.append(item.text() if item is not None else "")
                        writer.writerow(row_data)
                QMessageBox.information(parent, "Éxito", "Los datos se han exportado correctamente.")
            except Exception as e:
                QMessageBox.critical(parent, "Error", f"Hubo un error al exportar: {e}")

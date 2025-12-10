from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFileDialog,
    QMessageBox,
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from app.controllers.report_parser import ReportParser


class CargaReportesWidget(QWidget):
    def __init__(self, parent_callback_cancelar):
        super().__init__()
        self.callback_cancelar = parent_callback_cancelar
        self.datos_parseados = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 1. Header y Selección
        title = QLabel("<h2>Importación de Reporte de Ventas (CSV)</h2>")
        layout.addWidget(title)

        file_layout = QHBoxLayout()
        btn_select = QPushButton("Seleccionar Archivo CSV")
        btn_select.setStyleSheet(
            "background-color: #3498db; color: white; padding: 10px; font-weight: bold;"
        )
        btn_select.clicked.connect(self.abrir_dialogo_archivo)

        self.lbl_info_archivo = QLabel("Ningún archivo seleccionado")
        self.lbl_info_archivo.setStyleSheet("color: #7f8c8d; font-style: italic;")

        file_layout.addWidget(btn_select)
        file_layout.addWidget(self.lbl_info_archivo)
        layout.addLayout(file_layout)

        # 2. Info de Metadatos (Fechas detectadas en el reporte)
        meta_layout = QHBoxLayout()
        self.lbl_desde = QLabel("<b>Desde:</b> --")
        self.lbl_hasta = QLabel("<b>Hasta:</b> --")
        meta_layout.addWidget(self.lbl_desde)
        meta_layout.addWidget(self.lbl_hasta)
        meta_layout.addStretch()
        layout.addLayout(meta_layout)

        # 3. Tabla de Previsualización
        self.tabla = QTableWidget()
        # Ajustamos columnas a lo que devuelve el Parser: Code, Desc, Qty, Total
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(
            ["Código", "Descripción", "Cantidad", "Total Ventas ($)"]
        )
        self.tabla.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )  # Descripción estirada
        self.tabla.setAlternatingRowColors(True)
        layout.addWidget(self.tabla)

        # 4. Botones Acción
        action_layout = QHBoxLayout()
        self.btn_confirmar = QPushButton("Confirmar e Insertar en BD")
        self.btn_confirmar.setStyleSheet(
            "background-color: #27ae60; color: white; padding: 10px; font-weight: bold;"
        )
        self.btn_confirmar.setEnabled(
            False
        )  # Deshabilitado hasta que haya datos válidos
        self.btn_confirmar.clicked.connect(self.guardar_en_bd)

        btn_cancelar = QPushButton("Cancelar / Volver")
        btn_cancelar.setStyleSheet(
            "background-color: #c0392b; color: white; padding: 10px;"
        )
        btn_cancelar.clicked.connect(self.callback_cancelar)

        action_layout.addWidget(self.btn_confirmar)
        action_layout.addWidget(btn_cancelar)
        layout.addLayout(action_layout)

        self.setLayout(layout)

    def abrir_dialogo_archivo(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Reporte CSV",
            "",
            "Archivos CSV (*.csv);;Todos los archivos (*)",
            options=options,
        )
        if file_path:
            self.lbl_info_archivo.setText(file_path)
            self.procesar_archivo(file_path)

    def procesar_archivo(self, file_path):
        # Llamamos al Parser (Controlador)
        metadata, records, error = ReportParser.parse_csv(file_path)

        if error:
            QMessageBox.critical(self, "Error de Lectura", error)
            return

        if not records:
            QMessageBox.warning(
                self,
                "Aviso",
                "El archivo no contiene registros válidos o el formato no coincide.",
            )
            return

        # Actualizar UI
        self.lbl_desde.setText(f"<b>Desde:</b> {metadata['desde']}")
        self.lbl_hasta.setText(f"<b>Hasta:</b> {metadata['hasta']}")

        # Guardamos en memoria para uso posterior
        self.datos_parseados = records
        self.btn_confirmar.setEnabled(True)

        # Llenar Tabla
        self.llenar_tabla(records)
        QMessageBox.information(
            self,
            "Éxito",
            f"Se detectaron {len(records)} registros. Revisa la tabla antes de confirmar.",
        )

    def llenar_tabla(self, records):
        self.tabla.setRowCount(0)
        for row_idx, item in enumerate(records):
            self.tabla.insertRow(row_idx)

            # Código
            self.tabla.setItem(row_idx, 0, QTableWidgetItem(str(item["code"])))

            # Descripción
            self.tabla.setItem(row_idx, 1, QTableWidgetItem(str(item["desc"])))

            # Cantidad (Alineada derecha)
            qty_item = QTableWidgetItem(str(item["qty"]))
            qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabla.setItem(row_idx, 2, qty_item)

            # Total (Alineada derecha y formateada)
            total_item = QTableWidgetItem(f"{item['total']:.2f}")
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabla.setItem(row_idx, 3, total_item)

    def guardar_en_bd(self):
        # Esta función será el siguiente paso: iterar self.datos_parseados e insertar en tabla 'ventas' o 'movimientos'
        # Por ahora solo mostramos los datos que tenemos listos
        cantidad_total = len(self.datos_parseados)
        monto_total = sum(d["total"] for d in self.datos_parseados)

        msg = (
            f"¿Estás seguro de procesar estos {cantidad_total} registros?\n"
            f"Monto total: ${monto_total:.2f}"
        )

        confirm = QMessageBox.question(
            self, "Confirmar Carga", msg, QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            # TODO: Aquí llamaremos a self.db.insertar_venta_lote(...)
            QMessageBox.information(
                self,
                "Procesando",
                "Aquí se insertarán los datos en la base de datos (Lógica pendiente).",
            )

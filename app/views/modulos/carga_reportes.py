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
from app.database.connection import DatabaseManager


class CargaReportesWidget(QWidget):
    def __init__(self, parent_callback_cancelar):
        super().__init__()
        self.callback_cancelar = parent_callback_cancelar
        self.db = DatabaseManager()
        self.datos_parseados = []
        self.metadata_actual = {}
        self.init_ui()

    def init_ui(self):
        # Aumentar un poco el tamaño sugerido si la ventana es flotante
        self.setMinimumSize(900, 600)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 1. Header
        title = QLabel("Importación de Ventas Semanales (CSV)")
        title.setProperty("class", "header-title")
        layout.addWidget(title)

        # Selector de archivo
        file_layout = QHBoxLayout()
        btn_select = QPushButton("Seleccionar Archivo CSV")
        btn_select.setCursor(Qt.PointingHandCursor)
        btn_select.setProperty("class", "btn-primary")
        btn_select.clicked.connect(self.abrir_dialogo_archivo)

        self.lbl_info_archivo = QLabel("Ningún archivo seleccionado")
        self.lbl_info_archivo.setStyleSheet("color: #7f8c8d; font-style: italic;")

        file_layout.addWidget(btn_select)
        file_layout.addWidget(self.lbl_info_archivo)
        layout.addLayout(file_layout)

        # Info de Fechas
        meta_layout = QHBoxLayout()
        self.lbl_desde = QLabel("<b>Desde:</b> --")
        self.lbl_hasta = QLabel("<b>Hasta:</b> --")
        font_dates = QFont()
        font_dates.setPointSize(11)
        self.lbl_desde.setFont(font_dates)
        self.lbl_hasta.setFont(font_dates)

        meta_layout.addWidget(self.lbl_desde)
        meta_layout.addSpacing(20)
        meta_layout.addWidget(self.lbl_hasta)
        meta_layout.addStretch()
        layout.addLayout(meta_layout)

        # --- TABLA CONFIGURACIÓN ---
        self.tabla = QTableWidget()
        # Columnas: Código, Descripción, Día, Cantidad, Prom/Med, Total
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(
            ["Código", "Descripción", "Día", "Cant.", "Prom/Med", "Total ($)"]
        )

        # Ajuste de ancho de columnas para lectura correcta
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Código
        header.setSectionResizeMode(
            1, QHeaderView.Stretch
        )  # Descripción (ocupa lo que sobre)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Día
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Cantidad
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Prom/Med
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Total

        self.tabla.setAlternatingRowColors(True)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setShowGrid(False)  # Estilo más limpio

        layout.addWidget(self.tabla)

        # Botones Acción
        action_layout = QHBoxLayout()
        self.btn_confirmar = QPushButton("Confirmar e Insertar en BD")
        self.btn_confirmar.setCursor(Qt.PointingHandCursor)
        self.btn_confirmar.setProperty("class", "btn-success")
        self.btn_confirmar.setEnabled(False)
        self.btn_confirmar.clicked.connect(self.guardar_en_bd)

        btn_cancelar = QPushButton("Cancelar / Volver")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setProperty("class", "btn-danger")
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
        metadata, records, error = ReportParser.parse_csv(file_path)

        if error:
            QMessageBox.critical(self, "Error de Lectura", error)
            return

        if not records:
            QMessageBox.warning(self, "Aviso", "No se encontraron registros válidos.")
            return

        self.lbl_desde.setText(f"<b>Desde:</b> {metadata['desde']}")
        self.lbl_hasta.setText(f"<b>Hasta:</b> {metadata['hasta']}")

        self.datos_parseados = records
        self.metadata_actual = metadata
        self.btn_confirmar.setEnabled(True)

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

            # 0. Código
            self.tabla.setItem(row_idx, 0, QTableWidgetItem(str(item["code"])))
            # 1. Descripción
            self.tabla.setItem(row_idx, 1, QTableWidgetItem(str(item["desc"])))
            # 2. Día
            self.tabla.setItem(row_idx, 2, QTableWidgetItem(str(item["day"])))

            # 3. Cantidad
            qty_item = QTableWidgetItem(str(item["qty"]))
            qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabla.setItem(row_idx, 3, qty_item)

            # 4. Promedio (Nuevo)
            prom_item = QTableWidgetItem(f"{item.get('prom', 0.0):.2f}")
            prom_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabla.setItem(row_idx, 4, prom_item)

            # 5. Total
            total_item = QTableWidgetItem(f"{item['total']:.2f}")
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabla.setItem(row_idx, 5, total_item)

    def guardar_en_bd(self):
        if not self.datos_parseados:
            return

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
            success, message = self.db.insert_report_batch(
                self.datos_parseados,
                self.metadata_actual.get("desde", ""),
                self.metadata_actual.get("hasta", ""),
            )

            if success:
                QMessageBox.information(self, "Éxito", message)
                self.btn_confirmar.setEnabled(False)
                self.tabla.setRowCount(0)
                self.lbl_info_archivo.setText("Carga completada.")
            else:
                QMessageBox.critical(self, "Error BD", f"No se pudo guardar: {message}")

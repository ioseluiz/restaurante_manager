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


class CargaReportesWidget(QWidget):
    def __init__(self, parent_callback_cancelar):
        super().__init__()
        self.callback_cancelar = parent_callback_cancelar
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 1. Sección de Selección de Archivo
        file_layout = QHBoxLayout()
        btn_select = QPushButton("Seleccionar Archivo (CSV/Excel)")
        btn_select.setStyleSheet(
            "background-color: #3498db; color: white; padding: 10px; font-weight: bold;"
        )
        btn_select.clicked.connect(self.seleccionar_archivo_carga)

        self.lbl_archivo_seleccionado = QLabel("Ningún archivo seleccionado")
        self.lbl_archivo_seleccionado.setStyleSheet(
            "color: #7f8c8d; font-style: italic;"
        )

        file_layout.addWidget(btn_select)
        file_layout.addWidget(self.lbl_archivo_seleccionado)
        layout.addLayout(file_layout)

        # 2. Sección de Previsualización (Tabla)
        lbl_preview = QLabel("Previsualización de Datos:")
        lbl_preview.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(lbl_preview)

        self.tabla_preview_carga = QTableWidget()
        self.tabla_preview_carga.setColumnCount(4)
        self.tabla_preview_carga.setHorizontalHeaderLabels(
            ["Fecha", "Producto", "Cantidad", "Total ($)"]
        )
        self.tabla_preview_carga.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        layout.addWidget(self.tabla_preview_carga)

        # 3. Botones de Acción
        action_layout = QHBoxLayout()
        btn_cargar = QPushButton("Confirmar Carga")
        btn_cargar.setStyleSheet(
            "background-color: #27ae60; color: white; padding: 10px; font-weight: bold;"
        )
        btn_cargar.clicked.connect(self.procesar_carga)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet(
            "background-color: #c0392b; color: white; padding: 10px; font-weight: bold;"
        )
        # Usamos el callback para volver al menú principal
        btn_cancelar.clicked.connect(self.callback_cancelar)

        action_layout.addWidget(btn_cargar)
        action_layout.addWidget(btn_cancelar)
        layout.addLayout(action_layout)

        self.setLayout(layout)

    def seleccionar_archivo_carga(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Reporte",
            "",
            "Archivos de Datos (*.csv *.xlsx);;Todos los archivos (*)",
            options=options,
        )
        if file_name:
            self.lbl_archivo_seleccionado.setText(file_name)
            self.simular_previsualizacion()

    def simular_previsualizacion(self):
        # Datos ficticios para la demo
        datos_simulados = [
            ("2023-11-20", "Hamburguesa Especial", "15", "180.00"),
            ("2023-11-20", "Refresco Cola", "30", "60.00"),
            ("2023-11-21", "Papas Fritas", "25", "100.00"),
            ("2023-11-21", "Ensalada César", "10", "120.00"),
        ]

        self.tabla_preview_carga.setRowCount(len(datos_simulados))
        for row_idx, row_data in enumerate(datos_simulados):
            for col_idx, data in enumerate(row_data):
                self.tabla_preview_carga.setItem(
                    row_idx, col_idx, QTableWidgetItem(data)
                )

        QMessageBox.information(
            self, "Previsualización", "Datos cargados en vista previa (Simulación)"
        )

    def procesar_carga(self):
        # Aquí iría la lógica de insertar en BD usando un Hilo
        QMessageBox.information(self, "Info", "Iniciando procesamiento de archivo...")

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
)
from PyQt5.QtCore import Qt
from app.controllers.report_parser import ReportParser


class CargaReportesWidget(QWidget):
    def __init__(self, db, parent_callback_cancelar=None):
        """
        :param db: Instancia de DatabaseManager
        :param parent_callback_cancelar: Función para volver al menú principal
        """
        super().__init__()
        self.db = db
        self.callback_cancelar = parent_callback_cancelar
        self.current_records = []  # Para guardar los datos parseados temporalmente
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Título y Botón de Carga
        top_layout = QHBoxLayout()
        self.lbl_info = QLabel("Cargue el archivo CSV semanal (Reporte de Ventas)")
        btn_cargar = QPushButton("Seleccionar Archivo...")
        btn_cargar.clicked.connect(self.seleccionar_archivo)

        top_layout.addWidget(self.lbl_info)
        top_layout.addWidget(btn_cargar)
        layout.addLayout(top_layout)

        # Info del Reporte detectado
        info_layout = QHBoxLayout()
        self.lbl_fechas = QLabel("Periodo: -")
        self.lbl_registros = QLabel("Registros: 0")
        info_layout.addWidget(self.lbl_fechas)
        info_layout.addWidget(self.lbl_registros)
        layout.addLayout(info_layout)

        # Tabla de Previsualización
        self.table = QTableWidget()
        # Columnas: Código, Descripción, Día, Cantidad, Promedio, Total
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Código", "Descripción", "Día", "Cant.", "Prom/Med", "Total ($)"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

        # Botones de Acción (Confirmar / Cancelar)
        actions_layout = QHBoxLayout()

        btn_confirmar = QPushButton("Confirmar e Insertar en BD")
        btn_confirmar.setStyleSheet(
            "background-color: #28a745; color: white; font-weight: bold; padding: 10px;"
        )
        btn_confirmar.clicked.connect(self.guardar_en_bd)

        btn_cancelar = QPushButton("Cancelar / Volver")
        btn_cancelar.setStyleSheet(
            "background-color: #dc3545; color: white; padding: 10px;"
        )

        # Conexión segura: verificamos si existe el callback antes de conectar
        if self.callback_cancelar:
            btn_cancelar.clicked.connect(self.accion_cancelar)
        else:
            btn_cancelar.setEnabled(False)

        actions_layout.addWidget(btn_cancelar)
        actions_layout.addWidget(btn_confirmar)
        layout.addLayout(actions_layout)

        self.setLayout(layout)

    def seleccionar_archivo(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, "Abrir Reporte CSV", "", "CSV Files (*.csv)"
        )
        if fname:
            try:
                parser = ReportParser(fname)
                self.current_records = parser.parse()
                self.mostrar_datos(self.current_records, parser.metadata)
            except Exception as e:
                QMessageBox.critical(
                    self, "Error de Lectura", f"No se pudo leer el archivo:\n{str(e)}"
                )

    def mostrar_datos(self, records, metadata):
        # Actualizar Etiquetas
        inicio = metadata.get("fecha_inicio", "?")
        fin = metadata.get("fecha_fin", "?")
        self.lbl_fechas.setText(f"Periodo: {inicio} al {fin}")
        self.lbl_registros.setText(f"Registros: {len(records)}")

        # Llenar Tabla
        self.table.setRowCount(0)
        for r_idx, row in enumerate(records):
            self.table.insertRow(r_idx)
            self.table.setItem(r_idx, 0, QTableWidgetItem(str(row["code"])))
            self.table.setItem(r_idx, 1, QTableWidgetItem(str(row["desc"])))
            self.table.setItem(r_idx, 2, QTableWidgetItem(str(row["day"])))
            self.table.setItem(r_idx, 3, QTableWidgetItem(str(row["qty"])))
            self.table.setItem(
                r_idx, 4, QTableWidgetItem(str(row.get("prom", 0.0)))
            )  # Promedio
            self.table.setItem(r_idx, 5, QTableWidgetItem(str(row["total"])))

    def guardar_en_bd(self):
        if not self.current_records:
            return QMessageBox.warning(self, "Vacío", "No hay datos para guardar.")

        # Obtener fechas del label (un poco sucio, pero funcional por ahora)
        texto_fechas = self.lbl_fechas.text().replace("Periodo: ", "")
        try:
            f_inicio, f_fin = texto_fechas.split(" al ")
        except:
            f_inicio, f_fin = "Unknown", "Unknown"

        # Llamar al manager
        success, msg = self.db.insert_report_batch(
            self.current_records, f_inicio, f_fin
        )

        if success:
            QMessageBox.information(self, "Éxito", msg)
            self.limpiar_interfaz()
        else:
            QMessageBox.critical(self, "Error de Base de Datos", msg)

    def limpiar_interfaz(self):
        """Limpia la tabla y variables temporales."""
        self.current_records = []
        self.table.setRowCount(0)
        self.lbl_fechas.setText("Periodo: -")
        self.lbl_registros.setText("Registros: 0")

    def accion_cancelar(self):
        """Limpia y ejecuta el callback de regreso."""
        self.limpiar_interfaz()
        if self.callback_cancelar:
            self.callback_cancelar()

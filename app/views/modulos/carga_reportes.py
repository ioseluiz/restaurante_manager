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
    QTabWidget,
    QSplitter,
    QAbstractItemView,
)
from PyQt5.QtCore import Qt
from app.controllers.report_parser import ReportParser


class CargaReportesWidget(QWidget):
    """
    Widget principal que contiene las pestañas para Cargar y Visualizar Reportes.
    """

    def __init__(self, db, parent_callback_cancelar=None):
        super().__init__()
        self.db = db
        self.callback_cancelar = parent_callback_cancelar
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Título General
        lbl_main = QLabel("Gestión de Reportes Mensuales")
        lbl_main.setStyleSheet(
            "font-size: 18px; font-weight: bold; margin-bottom: 10px;"
        )
        layout.addWidget(lbl_main)

        # Sistema de Pestañas
        self.tabs = QTabWidget()

        # Pestaña 1: Carga (Instancia de la clase interna PestanaCarga)
        self.tab_carga = PestanaCarga(self.db, self.callback_cancelar)

        # Pestaña 2: Historial (Instancia de la clase interna PestanaHistorial)
        self.tab_historial = PestanaHistorial(self.db)

        self.tabs.addTab(self.tab_carga, "📥 Cargar Nuevo Reporte")
        self.tabs.addTab(self.tab_historial, "📋 Historial y Consultas")

        # Evento al cambiar de pestaña (para refrescar el historial al entrar)
        self.tabs.currentChanged.connect(self.al_cambiar_pestana)

        layout.addWidget(self.tabs)

    def al_cambiar_pestana(self, index):
        # Si cambiamos a la pestaña de historial (índice 1), refrescar datos
        if index == 1:
            self.tab_historial.cargar_lista_reportes()


class PestanaCarga(QWidget):
    """
    Funcionalidad de carga de CSV.
    """

    def __init__(self, db, callback_cancelar):
        super().__init__()
        self.db = db
        self.callback_cancelar = callback_cancelar
        self.current_records = []
        self.current_metadata = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Instrucciones
        lbl_info = QLabel(
            "Seleccione el archivo CSV generado por el POS para cargar al sistema."
        )
        layout.addWidget(lbl_info)

        # Botón de Selección
        top_layout = QHBoxLayout()
        btn_cargar = QPushButton("Seleccionar Archivo CSV...")
        btn_cargar.setStyleSheet("padding: 8px;")
        btn_cargar.clicked.connect(self.seleccionar_archivo)
        top_layout.addWidget(btn_cargar)
        layout.addLayout(top_layout)

        # Info del Reporte detectado
        info_group = QHBoxLayout()
        self.lbl_fechas = QLabel("Periodo Detectado: -")
        self.lbl_fechas.setStyleSheet("font-weight: bold; color: #007bff;")
        self.lbl_registros = QLabel("Registros: 0")
        info_group.addWidget(self.lbl_fechas)
        info_group.addWidget(self.lbl_registros)
        layout.addLayout(info_group)

        # Tabla de Previsualización
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Código", "Descripción", "Día", "Cant.", "Venta ($)", "Costo ($)"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

        # Botones de Acción
        actions_layout = QHBoxLayout()
        btn_confirmar = QPushButton("Guardar en Base de Datos")
        btn_confirmar.setStyleSheet(
            "background-color: #28a745; color: white; font-weight: bold; padding: 10px;"
        )
        btn_confirmar.clicked.connect(self.guardar_en_bd)

        btn_cancelar = QPushButton("Cancelar / Cerrar")
        btn_cancelar.setStyleSheet(
            "background-color: #6c757d; color: white; padding: 10px;"
        )
        if self.callback_cancelar:
            btn_cancelar.clicked.connect(self.callback_cancelar)

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
                metadata, records, error = ReportParser.parse_csv(fname)
                if error:
                    QMessageBox.warning(self, "Advertencia", error)

                self.current_records = records
                self.current_metadata = metadata
                self.mostrar_datos(records, metadata)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error leyendo archivo:\n{str(e)}")

    def mostrar_datos(self, records, metadata):
        inicio = metadata.get("desde", "N/A")
        fin = metadata.get("hasta", "N/A")
        self.lbl_fechas.setText(f"Periodo Detectado: {inicio} al {fin}")
        self.lbl_registros.setText(f"Registros: {len(records)}")

        limit = min(len(records), 500)
        self.table.setRowCount(limit)
        for r_idx in range(limit):
            row = records[r_idx]
            self.table.setItem(r_idx, 0, QTableWidgetItem(str(row["code"])))
            self.table.setItem(r_idx, 1, QTableWidgetItem(str(row["desc"])))
            self.table.setItem(r_idx, 2, QTableWidgetItem(str(row["day"])))
            self.table.setItem(r_idx, 3, QTableWidgetItem(str(row["qty"])))
            self.table.setItem(r_idx, 4, QTableWidgetItem(f"{row['total_venta']:.2f}"))
            self.table.setItem(r_idx, 5, QTableWidgetItem(f"{row['total_costo']:.2f}"))

    def guardar_en_bd(self):
        if not self.current_records:
            return QMessageBox.warning(self, "Vacío", "No hay datos para guardar.")

        confirm = QMessageBox.question(
            self,
            "Confirmar",
            "¿Guardar este reporte en el historial?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            success, msg = self.db.guardar_reporte_mensual(
                self.current_metadata, self.current_records
            )
            if success:
                QMessageBox.information(self, "Éxito", msg)
                self.limpiar()
            else:
                QMessageBox.critical(self, "Error BD", msg)

    def limpiar(self):
        self.current_records = []
        self.table.setRowCount(0)
        self.lbl_fechas.setText("Periodo Detectado: -")
        self.lbl_registros.setText("Registros: 0")


class PestanaHistorial(QWidget):
    """
    Nueva pestaña para visualizar reportes guardados.
    """

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Usamos un Splitter para dividir la lista de reportes (arriba) y el detalle (abajo)
        splitter = QSplitter(Qt.Vertical)

        # --- SECCIÓN SUPERIOR: LISTA DE REPORTES ---
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.addWidget(
            QLabel("<b>1. Reportes Disponibles</b> (Haga clic para ver detalle)")
        )

        self.tabla_reportes = QTableWidget()
        self.tabla_reportes.setColumnCount(5)
        self.tabla_reportes.setHorizontalHeaderLabels(
            ["ID", "Inicio Periodo", "Fin Periodo", "Total Ventas ($)", "Fecha Carga"]
        )
        self.tabla_reportes.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_reportes.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_reportes.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_reportes.itemClicked.connect(self.cargar_detalle_reporte)

        top_layout.addWidget(self.tabla_reportes)

        # Botón Eliminar Reporte
        btn_eliminar = QPushButton("Eliminar Reporte Seleccionado")
        btn_eliminar.setStyleSheet(
            "background-color: #dc3545; color: white; padding: 5px;"
        )
        btn_eliminar.clicked.connect(self.eliminar_reporte)
        top_layout.addWidget(btn_eliminar, alignment=Qt.AlignRight)

        splitter.addWidget(top_widget)

        # --- SECCIÓN INFERIOR: DETALLE DEL REPORTE ---
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        self.lbl_detalle = QLabel("<b>2. Detalle de Ventas</b>")
        bottom_layout.addWidget(self.lbl_detalle)

        self.tabla_detalle = QTableWidget()
        self.tabla_detalle.setColumnCount(6)
        self.tabla_detalle.setHorizontalHeaderLabels(
            ["Código", "Producto", "Día", "Cant.", "Venta ($)", "Costo ($)"]
        )
        self.tabla_detalle.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        bottom_layout.addWidget(self.tabla_detalle)
        splitter.addWidget(bottom_widget)

        layout.addWidget(splitter)

        # Carga inicial
        self.cargar_lista_reportes()

    def cargar_lista_reportes(self):
        """Consulta la BD y llena la tabla superior."""
        reportes = self.db.obtener_reportes_registrados()
        self.tabla_reportes.setRowCount(0)
        self.tabla_detalle.setRowCount(0)
        self.lbl_detalle.setText("<b>2. Detalle de Ventas</b>")

        for i, row in enumerate(reportes):
            self.tabla_reportes.insertRow(i)
            # row: id, inicio, fin, total, fecha_carga
            id_rep = str(row[0])
            self.tabla_reportes.setItem(i, 0, QTableWidgetItem(id_rep))
            self.tabla_reportes.setItem(i, 1, QTableWidgetItem(str(row[1])))
            self.tabla_reportes.setItem(i, 2, QTableWidgetItem(str(row[2])))
            self.tabla_reportes.setItem(i, 3, QTableWidgetItem(f"{row[3]:.2f}"))
            self.tabla_reportes.setItem(i, 4, QTableWidgetItem(str(row[4])))

    def cargar_detalle_reporte(self, item):
        """Carga los ítems del reporte seleccionado."""
        row_idx = item.row()
        reporte_id = self.tabla_reportes.item(row_idx, 0).text()
        periodo = f"{self.tabla_reportes.item(row_idx, 1).text()} al {self.tabla_reportes.item(row_idx, 2).text()}"

        self.lbl_detalle.setText(
            f"<b>2. Detalle de Ventas</b> (Reporte #{reporte_id}: {periodo})"
        )

        detalles = self.db.obtener_detalle_reporte(reporte_id)
        self.tabla_detalle.setRowCount(len(detalles))

        for i, row in enumerate(detalles):
            # row: codigo, nombre, dia, cantidad, venta, costo
            self.tabla_detalle.setItem(i, 0, QTableWidgetItem(str(row[0])))
            self.tabla_detalle.setItem(i, 1, QTableWidgetItem(str(row[1])))
            self.tabla_detalle.setItem(i, 2, QTableWidgetItem(str(row[2])))
            self.tabla_detalle.setItem(i, 3, QTableWidgetItem(str(row[3])))
            self.tabla_detalle.setItem(i, 4, QTableWidgetItem(f"{row[4]:.2f}"))
            self.tabla_detalle.setItem(i, 5, QTableWidgetItem(f"{row[5]:.2f}"))

    def eliminar_reporte(self):
        filas = self.tabla_reportes.selectionModel().selectedRows()
        if not filas:
            return QMessageBox.warning(
                self, "Aviso", "Seleccione un reporte de la lista superior."
            )

        row_idx = filas[0].row()
        reporte_id = self.tabla_reportes.item(row_idx, 0).text()

        confirm = QMessageBox.question(
            self,
            "Eliminar",
            f"¿Eliminar permanentemente el reporte #{reporte_id}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            success, msg = self.db.eliminar_reporte(reporte_id)
            if success:
                self.cargar_lista_reportes()
                QMessageBox.information(self, "Éxito", msg)
            else:
                QMessageBox.critical(self, "Error", msg)

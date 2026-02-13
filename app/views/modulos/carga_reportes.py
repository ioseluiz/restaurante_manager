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
from PyQt5.QtGui import QColor  # Importación necesaria para el color
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

        # Pestaña 1: Carga
        self.tab_carga = PestanaCarga(self.db, self.callback_cancelar)

        # Pestaña 2: Historial
        self.tab_historial = PestanaHistorial(self.db)

        self.tabs.addTab(self.tab_carga, "📥 Cargar Nuevo Reporte")
        self.tabs.addTab(self.tab_historial, "📋 Historial y Consultas")

        self.tabs.currentChanged.connect(self.al_cambiar_pestana)

        layout.addWidget(self.tabs)

    def al_cambiar_pestana(self, index):
        if index == 1:
            self.tab_historial.cargar_lista_reportes()


class PestanaCarga(QWidget):
    """
    Funcionalidad de carga de CSV con validación visual.
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
        lbl_info = QLabel("Seleccione el archivo CSV generado por el POS.")
        layout.addWidget(lbl_info)

        # Leyenda de Colores
        lbl_leyenda = QLabel(
            "Leyenda: <span style='background-color:#ffcccc'>&nbsp;&nbsp;&nbsp;&nbsp;</span> El código NO existe en el Menú (debe registrarlo)."
        )
        lbl_leyenda.setTextFormat(Qt.RichText)
        layout.addWidget(lbl_leyenda)

        # Botón de Selección
        top_layout = QHBoxLayout()
        btn_cargar = QPushButton("Seleccionar Archivo CSV...")
        btn_cargar.setStyleSheet("padding: 8px;")
        btn_cargar.clicked.connect(self.seleccionar_archivo)
        top_layout.addWidget(btn_cargar)
        layout.addLayout(top_layout)

        # Info del Reporte
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

        btn_cancelar = QPushButton("Limpiar / Cancelar")
        btn_cancelar.setStyleSheet(
            "background-color: #6c757d; color: white; padding: 10px;"
        )

        # CORRECCIÓN: Conectamos siempre a la función local, no condicionalmente
        btn_cancelar.clicked.connect(self.accion_cancelar)

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
        # 1. Obtener lista de códigos existentes en la BD para comparar
        codigos_bd = self.db.obtener_todos_codigos_menu()

        # UI Info
        inicio = metadata.get("desde", "N/A")
        fin = metadata.get("hasta", "N/A")
        self.lbl_fechas.setText(f"Periodo Detectado: {inicio} al {fin}")
        self.lbl_registros.setText(f"Registros: {len(records)}")

        # Limitar visualización para rendimiento
        limit = min(len(records), 500)
        self.table.setRowCount(limit)

        color_alerta = QColor("#ffcccc")  # Rojo claro

        for r_idx in range(limit):
            row = records[r_idx]
            codigo_reporte = str(row["code"]).strip()

            # Crear items
            item_code = QTableWidgetItem(codigo_reporte)
            item_desc = QTableWidgetItem(str(row["desc"]))
            item_day = QTableWidgetItem(str(row["day"]))
            item_qty = QTableWidgetItem(str(row["qty"]))
            item_venta = QTableWidgetItem(f"{row['total_venta']:.2f}")
            item_costo = QTableWidgetItem(f"{row['total_costo']:.2f}")

            # VALIDACIÓN: Si el código NO está en la lista de la BD, pintar de rojo
            if codigo_reporte not in codigos_bd:
                for item in [
                    item_code,
                    item_desc,
                    item_day,
                    item_qty,
                    item_venta,
                    item_costo,
                ]:
                    item.setBackground(color_alerta)
                    item.setToolTip("Este código no existe en el menú actual.")

            self.table.setItem(r_idx, 0, item_code)
            self.table.setItem(r_idx, 1, item_desc)
            self.table.setItem(r_idx, 2, item_day)
            self.table.setItem(r_idx, 3, item_qty)
            self.table.setItem(r_idx, 4, item_venta)
            self.table.setItem(r_idx, 5, item_costo)

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

    def accion_cancelar(self):
        """Limpia el formulario y ejecuta el callback si existe."""
        self.limpiar()
        if self.callback_cancelar:
            self.callback_cancelar()

    def limpiar(self):
        self.current_records = []
        self.current_metadata = {}
        self.table.setRowCount(0)
        self.lbl_fechas.setText("Periodo Detectado: -")
        self.lbl_registros.setText("Registros: 0")


class PestanaHistorial(QWidget):
    """
    Pestaña para visualizar reportes guardados.
    """

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Splitter Vertical
        splitter = QSplitter(Qt.Vertical)

        # --- ARRIBA: LISTA ---
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.addWidget(
            QLabel("<b>1. Reportes Disponibles</b> (Click para ver detalle)")
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

        btn_eliminar = QPushButton("Eliminar Reporte Seleccionado")
        btn_eliminar.setStyleSheet(
            "background-color: #dc3545; color: white; padding: 5px;"
        )
        btn_eliminar.clicked.connect(self.eliminar_reporte)
        top_layout.addWidget(btn_eliminar, alignment=Qt.AlignRight)

        splitter.addWidget(top_widget)

        # --- ABAJO: DETALLE ---
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
        row_idx = item.row()
        reporte_id = self.tabla_reportes.item(row_idx, 0).text()
        periodo = f"{self.tabla_reportes.item(row_idx, 1).text()} al {self.tabla_reportes.item(row_idx, 2).text()}"

        self.lbl_detalle.setText(
            f"<b>2. Detalle de Ventas</b> (Reporte #{reporte_id}: {periodo})"
        )

        detalles = self.db.obtener_detalle_reporte(reporte_id)
        self.tabla_detalle.setRowCount(len(detalles))

        for i, row in enumerate(detalles):
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

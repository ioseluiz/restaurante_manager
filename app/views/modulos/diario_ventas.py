from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QLineEdit,
    QDialog,
    QFormLayout,
    QHeaderView,
    QMessageBox,
    QDateEdit,
    QDoubleSpinBox,
    QSpinBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor

class NumericItem(QTableWidgetItem):
    """Permite ordenar columnas numéricas correctamente."""
    def __lt__(self, other):
        try:
            return float(self.text()) < float(other.text())
        except ValueError:
            return super().__lt__(other)

class DiarioVentasDialog(QDialog):
    def __init__(self, db_manager, data=None, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.data = data
        self.setWindowTitle("Registro de Diario de Ventas")
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        self.fecha_input = QDateEdit()
        self.fecha_input.setCalendarPopup(True)
        self.fecha_input.setDisplayFormat("yyyy-MM-dd")
        self.fecha_input.setDate(QDate.currentDate())
        
        self.total_ventas_input = QDoubleSpinBox()
        self.total_ventas_input.setMaximum(999999999.99)
        self.total_ventas_input.setDecimals(2)
        font = self.total_ventas_input.font()
        font.setBold(True)
        self.total_ventas_input.setFont(font)
        
        self.yappy_input = QDoubleSpinBox()
        self.yappy_input.setMaximum(999999999.99)
        self.yappy_input.setDecimals(2)
        
        self.pedidos_ya_input = QDoubleSpinBox()
        self.pedidos_ya_input.setMaximum(999999999.99)
        self.pedidos_ya_input.setDecimals(2)
        
        self.no_facturas_input = QSpinBox()
        self.no_facturas_input.setMaximum(9999999)
        
        self.sobrante_input = QDoubleSpinBox()
        self.sobrante_input.setMaximum(999999999.99)
        self.sobrante_input.setDecimals(2)
        
        self.faltante_input = QDoubleSpinBox()
        self.faltante_input.setMaximum(999999999.99)
        self.faltante_input.setDecimals(2)
        
        self.depositos_input = QDoubleSpinBox()
        self.depositos_input.setMaximum(999999999.99)
        self.depositos_input.setDecimals(2)

        form.addRow("Fecha:", self.fecha_input)
        form.addRow("TOTAL VENTAS:", self.total_ventas_input)
        form.addRow("Pagos Yappy:", self.yappy_input)
        form.addRow("Pagos Pedidos Ya:", self.pedidos_ya_input)
        form.addRow("No. Facturas:", self.no_facturas_input)
        form.addRow("Sobrante Caja:", self.sobrante_input)
        form.addRow("Faltante Caja:", self.faltante_input)
        form.addRow("Depósitos:", self.depositos_input)

        if self.data:
            self.fecha_input.setDate(QDate.fromString(self.data.get("fecha", ""), "yyyy-MM-dd"))
            self.total_ventas_input.setValue(float(self.data.get("total_ventas", 0.0)))
            self.yappy_input.setValue(float(self.data.get("yappy", 0.0)))
            self.pedidos_ya_input.setValue(float(self.data.get("pedidos_ya", 0.0)))
            self.no_facturas_input.setValue(int(self.data.get("no_facturas", 0)))
            self.sobrante_input.setValue(float(self.data.get("sobrante", 0.0)))
            self.faltante_input.setValue(float(self.data.get("faltante", 0.0)))
            self.depositos_input.setValue(float(self.data.get("depositos", 0.0)))

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Guardar")
        btn_save.setProperty("class", "btn-success")
        btn_save.clicked.connect(self.save)
        
        btn_save_and_add = QPushButton("Guardar y Añadir Otro")
        btn_save_and_add.clicked.connect(self.save_and_add)
        if self.data:
            btn_save_and_add.hide()
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_save_and_add)
        btn_layout.addWidget(btn_cancel)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def guardar_registro(self):
        fecha = self.fecha_input.date().toString("yyyy-MM-dd")
        total_ventas = self.total_ventas_input.value()
        yappy = self.yappy_input.value()
        pedidos_ya = self.pedidos_ya_input.value()
        no_facturas = self.no_facturas_input.value()
        sobrante = self.sobrante_input.value()
        faltante = self.faltante_input.value()
        depositos = self.depositos_input.value()

        if self.data:
            query = """
                UPDATE diario_ventas 
                SET fecha=?, total_ventas=?, yappy=?, pedidos_ya=?, no_facturas=?, sobrante=?, faltante=?, depositos=?
                WHERE id=?
            """
            self.db.cursor.execute(query, (fecha, total_ventas, yappy, pedidos_ya, no_facturas, sobrante, faltante, depositos, self.data["id"]))
        else:
            query = """
                INSERT INTO diario_ventas (fecha, total_ventas, yappy, pedidos_ya, no_facturas, sobrante, faltante, depositos)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.db.cursor.execute(query, (fecha, total_ventas, yappy, pedidos_ya, no_facturas, sobrante, faltante, depositos))
            
        self.db.conn.commit()
        return True

    def save(self):
        if self.guardar_registro():
            self.accept()

    def save_and_add(self):
        if self.guardar_registro():
            self.total_ventas_input.setValue(0.0)
            self.yappy_input.setValue(0.0)
            self.pedidos_ya_input.setValue(0.0)
            self.no_facturas_input.setValue(0)
            self.sobrante_input.setValue(0.0)
            self.faltante_input.setValue(0.0)
            self.depositos_input.setValue(0.0)
            self.total_ventas_input.setFocus()


class DiarioVentasView(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.filtros = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # --- HEADER ---
        header_layout = QHBoxLayout()
        title = QLabel("<h2>Diario de Ventas</h2>")
        header_layout.addWidget(title)
        header_layout.addStretch()

        btn_add = QPushButton(" + Nuevo Registro")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setProperty("class", "btn-success")
        btn_add.clicked.connect(self.abrir_crear)

        btn_edit = QPushButton("Editar Seleccionado")
        btn_edit.setCursor(Qt.PointingHandCursor)
        btn_edit.clicked.connect(self.abrir_editar)

        btn_del = QPushButton("Eliminar")
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setProperty("class", "btn-danger")
        btn_del.clicked.connect(self.eliminar)

        header_layout.addWidget(btn_add)
        header_layout.addWidget(btn_edit)
        header_layout.addWidget(btn_del)
        layout.addLayout(header_layout)

        # --- RESUMEN MENSUAL ---
        lbl_resumen = QLabel("<h3>Resumen Mensual de Ventas</h3>")
        layout.addWidget(lbl_resumen)

        self.table_resumen = QTableWidget()
        self.table_resumen.setColumnCount(3)
        self.table_resumen.setHorizontalHeaderLabels(["Mes/Año", "Total Ventas", "Total Depósitos"])
        self.table_resumen.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_resumen.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_resumen.setMaximumHeight(150)
        layout.addWidget(self.table_resumen)

        lbl_transacciones = QLabel("<h3>Registro Diario</h3>")
        layout.addWidget(lbl_transacciones)

        # --- FILTROS ---
        filter_layout = QHBoxLayout()
        inp_fecha = QLineEdit()
        inp_fecha.setPlaceholderText("Filtrar Fecha (YYYY-MM-DD)")
        inp_fecha.setClearButtonEnabled(True)
        inp_fecha.textChanged.connect(self.aplicar_filtros)
        self.filtros[1] = inp_fecha # Columna 1 es Fecha
        filter_layout.addWidget(inp_fecha)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # --- TABLA ---
        self.table = QTableWidget()
        
        self.columnas = [
            "ID", "FECHA", "TOTAL VENTAS", "YAPPY", "PEDIDOS YA", "NO FACT", "SOBRANTE", "FALTANTE", "DEPOSITOS"
        ]
        self.db_columns = [
            "id", "fecha", "total_ventas", "yappy", "pedidos_ya", "no_facturas", "sobrante", "faltante", "depositos"
        ]
        
        self.table.setColumnCount(len(self.columnas))
        self.table.setHorizontalHeaderLabels(self.columnas)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.table.setColumnWidth(1, 100) # Fecha
        for i in range(2, len(self.columnas) - 1):
            self.table.setColumnWidth(i, 90)
        
        # Stretch last column to avoid black space
        header.setSectionResizeMode(len(self.columnas) - 1, QHeaderView.Stretch)
            
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.hideColumn(0)  # Ocultar ID
        
        layout.addWidget(self.table)
        self.setLayout(layout)

    def cargar_datos(self):
        self.cargar_resumen()
        
        self.table.setSortingEnabled(False)
        cols_query = ", ".join(self.db_columns)
        self.db.cursor.execute(f"SELECT {cols_query} FROM diario_ventas ORDER BY fecha DESC, id DESC")
        rows = self.db.cursor.fetchall()
        self.table.setRowCount(0)

        for r_idx, row in enumerate(rows):
            self.table.insertRow(r_idx)
            
            # ID
            self.table.setItem(r_idx, 0, NumericItem(str(row[0])))
            # FECHA
            self.table.setItem(r_idx, 1, QTableWidgetItem(str(row[1] or "")))
            
            # TOTAL VENTAS
            item_total = NumericItem(f"{float(row[2] or 0.0):.2f}")
            font = item_total.font()
            font.setBold(True)
            item_total.setFont(font)
            self.table.setItem(r_idx, 2, item_total)
            
            # Montos
            self.table.setItem(r_idx, 3, NumericItem(f"{float(row[3] or 0.0):.2f}"))
            self.table.setItem(r_idx, 4, NumericItem(f"{float(row[4] or 0.0):.2f}"))
            
            # NO FACT (entero)
            self.table.setItem(r_idx, 5, NumericItem(str(row[5] or 0)))
            
            # Sobrante / Faltante / Depositos
            item_sob = NumericItem(f"{float(row[6] or 0.0):.2f}")
            if float(row[6] or 0.0) > 0:
                item_sob.setForeground(QColor("green"))
            self.table.setItem(r_idx, 6, item_sob)
            
            item_falt = NumericItem(f"{float(row[7] or 0.0):.2f}")
            if float(row[7] or 0.0) > 0:
                item_falt.setForeground(QColor("red"))
            self.table.setItem(r_idx, 7, item_falt)
            
            self.table.setItem(r_idx, 8, NumericItem(f"{float(row[8] or 0.0):.2f}"))

        self.table.setSortingEnabled(True)
        self.aplicar_filtros()

    def cargar_resumen(self):
        self.db.cursor.execute("""
            SELECT 
                strftime('%Y-%m', fecha) as mes_anio,
                SUM(total_ventas) as suma_ventas,
                SUM(depositos) as suma_depositos
            FROM diario_ventas
            GROUP BY mes_anio
            ORDER BY mes_anio DESC
        """)
        
        rows = self.db.cursor.fetchall()
        self.table_resumen.setRowCount(0)
        
        for r_idx, row in enumerate(rows):
            self.table_resumen.insertRow(r_idx)
            
            mes_anio = row[0]
            ventas = float(row[1] or 0.0)
            depositos = float(row[2] or 0.0)
            
            self.table_resumen.setItem(r_idx, 0, QTableWidgetItem(mes_anio))
            
            item_ventas = NumericItem(f"{ventas:.2f}")
            item_ventas.setForeground(QColor("green"))
            self.table_resumen.setItem(r_idx, 1, item_ventas)
            
            self.table_resumen.setItem(r_idx, 2, NumericItem(f"{depositos:.2f}"))

    def aplicar_filtros(self):
        rows = self.table.rowCount()
        for row in range(rows):
            mostrar = True
            for col, inp in self.filtros.items():
                texto_filtro = inp.text().lower().strip()
                if not texto_filtro:
                    continue
                item = self.table.item(row, col)
                if item:
                    if texto_filtro not in item.text().lower():
                        mostrar = False
                        break
            self.table.setRowHidden(row, not mostrar)

    def abrir_crear(self):
        dlg = DiarioVentasDialog(self.db, parent=self)
        if dlg.exec_():
            self.cargar_datos()

    def abrir_editar(self):
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(self, "Aviso", "Seleccione un registro para editar.")

        id_registro = self.table.item(row, 0).text()
        
        cols_query = ", ".join(self.db_columns)
        self.db.cursor.execute(f"SELECT {cols_query} FROM diario_ventas WHERE id=?", (id_registro,))
        row_data = self.db.cursor.fetchone()
        
        if row_data:
            data = dict(zip(self.db_columns, row_data))
            dlg = DiarioVentasDialog(self.db, data=data, parent=self)
            if dlg.exec_():
                self.cargar_datos()

    def eliminar(self):
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(self, "Aviso", "Seleccione un registro para eliminar.")

        id_registro = self.table.item(row, 0).text()
        reply = QMessageBox.question(self, 'Confirmar', '¿Está seguro de eliminar este registro?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.db.cursor.execute("DELETE FROM diario_ventas WHERE id=?", (id_registro,))
            self.db.conn.commit()
            self.cargar_datos()
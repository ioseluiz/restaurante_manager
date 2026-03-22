from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QLineEdit,
    QTextEdit,
    QDialog,
    QFormLayout,
    QHeaderView,
    QMessageBox,
    QDateEdit,
    QDoubleSpinBox,
    QScrollArea,
    QComboBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor

class NumericItem(QTableWidgetItem):
    def __lt__(self, other):
        try:
            return float(self.text()) < float(other.text())
        except ValueError:
            return super().__lt__(other)

class PagoEfectivoDialog(QDialog):
    def __init__(self, db_manager, data=None, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.data = data
        self.setWindowTitle("Registro de Pago en Efectivo")
        self.setMinimumWidth(550)
        
        self.etiquetas_db = {
            "Costo de Víveres": "costo_viveres",
            "Costo de Carnes": "costo_carnes",
            "Desayunos": "desayunos",
            "Otros": "otros",
            "Planilla": "planilla",
            "Gastos Propietarios": "gastos_propietarios",
            "Honorarios": "honorarios",
            "Reparaciones y Mantenimiento": "reparaciones_mantenimiento",
            "Atención Empleados": "atencion_empleados",
            "Combustible": "combustible",
            "Medicamentos": "medicamentos"
        }
        
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # Upper form
        form_layout = QFormLayout()
        
        self.fecha_input = QDateEdit()
        self.fecha_input.setCalendarPopup(True)
        self.fecha_input.setDisplayFormat("yyyy-MM-dd")
        self.fecha_input.setDate(QDate.currentDate())
        
        self.proveedor_input = QLineEdit()
        self.descripcion_input = QTextEdit()
        self.descripcion_input.setMinimumHeight(60)

        self.total_input = QDoubleSpinBox()
        self.total_input.setMaximum(999999999.99)
        self.total_input.setDecimals(2)
        self.total_input.valueChanged.connect(self.actualizar_suma)
        font = self.total_input.font()
        font.setBold(True)
        self.total_input.setFont(font)
        
        form_layout.addRow("Fecha:", self.fecha_input)
        form_layout.addRow("Proveedor:", self.proveedor_input)
        form_layout.addRow("Descripción:", self.descripcion_input)
        form_layout.addRow("TOTAL DEL PAGO:", self.total_input)
        
        main_layout.addLayout(form_layout)
        
        # Desglose section
        lbl_desglose = QLabel("<b>Desglose de Categorías</b>")
        lbl_desglose.setStyleSheet("margin-top: 15px; color: #34495e;")
        main_layout.addWidget(lbl_desglose)
        
        add_layout = QHBoxLayout()
        self.combo_categorias = QComboBox()
        self.combo_categorias.addItems(list(self.etiquetas_db.keys()))
        
        self.monto_cat_input = QDoubleSpinBox()
        self.monto_cat_input.setMaximum(999999999.99)
        self.monto_cat_input.setDecimals(2)
        
        btn_add_cat = QPushButton("Agregar")
        btn_add_cat.setProperty("class", "btn-primary")
        btn_add_cat.clicked.connect(self.agregar_categoria)
        
        add_layout.addWidget(QLabel("Categoría:"))
        add_layout.addWidget(self.combo_categorias)
        add_layout.addWidget(QLabel("Monto:"))
        add_layout.addWidget(self.monto_cat_input)
        add_layout.addWidget(btn_add_cat)
        
        main_layout.addLayout(add_layout)
        
        # Table for added categories
        self.table_desglose = QTableWidget()
        self.table_desglose.setColumnCount(3)
        self.table_desglose.setHorizontalHeaderLabels(["Categoría", "Monto", "Acción"])
        self.table_desglose.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_desglose.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_desglose.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_desglose.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_desglose.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_desglose.setMaximumHeight(150)
        
        main_layout.addWidget(self.table_desglose)
        
        # Totals indicator
        self.lbl_sum = QLabel("Suma actual: 0.00")
        self.lbl_sum.setStyleSheet("font-weight: bold; color: #7f8c8d;")
        main_layout.addWidget(self.lbl_sum, alignment=Qt.AlignRight)

        # Botones
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Guardar")
        btn_save.setProperty("class", "btn-success")
        btn_save.clicked.connect(self.save)
        
        self.btn_save_and_add = QPushButton("Guardar y Añadir Otro")
        self.btn_save_and_add.clicked.connect(self.save_and_add)
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(self.btn_save_and_add)
        btn_layout.addWidget(btn_cancel)

        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)
        
        # Load data if edit mode
        if self.data:
            self.btn_save_and_add.hide()
            self.fecha_input.setDate(QDate.fromString(self.data.get("fecha", ""), "yyyy-MM-dd"))
            self.proveedor_input.setText(self.data.get("proveedor", ""))
            self.descripcion_input.setPlainText(self.data.get("descripcion", ""))
            
            # Bloqueamos el input temporalmente
            self.total_input.blockSignals(True)
            self.total_input.setValue(float(self.data.get("total", 0.0)))
            self.total_input.blockSignals(False)
            
            for cat_label, db_col in self.etiquetas_db.items():
                val = float(self.data.get(db_col, 0.0))
                if val > 0:
                    self.insertar_fila_desglose(cat_label, val)
                    
        self.actualizar_suma()

    def agregar_categoria(self):
        cat = self.combo_categorias.currentText()
        monto = self.monto_cat_input.value()
        
        if monto <= 0:
            QMessageBox.warning(self, "Aviso", "El monto debe ser mayor a cero.")
            return
            
        # Check if category already exists
        for row in range(self.table_desglose.rowCount()):
            if self.table_desglose.item(row, 0).text() == cat:
                current_monto = float(self.table_desglose.item(row, 1).text())
                nuevo_monto = current_monto + monto
                self.table_desglose.setItem(row, 1, NumericItem(f"{nuevo_monto:.2f}"))
                self.monto_cat_input.setValue(0.0)
                self.actualizar_suma()
                return
                
        self.insertar_fila_desglose(cat, monto)
        self.monto_cat_input.setValue(0.0)
        self.actualizar_suma()
        
    def insertar_fila_desglose(self, cat, monto):
        row = self.table_desglose.rowCount()
        self.table_desglose.insertRow(row)
        
        self.table_desglose.setItem(row, 0, QTableWidgetItem(cat))
        self.table_desglose.setItem(row, 1, NumericItem(f"{monto:.2f}"))
        
        btn_eliminar = QPushButton("X")
        btn_eliminar.setProperty("class", "btn-danger")
        btn_eliminar.setCursor(Qt.PointingHandCursor)
        btn_eliminar.setFixedSize(25, 25)
        btn_eliminar.clicked.connect(self.eliminar_fila)
        
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(btn_eliminar, alignment=Qt.AlignCenter)
        self.table_desglose.setCellWidget(row, 2, widget)

    def eliminar_fila(self):
        button = self.sender()
        if button:
            widget = button.parent()
            for r in range(self.table_desglose.rowCount()):
                if self.table_desglose.cellWidget(r, 2) == widget:
                    self.table_desglose.removeRow(r)
                    self.actualizar_suma()
                    break

    def actualizar_suma(self):
        suma = 0.0
        for row in range(self.table_desglose.rowCount()):
            suma += float(self.table_desglose.item(row, 1).text())
        
        self.lbl_sum.setText(f"Suma actual: {suma:.2f}")
        total_input = self.total_input.value()
        
        if abs(suma - total_input) > 0.001 and suma > 0:
            self.lbl_sum.setStyleSheet("font-weight: bold; color: #e74c3c;") # Red
        elif abs(suma - total_input) <= 0.001 and suma > 0:
            self.lbl_sum.setStyleSheet("font-weight: bold; color: #2ecc71;") # Green
        else:
            self.lbl_sum.setStyleSheet("font-weight: bold; color: #7f8c8d;") # Gray
            
        return suma

    def guardar_registro(self):
        fecha = self.fecha_input.date().toString("yyyy-MM-dd")
        proveedor = self.proveedor_input.text().strip()
        descripcion = self.descripcion_input.toPlainText().strip()
        total = self.total_input.value()

        if total <= 0:
            QMessageBox.warning(self, "Aviso", "El total del pago debe ser mayor a cero.")
            return False

        # Validate sum
        suma = self.actualizar_suma()
        if abs(suma - total) > 0.001:
            QMessageBox.warning(self, "Error de Validación", f"La suma de las categorías desglosadas ({suma:.2f}) no coincide con el total ingresado ({total:.2f}).")
            return False

        v = {col: 0.0 for col in self.etiquetas_db.values()}
        
        for row in range(self.table_desglose.rowCount()):
            cat_label = self.table_desglose.item(row, 0).text()
            monto = float(self.table_desglose.item(row, 1).text())
            db_col = self.etiquetas_db[cat_label]
            v[db_col] = monto

        if self.data:
            query = """
                UPDATE pagos_efectivo 
                SET fecha=?, proveedor=?, descripcion=?, total=?, 
                    costo_viveres=?, costo_carnes=?, desayunos=?, otros=?, planilla=?, 
                    gastos_propietarios=?, honorarios=?, reparaciones_mantenimiento=?, 
                    atencion_empleados=?, combustible=?, medicamentos=?
                WHERE id=?
            """
            params = (
                fecha, proveedor, descripcion, total,
                v["costo_viveres"], v["costo_carnes"], v["desayunos"], v["otros"], v["planilla"],
                v["gastos_propietarios"], v["honorarios"], v["reparaciones_mantenimiento"],
                v["atencion_empleados"], v["combustible"], v["medicamentos"],
                self.data["id"]
            )
            self.db.cursor.execute(query, params)
        else:
            query = """
                INSERT INTO pagos_efectivo (
                    fecha, proveedor, descripcion, total, 
                    costo_viveres, costo_carnes, desayunos, otros, planilla, 
                    gastos_propietarios, honorarios, reparaciones_mantenimiento, 
                    atencion_empleados, combustible, medicamentos
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                fecha, proveedor, descripcion, total,
                v["costo_viveres"], v["costo_carnes"], v["desayunos"], v["otros"], v["planilla"],
                v["gastos_propietarios"], v["honorarios"], v["reparaciones_mantenimiento"],
                v["atencion_empleados"], v["combustible"], v["medicamentos"]
            )
            self.db.cursor.execute(query, params)
            
        self.db.conn.commit()
        return True

    def save(self):
        if self.guardar_registro():
            self.accept()
            
    def save_and_add(self):
        if self.guardar_registro():
            self.proveedor_input.clear()
            self.descripcion_input.clear()
            self.total_input.setValue(0.0)
            self.table_desglose.setRowCount(0)
            self.actualizar_suma()
            self.proveedor_input.setFocus()


class PagosEfectivoView(QWidget):
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
        title = QLabel("<h2>Pagos en Efectivo</h2>")
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
        lbl_resumen = QLabel("<h3>Resumen Mensual de Pagos en Efectivo</h3>")
        layout.addWidget(lbl_resumen)

        self.table_resumen = QTableWidget()
        self.table_resumen.setColumnCount(2)
        self.table_resumen.setHorizontalHeaderLabels(["Mes/Año", "Total Pagado"])
        self.table_resumen.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_resumen.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_resumen.setMaximumHeight(150)
        layout.addWidget(self.table_resumen)

        lbl_transacciones = QLabel("<h3>Registro de Pagos</h3>")
        layout.addWidget(lbl_transacciones)

        # --- FILTROS ---
        filter_layout = QHBoxLayout()
        config_filtros = [
            (1, "Filtrar Fecha (YYYY-MM-DD)"),
            (2, "Filtrar Proveedor"),
            (3, "Filtrar Descripción"),
        ]

        for col_idx, placeholder in config_filtros:
            inp = QLineEdit()
            inp.setPlaceholderText(placeholder)
            inp.setClearButtonEnabled(True)
            inp.textChanged.connect(self.aplicar_filtros)
            self.filtros[col_idx] = inp
            filter_layout.addWidget(inp)

        layout.addLayout(filter_layout)

        # --- TABLA ---
        self.table = QTableWidget()
        
        self.columnas = [
            "ID", "FECHA", "PROVEEDOR", "DESCRIPCION", "TOTAL", "DESGLOSE"
        ]
        self.db_columns = [
            "id", "fecha", "proveedor", "descripcion", "total",
            "costo_viveres", "costo_carnes", "desayunos", "otros", "planilla",
            "gastos_propietarios", "honorarios", "reparaciones_mantenimiento",
            "atencion_empleados", "combustible", "medicamentos"
        ]
        
        self.table.setColumnCount(len(self.columnas))
        self.table.setHorizontalHeaderLabels(self.columnas)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.table.setColumnWidth(1, 90)  # Fecha
        self.table.setColumnWidth(2, 120) # Proveedor
        self.table.setColumnWidth(3, 180) # Descripcion
        self.table.setColumnWidth(4, 80)  # Total
        header.setSectionResizeMode(5, QHeaderView.Stretch) # Desglose
            
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
        self.db.cursor.execute(f"SELECT {cols_query} FROM pagos_efectivo ORDER BY fecha DESC, id DESC")
        rows = self.db.cursor.fetchall()
        self.table.setRowCount(0)
        
        # Mapeo de índices a nombres de columnas para el desglose (índices 5 al 15)
        nombres_categorias = [
            "Víveres", "Carnes", "Desayunos", "Otros", "Planilla",
            "Propietarios", "Honorarios", "Mantenimiento",
            "Empleados", "Combustible", "Medicamentos"
        ]

        for r_idx, row in enumerate(rows):
            self.table.insertRow(r_idx)
            
            # Texto (ID, Fecha, Proveedor, Descripcion)
            for c_idx in range(4):
                self.table.setItem(r_idx, c_idx, QTableWidgetItem(str(row[c_idx] or "")))
                
            # TOTAL
            total_val = float(row[4] or 0.0)
            item_total = NumericItem(f"{total_val:.2f}")
            font = item_total.font()
            font.setBold(True)
            item_total.setFont(font)
            self.table.setItem(r_idx, 4, item_total)
            
            # DESGLOSE
            desglose_partes = []
            for i in range(5, len(row)):
                val = float(row[i] or 0.0)
                if val > 0:
                    nombre = nombres_categorias[i-5]
                    desglose_partes.append(f"{nombre}: {val:.2f}")
            
            texto_desglose = " | ".join(desglose_partes)
            item_desglose = QTableWidgetItem(texto_desglose)
            if not texto_desglose:
                item_desglose.setForeground(Qt.gray)
                item_desglose.setText("Sin desglose")
                
            self.table.setItem(r_idx, 5, item_desglose)

        self.table.setSortingEnabled(True)
        self.aplicar_filtros()

    def cargar_resumen(self):
        self.db.cursor.execute("""
            SELECT 
                strftime('%Y-%m', fecha) as mes_anio,
                SUM(total) as total_pagos
            FROM pagos_efectivo
            GROUP BY mes_anio
            ORDER BY mes_anio DESC
        """)
        
        rows = self.db.cursor.fetchall()
        self.table_resumen.setRowCount(0)
        
        for r_idx, row in enumerate(rows):
            self.table_resumen.insertRow(r_idx)
            
            mes_anio = row[0]
            pagos = float(row[1] or 0.0)
            
            self.table_resumen.setItem(r_idx, 0, QTableWidgetItem(mes_anio))
            
            item_pagos = NumericItem(f"{pagos:.2f}")
            item_pagos.setForeground(QColor("red"))
            self.table_resumen.setItem(r_idx, 1, item_pagos)

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
        dlg = PagoEfectivoDialog(self.db, parent=self)
        if dlg.exec_():
            self.cargar_datos()

    def abrir_editar(self):
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(self, "Aviso", "Seleccione un registro para editar.")

        # Obtener ID para consulta a BD
        id_registro = self.table.item(row, 0).text()
        
        cols_query = ", ".join(self.db_columns)
        self.db.cursor.execute(f"SELECT {cols_query} FROM pagos_efectivo WHERE id=?", (id_registro,))
        row_data = self.db.cursor.fetchone()
        
        if row_data:
            data = dict(zip(self.db_columns, row_data))
            dlg = PagoEfectivoDialog(self.db, data=data, parent=self)
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
            self.db.cursor.execute("DELETE FROM pagos_efectivo WHERE id=?", (id_registro,))
            self.db.conn.commit()
            self.cargar_datos()

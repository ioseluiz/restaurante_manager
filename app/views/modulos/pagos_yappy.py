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
    QComboBox
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

class YappyDialog(QDialog):
    def __init__(self, db_manager, data=None, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.data = data
        self.setWindowTitle("Registro de Cuenta Yappy")
        self.setMinimumWidth(350)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        self.nombre_input = QLineEdit()
        self.nombre_input.setPlaceholderText("Ej: Negocio Principal")
        
        self.numero_input = QLineEdit()
        self.numero_input.setPlaceholderText("Ej: 6000-0000")

        form.addRow("Nombre:", self.nombre_input)
        form.addRow("Número / Celular:", self.numero_input)

        if self.data:
            self.nombre_input.setText(self.data.get("nombre", ""))
            self.numero_input.setText(self.data.get("numero", ""))

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Guardar")
        btn_save.setProperty("class", "btn-success")
        btn_save.clicked.connect(self.save)
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def save(self):
        nombre = self.nombre_input.text().strip()
        numero = self.numero_input.text().strip()

        if not nombre or not numero:
            QMessageBox.warning(self, "Aviso", "Nombre y Número son requeridos.")
            return

        if self.data:
            query = "UPDATE yappy_cuentas SET nombre=?, numero=? WHERE id=?"
            self.db.cursor.execute(query, (nombre, numero, self.data["id"]))
        else:
            query = "INSERT INTO yappy_cuentas (nombre, numero) VALUES (?, ?)"
            self.db.cursor.execute(query, (nombre, numero))
            
        self.db.conn.commit()
        self.accept()


class GestionYappyDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle("Gestión de Cuentas Yappy")
        self.resize(500, 300)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        lbl_info = QLabel("Administre aquí las cuentas de Yappy disponibles.")
        layout.addWidget(lbl_info)

        btn_layout = QHBoxLayout()
        btn_add = QPushButton("+ Nueva Cuenta Yappy")
        btn_add.setProperty("class", "btn-success")
        btn_add.clicked.connect(self.abrir_crear_yappy)
        
        btn_edit = QPushButton("Editar")
        btn_edit.clicked.connect(self.abrir_editar_yappy)
        
        btn_del = QPushButton("Eliminar")
        btn_del.setProperty("class", "btn-danger")
        btn_del.clicked.connect(self.eliminar_yappy)
        
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_del)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.table_yappy = QTableWidget()
        self.table_yappy.setColumnCount(3)
        self.table_yappy.setHorizontalHeaderLabels(["ID", "Nombre", "Número"])
        self.table_yappy.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_yappy.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_yappy.setSelectionMode(QTableWidget.SingleSelection)
        self.table_yappy.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_yappy.hideColumn(0)
        layout.addWidget(self.table_yappy)

        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignRight)

        self.setLayout(layout)
        self.cargar_yappys()

    def cargar_yappys(self):
        self.db.cursor.execute("SELECT id, nombre, numero FROM yappy_cuentas ORDER BY id DESC")
        rows = self.db.cursor.fetchall()
        self.table_yappy.setRowCount(0)
        
        for r_idx, row in enumerate(rows):
            self.table_yappy.insertRow(r_idx)
            self.table_yappy.setItem(r_idx, 0, QTableWidgetItem(str(row[0])))
            self.table_yappy.setItem(r_idx, 1, QTableWidgetItem(row[1]))
            self.table_yappy.setItem(r_idx, 2, QTableWidgetItem(row[2]))

    def abrir_crear_yappy(self):
        dlg = YappyDialog(self.db, parent=self)
        if dlg.exec_():
            self.cargar_yappys()

    def abrir_editar_yappy(self):
        row = self.table_yappy.currentRow()
        if row < 0:
            return QMessageBox.warning(self, "Aviso", "Seleccione una cuenta Yappy para editar.")

        yappy_id = self.table_yappy.item(row, 0).text()
        
        self.db.cursor.execute("SELECT id, nombre, numero FROM yappy_cuentas WHERE id=?", (yappy_id,))
        row_data = self.db.cursor.fetchone()
        
        if row_data:
            data = {"id": row_data[0], "nombre": row_data[1], "numero": row_data[2]}
            dlg = YappyDialog(self.db, data=data, parent=self)
            if dlg.exec_():
                self.cargar_yappys()

    def eliminar_yappy(self):
        row = self.table_yappy.currentRow()
        if row < 0:
            return QMessageBox.warning(self, "Aviso", "Seleccione una cuenta Yappy para eliminar.")

        yappy_id = self.table_yappy.item(row, 0).text()
        reply = QMessageBox.question(self, 'Confirmar', '¿Eliminar cuenta Yappy y todas sus transacciones?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.db.cursor.execute("DELETE FROM yappy_cuentas WHERE id=?", (yappy_id,))
            self.db.conn.commit()
            self.cargar_yappys()


class TransaccionYappyDialog(QDialog):
    def __init__(self, db_manager, yappy_id, data=None, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.yappy_id = yappy_id
        self.data = data
        self.setWindowTitle("Transacción Yappy")
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        self.fecha_input = QDateEdit()
        self.fecha_input.setCalendarPopup(True)
        self.fecha_input.setDisplayFormat("yyyy-MM-dd")
        self.fecha_input.setDate(QDate.currentDate())
        
        self.proveedor_input = QLineEdit()
        self.descripcion_input = QTextEdit()
        self.descripcion_input.setMinimumHeight(60)
        
        self.monto_input = QDoubleSpinBox()
        self.monto_input.setMaximum(999999999.99)
        self.monto_input.setDecimals(2)

        form.addRow("Fecha:", self.fecha_input)
        form.addRow("Proveedor/Comercio:", self.proveedor_input)
        form.addRow("Descripción:", self.descripcion_input)
        form.addRow("Monto:", self.monto_input)

        if self.data:
            self.fecha_input.setDate(QDate.fromString(self.data.get("fecha", ""), "yyyy-MM-dd"))
            self.proveedor_input.setText(self.data.get("proveedor", ""))
            self.descripcion_input.setPlainText(self.data.get("descripcion", ""))
            self.monto_input.setValue(float(self.data.get("monto", 0.0)))

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
        proveedor = self.proveedor_input.text().strip()
        descripcion = self.descripcion_input.toPlainText().strip()
        monto = self.monto_input.value()

        if monto <= 0:
            QMessageBox.warning(self, "Aviso", "El monto debe ser mayor a cero.")
            return False

        if self.data:
            query = """
                UPDATE transacciones_yappy 
                SET fecha=?, proveedor=?, descripcion=?, monto=?
                WHERE id=?
            """
            self.db.cursor.execute(query, (fecha, proveedor, descripcion, monto, self.data["id"]))
        else:
            query = """
                INSERT INTO transacciones_yappy (yappy_id, fecha, proveedor, descripcion, monto)
                VALUES (?, ?, ?, ?, ?)
            """
            self.db.cursor.execute(query, (self.yappy_id, fecha, proveedor, descripcion, monto))
            
        self.db.conn.commit()
        return True

    def save(self):
        if self.guardar_registro():
            self.accept()

    def save_and_add(self):
        if self.guardar_registro():
            self.proveedor_input.clear()
            self.descripcion_input.clear()
            self.monto_input.setValue(0.0)
            self.proveedor_input.setFocus()


class PagosYappyView(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.yappy_seleccionado_id = None
        self.filtros = {}
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # --- HEADER / SELECTOR DE YAPPY ---
        header_layout = QHBoxLayout()
        
        lbl_selector = QLabel("<b>Cuenta Yappy Seleccionada:</b>")
        lbl_selector.setStyleSheet("font-size: 14px;")
        header_layout.addWidget(lbl_selector)
        
        self.combo_yappy = QComboBox()
        self.combo_yappy.setMinimumWidth(300)
        self.combo_yappy.setStyleSheet("padding: 5px; font-size: 14px;")
        self.combo_yappy.currentIndexChanged.connect(self.on_yappy_changed)
        header_layout.addWidget(self.combo_yappy)
        
        header_layout.addStretch()
        
        btn_gestionar = QPushButton("📱 Gestionar Cuentas Yappy")
        btn_gestionar.setCursor(Qt.PointingHandCursor)
        btn_gestionar.setStyleSheet("padding: 8px 15px; font-weight: bold;")
        btn_gestionar.clicked.connect(self.abrir_gestion_yappys)
        header_layout.addWidget(btn_gestionar)

        main_layout.addLayout(header_layout)

        # --- CONTENEDOR PRINCIPAL ---
        self.container_widget = QWidget()
        container_layout = QVBoxLayout(self.container_widget)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(20)

        # --- PANEL SUPERIOR: BALANCE MENSUAL ---
        lbl_resumen = QLabel("<h3>Resumen Mensual de Pagos</h3>")
        container_layout.addWidget(lbl_resumen)
        
        self.table_resumen = QTableWidget()
        self.table_resumen.setColumnCount(2)
        self.table_resumen.setHorizontalHeaderLabels(["Mes/Año", "Total Pagado"])
        self.table_resumen.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_resumen.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_resumen.setMaximumHeight(200)
        container_layout.addWidget(self.table_resumen)

        # --- PANEL INFERIOR: TRANSACCIONES ---
        trans_header = QHBoxLayout()
        lbl_transacciones = QLabel("<h3>Transacciones Yappy</h3>")
        trans_header.addWidget(lbl_transacciones)
        
        btn_add_trans = QPushButton("+ Nueva Transacción")
        btn_add_trans.setProperty("class", "btn-success")
        btn_add_trans.clicked.connect(self.abrir_crear_transaccion)
        
        btn_edit_trans = QPushButton("Editar")
        btn_edit_trans.clicked.connect(self.abrir_editar_transaccion)
        
        btn_del_trans = QPushButton("Eliminar")
        btn_del_trans.setProperty("class", "btn-danger")
        btn_del_trans.clicked.connect(self.eliminar_transaccion)
        
        trans_header.addStretch()
        trans_header.addWidget(btn_add_trans)
        trans_header.addWidget(btn_edit_trans)
        trans_header.addWidget(btn_del_trans)
        
        container_layout.addLayout(trans_header)

        # Filtros
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
        container_layout.addLayout(filter_layout)

        self.table_transacciones = QTableWidget()
        self.table_transacciones.setColumnCount(5)
        self.table_transacciones.setHorizontalHeaderLabels(["ID", "Fecha", "Proveedor", "Descripción", "Monto"])
        self.table_transacciones.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_transacciones.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_transacciones.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_transacciones.hideColumn(0)
        self.table_transacciones.setSortingEnabled(True)
        container_layout.addWidget(self.table_transacciones)

        main_layout.addWidget(self.container_widget)
        self.setLayout(main_layout)
        
        self.container_widget.setEnabled(False)

    def cargar_datos(self):
        self.actualizar_combo_yappy()

    def actualizar_combo_yappy(self):
        current_id = self.combo_yappy.currentData()
        
        self.db.cursor.execute("SELECT id, nombre, numero FROM yappy_cuentas ORDER BY id DESC")
        rows = self.db.cursor.fetchall()
        
        self.combo_yappy.blockSignals(True)
        self.combo_yappy.clear()
        
        if not rows:
            self.combo_yappy.addItem("No hay cuentas Yappy registradas", None)
            self.container_widget.setEnabled(False)
            self.yappy_seleccionado_id = None
        else:
            index_to_select = 0
            for i, row in enumerate(rows):
                t_id = row[0]
                nombre = row[1]
                numero = row[2]
                display_text = f"{nombre} ({numero})"
                
                self.combo_yappy.addItem(display_text, t_id)
                
                if current_id == t_id:
                    index_to_select = i
            
            self.combo_yappy.setCurrentIndex(index_to_select)
            self.yappy_seleccionado_id = self.combo_yappy.currentData()
            self.container_widget.setEnabled(True)
            self.cargar_resumen()
            self.cargar_transacciones()
            
        self.combo_yappy.blockSignals(False)

    def on_yappy_changed(self):
        yappy_id = self.combo_yappy.currentData()
        if yappy_id is not None:
            self.yappy_seleccionado_id = yappy_id
            self.container_widget.setEnabled(True)
            self.cargar_resumen()
            self.cargar_transacciones()
        else:
            self.yappy_seleccionado_id = None
            self.container_widget.setEnabled(False)
            self.table_transacciones.setRowCount(0)
            self.table_resumen.setRowCount(0)

    def abrir_gestion_yappys(self):
        dlg = GestionYappyDialog(self.db, parent=self)
        dlg.exec_()
        self.actualizar_combo_yappy()

    def cargar_transacciones(self):
        if not self.yappy_seleccionado_id:
            return
            
        self.table_transacciones.setSortingEnabled(False)
        self.db.cursor.execute("""
            SELECT id, fecha, proveedor, descripcion, monto 
            FROM transacciones_yappy 
            WHERE yappy_id = ? 
            ORDER BY fecha DESC, id DESC
        """, (self.yappy_seleccionado_id,))
        rows = self.db.cursor.fetchall()
        self.table_transacciones.setRowCount(0)

        for r_idx, row in enumerate(rows):
            self.table_transacciones.insertRow(r_idx)
            
            self.table_transacciones.setItem(r_idx, 0, QTableWidgetItem(str(row[0])))
            self.table_transacciones.setItem(r_idx, 1, QTableWidgetItem(str(row[1])))
            self.table_transacciones.setItem(r_idx, 2, QTableWidgetItem(str(row[2] or "")))
            self.table_transacciones.setItem(r_idx, 3, QTableWidgetItem(str(row[3] or "")))
            
            item_monto = NumericItem(f"{float(row[4]):.2f}")
            self.table_transacciones.setItem(r_idx, 4, item_monto)
                    
        self.table_transacciones.setSortingEnabled(True)
        self.aplicar_filtros()

    def aplicar_filtros(self):
        rows = self.table_transacciones.rowCount()
        for row in range(rows):
            mostrar = True
            for col, inp in self.filtros.items():
                texto_filtro = inp.text().lower().strip()
                if not texto_filtro:
                    continue
                item = self.table_transacciones.item(row, col)
                if item:
                    if texto_filtro not in item.text().lower():
                        mostrar = False
                        break
            self.table_transacciones.setRowHidden(row, not mostrar)

    def cargar_resumen(self):
        if not self.yappy_seleccionado_id:
            return
            
        self.db.cursor.execute("""
            SELECT 
                strftime('%Y-%m', fecha) as mes_anio,
                SUM(monto) as total_pagos
            FROM transacciones_yappy
            WHERE yappy_id = ?
            GROUP BY mes_anio
            ORDER BY mes_anio DESC
        """, (self.yappy_seleccionado_id,))
        
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

    # --- TRANSACCIONES CRUD ---
    def abrir_crear_transaccion(self):
        if not self.yappy_seleccionado_id:
            return
        dlg = TransaccionYappyDialog(self.db, self.yappy_seleccionado_id, parent=self)
        if dlg.exec_():
            self.cargar_transacciones()
            self.cargar_resumen()

    def abrir_editar_transaccion(self):
        if not self.yappy_seleccionado_id:
            return
            
        row = self.table_transacciones.currentRow()
        if row < 0:
            return QMessageBox.warning(self, "Aviso", "Seleccione una transacción para editar.")

        data = {
            "id": self.table_transacciones.item(row, 0).text(),
            "fecha": self.table_transacciones.item(row, 1).text(),
            "proveedor": self.table_transacciones.item(row, 2).text(),
            "descripcion": self.table_transacciones.item(row, 3).text(),
            "monto": self.table_transacciones.item(row, 4).text(),
        }

        dlg = TransaccionYappyDialog(self.db, self.yappy_seleccionado_id, data=data, parent=self)
        if dlg.exec_():
            self.cargar_transacciones()
            self.cargar_resumen()

    def eliminar_transaccion(self):
        row = self.table_transacciones.currentRow()
        if row < 0:
            return QMessageBox.warning(self, "Aviso", "Seleccione una transacción para eliminar.")

        trans_id = self.table_transacciones.item(row, 0).text()
        reply = QMessageBox.question(self, 'Confirmar', '¿Eliminar esta transacción?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.db.cursor.execute("DELETE FROM transacciones_yappy WHERE id=?", (trans_id,))
            self.db.conn.commit()
            self.cargar_transacciones()
            self.cargar_resumen()
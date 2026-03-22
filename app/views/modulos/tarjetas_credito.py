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
    QComboBox,
    QSplitter
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

class TarjetaDialog(QDialog):
    def __init__(self, db_manager, data=None, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.data = data
        self.setWindowTitle("Registro de Tarjeta de Crédito")
        self.setMinimumWidth(350)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        self.numero_input = QLineEdit()
        self.numero_input.setPlaceholderText("Ej: 1234567890123456")
        
        self.tipo_input = QComboBox()
        self.tipo_input.addItems(["Visa", "MasterCard", "American Express", "Diners Club", "Otra"])
        
        self.banco_input = QLineEdit()

        form.addRow("Número:", self.numero_input)
        form.addRow("Tipo:", self.tipo_input)
        form.addRow("Banco:", self.banco_input)

        if self.data:
            self.numero_input.setText(self.data.get("numero", ""))
            tipo = self.data.get("tipo", "")
            idx = self.tipo_input.findText(tipo)
            if idx >= 0:
                self.tipo_input.setCurrentIndex(idx)
            else:
                self.tipo_input.setEditText(tipo)
            self.banco_input.setText(self.data.get("banco", ""))

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
        numero = self.numero_input.text().strip()
        tipo = self.tipo_input.currentText()
        banco = self.banco_input.text().strip()

        if not numero or not banco:
            QMessageBox.warning(self, "Aviso", "Número y Banco son requeridos.")
            return

        if self.data:
            query = "UPDATE tarjetas_credito SET numero=?, tipo=?, banco=? WHERE id=?"
            self.db.cursor.execute(query, (numero, tipo, banco, self.data["id"]))
        else:
            query = "INSERT INTO tarjetas_credito (numero, tipo, banco) VALUES (?, ?, ?)"
            self.db.cursor.execute(query, (numero, tipo, banco))
            
        self.db.conn.commit()
        self.accept()


class GestionTarjetasDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle("Gestión de Tarjetas de Crédito")
        self.resize(600, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        lbl_info = QLabel("Administre aquí las tarjetas de crédito disponibles.")
        layout.addWidget(lbl_info)

        btn_layout = QHBoxLayout()
        btn_add = QPushButton("+ Nueva Tarjeta")
        btn_add.setProperty("class", "btn-success")
        btn_add.clicked.connect(self.abrir_crear_tarjeta)
        
        btn_edit = QPushButton("Editar")
        btn_edit.clicked.connect(self.abrir_editar_tarjeta)
        
        btn_del = QPushButton("Eliminar")
        btn_del.setProperty("class", "btn-danger")
        btn_del.clicked.connect(self.eliminar_tarjeta)
        
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_del)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.table_tarjetas = QTableWidget()
        self.table_tarjetas.setColumnCount(4)
        self.table_tarjetas.setHorizontalHeaderLabels(["ID", "Banco", "Tipo", "Número"])
        self.table_tarjetas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_tarjetas.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_tarjetas.setSelectionMode(QTableWidget.SingleSelection)
        self.table_tarjetas.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_tarjetas.hideColumn(0)
        layout.addWidget(self.table_tarjetas)

        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignRight)

        self.setLayout(layout)
        self.cargar_tarjetas()

    def cargar_tarjetas(self):
        self.db.cursor.execute("SELECT id, banco, tipo, numero FROM tarjetas_credito ORDER BY id DESC")
        rows = self.db.cursor.fetchall()
        self.table_tarjetas.setRowCount(0)
        
        for r_idx, row in enumerate(rows):
            self.table_tarjetas.insertRow(r_idx)
            self.table_tarjetas.setItem(r_idx, 0, QTableWidgetItem(str(row[0])))
            self.table_tarjetas.setItem(r_idx, 1, QTableWidgetItem(row[1]))
            self.table_tarjetas.setItem(r_idx, 2, QTableWidgetItem(row[2]))
            
            num = row[3]
            if len(num) >= 4:
                masked = f"**** **** **** {num[-4:]}"
            else:
                masked = f"**** {num}"
            self.table_tarjetas.setItem(r_idx, 3, QTableWidgetItem(masked))

    def abrir_crear_tarjeta(self):
        dlg = TarjetaDialog(self.db, parent=self)
        if dlg.exec_():
            self.cargar_tarjetas()

    def abrir_editar_tarjeta(self):
        row = self.table_tarjetas.currentRow()
        if row < 0:
            return QMessageBox.warning(self, "Aviso", "Seleccione una tarjeta para editar.")

        tarjeta_id = self.table_tarjetas.item(row, 0).text()
        
        self.db.cursor.execute("SELECT id, numero, tipo, banco FROM tarjetas_credito WHERE id=?", (tarjeta_id,))
        row_data = self.db.cursor.fetchone()
        
        if row_data:
            data = {"id": row_data[0], "numero": row_data[1], "tipo": row_data[2], "banco": row_data[3]}
            dlg = TarjetaDialog(self.db, data=data, parent=self)
            if dlg.exec_():
                self.cargar_tarjetas()

    def eliminar_tarjeta(self):
        row = self.table_tarjetas.currentRow()
        if row < 0:
            return QMessageBox.warning(self, "Aviso", "Seleccione una tarjeta para eliminar.")

        tarjeta_id = self.table_tarjetas.item(row, 0).text()
        reply = QMessageBox.question(self, 'Confirmar', '¿Eliminar tarjeta y todas sus transacciones?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.db.cursor.execute("DELETE FROM tarjetas_credito WHERE id=?", (tarjeta_id,))
            self.db.conn.commit()
            self.cargar_tarjetas()


class TransaccionDialog(QDialog):
    def __init__(self, db_manager, tarjeta_id, data=None, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.tarjeta_id = tarjeta_id
        self.data = data
        self.setWindowTitle("Transacción de Tarjeta")
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        self.fecha_input = QDateEdit()
        self.fecha_input.setCalendarPopup(True)
        self.fecha_input.setDisplayFormat("yyyy-MM-dd")
        self.fecha_input.setDate(QDate.currentDate())
        
        self.tipo_input = QComboBox()
        self.tipo_input.addItems(["COMPRA", "PAGO"])
        self.tipo_input.currentTextChanged.connect(self.toggle_comercio)
        
        self.comercio_input = QLineEdit()
        self.descripcion_input = QTextEdit()
        self.descripcion_input.setMinimumHeight(60)
        
        self.monto_input = QDoubleSpinBox()
        self.monto_input.setMaximum(999999999.99)
        self.monto_input.setDecimals(2)

        form.addRow("Fecha:", self.fecha_input)
        form.addRow("Tipo:", self.tipo_input)
        form.addRow("Comercio:", self.comercio_input)
        form.addRow("Descripción:", self.descripcion_input)
        form.addRow("Monto:", self.monto_input)

        if self.data:
            self.fecha_input.setDate(QDate.fromString(self.data.get("fecha", ""), "yyyy-MM-dd"))
            self.tipo_input.setCurrentText(self.data.get("tipo_transaccion", "COMPRA"))
            self.comercio_input.setText(self.data.get("comercio", ""))
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
        self.toggle_comercio()

    def toggle_comercio(self):
        if self.tipo_input.currentText() == "PAGO":
            self.comercio_input.setEnabled(False)
            self.comercio_input.clear()
        else:
            self.comercio_input.setEnabled(True)

    def guardar_registro(self):
        fecha = self.fecha_input.date().toString("yyyy-MM-dd")
        tipo = self.tipo_input.currentText()
        comercio = self.comercio_input.text().strip()
        descripcion = self.descripcion_input.toPlainText().strip()
        monto = self.monto_input.value()

        if monto <= 0:
            QMessageBox.warning(self, "Aviso", "El monto debe ser mayor a cero.")
            return False

        if self.data:
            query = """
                UPDATE transacciones_tarjeta 
                SET fecha=?, comercio=?, descripcion=?, tipo_transaccion=?, monto=?
                WHERE id=?
            """
            self.db.cursor.execute(query, (fecha, comercio, descripcion, tipo, monto, self.data["id"]))
        else:
            query = """
                INSERT INTO transacciones_tarjeta (tarjeta_id, fecha, comercio, descripcion, tipo_transaccion, monto)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            self.db.cursor.execute(query, (self.tarjeta_id, fecha, comercio, descripcion, tipo, monto))
            
        self.db.conn.commit()
        return True

    def save(self):
        if self.guardar_registro():
            self.accept()

    def save_and_add(self):
        if self.guardar_registro():
            # Limpiar campos para nueva entrada rápida
            self.comercio_input.clear()
            self.descripcion_input.clear()
            self.monto_input.setValue(0.0)
            if self.tipo_input.currentText() == "COMPRA":
                self.comercio_input.setFocus()
            else:
                self.descripcion_input.setFocus()


class TarjetasCreditoView(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.tarjeta_seleccionada_id = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # --- HEADER / SELECTOR DE TARJETA ---
        header_layout = QHBoxLayout()
        
        lbl_selector = QLabel("<b>Tarjeta Seleccionada:</b>")
        lbl_selector.setStyleSheet("font-size: 14px;")
        header_layout.addWidget(lbl_selector)
        
        self.combo_tarjetas = QComboBox()
        self.combo_tarjetas.setMinimumWidth(300)
        self.combo_tarjetas.setStyleSheet("padding: 5px; font-size: 14px;")
        self.combo_tarjetas.currentIndexChanged.connect(self.on_tarjeta_changed)
        header_layout.addWidget(self.combo_tarjetas)
        
        header_layout.addStretch()
        
        btn_gestionar_tarjetas = QPushButton("💳 Gestionar Tarjetas")
        btn_gestionar_tarjetas.setCursor(Qt.PointingHandCursor)
        btn_gestionar_tarjetas.setStyleSheet("padding: 8px 15px; font-weight: bold;")
        btn_gestionar_tarjetas.clicked.connect(self.abrir_gestion_tarjetas)
        header_layout.addWidget(btn_gestionar_tarjetas)

        main_layout.addLayout(header_layout)

        # --- CONTENEDOR PRINCIPAL (Se habilita solo si hay tarjeta seleccionada) ---
        self.container_widget = QWidget()
        container_layout = QVBoxLayout(self.container_widget)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(20)

        # --- PANEL SUPERIOR: BALANCE MENSUAL ---
        lbl_resumen = QLabel("<h3>Balance Mensual (Gastado vs Pagado)</h3>")
        container_layout.addWidget(lbl_resumen)
        
        self.table_resumen = QTableWidget()
        self.table_resumen.setColumnCount(4)
        self.table_resumen.setHorizontalHeaderLabels(["Mes/Año", "Total Compras", "Total Pagos", "Balance"])
        self.table_resumen.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_resumen.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_resumen.setMaximumHeight(200) # Un poco más alto para ver más meses
        container_layout.addWidget(self.table_resumen)

        # --- PANEL INFERIOR: TRANSACCIONES ---
        trans_header = QHBoxLayout()
        lbl_transacciones = QLabel("<h3>Transacciones de la Tarjeta</h3>")
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

        self.table_transacciones = QTableWidget()
        self.table_transacciones.setColumnCount(7)
        self.table_transacciones.setHorizontalHeaderLabels(["ID", "Fecha", "Tipo", "Comercio", "Descripción", "Monto", ""])
        self.table_transacciones.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_transacciones.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_transacciones.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_transacciones.hideColumn(0)
        self.table_transacciones.hideColumn(6) # Para colorear sin ensuciar datos
        self.table_transacciones.setSortingEnabled(True)
        container_layout.addWidget(self.table_transacciones)

        main_layout.addWidget(self.container_widget)
        self.setLayout(main_layout)
        
        self.container_widget.setEnabled(False)

    def cargar_datos(self):
        self.actualizar_combo_tarjetas()

    def actualizar_combo_tarjetas(self):
        # Guardar ID seleccionado actualmente si existe
        current_id = self.combo_tarjetas.currentData()
        
        self.db.cursor.execute("SELECT id, banco, tipo, numero FROM tarjetas_credito ORDER BY id DESC")
        rows = self.db.cursor.fetchall()
        
        self.combo_tarjetas.blockSignals(True)
        self.combo_tarjetas.clear()
        
        if not rows:
            self.combo_tarjetas.addItem("No hay tarjetas registradas", None)
            self.container_widget.setEnabled(False)
            self.tarjeta_seleccionada_id = None
        else:
            index_to_select = 0
            for i, row in enumerate(rows):
                t_id = row[0]
                banco = row[1]
                tipo = row[2]
                num = row[3]
                masked = f"**** {num[-4:]}" if len(num) >= 4 else f"**** {num}"
                display_text = f"{banco} - {tipo} ({masked})"
                
                self.combo_tarjetas.addItem(display_text, t_id)
                
                if current_id == t_id:
                    index_to_select = i
            
            self.combo_tarjetas.setCurrentIndex(index_to_select)
            self.tarjeta_seleccionada_id = self.combo_tarjetas.currentData()
            self.container_widget.setEnabled(True)
            self.cargar_resumen()
            self.cargar_transacciones()
            
        self.combo_tarjetas.blockSignals(False)

    def on_tarjeta_changed(self):
        card_id = self.combo_tarjetas.currentData()
        if card_id is not None:
            self.tarjeta_seleccionada_id = card_id
            self.container_widget.setEnabled(True)
            self.cargar_resumen()
            self.cargar_transacciones()
        else:
            self.tarjeta_seleccionada_id = None
            self.container_widget.setEnabled(False)
            self.table_transacciones.setRowCount(0)
            self.table_resumen.setRowCount(0)

    def abrir_gestion_tarjetas(self):
        dlg = GestionTarjetasDialog(self.db, parent=self)
        dlg.exec_()
        # Al cerrar, recargar el combo
        self.actualizar_combo_tarjetas()

    def cargar_transacciones(self):
        if not self.tarjeta_seleccionada_id:
            return
            
        self.table_transacciones.setSortingEnabled(False)
        self.db.cursor.execute("""
            SELECT id, fecha, tipo_transaccion, comercio, descripcion, monto 
            FROM transacciones_tarjeta 
            WHERE tarjeta_id = ? 
            ORDER BY fecha DESC, id DESC
        """, (self.tarjeta_seleccionada_id,))
        rows = self.db.cursor.fetchall()
        self.table_transacciones.setRowCount(0)

        for r_idx, row in enumerate(rows):
            self.table_transacciones.insertRow(r_idx)
            
            tipo = row[2]
            color = QColor("#fdeaea") if tipo == "COMPRA" else QColor("#eafdef")
            
            self.table_transacciones.setItem(r_idx, 0, QTableWidgetItem(str(row[0])))
            self.table_transacciones.setItem(r_idx, 1, QTableWidgetItem(str(row[1])))
            self.table_transacciones.setItem(r_idx, 2, QTableWidgetItem(tipo))
            self.table_transacciones.setItem(r_idx, 3, QTableWidgetItem(str(row[3] or "")))
            self.table_transacciones.setItem(r_idx, 4, QTableWidgetItem(str(row[4] or "")))
            self.table_transacciones.setItem(r_idx, 5, NumericItem(f"{float(row[5]):.2f}"))
            
            for col in range(6):
                item = self.table_transacciones.item(r_idx, col)
                if item:
                    item.setBackground(color)
                    
        self.table_transacciones.setSortingEnabled(True)

    def cargar_resumen(self):
        if not self.tarjeta_seleccionada_id:
            return
            
        self.db.cursor.execute("""
            SELECT 
                strftime('%Y-%m', fecha) as mes_anio,
                SUM(CASE WHEN tipo_transaccion = 'COMPRA' THEN monto ELSE 0 END) as total_compras,
                SUM(CASE WHEN tipo_transaccion = 'PAGO' THEN monto ELSE 0 END) as total_pagos
            FROM transacciones_tarjeta
            WHERE tarjeta_id = ?
            GROUP BY mes_anio
            ORDER BY mes_anio DESC
        """, (self.tarjeta_seleccionada_id,))
        
        rows = self.db.cursor.fetchall()
        self.table_resumen.setRowCount(0)
        
        for r_idx, row in enumerate(rows):
            self.table_resumen.insertRow(r_idx)
            
            mes_anio = row[0]
            compras = float(row[1] or 0.0)
            pagos = float(row[2] or 0.0)
            balance = compras - pagos
            
            self.table_resumen.setItem(r_idx, 0, QTableWidgetItem(mes_anio))
            self.table_resumen.setItem(r_idx, 1, NumericItem(f"{compras:.2f}"))
            self.table_resumen.setItem(r_idx, 2, NumericItem(f"{pagos:.2f}"))
            
            bal_item = NumericItem(f"{balance:.2f}")
            if balance > 0:
                bal_item.setForeground(QColor("red"))
            elif balance < 0:
                bal_item.setForeground(QColor("green"))
                
            self.table_resumen.setItem(r_idx, 3, bal_item)

    # --- TRANSACCIONES CRUD ---
    def abrir_crear_transaccion(self):
        if not self.tarjeta_seleccionada_id:
            return
        dlg = TransaccionDialog(self.db, self.tarjeta_seleccionada_id, parent=self)
        if dlg.exec_():
            self.cargar_transacciones()
            self.cargar_resumen()

    def abrir_editar_transaccion(self):
        if not self.tarjeta_seleccionada_id:
            return
            
        row = self.table_transacciones.currentRow()
        if row < 0:
            return QMessageBox.warning(self, "Aviso", "Seleccione una transacción para editar.")

        data = {
            "id": self.table_transacciones.item(row, 0).text(),
            "fecha": self.table_transacciones.item(row, 1).text(),
            "tipo_transaccion": self.table_transacciones.item(row, 2).text(),
            "comercio": self.table_transacciones.item(row, 3).text(),
            "descripcion": self.table_transacciones.item(row, 4).text(),
            "monto": self.table_transacciones.item(row, 5).text(),
        }

        dlg = TransaccionDialog(self.db, self.tarjeta_seleccionada_id, data=data, parent=self)
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
            self.db.cursor.execute("DELETE FROM transacciones_tarjeta WHERE id=?", (trans_id,))
            self.db.conn.commit()
            self.cargar_transacciones()
            self.cargar_resumen()

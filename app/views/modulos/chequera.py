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
    QDoubleSpinBox
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


class ChequeraDialog(QDialog):
    def __init__(self, db_manager, data=None, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.data = data
        self.setWindowTitle("Registro en Chequera")
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        self.fecha_input = QDateEdit()
        self.fecha_input.setCalendarPopup(True)
        self.fecha_input.setDisplayFormat("yyyy-MM-dd")
        self.fecha_input.setDate(QDate.currentDate())
        
        self.nock_input = QLineEdit()
        self.nombre_input = QLineEdit()
        self.detalle_input = QLineEdit()
        
        self.deposito_input = QDoubleSpinBox()
        self.deposito_input.setMaximum(999999999.99)
        self.deposito_input.setDecimals(2)
        
        self.monto_input = QDoubleSpinBox()
        self.monto_input.setMaximum(999999999.99)
        self.monto_input.setDecimals(2)

        form.addRow("Fecha:", self.fecha_input)
        form.addRow("No.CK:", self.nock_input)
        form.addRow("Nombre Cheque:", self.nombre_input)
        form.addRow("Detalle:", self.detalle_input)
        form.addRow("Depósito:", self.deposito_input)
        form.addRow("Monto:", self.monto_input)

        if self.data:
            # Edit mode
            self.fecha_input.setDate(QDate.fromString(self.data.get("fecha", ""), "yyyy-MM-dd"))
            self.nock_input.setText(self.data.get("no_ck", ""))
            self.nombre_input.setText(self.data.get("nombre_cheque", ""))
            self.detalle_input.setText(self.data.get("detalle", ""))
            self.deposito_input.setValue(float(self.data.get("deposito", 0.0)))
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
        no_ck = self.nock_input.text().strip()
        nombre = self.nombre_input.text().strip()
        detalle = self.detalle_input.text().strip()
        deposito = self.deposito_input.value()
        monto = self.monto_input.value()

        if self.data:
            query = """
                UPDATE chequera 
                SET fecha=?, no_ck=?, nombre_cheque=?, detalle=?, deposito=?, monto=?
                WHERE id=?
            """
            self.db.cursor.execute(query, (fecha, no_ck, nombre, detalle, deposito, monto, self.data["id"]))
        else:
            query = """
                INSERT INTO chequera (fecha, no_ck, nombre_cheque, detalle, deposito, monto)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            self.db.cursor.execute(query, (fecha, no_ck, nombre, detalle, deposito, monto))
        self.db.conn.commit()
        return True

    def save(self):
        if self.guardar_registro():
            self.accept()
            
    def save_and_add(self):
        if self.guardar_registro():
            # Limpiar campos excepto la fecha para facilitar la entrada múltiple
            self.nock_input.clear()
            self.nombre_input.clear()
            self.detalle_input.clear()
            self.deposito_input.setValue(0.0)
            self.monto_input.setValue(0.0)
            self.nock_input.setFocus()
            # No cerramos el diálogo


class ChequeraCRUD(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.filtros = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # --- HEADER ---
        header_layout = QHBoxLayout()
        title = QLabel("<h2>Módulo de Consolidados: Chequera</h2>")
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
        lbl_resumen = QLabel("<h3>Resumen Mensual de Chequera</h3>")
        layout.addWidget(lbl_resumen)
        
        self.table_resumen = QTableWidget()
        self.table_resumen.setColumnCount(4)
        self.table_resumen.setHorizontalHeaderLabels(["Mes/Año", "Total Depósitos", "Total Retiros", "Balance"])
        self.table_resumen.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_resumen.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_resumen.setMaximumHeight(150)
        layout.addWidget(self.table_resumen)

        lbl_transacciones = QLabel("<h3>Registro de Transacciones</h3>")
        layout.addWidget(lbl_transacciones)

        # --- FILTROS ---
        filter_layout = QHBoxLayout()
        config_filtros = [
            (1, "Filtrar Fecha (YYYY-MM-DD)"),
            (2, "Filtrar No.CK"),
            (3, "Filtrar Nombre"),
            (4, "Filtrar Detalle"),
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
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "FECHA", "No.CK", "NOMBRE CHEQUE", "DETALLE", "DEPOSITO", "MONTO"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.hideColumn(0)  # Ocultar la columna de ID, aunque está disponible para lógica
        layout.addWidget(self.table)

        self.setLayout(layout)

    def cargar_datos(self):
        self.cargar_resumen()
        self.table.setSortingEnabled(False)
        self.db.cursor.execute("SELECT id, fecha, no_ck, nombre_cheque, detalle, deposito, monto FROM chequera ORDER BY fecha DESC, id DESC")
        rows = self.db.cursor.fetchall()
        self.table.setRowCount(0)

        for r_idx, row in enumerate(rows):
            self.table.insertRow(r_idx)
            
            # ID
            self.table.setItem(r_idx, 0, NumericItem(str(row[0])))
            # FECHA
            self.table.setItem(r_idx, 1, QTableWidgetItem(str(row[1] or "")))
            # No.CK
            self.table.setItem(r_idx, 2, QTableWidgetItem(str(row[2] or "")))
            # NOMBRE CHEQUE
            self.table.setItem(r_idx, 3, QTableWidgetItem(str(row[3] or "")))
            # DETALLE
            self.table.setItem(r_idx, 4, QTableWidgetItem(str(row[4] or "")))
            
            # DEPOSITO (Numérico)
            self.table.setItem(r_idx, 5, NumericItem(f"{float(row[5] or 0.0):.2f}"))
            # MONTO (Numérico)
            self.table.setItem(r_idx, 6, NumericItem(f"{float(row[6] or 0.0):.2f}"))

        self.table.setSortingEnabled(True)
        self.aplicar_filtros()

    def cargar_resumen(self):
        self.db.cursor.execute("""
            SELECT 
                strftime('%Y-%m', fecha) as mes_anio,
                SUM(deposito) as total_depositos,
                SUM(monto) as total_retiros
            FROM chequera
            GROUP BY mes_anio
            ORDER BY mes_anio DESC
        """)
        
        rows = self.db.cursor.fetchall()
        self.table_resumen.setRowCount(0)
        
        for r_idx, row in enumerate(rows):
            self.table_resumen.insertRow(r_idx)
            
            mes_anio = row[0]
            depositos = float(row[1] or 0.0)
            retiros = float(row[2] or 0.0)
            balance = depositos - retiros
            
            self.table_resumen.setItem(r_idx, 0, QTableWidgetItem(mes_anio))
            self.table_resumen.setItem(r_idx, 1, NumericItem(f"{depositos:.2f}"))
            self.table_resumen.setItem(r_idx, 2, NumericItem(f"{retiros:.2f}"))
            
            bal_item = NumericItem(f"{balance:.2f}")
            if balance < 0:
                bal_item.setForeground(QColor("red"))
            elif balance > 0:
                bal_item.setForeground(QColor("green"))
                
            self.table_resumen.setItem(r_idx, 3, bal_item)

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
        dlg = ChequeraDialog(self.db, parent=self)
        dlg.exec_()
        self.cargar_datos()

    def abrir_editar(self):
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(self, "Aviso", "Seleccione un registro para editar.")

        data = {
            "id": self.table.item(row, 0).text(),
            "fecha": self.table.item(row, 1).text(),
            "no_ck": self.table.item(row, 2).text(),
            "nombre_cheque": self.table.item(row, 3).text(),
            "detalle": self.table.item(row, 4).text(),
            "deposito": self.table.item(row, 5).text(),
            "monto": self.table.item(row, 6).text(),
        }

        dlg = ChequeraDialog(self.db, data=data, parent=self)
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
            self.db.cursor.execute("DELETE FROM chequera WHERE id=?", (id_registro,))
            self.db.conn.commit()
            self.cargar_datos()

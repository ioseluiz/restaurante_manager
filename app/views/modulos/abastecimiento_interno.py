import sqlite3
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QDialog,
    QFormLayout,
    QHeaderView,
    QMessageBox,
    QDateEdit,
    QComboBox,
    QDoubleSpinBox
)
from PyQt5.QtCore import Qt, QDate

class NumericItem(QTableWidgetItem):
    def __lt__(self, other):
        try:
            return float(self.text()) < float(other.text())
        except ValueError:
            return super().__lt__(other)

class NuevoAbastecimientoDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle("Nuevo Abastecimiento Interno")
        self.resize(800, 600)
        self.detalles = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        form_layout = QHBoxLayout()
        
        # Fecha
        layout_fecha = QVBoxLayout()
        layout_fecha.addWidget(QLabel("Fecha:"))
        self.fecha_input = QDateEdit()
        self.fecha_input.setCalendarPopup(True)
        self.fecha_input.setDisplayFormat("yyyy-MM-dd")
        self.fecha_input.setDate(QDate.currentDate())
        layout_fecha.addWidget(self.fecha_input)
        form_layout.addLayout(layout_fecha)
        
        # Sucursal Origen
        layout_origen = QVBoxLayout()
        layout_origen.addWidget(QLabel("Sucursal Origen:"))
        self.origen_combo = QComboBox()
        layout_origen.addWidget(self.origen_combo)
        form_layout.addLayout(layout_origen)

        # Sucursal Destino
        layout_destino = QVBoxLayout()
        layout_destino.addWidget(QLabel("Sucursal Destino:"))
        self.destino_combo = QComboBox()
        layout_destino.addWidget(self.destino_combo)
        form_layout.addLayout(layout_destino)
        
        layout.addLayout(form_layout)
        
        self.cargar_sucursales()

        # Detalle de insumos
        lbl_detalles = QLabel("<h3>Insumos a Transferir</h3>")
        layout.addWidget(lbl_detalles)

        add_item_layout = QHBoxLayout()
        self.insumo_combo = QComboBox()
        self.insumo_combo.setMinimumWidth(200)
        add_item_layout.addWidget(QLabel("Insumo:"))
        add_item_layout.addWidget(self.insumo_combo)

        self.cantidad_input = QDoubleSpinBox()
        self.cantidad_input.setDecimals(4)
        self.cantidad_input.setMaximum(999999.9999)
        add_item_layout.addWidget(QLabel("Cantidad:"))
        add_item_layout.addWidget(self.cantidad_input)

        btn_add_detalle = QPushButton("Agregar Insumo")
        btn_add_detalle.clicked.connect(self.agregar_detalle)
        add_item_layout.addWidget(btn_add_detalle)
        
        layout.addLayout(add_item_layout)

        self.cargar_insumos()

        self.table_detalles = QTableWidget()
        self.table_detalles.setColumnCount(5)
        self.table_detalles.setHorizontalHeaderLabels(["ID Insumo", "Insumo", "Cantidad", "Unidad", "Acción"])
        self.table_detalles.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_detalles)

        # Botones de guardar
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Guardar Abastecimiento")
        btn_save.setProperty("class", "btn-success")
        btn_save.clicked.connect(self.guardar_abastecimiento)
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def cargar_sucursales(self):
        self.db.cursor.execute("SELECT id, nombre, es_principal FROM sucursales ORDER BY nombre")
        rows = self.db.cursor.fetchall()
        for r in rows:
            nombre = f"{r[1]} (Central)" if r[2] else r[1]
            self.origen_combo.addItem(nombre, r[0])
            self.destino_combo.addItem(nombre, r[0])

    def cargar_insumos(self):
        self.db.cursor.execute("""
            SELECT i.id, i.nombre, u.abreviatura, u.id
            FROM insumos i
            LEFT JOIN unidades_medida u ON i.unidad_base_id = u.id
            ORDER BY i.nombre
        """)
        rows = self.db.cursor.fetchall()
        for r in rows:
            texto = f"{r[1]} ({r[2]})"
            self.insumo_combo.addItem(texto, {"id": r[0], "unidad_str": r[2], "unidad_id": r[3], "nombre": r[1]})

    def agregar_detalle(self):
        if self.insumo_combo.currentIndex() < 0:
            return
            
        data = self.insumo_combo.currentData()
        cantidad = self.cantidad_input.value()
        
        if cantidad <= 0:
            QMessageBox.warning(self, "Aviso", "La cantidad debe ser mayor a 0.")
            return
            
        # Revisar si ya existe
        for i in range(self.table_detalles.rowCount()):
            if self.table_detalles.item(i, 0).text() == str(data["id"]):
                QMessageBox.warning(self, "Aviso", "El insumo ya está en la lista.")
                return

        row = self.table_detalles.rowCount()
        self.table_detalles.insertRow(row)
        
        self.table_detalles.setItem(row, 0, QTableWidgetItem(str(data["id"])))
        self.table_detalles.setItem(row, 1, QTableWidgetItem(data["nombre"]))
        self.table_detalles.setItem(row, 2, QTableWidgetItem(str(cantidad)))
        
        item_unidad = QTableWidgetItem(data["unidad_str"])
        item_unidad.setData(Qt.UserRole, data["unidad_id"])
        self.table_detalles.setItem(row, 3, item_unidad)
        
        btn_eliminar = QPushButton("X")
        btn_eliminar.setStyleSheet("color: red; font-weight: bold;")
        btn_eliminar.clicked.connect(lambda _, r=row: self.table_detalles.removeRow(r))
        self.table_detalles.setCellWidget(row, 4, btn_eliminar)
        
        self.cantidad_input.setValue(0.0)

    def guardar_abastecimiento(self):
        origen_id = self.origen_combo.currentData()
        destino_id = self.destino_combo.currentData()
        fecha = self.fecha_input.date().toString("yyyy-MM-dd")
        
        if origen_id == destino_id:
            QMessageBox.warning(self, "Aviso", "La sucursal de origen y destino no pueden ser la misma.")
            return
            
        if self.table_detalles.rowCount() == 0:
            QMessageBox.warning(self, "Aviso", "Debe agregar al menos un insumo al abastecimiento.")
            return

        try:
            self.db.cursor.execute("BEGIN TRANSACTION")
            
            # Obtener datos de origen y destino para ver si son principales
            self.db.cursor.execute("SELECT es_principal FROM sucursales WHERE id=?", (origen_id,))
            origen_es_principal = bool(self.db.cursor.fetchone()[0])
            
            self.db.cursor.execute("SELECT es_principal FROM sucursales WHERE id=?", (destino_id,))
            destino_es_principal = bool(self.db.cursor.fetchone()[0])

            # Insertar abastecimiento
            self.db.cursor.execute("""
                INSERT INTO abastecimiento_interno (fecha, sucursal_origen_id, sucursal_destino_id)
                VALUES (?, ?, ?)
            """, (fecha, origen_id, destino_id))
            
            abastecimiento_id = self.db.cursor.lastrowid
            
            # Insertar detalles y afectar inventario
            for i in range(self.table_detalles.rowCount()):
                insumo_id = int(self.table_detalles.item(i, 0).text())
                cantidad = float(self.table_detalles.item(i, 2).text())
                unidad_id = int(self.table_detalles.item(i, 3).data(Qt.UserRole))
                
                self.db.cursor.execute("""
                    INSERT INTO detalle_abastecimiento (abastecimiento_id, insumo_id, cantidad, unidad_id)
                    VALUES (?, ?, ?, ?)
                """, (abastecimiento_id, insumo_id, cantidad, unidad_id))
                
                # Afectar inventario global si interviene la sucursal principal
                if origen_es_principal:
                    # Sale de la principal, descontar stock
                    self.db.cursor.execute("UPDATE insumos SET stock_actual = stock_actual - ? WHERE id = ?", (cantidad, insumo_id))
                
                if destino_es_principal:
                    # Entra a la principal, aumentar stock
                    self.db.cursor.execute("UPDATE insumos SET stock_actual = stock_actual + ? WHERE id = ?", (cantidad, insumo_id))
            
            self.db.conn.commit()
            QMessageBox.information(self, "Éxito", "Abastecimiento registrado correctamente.")
            self.accept()
            
        except Exception as e:
            self.db.conn.rollback()
            QMessageBox.critical(self, "Error", f"Error al guardar abastecimiento: {e}")

class TabAbastecimientoInterno(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<h3>Registro de Abastecimiento Interno</h3>"))
        header_layout.addStretch()

        btn_add = QPushButton(" + Nuevo Abastecimiento")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setProperty("class", "btn-success")
        btn_add.clicked.connect(self.abrir_crear)
        header_layout.addWidget(btn_add)
        
        btn_eliminar = QPushButton("Eliminar")
        btn_eliminar.setProperty("class", "btn-danger")
        btn_eliminar.clicked.connect(self.eliminar_abastecimiento)
        header_layout.addWidget(btn_eliminar)

        layout.addLayout(header_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Fecha", "Origen", "Destino", "Estado"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.hideColumn(0)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def cargar_datos(self):
        self.db.cursor.execute("""
            SELECT a.id, a.fecha, s_origen.nombre, s_destino.nombre, a.estado
            FROM abastecimiento_interno a
            JOIN sucursales s_origen ON a.sucursal_origen_id = s_origen.id
            JOIN sucursales s_destino ON a.sucursal_destino_id = s_destino.id
            ORDER BY a.fecha DESC, a.id DESC
        """)
        rows = self.db.cursor.fetchall()
        self.table.setRowCount(0)
        for r_idx, row in enumerate(rows):
            self.table.insertRow(r_idx)
            self.table.setItem(r_idx, 0, QTableWidgetItem(str(row[0])))
            self.table.setItem(r_idx, 1, QTableWidgetItem(row[1]))
            self.table.setItem(r_idx, 2, QTableWidgetItem(row[2]))
            self.table.setItem(r_idx, 3, QTableWidgetItem(row[3]))
            self.table.setItem(r_idx, 4, QTableWidgetItem(row[4]))

    def abrir_crear(self):
        dlg = NuevoAbastecimientoDialog(self.db, parent=self)
        if dlg.exec_():
            self.cargar_datos()
            
    def eliminar_abastecimiento(self):
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(self, "Aviso", "Seleccione un registro para eliminar.")
            
        abastecimiento_id = self.table.item(row, 0).text()
        reply = QMessageBox.question(self, "Confirmar", "¿Eliminar este abastecimiento y revertir inventario?", QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                self.db.cursor.execute("BEGIN TRANSACTION")
                
                # Obtener detalles para revertir inventario
                self.db.cursor.execute("SELECT sucursal_origen_id, sucursal_destino_id FROM abastecimiento_interno WHERE id=?", (abastecimiento_id,))
                origen_id, destino_id = self.db.cursor.fetchone()
                
                self.db.cursor.execute("SELECT es_principal FROM sucursales WHERE id=?", (origen_id,))
                origen_es_principal = bool(self.db.cursor.fetchone()[0])
                
                self.db.cursor.execute("SELECT es_principal FROM sucursales WHERE id=?", (destino_id,))
                destino_es_principal = bool(self.db.cursor.fetchone()[0])
                
                self.db.cursor.execute("SELECT insumo_id, cantidad FROM detalle_abastecimiento WHERE abastecimiento_id=?", (abastecimiento_id,))
                detalles = self.db.cursor.fetchall()
                
                for insumo_id, cantidad in detalles:
                    if origen_es_principal:
                        # Si salió de principal, devolver
                        self.db.cursor.execute("UPDATE insumos SET stock_actual = stock_actual + ? WHERE id = ?", (cantidad, insumo_id))
                    if destino_es_principal:
                        # Si entró a principal, quitar
                        self.db.cursor.execute("UPDATE insumos SET stock_actual = stock_actual - ? WHERE id = ?", (cantidad, insumo_id))
                
                self.db.cursor.execute("DELETE FROM abastecimiento_interno WHERE id=?", (abastecimiento_id,))
                self.db.conn.commit()
                self.cargar_datos()
                QMessageBox.information(self, "Éxito", "Registro eliminado correctamente.")
            except Exception as e:
                self.db.conn.rollback()
                QMessageBox.critical(self, "Error", f"No se pudo eliminar: {e}")

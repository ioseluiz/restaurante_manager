import sqlite3
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
    QCheckBox
)
from PyQt5.QtCore import Qt

class SucursalDialog(QDialog):
    def __init__(self, db_manager, sucursal_id=None, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.sucursal_id = sucursal_id
        self.setWindowTitle(
            "Editar Sucursal" if sucursal_id else "Nueva Sucursal"
        )
        self.setMinimumWidth(350)
        self.init_ui()
        if self.sucursal_id:
            self.cargar_datos()

    def init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        self.nombre_input = QLineEdit()
        self.direccion_input = QLineEdit()
        self.telefono_input = QLineEdit()
        self.es_principal_checkbox = QCheckBox("Es sucursal principal (Central)")

        form.addRow("Nombre:", self.nombre_input)
        form.addRow("Dirección:", self.direccion_input)
        form.addRow("Teléfono:", self.telefono_input)
        form.addRow("", self.es_principal_checkbox)

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

    def cargar_datos(self):
        self.db.cursor.execute(
            "SELECT nombre, direccion, telefono, es_principal FROM sucursales WHERE id=?",
            (self.sucursal_id,),
        )
        row = self.db.cursor.fetchone()
        if row:
            self.nombre_input.setText(row[0])
            self.direccion_input.setText(row[1] or "")
            self.telefono_input.setText(row[2] or "")
            self.es_principal_checkbox.setChecked(bool(row[3]))

    def save(self):
        nombre = self.nombre_input.text().strip()
        direccion = self.direccion_input.text().strip()
        telefono = self.telefono_input.text().strip()
        es_principal = 1 if self.es_principal_checkbox.isChecked() else 0

        if not nombre:
            QMessageBox.warning(self, "Aviso", "El nombre es obligatorio.")
            return

        try:
            if es_principal:
                # Si se marca como principal, desmarcamos a las demás
                self.db.cursor.execute("UPDATE sucursales SET es_principal = 0")
                
            if self.sucursal_id:
                self.db.cursor.execute(
                    "UPDATE sucursales SET nombre=?, direccion=?, telefono=?, es_principal=? WHERE id=?",
                    (nombre, direccion, telefono, es_principal, self.sucursal_id),
                )
            else:
                self.db.cursor.execute(
                    "INSERT INTO sucursales (nombre, direccion, telefono, es_principal) VALUES (?, ?, ?, ?)",
                    (nombre, direccion, telefono, es_principal),
                )
            self.db.conn.commit()
            self.accept()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error BD", str(e))


class SucursalesCRUD(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        header_layout = QHBoxLayout()
        title = QLabel("<h2>Gestión de Sucursales</h2>")
        header_layout.addWidget(title)
        header_layout.addStretch()

        btn_add = QPushButton(" + Nueva Sucursal")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setProperty("class", "btn-success")
        btn_add.clicked.connect(self.abrir_crear)

        btn_edit = QPushButton("Editar")
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

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Dirección", "Teléfono", "Principal"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.hideColumn(0)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def cargar_datos(self):
        self.db.cursor.execute("SELECT id, nombre, direccion, telefono, es_principal FROM sucursales ORDER BY nombre")
        rows = self.db.cursor.fetchall()
        self.table.setRowCount(0)

        for r_idx, row in enumerate(rows):
            self.table.insertRow(r_idx)
            self.table.setItem(r_idx, 0, QTableWidgetItem(str(row[0])))
            self.table.setItem(r_idx, 1, QTableWidgetItem(row[1]))
            self.table.setItem(r_idx, 2, QTableWidgetItem(row[2] or ""))
            self.table.setItem(r_idx, 3, QTableWidgetItem(row[3] or ""))
            
            lbl_principal = "Sí" if row[4] else "No"
            self.table.setItem(r_idx, 4, QTableWidgetItem(lbl_principal))

    def abrir_crear(self):
        dlg = SucursalDialog(self.db, parent=self)
        if dlg.exec_():
            self.cargar_datos()

    def abrir_editar(self):
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(
                self, "Aviso", "Seleccione una sucursal para editar."
            )
        sucursal_id = self.table.item(row, 0).text()
        dlg = SucursalDialog(self.db, sucursal_id, parent=self)
        if dlg.exec_():
            self.cargar_datos()

    def eliminar(self):
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(
                self, "Aviso", "Seleccione una sucursal para eliminar."
            )
            
        sucursal_id = self.table.item(row, 0).text()
        
        # Verificar si tiene abastecimientos asociados
        self.db.cursor.execute("SELECT COUNT(*) FROM abastecimiento_interno WHERE sucursal_origen_id = ? OR sucursal_destino_id = ?", (sucursal_id, sucursal_id))
        if self.db.cursor.fetchone()[0] > 0:
            return QMessageBox.warning(self, "Aviso", "No se puede eliminar la sucursal porque tiene movimientos de abastecimiento asociados.")

        reply = QMessageBox.question(
            self,
            "Confirmar",
            "¿Eliminar esta sucursal permanentemente?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.db.cursor.execute("DELETE FROM sucursales WHERE id=?", (sucursal_id,))
            self.db.conn.commit()
            self.cargar_datos()

import hashlib
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDialog,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QMessageBox,
    QLabel,
)
from PyQt5.QtCore import Qt


class UsuariosWidget(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # Encabezado
        header = QLabel("<h2>Gestión de Usuarios y Accesos</h2>")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Barra de Herramientas
        btn_layout = QHBoxLayout()

        btn_add = QPushButton("Nuevo Usuario")
        btn_add.setStyleSheet(
            "background-color: #2ecc71; color: white; font-weight: bold; padding: 8px;"
        )
        btn_add.clicked.connect(self.abrir_crear)

        btn_edit = QPushButton("Editar Seleccionado")
        btn_edit.clicked.connect(self.abrir_editar)

        btn_del = QPushButton("Eliminar Usuario")
        btn_del.setStyleSheet(
            "background-color: #e74c3c; color: white; font-weight: bold; padding: 8px;"
        )
        btn_del.clicked.connect(self.eliminar)

        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_del)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Tabla de Usuarios
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Usuario", "Rol"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addWidget(self.table)
        self.setLayout(layout)

        self.cargar_datos()

    def cargar_datos(self):
        """Recarga la lista de usuarios desde la base de datos."""
        query = "SELECT id, username, rol FROM usuarios ORDER BY username"
        rows = self.db.fetch_all(query)

        self.table.setRowCount(0)
        for r_idx, row in enumerate(rows):
            self.table.insertRow(r_idx)
            self.table.setItem(r_idx, 0, QTableWidgetItem(str(row[0])))
            self.table.setItem(r_idx, 1, QTableWidgetItem(str(row[1])))
            self.table.setItem(r_idx, 2, QTableWidgetItem(str(row[2])))

    def abrir_crear(self):
        dlg = UsuarioDialog(self.db, parent=self)
        if dlg.exec_():
            self.cargar_datos()

    def abrir_editar(self):
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(
                self, "Aviso", "Seleccione un usuario para editar."
            )

        id_user = int(self.table.item(row, 0).text())
        dlg = UsuarioDialog(self.db, user_id=id_user, parent=self)
        if dlg.exec_():
            self.cargar_datos()

    def eliminar(self):
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(
                self, "Aviso", "Seleccione un usuario para eliminar."
            )

        id_user = self.table.item(row, 0).text()
        nombre = self.table.item(row, 1).text()

        if nombre == "admin":
            return QMessageBox.critical(
                self,
                "Error",
                "No se puede eliminar al administrador principal por defecto.",
            )

        confirm = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Está seguro de eliminar al usuario '{nombre}'?\nEsta acción es irreversible.",
            QMessageBox.Yes | QMessageBox.No,
        )

        if confirm == QMessageBox.Yes:
            try:
                self.db.execute_query("DELETE FROM usuarios WHERE id=?", (id_user,))
                self.cargar_datos()
                QMessageBox.information(
                    self, "Éxito", "Usuario eliminado correctamente."
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"No se pudo eliminar el usuario: {e}"
                )


class UsuarioDialog(QDialog):
    def __init__(self, db, user_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.user_id = user_id
        self.setWindowTitle("Detalle de Usuario")
        self.setFixedSize(350, 250)

        layout = QFormLayout()

        self.txt_user = QLineEdit()
        self.txt_pass = QLineEdit()
        self.txt_pass.setEchoMode(QLineEdit.Password)
        self.txt_pass.setPlaceholderText(
            "Dejar vacío para mantener actual" if user_id else "Requerido"
        )

        self.cmb_rol = QComboBox()
        self.cmb_rol.addItems(["empleado", "admin", "gerente"])

        layout.addRow("Usuario:", self.txt_user)
        layout.addRow("Contraseña:", self.txt_pass)
        layout.addRow("Rol:", self.cmb_rol)

        btn_save = QPushButton("Guardar Usuario")
        btn_save.setStyleSheet(
            "background-color: #3498db; color: white; font-weight: bold; padding: 10px;"
        )
        btn_save.clicked.connect(self.guardar)

        layout.addRow(btn_save)
        self.setLayout(layout)

        if self.user_id:
            self.cargar_datos()

    def cargar_datos(self):
        row = self.db.fetch_all(
            "SELECT username, rol FROM usuarios WHERE id=?", (self.user_id,)
        )
        if row:
            self.txt_user.setText(row[0][0])
            # Si es el admin por defecto, no permitir cambiar nombre ni rol para evitar bloqueos
            if row[0][0] == "admin":
                self.txt_user.setReadOnly(True)
                self.cmb_rol.setEnabled(False)

            index = self.cmb_rol.findText(row[0][1])
            if index >= 0:
                self.cmb_rol.setCurrentIndex(index)

    def guardar(self):
        user = self.txt_user.text().strip()
        pwd = self.txt_pass.text()
        rol = self.cmb_rol.currentText()

        if not user:
            return QMessageBox.warning(
                self, "Error", "El nombre de usuario es obligatorio."
            )

        try:
            # Modo Edición
            if self.user_id:
                if pwd:  # Si escribió contraseña, actualizamos todo
                    pwd_hash = hashlib.sha256(pwd.encode()).hexdigest()
                    self.db.execute_query(
                        "UPDATE usuarios SET username=?, password_hash=?, rol=? WHERE id=?",
                        (user, pwd_hash, rol, self.user_id),
                    )
                else:  # Si no, solo actualizamos info
                    self.db.execute_query(
                        "UPDATE usuarios SET username=?, rol=? WHERE id=?",
                        (user, rol, self.user_id),
                    )
            # Modo Creación
            else:
                if not pwd:
                    return QMessageBox.warning(
                        self,
                        "Error",
                        "La contraseña es obligatoria para nuevos usuarios.",
                    )

                pwd_hash = hashlib.sha256(pwd.encode()).hexdigest()
                self.db.execute_query(
                    "INSERT INTO usuarios (username, password_hash, rol) VALUES (?,?,?)",
                    (user, pwd_hash, rol),
                )

            self.accept()
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                QMessageBox.critical(self, "Error", "El nombre de usuario ya existe.")
            else:
                QMessageBox.critical(self, "Error", str(e))

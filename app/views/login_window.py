from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
)
from PyQt5.QtCore import Qt


class LoginWindow(QDialog):
    def __init__(self, auth_controller):
        super().__init__()
        self.auth = auth_controller
        self.setWindowTitle("Login - Restaurante Italos")
        self.setFixedSize(300, 200)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Usuario:"))
        self.txt_user = QLineEdit()
        layout.addWidget(self.txt_user)

        layout.addWidget(QLabel("Password:"))
        self.txt_pass = QLineEdit()
        self.txt_pass.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.txt_pass)
        self.btn_login = QPushButton("Ingresar")
        self.btn_login.clicked.connect(self.attempt_login)
        layout.addWidget(self.btn_login)
        self.setLayout(layout)

    def attempt_login(self):
        user = self.txt_user.text()
        pwd = self.txt_pass.text()

        if self.auth.login(user, pwd):
            self.accept()  # Cierra el dialogo y retorna QDialog.Accepted
        else:
            QMessageBox.warning(self, "Error", "Credenciales incorrectas")

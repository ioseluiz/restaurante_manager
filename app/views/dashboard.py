from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt


class Dashboard(QWidget):
    def __init__(self, navigate_callback):
        super().__init__()
        self.navigate = navigate_callback  # Funcion para cambiar de pantalla
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        title = QLabel("Bienvenido al Sistema")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:24px; font-weight:bold; margin: 20px;")
        layout.addWidget(title)

        grid = QGridLayout()
        # Botones del Menu Principal
        btn_pos = self.create_btn("Ventas", lambda: self.navigate("ventas"))
        btn_insumos = self.create_btn(
            "Gestion de Insumos (CRUD)", lambda: self.navigate("insumos")
        )
        btn_menu = self.create_btn("Gestion Menu", lambda: self.navigate("menu"))
        btn_users = self.create_btn("Usuarios", lambda: self.navigate("usuarios"))

        grid.addWidget(btn_pos, 0, 0)
        grid.addWidget(btn_insumos, 0, 1)
        grid.addWidget(btn_menu, 1, 0)
        grid.addWidget(btn_users, 1, 1)

        layout.addLayout(grid)
        self.setLayout(layout)

    def create_btn(self, text, callback):
        btn = QPushButton(text)
        btn.setFixedSize(200, 150)
        btn.setStyleSheet("""
                          QPushButton {
                              background-color: #007BFF;
                              color: white;
                              font-size: 16px;
                              border-radius: 10px;
                          }
                          QPushButton: hover {
                              background-color: #0056b3;
                          }
                          """)
        btn.clicked.connect(callback)
        return btn

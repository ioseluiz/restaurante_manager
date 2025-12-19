from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt


class Dashboard(QWidget):
    def __init__(self, navigate_callback):
        super().__init__()
        self.navigate = navigate_callback
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        # Márgenes externos amplios para que se vea limpio
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Título
        title = QLabel("Panel de Control")
        title.setProperty("class", "header-title")  # Usamos la clase del CSS global
        title.setAlignment(Qt.AlignLeft)
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(20)  # Espacio entre tarjetas

        # Definimos los botones con sus etiquetas y claves de navegación
        menu_items = [
            ("Ventas (POS)", "ventas"),
            ("Gestión de Insumos", "insumos"),
            ("Gestión de Menú", "menu"),
            ("Categorías Insumos", "categorias"),
            ("Carga de Reportes", "reportes"),
            ("Usuarios", "usuarios"),
        ]

        # Posicionamiento en Grilla (2 columnas)
        row = 0
        col = 0

        for text, key in menu_items:
            # --- CORRECCIÓN AQUÍ ---
            # Usamos 'ignore' para recibir el booleano del click y no usarlo.
            # Usamos 'k=key' para capturar el valor actual de la iteración.
            btn = self.create_dashboard_card(
                text, lambda ignore, k=key: self.navigate(k)
            )

            grid.addWidget(btn, row, col)

            # Lógica para avanzar columnas/filas
            col += 1
            if col > 1:  # 2 columnas por fila
                col = 0
                row += 1

        layout.addLayout(grid)
        layout.addStretch()  # Empuja todo hacia arriba para que no se estiren los botones
        self.setLayout(layout)

    def create_dashboard_card(self, text, callback):
        btn = QPushButton(text)
        btn.setFixedSize(250, 120)
        btn.setCursor(Qt.PointingHandCursor)
        # Asignamos la clase para que el CSS global lo estilice como tarjeta
        btn.setProperty("class", "btn-dashboard")
        btn.clicked.connect(callback)
        return btn

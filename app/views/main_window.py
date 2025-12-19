from PyQt5.QtWidgets import (
    QMainWindow,
    QStackedWidget,
    QToolBar,
    QPushButton,
    QWidget,
    QSizePolicy,
    QLabel,
)
from PyQt5.QtCore import Qt
from app.views.dashboard import Dashboard
from app.views.modulos.insumos_crud import InsumosCRUD
from app.views.modulos.menu_crud import MenuCRUD
from app.views.modulos.carga_reportes import CargaReportesWidget
from app.views.modulos.categorias_crud import CategoriasCRUD


class MainWindow(QMainWindow):
    def __init__(self, db_manager, auth_controller):
        super().__init__()
        self.db = db_manager
        self.auth = auth_controller

        self.setWindowTitle("Restaurante Italos - Administración")
        self.setGeometry(100, 100, 1024, 768)

        # Stacked Widget para las vistas
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Inicializar UI
        self.init_toolbar()  # Creamos la barra superior primero
        self.init_views()

        # Configurar lógica de navegación inicial
        self.stack.currentChanged.connect(self.actualizar_toolbar)
        self.actualizar_toolbar(0)  # Forzar estado inicial

    def init_toolbar(self):
        self.toolbar = QToolBar("Navegación")
        self.toolbar.setMovable(False)  # Evitar que el usuario la mueva
        self.toolbar.setFloatable(False)
        self.toolbar.setContextMenuPolicy(
            Qt.PreventContextMenu
        )  # Click derecho deshabilitado
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        # --- BOTÓN DE INICIO PERSONALIZADO ---
        self.btn_home = QPushButton("  Volver al Menú Principal")
        # Usamos un emoji como ícono rápido, o podrías usar QIcon con un archivo .png
        self.btn_home.setText(" 🏠  Inicio / Menú ")
        self.btn_home.setCursor(Qt.PointingHandCursor)
        self.btn_home.setProperty("class", "btn-navbar")  # Clase CSS para estilo
        self.btn_home.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        # Añadimos un espaciador o widget vacío si quisieras alinear a la derecha,
        # pero por defecto a la izquierda está bien.
        self.toolbar.addWidget(self.btn_home)

        # Widget espaciador para empujar info de usuario a la derecha (Opcional)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(spacer)

        # Etiqueta de Usuario (Visualmente útil)
        lbl_user = QLabel(
            f"Usuario: {self.auth.current_user[1] if self.auth.current_user else 'Admin'} "
        )
        lbl_user.setStyleSheet("color: #7f8c8d; font-weight: bold; margin-right: 15px;")
        self.toolbar.addWidget(lbl_user)

    def init_views(self):
        # Index 0: Dashboard
        self.dashboard = Dashboard(self.navigate_to)
        self.stack.addWidget(self.dashboard)

        # Index 1: Insumos CRUD
        self.view_insumos = InsumosCRUD(self.db)
        self.stack.addWidget(self.view_insumos)

        # Index 2: Gestión de Menu
        self.view_menu = MenuCRUD(self.db)
        self.stack.addWidget(self.view_menu)

        # Index 3: Categorías
        self.view_categorias = CategoriasCRUD(self.db)
        self.stack.addWidget(self.view_categorias)

        # Index 4: Carga de Reportes
        self.view_reportes = CargaReportesWidget(
            parent_callback_cancelar=lambda: self.stack.setCurrentIndex(0)
        )
        self.stack.addWidget(self.view_reportes)

    def navigate_to(self, screen_name):
        if screen_name == "insumos":
            self.view_insumos.cargar_datos()
            self.stack.setCurrentIndex(1)
        elif screen_name == "menu":
            self.view_menu.cargar_datos()
            self.stack.setCurrentIndex(2)
        elif screen_name == "categorias":
            self.view_categorias.cargar_datos()
            self.stack.setCurrentIndex(3)
        elif screen_name == "reportes":
            self.stack.setCurrentIndex(4)
        elif screen_name == "usuarios":
            print("Navegando a usuarios (Pendiente)...")

    def actualizar_toolbar(self, index):
        """
        Muestra la barra de navegación solo si NO estamos en el Dashboard (index 0).
        """
        if index == 0:
            self.toolbar.hide()
        else:
            self.toolbar.show()

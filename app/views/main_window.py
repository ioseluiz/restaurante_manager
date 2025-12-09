from PyQt5.QtWidgets import QMainWindow, QStackedWidget, QAction, QToolBar
from app.views.dashboard import Dashboard
from app.views.modulos.insumos_crud import InsumosCRUD
from app.views.modulos.menu_crud import MenuCRUD


class MainWindow(QMainWindow):
    def __init__(self, db_manager, auth_controller):
        super().__init__()
        self.db = db_manager
        self.auth = auth_controller

        self.setWindowTitle("Restaurante Italos - Administracion")
        self.setGeometry(100, 100, 1024, 768)
        # Contenedor Central que cambia pantallas
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Inicializar vistas
        self.init_views()

        # Barra de herramientas (boton volver al inicio)
        self.toolbar = QToolBar("Navegacion")
        self.addToolBar(self.toolbar)
        self.action_home = QAction("Inicio / Dashboard", self)

        self.action_home.triggered.connect(lambda: self.stack.setCurrentIndex(0))
        self.toolbar.addAction(self.action_home)

    def init_views(self):
        # Index 0: Dashboard
        self.dashboard = Dashboard(self.navigate_to)
        self.stack.addWidget(self.dashboard)

        # Index 1: Insumos CRUD
        self.view_insumos = InsumosCRUD(self.db)
        self.stack.addWidget(self.view_insumos)

        # Index 2: Gestion de Menu (Nuevo)
        self.view_menu = MenuCRUD(self.db)
        self.stack.addWidget(self.view_menu)

    def navigate_to(self, screen_name):
        if screen_name == "insumos":
            self.view_insumos.cargar_datos()
            # Refrescar al entrar
            self.stack.setCurrentIndex(1)
        elif screen_name == "menu":
            self.view_menu.cargar_datos()
            self.stack.setCurrentIndex(2)
        elif screen_name == "users":
            print("Navegando a Gestion de Usuarios..")

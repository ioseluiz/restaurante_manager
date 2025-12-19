from PyQt5.QtWidgets import QMainWindow, QStackedWidget, QAction, QToolBar, QLabel
from app.views.dashboard import Dashboard
from app.views.modulos.insumos_crud import InsumosCRUD
from app.views.modulos.menu_crud import MenuCRUD
from app.views.modulos.carga_reportes import CargaReportesWidget

# --- IMPORTAR NUEVA VISTA ---
from app.views.modulos.categorias_crud import CategoriasCRUD


class MainWindow(QMainWindow):
    def __init__(self, db_manager, auth_controller):
        super().__init__()
        self.db = db_manager
        self.auth = auth_controller

        self.setWindowTitle("Restaurante Italos - Administracion")
        self.setGeometry(100, 100, 1024, 768)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.init_views()

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

        # Index 2: Gestion de Menu
        self.view_menu = MenuCRUD(self.db)
        self.stack.addWidget(self.view_menu)

        # Index 3: Categorias CRUD (Ocupamos un espacio o reordenamos)
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
        elif screen_name == "categorias":  # --- NUEVA NAVEGACIÓN ---
            self.view_categorias.cargar_datos()
            self.stack.setCurrentIndex(3)
        elif screen_name == "reportes":
            self.stack.setCurrentIndex(4)
        elif screen_name == "usuarios":
            print("Navegando a usuarios...")

import sys
import os
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QToolButton,
    QLabel,
    QStackedWidget,
    QGridLayout,
    QSizePolicy,  # <--- IMPORTANTE: Agregado para manejar políticas de tamaño
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize

# --- IMPORTACIÓN DE VISTAS ---
# from app.views.modulos.ventas_pos import VentasPOSWidget
from app.views.modulos.insumos_crud import InsumosCRUD

# from app.views.modulos.menu_crud import MenuCRUD
# from app.views.modulos.categorias_crud import CategoriasCRUD
from app.views.modulos.carga_reportes import CargaReportesWidget
# from app.views.modulos.usuarios import UsuariosWidget


class MainWindow(QMainWindow):
    def __init__(self, db_manager, auth_controller):
        """
        Inicializa la ventana principal.
        :param db_manager: Instancia del gestor de base de datos.
        :param auth_controller: Controlador de autenticación.
        """
        super().__init__()

        self.db = db_manager
        self.auth = auth_controller

        # Bandera para controlar el cierre de sesión
        self.logout_requested = False

        self.setWindowTitle("Sistema de Gestión de Restaurante")
        self.setMinimumSize(1200, 800)

        # Configuración de rutas para assets
        base_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(base_dir))
        self.assets_dir = os.path.join(project_root, "assets")

        # Widget Central Principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Inicializar UI
        self.setup_ui()

    def setup_ui(self):
        # 1. Sidebar (Menú Lateral)
        self.sidebar = self.create_sidebar()
        self.main_layout.addWidget(self.sidebar)

        # 2. Área Principal (Contenido)
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # Header Superior (Título de la sección actual)
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 10)

        self.header_label = QLabel("Bienvenido")
        self.header_label.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #333;"
        )
        header_layout.addWidget(self.header_label)
        header_layout.addStretch()

        content_layout.addWidget(header_widget)

        # Stacked Widget para cambiar vistas
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)

        self.main_layout.addWidget(content_area)

        # Crear página de bienvenida vacía o Dashboard
        welcome = QLabel("Seleccione una opción del menú")
        welcome.setAlignment(Qt.AlignCenter)
        self.stack.addWidget(welcome)

        # Diccionario para guardar referencias a los módulos cargados
        self.modules = {}

    def create_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("background-color: #2c3e50; color: white;")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Título App en Sidebar
        app_title = QLabel("Restaurante\nManager")
        app_title.setAlignment(Qt.AlignCenter)
        app_title.setStyleSheet(
            "font-size: 20px; font-weight: bold; padding: 20px; background-color: #1a252f;"
        )
        layout.addWidget(app_title)

        # Botones del Menú
        buttons = [
            ("Punto de Venta", "icon_pos_ventas.png", self.show_pos),
            ("Gestión de Insumos", "icon_insumos.png", self.show_insumos),
            ("Gestión del Menú", "icon_gestion_menu.png", self.show_menu),
            ("Categorías", "icon04.png", self.show_categorias),
            ("Carga de Reportes", "icon_upload_reports.png", self.show_reportes),
            ("Usuarios", "icon_user.png", self.show_usuarios),
        ]

        for text, icon_name, callback in buttons:
            btn = self.create_nav_button(text, icon_name, callback)
            layout.addWidget(btn)

        layout.addStretch()

        # Botón Salir
        btn_exit = self.create_nav_button("Cerrar Sesión", None, self.logout)
        btn_exit.setStyleSheet("""
            QToolButton {
                background-color: #c0392b; 
                color: white; 
                border: none; 
                padding: 15px; 
                text-align: left; 
                font-size: 14px;
            }
            QToolButton:hover { background-color: #e74c3c; }
        """)
        layout.addWidget(btn_exit)

        return sidebar

    def create_nav_button(self, text, icon_name, callback):
        btn = QToolButton()
        btn.setText(f"  {text}")
        btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        btn.setFixedHeight(50)
        btn.setCursor(Qt.PointingHandCursor)

        # Estilo Base
        btn.setStyleSheet("""
            QToolButton {
                background-color: transparent; 
                color: white; 
                border: none; 
                padding-left: 20px; 
                text-align: left; 
                font-size: 14px;
            }
            QToolButton:hover { background-color: #34495e; }
            QToolButton:pressed { background-color: #1abc9c; }
        """)

        # Icono (Si existe)
        if icon_name:
            icon_path = os.path.join(self.assets_dir, "icons", icon_name)
            if os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
                btn.setIconSize(QSize(24, 24))

        btn.clicked.connect(callback)

        # --- CORRECCIÓN AQUÍ ---
        # Usamos QSizePolicy.Expanding (Horizontal) y QSizePolicy.Fixed (Vertical)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        return btn

    def load_module(self, name, widget_class, title, needs_db=False):
        """
        Carga un módulo en el stack si no existe.
        Maneja inteligentemente dependencias de DB y Callbacks.
        """
        if name not in self.modules:
            widget = None

            # Intento 1: Si necesita DB, probamos inyectar DB + Callback (Para widgets complejos como CargaReportes)
            if needs_db:
                try:
                    widget = widget_class(
                        self.db, parent_callback_cancelar=self.go_home
                    )
                except TypeError:
                    # Si falla (ej. InsumosCRUD no acepta callback), intentamos solo con DB
                    try:
                        widget = widget_class(self.db)
                    except TypeError:
                        print(
                            f"Error cargando {name}: El constructor no acepta 'db_manager'"
                        )

            # Intento 2: Si no necesita DB (o falló lo anterior y widget sigue None)
            if widget is None:
                try:
                    widget = widget_class(parent_callback_cancelar=self.go_home)
                except TypeError:
                    # Último recurso: Constructor vacío
                    widget = widget_class()

            self.modules[name] = widget
            self.stack.addWidget(widget)

        self.stack.setCurrentWidget(self.modules[name])
        self.header_label.setText(title)

        # Si el módulo tiene un método cargar_datos, lo llamamos para refrescar
        if hasattr(self.modules[name], "cargar_datos"):
            self.modules[name].cargar_datos()

    # --- Slots de Navegación ---

    def show_pos(self):
        print("Navegando a POS...")
        # self.load_module("pos", VentasPOSWidget, "Punto de Venta", needs_db=True)

    def show_insumos(self):
        print("Navegando a Insumos...")
        self.load_module("insumos", InsumosCRUD, "Gestión de Insumos", needs_db=True)

    def show_menu(self):
        print("Navegando a Menú...")
        # self.load_module("menu", MenuCRUD, "Gestión del Menú", needs_db=True)

    def show_categorias(self):
        print("Navegando a Categorías...")
        # self.load_module("categorias", CategoriasCRUD, "Categorías de Insumos", needs_db=True)

    def show_reportes(self):
        self.load_module(
            "reportes",
            CargaReportesWidget,
            "Carga y Procesamiento de Reportes",
            needs_db=True,
        )

    def show_usuarios(self):
        print("Navegando a Usuarios...")
        # self.load_module("usuarios", UsuariosWidget, "Gestión de Usuarios", needs_db=True)

    def go_home(self):
        self.stack.setCurrentIndex(0)
        self.header_label.setText("Bienvenido")

    def logout(self):
        self.logout_requested = True
        self.close()

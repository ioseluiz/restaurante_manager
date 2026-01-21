import sys
import os
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,  # <--- Agregado para el header horizontal
    QPushButton,
    QToolButton,
    QLabel,
    QStackedWidget,
    QGridLayout,
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize

# Importamos las vistas (descomentar a medida que las vayas arreglando/creando)
# from app.views.modulos.ventas_pos import VentasPOSWidget
# from app.views.modulos.insumos_crud import InsumosCRUD
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
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(base_dir)))

        # Intento robusto de encontrar la carpeta assets
        posibles_rutas = [
            os.path.join(os.getcwd(), "assets", "icons"),
            os.path.join(root_dir, "assets", "icons"),
            os.path.join(base_dir, "..", "..", "assets", "icons"),
        ]

        self.icons_path = ""
        for ruta in posibles_rutas:
            if os.path.exists(ruta):
                self.icons_path = ruta
                break

        if not self.icons_path:
            self.icons_path = os.path.join(os.getcwd(), "assets", "icons")

        # Widget central
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- Header (Barra Superior) ---
        # Creamos un widget contenedor para la barra superior
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #2c3e50;")

        # Layout horizontal para el header: Titulo a la izquierda, Botón a la derecha
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 15, 20, 15)

        # Etiqueta del Título
        self.header_label = QLabel("Menu Principal")
        self.header_label.setStyleSheet("""
            color: white;
            font-size: 24px;
            font-weight: bold;
            border: none;
            background: transparent;
        """)

        # Botón de Cerrar Sesión
        self.btn_logout = QPushButton("Cerrar Sesión")
        self.btn_logout.setCursor(Qt.PointingHandCursor)
        # Estilo rojo (danger) para indicar salida, acorde a la paleta
        self.btn_logout.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c; 
                color: white; 
                border: none;
                border-radius: 5px; 
                padding: 8px 15px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c0392b; 
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        self.btn_logout.clicked.connect(self.logout)

        # Añadimos widgets al layout del header
        header_layout.addWidget(self.header_label)
        header_layout.addStretch()  # Espaciador flexible
        header_layout.addWidget(self.btn_logout)

        # Añadimos el header al layout principal
        self.main_layout.addWidget(header_widget)

        # --- Stack de Vistas ---
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        # Inicializamos el Dashboard (Índice 0)
        self.dashboard_widget = self.create_dashboard_menu()
        self.stack.addWidget(self.dashboard_widget)

        # Diccionario para carga perezosa de módulos
        self.modules = {}

    def logout(self):
        """Gestiona el cierre de sesión."""
        self.logout_requested = True
        self.close()

    def create_dashboard_menu(self):
        """Crea el menú principal con botones grandes e iconos."""
        menu_widget = QWidget()
        grid_layout = QGridLayout(menu_widget)
        grid_layout.setContentsMargins(50, 50, 50, 50)
        grid_layout.setSpacing(30)

        buttons_config = [
            ("Ventas (POS)", self.show_pos, "icon_pos_ventas.png"),
            ("Gestión de Insumos", self.show_insumos, "icon_chicken.png"),
            ("Gestión de Menú", self.show_menu, "icon_gestion_menu.png"),
            ("Categorías de Insumos", self.show_categorias, "icon_insumos_meat.png"),
            ("Carga de Reportes", self.show_reportes, "icon_upload_reports.png"),
            ("Usuarios", self.show_usuarios, "icon_user.png"),
        ]

        row, col = 0, 0
        for text, slot, icon_file in buttons_config:
            full_icon_path = os.path.join(self.icons_path, icon_file)

            btn = self.create_dashboard_button(text, slot, icon_path=full_icon_path)
            grid_layout.addWidget(btn, row, col)

            col += 1
            if col > 2:  # 3 columnas
                col = 0
                row += 1

        return menu_widget

    def create_dashboard_button(self, text, slot_func, icon_path=None):
        btn = QToolButton()
        btn.setText(text)
        btn.setFixedSize(220, 180)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(slot_func)

        # Configuración del Icono
        if icon_path and os.path.exists(icon_path):
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(80, 80))
            btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        else:
            print(f"Aviso: Icono no encontrado en {icon_path}")

        # Estilo: Fondo blanco, Icono y Texto azul (#3498db)
        btn.setStyleSheet("""
            QToolButton {
                background-color: #ffffff;
                color: #3498db;
                border: 2px solid #3498db;
                border-radius: 15px;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
            }
            QToolButton:hover {
                background-color: #f0f8ff;
                border: 2px solid #2980b9;
            }
            QToolButton:pressed {
                background-color: #d6eaf8;
            }
        """)
        return btn

    def go_home(self):
        """Regresa al dashboard principal."""
        self.header_label.setText("Menu Principal")
        self.stack.setCurrentIndex(0)

    def load_module(self, name, widget_class, title, needs_db=False):
        """
        Carga un módulo en el stack si no existe.
        """
        if name not in self.modules:
            try:
                if needs_db:
                    widget = widget_class(self.db)
                else:
                    widget = widget_class(parent_callback_cancelar=self.go_home)
            except TypeError:
                widget = widget_class()

            self.modules[name] = widget
            self.stack.addWidget(widget)

        self.stack.setCurrentWidget(self.modules[name])
        self.header_label.setText(title)

    # --- Slots de Navegación ---

    def show_pos(self):
        print("Navegando a POS...")
        # self.load_module("pos", VentasPOSWidget, "Punto de Venta", needs_db=True)

    def show_insumos(self):
        print("Navegando a Insumos...")
        # self.load_module("insumos", InsumosCRUD, "Gestión de Insumos", needs_db=True)

    def show_menu(self):
        print("Navegando a Menú...")
        # self.load_module("menu", MenuCRUD, "Gestión del Menú", needs_db=True)

    def show_categorias(self):
        print("Navegando a Categorías...")
        # self.load_module("categorias", CategoriasCRUD, "Categorías de Insumos", needs_db=True)

    def show_reportes(self):
        self.load_module("reportes", CargaReportesWidget, "Carga de Reportes")

    def show_usuarios(self):
        print("Navegando a Usuarios...")
        # self.load_module("usuarios", UsuariosWidget, "Gestión de Usuarios", needs_db=True)

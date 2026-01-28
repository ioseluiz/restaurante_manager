import sys
import os
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QStackedWidget,
    QFrame,
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize

# --- IMPORTACIÓN DE VISTAS ---
from app.views.modulos.insumos_crud import InsumosCRUD
from app.views.modulos.menu_crud import MenuCRUD
from app.views.modulos.recetas_crud import RecetasCRUD
from app.views.modulos.unidades_crud import UnidadesCRUD
from app.views.modulos.carga_reportes import CargaReportesWidget
from app.views.modulos.usuarios import UsuariosWidget
from app.views.modulos.calculo_insumos import CalculoInsumosView
from app.views.modulos.compras_crud import ComprasCRUD

# --- NUEVA IMPORTACIÓN (INVENTARIO) ---
from app.views.modulos.inventario_view import InventarioView


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
        self.logout_requested = False

        # Diccionario para almacenar instancias de módulos cargados (Lazy Loading)
        self.modules = {}

        self.setWindowTitle(f"Sistema de Gestión - Usuario: {self.auth.current_user}")
        self.resize(1200, 800)
        self.setWindowIcon(QIcon("assets/icons/icon01.png"))  # Icono de la ventana

        self.init_ui()

    def init_ui(self):
        """Configura la interfaz gráfica principal."""

        # Widget central contenedor
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal (Horizontal: Sidebar + Contenido)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- SIDEBAR (Barra Lateral) ---
        sidebar_frame = QFrame()
        sidebar_frame.setFixedWidth(260)  # Un poco más ancho para los iconos
        sidebar_frame.setStyleSheet("background-color: #2c3e50; color: white;")
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(10)

        # Título / Header del Sidebar
        lbl_header = QLabel("Restaurante Manager")
        lbl_header.setStyleSheet(
            "font-size: 18px; font-weight: bold; margin-bottom: 20px; color: #ecf0f1;"
        )
        lbl_header.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(lbl_header)

        # --- BOTONES DE NAVEGACIÓN (Con Iconos Restaurados) ---

        # 1. Compras
        self.btn_compras = self.create_nav_button(
            "Compras y Proveedores",
            "assets/icons/icon_pos_ventas.png",
            self.show_compras,
        )
        sidebar_layout.addWidget(self.btn_compras)

        # 2. Inventario (NUEVO)
        # Usamos un icono genérico o de insumos para el inventario
        self.btn_inventario = self.create_nav_button(
            "Inventario (Kardex)", "assets/icons/icon_insumos.png", self.show_inventario
        )
        # Resaltamos un poco el botón nuevo si deseas, o lo dejamos igual
        self.btn_inventario.setStyleSheet(
            self.btn_inventario.styleSheet() + "border: 1px solid #3498db;"
        )
        sidebar_layout.addWidget(self.btn_inventario)

        # 3. Insumos
        self.btn_insumos = self.create_nav_button(
            "Catálogo de Insumos",
            "assets/icons/icon_insumos_meat.png",
            self.show_insumos,
        )
        sidebar_layout.addWidget(self.btn_insumos)

        # 4. Recetas
        self.btn_recetas = self.create_nav_button(
            "Recetas (Fichas)", "assets/icons/icon_chicken.png", self.show_recetas
        )
        sidebar_layout.addWidget(self.btn_recetas)

        # 5. Menú
        self.btn_menu = self.create_nav_button(
            "Gestión de Menú", "assets/icons/icon_gestion_menu.png", self.show_menu
        )
        sidebar_layout.addWidget(self.btn_menu)

        # 6. Cálculo (Presupuesto)
        self.btn_calculo = self.create_nav_button(
            "Cálculo de Insumos",
            "assets/icons/icon_generate_report.png",
            self.show_calculo_insumos,
        )
        sidebar_layout.addWidget(self.btn_calculo)

        # 7. Carga Reportes
        self.btn_reportes = self.create_nav_button(
            "Cargar Reportes Ventas",
            "assets/icons/icon_upload_reports.png",
            self.show_reportes,
        )
        sidebar_layout.addWidget(self.btn_reportes)

        # Separador
        sidebar_layout.addStretch()

        # Configuración / Admin
        lbl_config = QLabel("Configuración")
        lbl_config.setStyleSheet(
            "color: #95a5a6; font-size: 12px; font-weight: bold; margin-top: 10px; margin-left: 5px;"
        )
        sidebar_layout.addWidget(lbl_config)

        # 8. Unidades
        self.btn_unidades = self.create_nav_button(
            "Unidades de Medida", "assets/icons/icon_unidades.png", self.show_unidades
        )
        sidebar_layout.addWidget(self.btn_unidades)

        # 9. Usuarios
        self.btn_usuarios = self.create_nav_button(
            "Gestión de Usuarios", "assets/icons/icon_user.png", self.show_usuarios
        )
        sidebar_layout.addWidget(self.btn_usuarios)

        # Botón Salir
        btn_logout = QPushButton("  Cerrar Sesión")
        btn_logout.setIcon(
            QIcon("assets/icons/icon06.png")
        )  # Icono de salida (asumido icon06 o genérico)
        btn_logout.setIconSize(QSize(24, 24))
        btn_logout.setStyleSheet("""
            QPushButton {
                background-color: #c0392b; 
                color: white; 
                border: none; 
                padding: 10px; 
                border-radius: 5px;
                text-align: left;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #e74c3c; }
        """)
        btn_logout.clicked.connect(self.logout)
        sidebar_layout.addWidget(btn_logout)

        main_layout.addWidget(sidebar_frame)

        # --- ÁREA DE CONTENIDO (Stacked Widget) ---
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

    def create_nav_button(self, text, icon_path, callback):
        """
        Crea un botón de navegación estilizado con icono.
        """
        btn = QPushButton(f"  {text}")  # Espacio para separar del icono

        # Configurar Icono
        if icon_path and os.path.exists(icon_path):
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(32, 32))  # Tamaño visible y cómodo
        else:
            # Fallback si no encuentra el icono exacto
            btn.setIcon(QIcon("assets/icons/icon01.png"))
            btn.setIconSize(QSize(32, 32))

        btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 12px 10px;
                background-color: transparent;
                border: none;
                color: #ecf0f1;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
        """)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(callback)
        return btn

    def load_module(self, name, widget_class, title, needs_db=False):
        """
        Carga un módulo en el StackedWidget si no existe (Lazy Loading).
        """
        if name not in self.modules:
            # Instanciar el widget
            if needs_db:
                instance = widget_class(self.db)
            else:
                instance = widget_class()

            # Agregarlo al stack
            index = self.stacked_widget.addWidget(instance)
            self.modules[name] = {"instance": instance, "index": index, "title": title}

        # Mostrar el módulo
        module_data = self.modules[name]
        self.stacked_widget.setCurrentIndex(module_data["index"])

        # Refrescar datos si el módulo tiene el método
        if hasattr(module_data["instance"], "cargar_datos"):
            module_data["instance"].cargar_datos()
        elif hasattr(module_data["instance"], "cargar_inventario"):
            module_data["instance"].cargar_inventario()

    # --- MÉTODOS DE NAVEGACIÓN ---

    def show_compras(self):
        self.load_module("compras", ComprasCRUD, "Gestión de Compras", needs_db=True)

    def show_inventario(self):
        # Muestra la nueva vista de Inventario
        self.load_module(
            "inventario", InventarioView, "Inventario Actual", needs_db=True
        )

    def show_insumos(self):
        self.load_module("insumos", InsumosCRUD, "Catálogo de Insumos", needs_db=True)

    def show_menu(self):
        self.load_module("menu", MenuCRUD, "Gestión de Menú", needs_db=True)

    def show_recetas(self):
        self.load_module("recetas", RecetasCRUD, "Gestión de Recetas", needs_db=True)

    def show_calculo_insumos(self):
        self.load_module(
            "calculo_insumos", CalculoInsumosView, "Reporte de Compras", needs_db=True
        )

    def show_reportes(self):
        self.load_module(
            "reportes", CargaReportesWidget, "Carga de Reportes", needs_db=True
        )

    def show_unidades(self):
        self.load_module("unidades", UnidadesCRUD, "Unidades de Medida", needs_db=True)

    def show_usuarios(self):
        self.load_module(
            "usuarios", UsuariosWidget, "Gestión de Usuarios", needs_db=True
        )

    def logout(self):
        self.logout_requested = True
        self.close()

# [FILE: app/views/main_window.py]
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

from app.views.modulos.usuarios import UsuariosWidget
from app.views.modulos.presupuestos import (
    PresupuestosView,
)
from app.views.modulos.compras_crud import ComprasCRUD
from app.views.modulos.ventas import VentasModulo  # <--- IMPORTACIÓN DEL NUEVO MÓDULO

from app.views.modulos.inventario_view import InventarioView
from app.views.dashboard import DashboardView


class MainWindow(QMainWindow):
    def __init__(self, db_manager, auth_controller):
        super().__init__()
        self.db = db_manager
        self.auth = auth_controller
        self.logout_requested = False
        self.modules = {}

        self.setWindowTitle("Sistema de Gestión de Restaurante")
        self.resize(1200, 800)
        self.setWindowIcon(QIcon("assets/icons/icon01.png"))

        self.init_ui()
        self.setup_statusbar()

    def setup_statusbar(self):
        user_display = self.auth.current_user
        if isinstance(user_display, (list, tuple)) and len(user_display) > 1:
            user_display = user_display[1]

        self.statusBar().showMessage(f"Usuario: {user_display}")
        self.statusBar().setStyleSheet(
            "color: #2c3e50; font-weight: bold; border-top: 1px solid #bdc3c7;"
        )

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- SIDEBAR ---
        sidebar_frame = QFrame()
        sidebar_frame.setFixedWidth(260)
        sidebar_frame.setStyleSheet("background-color: #2c3e50; color: white;")
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(10)

        lbl_header = QLabel("Restaurante Manager")
        lbl_header.setStyleSheet(
            "font-size: 18px; font-weight: bold; margin-bottom: 20px; color: #ecf0f1;"
        )
        lbl_header.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(lbl_header)

        self.btn_inicio = self.create_nav_button(
            "Inicio / Dashboard", "assets/icons/home.png", self.show_dashboard
        )
        sidebar_layout.addWidget(self.btn_inicio)

        # <--- BOTÓN CONECTADO AL NUEVO MÓDULO DE VENTAS --->
        self.btn_ventas = self.create_nav_button(
            "Ventas",
            "assets/icons/icon_pos_ventas.png",
            self.show_ventas,
        )
        sidebar_layout.addWidget(self.btn_ventas)

        self.btn_compras = self.create_nav_button(
            "Compras y Proveedores",
            "assets/icons/shopping_cart.png",
            self.show_compras,
        )
        sidebar_layout.addWidget(self.btn_compras)

        self.btn_inventario = self.create_nav_button(
            "Inventario", "assets/icons/inventario.png", self.show_inventario
        )
        self.btn_inventario.setStyleSheet(
            self.btn_inventario.styleSheet() + "border: 1px solid #3498db;"
        )
        sidebar_layout.addWidget(self.btn_inventario)

        self.btn_insumos = self.create_nav_button(
            "Catálogo de Insumos",
            "assets/icons/icon_insumos_meat.png",
            self.show_insumos,
        )
        sidebar_layout.addWidget(self.btn_insumos)

        self.btn_recetas = self.create_nav_button(
            "Recetas (Fichas)", "assets/icons/recetas.png", self.show_recetas
        )
        sidebar_layout.addWidget(self.btn_recetas)

        self.btn_menu = self.create_nav_button(
            "Gestión de Menú", "assets/icons/icon_gestion_menu.png", self.show_menu
        )
        sidebar_layout.addWidget(self.btn_menu)

        self.btn_presupuestos = self.create_nav_button(
            "Presupuestos",
            "assets/icons/icon_generate_report.png",
            self.show_presupuestos,
        )
        sidebar_layout.addWidget(self.btn_presupuestos)

        sidebar_layout.addStretch()

        lbl_config = QLabel("Configuración")
        lbl_config.setStyleSheet(
            "color: #95a5a6; font-size: 12px; font-weight: bold; margin-top: 10px; margin-left: 5px;"
        )
        sidebar_layout.addWidget(lbl_config)

        self.btn_unidades = self.create_nav_button(
            "Unidades de Medida", "assets/icons/icon_unidades.png", self.show_unidades
        )
        sidebar_layout.addWidget(self.btn_unidades)

        self.btn_usuarios = self.create_nav_button(
            "Gestión de Usuarios", "assets/icons/icon_user.png", self.show_usuarios
        )
        sidebar_layout.addWidget(self.btn_usuarios)

        btn_logout = QPushButton("  Cerrar Sesión")
        btn_logout.setIcon(QIcon("assets/icons/logout.png"))
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

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.show_dashboard()

    def create_nav_button(self, text, icon_path, callback):
        btn = QPushButton(f"  {text}")
        if icon_path and os.path.exists(icon_path):
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(32, 32))
        else:
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
        if name not in self.modules:
            if needs_db:
                instance = widget_class(self.db)
            else:
                instance = widget_class()

            index = self.stacked_widget.addWidget(instance)
            self.modules[name] = {"instance": instance, "index": index, "title": title}

        module_data = self.modules[name]
        self.stacked_widget.setCurrentIndex(module_data["index"])

        if hasattr(module_data["instance"], "cargar_datos"):
            module_data["instance"].cargar_datos()
        elif hasattr(module_data["instance"], "cargar_inventario"):
            module_data["instance"].cargar_inventario()

    # <--- FUNCIÓN ACTUALIZADA PARA CARGAR EL MÓDULO CONSOLIDADO --->
    def show_ventas(self):
        self.load_module(
            "ventas",
            VentasModulo,
            "Módulo de Ventas",
            needs_db=True,
        )

    def show_compras(self):
        self.load_module("compras", ComprasCRUD, "Gestión de Compras", needs_db=True)

    def show_inventario(self):
        self.load_module(
            "inventario", InventarioView, "Inventario Actual", needs_db=True
        )

    def show_insumos(self):
        self.load_module("insumos", InsumosCRUD, "Catálogo de Insumos", needs_db=True)

    def show_menu(self):
        self.load_module("menu", MenuCRUD, "Gestión de Menú", needs_db=True)

    def show_recetas(self):
        self.load_module("recetas", RecetasCRUD, "Gestión de Recetas", needs_db=True)

    def show_presupuestos(self):
        self.load_module(
            "presupuestos", PresupuestosView, "Gestión de Presupuestos", needs_db=True
        )

    # Nota: Se eliminó def show_reportes(self) porque ya está integrado en VentasModulo

    def show_unidades(self):
        self.load_module("unidades", UnidadesCRUD, "Unidades de Medida", needs_db=True)

    def show_usuarios(self):
        self.load_module(
            "usuarios", UsuariosWidget, "Gestión de Usuarios", needs_db=True
        )

    def show_dashboard(self):
        self.load_module("dashboard", DashboardView, "Panel de Control", needs_db=True)

    def logout(self):
        self.logout_requested = True
        self.close()

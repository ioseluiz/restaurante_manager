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
    QMessageBox,
    QFileDialog,
    QButtonGroup,
    QApplication,
)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from app.utils.button_icons import auto_icon_buttons

# --- IMPORTACIÓN DE VISTAS ---
from app.views.modulos.insumos_crud import InsumosCRUD
from app.views.modulos.menu_crud import MenuCRUD
from app.views.modulos.recetas_crud import RecetasCRUD
from app.views.modulos.unidades_crud import UnidadesCRUD

from app.views.modulos.usuarios import UsuariosWidget
from app.views.modulos.presupuestos import PresupuestosView
from app.views.modulos.compras_crud import ComprasCRUD
from app.views.modulos.ventas import VentasModulo

from app.views.modulos.inventario_view import InventarioView
from app.views.modulos.conteo_inventario import ConteoInventarioView
from app.views.dashboard import DashboardView
from app.views.modulos.consolidados_view import ConsolidadosView
from app.views.modulos.sucursales_crud import SucursalesCRUD

SIDEBAR_W_EXPANDED = 220
SIDEBAR_W_COLLAPSED = 56

_NAV_BTN_EXPANDED = """
    QPushButton {
        text-align: left;
        padding: 10px 10px;
        background-color: transparent;
        border: none;
        border-left: 3px solid transparent;
        color: #4a4a4a;
        font-size: 13px;
        border-radius: 0px;
    }
    QPushButton:hover {
        background-color: #fff0f1;
        color: #a20f22;
        border-left: 3px solid #db9930;
    }
    QPushButton:pressed { background-color: #ffdde0; }
    QPushButton:checked {
        background-color: #ffe8ea;
        font-weight: bold;
        border-left: 3px solid #a20f22;
        color: #a20f22;
    }
"""

_NAV_BTN_COLLAPSED = """
    QPushButton {
        text-align: center;
        padding: 10px 4px;
        background-color: transparent;
        border: none;
        border-left: 3px solid transparent;
        color: #4a4a4a;
        border-radius: 0px;
    }
    QPushButton:hover {
        background-color: #fff0f1;
        color: #a20f22;
        border-left: 3px solid #db9930;
    }
    QPushButton:pressed { background-color: #ffdde0; }
    QPushButton:checked {
        background-color: #ffe8ea;
        border-left: 3px solid #a20f22;
        color: #a20f22;
    }
"""


def ruta_recurso(ruta_relativa):
    # Detecta si la aplicacion esta congelada por PyInstaller
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, ruta_relativa)
    return os.path.join(os.path.abspath("."), ruta_relativa)


class MainWindow(QMainWindow):
    def __init__(self, db_manager, auth_controller):
        super().__init__()
        self.db = db_manager
        self.auth = auth_controller
        self.logout_requested = False
        self.modules = {}
        self.sidebar_collapsed = False
        self._nav_buttons = []  # list of {"btn": QPushButton, "text": str}

        self.setWindowTitle("Sistema de Gestión de Restaurante")
        self.setWindowIcon(QIcon(ruta_recurso("assets/icons/app.ico")))

        self.init_ui()
        self.setup_statusbar()
        self._fit_to_screen()

    def _fit_to_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        w = min(1200, int(screen.width() * 0.92))
        h = min(800, int(screen.height() * 0.92))
        self.resize(w, h)
        self.move(
            screen.x() + (screen.width() - w) // 2,
            screen.y() + (screen.height() - h) // 2,
        )

    def setup_statusbar(self):
        sb = self.statusBar()
        sb.setStyleSheet(
            "color: #2c3e50; font-weight: bold; border-top: 1px solid #bdc3c7;"
        )

        # Permanent GitHub credit widget on the right
        gh_widget = QWidget()
        gh_row = QHBoxLayout(gh_widget)
        gh_row.setContentsMargins(0, 0, 8, 0)
        gh_row.setSpacing(5)

        gh_icon = QLabel()
        gh_px = QPixmap(ruta_recurso("assets/icons/github.svg"))
        if not gh_px.isNull():
            gh_px = gh_px.scaled(14, 14, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        gh_icon.setPixmap(gh_px)
        gh_row.addWidget(gh_icon)

        lbl_gh = QLabel('<a href="https://github.com/ioseluiz" style="color:#555555; text-decoration:none; font-weight:normal;">ioseluiz</a>')
        lbl_gh.setOpenExternalLinks(True)
        lbl_gh.setStyleSheet("font-size: 11px;")
        gh_row.addWidget(lbl_gh)

        sb.addPermanentWidget(gh_widget)

        self.actualizar_info_bd()

    def actualizar_info_bd(self):
        user_display = self.auth.current_user
        if isinstance(user_display, (list, tuple)) and len(user_display) > 1:
            username = user_display[1]
        else:
            username = "Desconocido"

        ruta_bd = getattr(self.db, "db_path", "Ruta Desconocida")
        self.statusBar().showMessage(
            f"Usuario: {username}  |  Base de Datos Activa: {ruta_bd}"
        )
        if hasattr(self, "lbl_db_info"):
            self.lbl_db_info.setText(f"BD:\n{ruta_bd}")

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.nav_button_group = QButtonGroup(self)
        self.nav_button_group.setExclusive(True)

        # --- SIDEBAR ---
        self.sidebar_frame = QFrame()
        self.sidebar_frame.setFixedWidth(SIDEBAR_W_EXPANDED)
        self.sidebar_frame.setStyleSheet(
            "background-color: #ffffff; border-right: 2px solid #f0e0e2;"
        )
        sidebar_layout = QVBoxLayout(self.sidebar_frame)
        sidebar_layout.setContentsMargins(8, 12, 8, 12)
        sidebar_layout.setSpacing(4)

        # Header row: title + toggle button
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)

        self.lbl_sidebar_header = QLabel()
        _logo_px = QPixmap(ruta_recurso("assets/imgs/italos_horizontal_transparente.png"))
        if not _logo_px.isNull():
            _logo_px = _logo_px.scaledToWidth(168, Qt.SmoothTransformation)
        self.lbl_sidebar_header.setPixmap(_logo_px)
        self.lbl_sidebar_header.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        header_row.addWidget(self.lbl_sidebar_header)

        self.btn_toggle_sidebar = QPushButton("◀")
        self.btn_toggle_sidebar.setProperty("skip-auto-icon", True)
        self.btn_toggle_sidebar.setToolTip("Ocultar / Mostrar panel")
        self.btn_toggle_sidebar.setFixedSize(28, 28)
        self.btn_toggle_sidebar.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #e0c0c3;
                border-radius: 4px;
                color: #a20f22;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #fff0f1; }
        """)
        self.btn_toggle_sidebar.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_sidebar.clicked.connect(self.toggle_sidebar)
        header_row.addWidget(self.btn_toggle_sidebar)
        sidebar_layout.addLayout(header_row)
        sidebar_layout.addSpacing(10)

        # Nav buttons
        self.btn_inicio = self.create_nav_button(
            "Inicio / Dashboard", "assets/icons/nav_home.svg", self.show_dashboard
        )
        sidebar_layout.addWidget(self.btn_inicio)

        self.btn_ventas = self.create_nav_button(
            "Ventas", "assets/icons/nav_ventas.svg", self.show_ventas
        )
        sidebar_layout.addWidget(self.btn_ventas)

        self.btn_compras = self.create_nav_button(
            "Compras y Proveedores", "assets/icons/nav_compras.svg", self.show_compras
        )
        sidebar_layout.addWidget(self.btn_compras)

        self.btn_inventario = self.create_nav_button(
            "Inventario", "assets/icons/nav_inventario.svg", self.show_inventario
        )
        sidebar_layout.addWidget(self.btn_inventario)

        self.btn_conteo = self.create_nav_button(
            "Toma de Inventario", "assets/icons/nav_conteo.svg", self.show_conteo
        )
        sidebar_layout.addWidget(self.btn_conteo)

        self.btn_insumos = self.create_nav_button(
            "Catálogo de Insumos", "assets/icons/nav_insumos.svg", self.show_insumos
        )
        sidebar_layout.addWidget(self.btn_insumos)

        self.btn_recetas = self.create_nav_button(
            "Recetas (Fichas)", "assets/icons/nav_recetas.svg", self.show_recetas
        )
        sidebar_layout.addWidget(self.btn_recetas)

        self.btn_menu = self.create_nav_button(
            "Gestión de Menú", "assets/icons/nav_menu.svg", self.show_menu
        )
        sidebar_layout.addWidget(self.btn_menu)

        self.btn_presupuestos = self.create_nav_button(
            "Presupuestos", "assets/icons/nav_presupuestos.svg", self.show_presupuestos
        )
        sidebar_layout.addWidget(self.btn_presupuestos)

        self.btn_consolidados = self.create_nav_button(
            "Consolidados", "assets/icons/nav_consolidados.svg", self.show_consolidados
        )
        sidebar_layout.addWidget(self.btn_consolidados)

        sidebar_layout.addStretch()

        self.lbl_config = QLabel("Configuración")
        self.lbl_config.setStyleSheet(
            "color: #aaaaaa; font-size: 11px; font-weight: bold; margin-top: 6px; margin-left: 10px;"
        )
        sidebar_layout.addWidget(self.lbl_config)

        self.btn_unidades = self.create_nav_button(
            "Unidades de Medida", "assets/icons/nav_unidades.svg", self.show_unidades
        )
        sidebar_layout.addWidget(self.btn_unidades)

        self.btn_sucursales = self.create_nav_button(
            "Sucursales", "assets/icons/nav_sucursales.svg", self.show_sucursales
        )
        sidebar_layout.addWidget(self.btn_sucursales)

        # Rol check
        user_rol = ""
        user_data = self.auth.current_user
        if isinstance(user_data, (list, tuple)) and len(user_data) > 2:
            user_rol = str(user_data[2]).lower()

        if user_rol in ["admin", "administrador"]:
            self.btn_usuarios = self.create_nav_button(
                "Gestión de Usuarios", "assets/icons/nav_usuarios.svg", self.show_usuarios
            )
            sidebar_layout.addWidget(self.btn_usuarios)

            self.btn_db_config = self.create_nav_button(
                "Configurar BD", "assets/icons/nav_db.svg",
                self.manage_db_connection, checkable=False,
            )
            self.btn_db_config.setStyleSheet(
                _NAV_BTN_EXPANDED + "QPushButton { color: #b8801f; }"
            )
            sidebar_layout.addWidget(self.btn_db_config)

        self.lbl_db_info = QLabel()
        self.lbl_db_info.setStyleSheet(
            "color: #aaaaaa; font-size: 10px; margin-top: 4px; margin-left: 10px;"
        )
        self.lbl_db_info.setWordWrap(True)
        sidebar_layout.addWidget(self.lbl_db_info)
        self.actualizar_info_bd()

        self.btn_logout = QPushButton("  Cerrar Sesión")
        self.btn_logout.setProperty("skip-auto-icon", True)
        self.btn_logout.setIcon(QIcon(ruta_recurso("assets/icons/nav_logout_white.svg")))
        self.btn_logout.setIconSize(QSize(20, 20))
        self.btn_logout.setStyleSheet("""
            QPushButton {
                background-color: #a20f22;
                color: white;
                border: none;
                padding: 9px;
                border-radius: 6px;
                text-align: left;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #7d0b1a; }
            QPushButton:pressed { background-color: #5e0814; }
        """)
        self.btn_logout.setCursor(Qt.PointingHandCursor)
        self.btn_logout.clicked.connect(self.logout)
        sidebar_layout.addWidget(self.btn_logout)

        main_layout.addWidget(self.sidebar_frame)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.btn_inicio.setChecked(True)
        self.show_dashboard()

    def toggle_sidebar(self):
        self.sidebar_collapsed = not self.sidebar_collapsed

        # Animate width
        anim_min = QPropertyAnimation(self.sidebar_frame, b"minimumWidth")
        anim_max = QPropertyAnimation(self.sidebar_frame, b"maximumWidth")
        for anim in (anim_min, anim_max):
            anim.setDuration(180)
            anim.setEasingCurve(QEasingCurve.InOutCubic)
            anim.setStartValue(self.sidebar_frame.width())
            anim.setEndValue(
                SIDEBAR_W_COLLAPSED if self.sidebar_collapsed else SIDEBAR_W_EXPANDED
            )

        self._sidebar_anim_group = QParallelAnimationGroup()
        self._sidebar_anim_group.addAnimation(anim_min)
        self._sidebar_anim_group.addAnimation(anim_max)
        self._sidebar_anim_group.finished.connect(self._on_sidebar_anim_done)
        self._sidebar_anim_group.start()

        # Update toggle arrow immediately
        self.btn_toggle_sidebar.setText("▶" if self.sidebar_collapsed else "◀")

        # Show/hide text elements
        self.lbl_sidebar_header.setVisible(not self.sidebar_collapsed)
        self.lbl_config.setVisible(not self.sidebar_collapsed)
        self.lbl_db_info.setVisible(not self.sidebar_collapsed)

        # Update nav button texts and styles
        for item in self._nav_buttons:
            btn = item["btn"]
            if self.sidebar_collapsed:
                btn.setText("")
                btn.setStyleSheet(_NAV_BTN_COLLAPSED)
            else:
                btn.setText(f"  {item['text']}")
                btn.setStyleSheet(_NAV_BTN_EXPANDED)

        # Logout button
        if self.sidebar_collapsed:
            self.btn_logout.setText("")
        else:
            self.btn_logout.setText("  Cerrar Sesión")

    def _on_sidebar_anim_done(self):
        # Lock the width after animation
        self.sidebar_frame.setFixedWidth(
            SIDEBAR_W_COLLAPSED if self.sidebar_collapsed else SIDEBAR_W_EXPANDED
        )

    def create_nav_button(self, text, icon_path, callback, checkable=True):
        btn = QPushButton(f"  {text}")
        btn.setProperty("skip-auto-icon", True)

        if checkable:
            btn.setCheckable(True)
            self.nav_button_group.addButton(btn)
            self._nav_buttons.append({"btn": btn, "text": text})

        abs_icon_path = ruta_recurso(icon_path) if icon_path else ""
        if abs_icon_path and os.path.exists(abs_icon_path):
            btn.setIcon(QIcon(abs_icon_path))
        else:
            btn.setIcon(QIcon(ruta_recurso("assets/icons/app.ico")))
        btn.setIconSize(QSize(24, 24))

        btn.setStyleSheet(_NAV_BTN_EXPANDED)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(callback)
        return btn

    def manage_db_connection(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Gestión de Base de Datos")
        msg.setText("¿Qué acción desea realizar con la base de datos?")

        btn_new = msg.addButton("Cargar Existente / Nueva BD", QMessageBox.ActionRole)
        btn_backup = msg.addButton("Crear Respaldo (Copia)", QMessageBox.ActionRole)
        msg.addButton("Cancelar", QMessageBox.RejectRole)
        msg.exec_()

        if msg.clickedButton() == btn_new:
            path, _ = QFileDialog.getSaveFileName(
                self, "Seleccionar o Crear Base de Datos", "", "SQLite Files (*.db)"
            )
            if path:
                self.db.switch_database(path)
                self.actualizar_info_bd()
                QMessageBox.information(self, "Éxito", f"Conectado exitosamente a:\n{path}")
                self.modules = {}
                self.show_dashboard()
                self.btn_inicio.setChecked(True)

        elif msg.clickedButton() == btn_backup:
            folder = QFileDialog.getExistingDirectory(
                self, "Seleccionar Carpeta para el Respaldo"
            )
            if folder:
                success, info = self.db.create_backup(folder)
                if success:
                    QMessageBox.information(
                        self, "Respaldo Creado", f"Copia de seguridad guardada en:\n{info}"
                    )
                else:
                    QMessageBox.critical(self, "Error", f"No se pudo crear el respaldo: {info}")

    def load_module(self, name, widget_class, title, needs_db=False):
        if name not in self.modules:
            instance = widget_class(self.db) if needs_db else widget_class()
            auto_icon_buttons(instance)
            index = self.stacked_widget.addWidget(instance)
            self.modules[name] = {"instance": instance, "index": index, "title": title}

        module_data = self.modules[name]
        self.stacked_widget.setCurrentIndex(module_data["index"])

        if hasattr(module_data["instance"], "cargar_datos"):
            module_data["instance"].cargar_datos()
        elif hasattr(module_data["instance"], "cargar_inventario"):
            module_data["instance"].cargar_inventario()

    def show_ventas(self):
        self.load_module("ventas", VentasModulo, "Módulo de Ventas", needs_db=True)

    def show_compras(self):
        self.load_module("compras", ComprasCRUD, "Gestión de Compras", needs_db=True)

    def show_inventario(self):
        self.load_module("inventario", InventarioView, "Inventario Actual", needs_db=True)

    def show_conteo(self):
        self.load_module("conteo", ConteoInventarioView, "Toma de Inventario", needs_db=True)

    def show_insumos(self):
        self.load_module("insumos", InsumosCRUD, "Catálogo de Insumos", needs_db=True)

    def show_menu(self):
        self.load_module("menu", MenuCRUD, "Gestión de Menú", needs_db=True)

    def show_recetas(self):
        self.load_module("recetas", RecetasCRUD, "Gestión de Recetas", needs_db=True)

    def show_presupuestos(self):
        self.load_module("presupuestos", PresupuestosView, "Gestión de Presupuestos", needs_db=True)

    def show_consolidados(self):
        self.load_module("consolidados", ConsolidadosView, "Módulo de Consolidados", needs_db=True)

    def show_unidades(self):
        self.load_module("unidades", UnidadesCRUD, "Unidades de Medida", needs_db=True)

    def show_sucursales(self):
        self.load_module("sucursales", SucursalesCRUD, "Gestión de Sucursales", needs_db=True)

    def show_usuarios(self):
        self.load_module("usuarios", UsuariosWidget, "Gestión de Usuarios", needs_db=True)

    def show_dashboard(self):
        self.load_module("dashboard", DashboardView, "Panel de Control", needs_db=True)

    def logout(self):
        self.logout_requested = True
        self.close()

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
    QAction,
    QScrollArea,
)
from PyQt5.QtGui import QIcon, QPixmap, QKeySequence
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from app.utils.button_icons import auto_icon_buttons, icono_flecha
from app.utils import ayuda
from app.version import etiqueta_version
from app.views.ayuda_dialog import AyudaDialog
from app.controllers.auth_controller import puede_ver
from app.controllers.restaurante_controller import RestauranteController
from app.database.config import agregar_reciente, get_recientes
from app.views.restaurante_dialog import RestauranteDialog, pixmap_logo

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
from app.views.modulos.etiquetas_view import EtiquetasView
from app.views.dashboard import DashboardView
from app.views.modulos.consolidados_view import ConsolidadosView
from app.views.modulos.sucursales_crud import SucursalesCRUD
from app.views.modulos.grafico_precios import GraficoPreciosView
from app.views.modulos.planilla import PlanillaView
from app.views.modulos.rentabilidad_view import RentabilidadView
from app.views.modulos.costo_platos import CostoPlatosView
from app.utils.plataforma import ruta_recurso

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




class MainWindow(QMainWindow):
    def __init__(self, db_manager, auth_controller):
        super().__init__()
        self.db = db_manager
        self.auth = auth_controller
        self.logout_requested = False
        self.modules = {}
        self._modulo_actual = None  # clave del módulo a la vista (para F1)
        self._ayuda_dialog = None
        self.sidebar_collapsed = False
        self._nav_buttons = []  # list of {"btn": QPushButton, "text": str}

        self.setWindowIcon(QIcon(ruta_recurso("assets/icons/app.ico")))

        self.init_ui()
        self.setup_menubar()
        self.setup_statusbar()
        self.aplicar_identidad()
        self._fit_to_screen()

    # ------------------------------------------------------------------
    # Identidad del restaurante (de la base de datos abierta)
    # ------------------------------------------------------------------
    def aplicar_identidad(self):
        """Muestra en título, menú lateral y barra de estado qué restaurante es el que se está viendo."""
        ctrl = RestauranteController(self.db)
        ident = ctrl.identidad()
        self.etiqueta_restaurante = ctrl.etiqueta(ident)
        self.setWindowTitle(f"{self.etiqueta_restaurante} — Italos Manager {etiqueta_version()}")
        self.lbl_sidebar_header.setPixmap(pixmap_logo(ident["logo"], 168, 46))
        sucursal = f"<br><span style='font-size:11px'>{ident['sucursal']}</span>" if ident["sucursal"] else ""
        self.lbl_restaurante.setText(f"<b>{ident['nombre']}</b>{sucursal}")
        self.lbl_restaurante.setToolTip(self.etiqueta_restaurante)
        self.sidebar_frame.setToolTip(self.etiqueta_restaurante if self.sidebar_collapsed else "")
        self.actualizar_info_bd()
        try:
            agregar_reciente(self.db.db_path, self.etiqueta_restaurante)
        except OSError:
            pass  # la lista de recientes es una comodidad: no debe impedir trabajar

    def _fit_to_screen(self):
        """Tamaño inicial según la pantalla: centrada en monitores amplios, maximizada en los chicos.

        La ventana nunca exige más que la pantalla: el menú lateral y cada módulo tienen scroll propio
        (antes el menú obligaba a ~1130 px de alto y se cortaba en laptops y monitores 16:9 con escala)."""
        screen = QApplication.primaryScreen().availableGeometry()
        w = min(1400, int(screen.width() * 0.94))
        h = min(900, int(screen.height() * 0.94))
        self.resize(w, h)
        self.move(
            screen.x() + (screen.width() - w) // 2,
            screen.y() + (screen.height() - h) // 2,
        )
        if screen.width() < 1400 or screen.height() < 860:
            self.setWindowState(self.windowState() | Qt.WindowMaximized)

    def setup_menubar(self):
        menu_rest = self.menuBar().addMenu("&Restaurante")
        self.menu_cambiar = menu_rest.addMenu("Cambiar de restaurante")
        self.menu_cambiar.aboutToShow.connect(self._llenar_menu_cambiar)
        if self.auth.rol == "admin":
            act_datos = QAction("Datos del restaurante…", self)
            act_datos.setStatusTip("Nombre, sucursal de esta instalación, logo y datos para los reportes")
            act_datos.triggered.connect(self.editar_restaurante)
            menu_rest.addAction(act_datos)

        menu_ayuda = self.menuBar().addMenu("&Ayuda")

        act_modulo = QAction("Ayuda de este módulo", self)
        act_modulo.setShortcut(QKeySequence("F1"))
        act_modulo.setStatusTip("Explica cómo usar el módulo que tiene abierto")
        act_modulo.triggered.connect(lambda: self.mostrar_ayuda(self._modulo_actual))
        menu_ayuda.addAction(act_modulo)

        act_indice = QAction("Índice de ayuda…", self)
        act_indice.setShortcut(QKeySequence("Ctrl+F1"))
        act_indice.setStatusTip("Guía de todos los módulos, con buscador")
        act_indice.triggered.connect(lambda: self.mostrar_ayuda(ayuda.TEMA_POR_DEFECTO))
        menu_ayuda.addAction(act_indice)

        menu_ayuda.addSeparator()
        act_acerca = QAction("Acerca de Italos Manager…", self)
        act_acerca.setStatusTip("Versión de la aplicación y base de datos en uso")
        act_acerca.triggered.connect(self.mostrar_acerca_de)
        act_acerca.setMenuRole(QAction.AboutRole)  # macOS: va al menú de la aplicación
        menu_ayuda.addAction(act_acerca)

    def _llenar_menu_cambiar(self):
        self.menu_cambiar.clear()
        actual = os.path.normcase(os.path.abspath(self.db.db_path))
        for r in get_recientes():
            act = self.menu_cambiar.addAction(r["nombre"])
            act.setStatusTip(r["ruta"])
            if os.path.normcase(r["ruta"]) == actual:
                act.setCheckable(True)
                act.setChecked(True)
                act.setEnabled(False)
            else:
                act.triggered.connect(lambda _=False, ruta=r["ruta"]: self.cambiar_de_restaurante(ruta))
        self.menu_cambiar.addSeparator()
        otra = self.menu_cambiar.addAction("Abrir otra base de datos…")
        otra.triggered.connect(lambda: self.cambiar_de_restaurante(None))

    def cambiar_de_restaurante(self, ruta=None):
        """Abre la base de otro restaurante. Cierra la sesión: los usuarios son de cada base."""
        if ruta is None:
            ruta, _ = QFileDialog.getOpenFileName(self, "Abrir base de datos de otro restaurante", "",
                                                  "SQLite Files (*.db)")
            if not ruta:
                return
        resp = QMessageBox.question(
            self, "Cambiar de restaurante",
            "Se cerrará la sesión y deberá ingresar con un usuario del otro restaurante.\n\n¿Continuar?",
            QMessageBox.Yes | QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        self._abrir_otra_bd(ruta)

    def _abrir_otra_bd(self, ruta):
        try:
            self.db.switch_database(ruta)
        except ValueError as e:
            QMessageBox.warning(self, "No se cambió la base de datos",
                                f"{e}\n\nSe sigue usando la base de datos anterior.")
            return False
        self.logout()  # vuelve al inicio de sesión de la base nueva
        return True

    def editar_restaurante(self):
        if RestauranteDialog(self.db, self).exec_():
            self.aplicar_identidad()
            suc = self.modules.get("sucursales")
            if suc:
                suc["instance"].cargar_datos()

    def mostrar_acerca_de(self):
        ruta_bd = getattr(self.db, "db_path", "—")
        QMessageBox.about(
            self,
            "Acerca de Italos Manager",
            "<h3>Italos Manager</h3>"
            "Sistema de gestión de restaurante.<br><br>"
            f"<b>Restaurante:</b> {getattr(self, 'etiqueta_restaurante', '—')}<br>"
            f"<b>Versión:</b> {etiqueta_version()}<br>"
            f"<b>Base de datos en uso:</b> {ruta_bd}<br><br>"
            "Indique esta versión cuando reporte un problema.",
        )

    def mostrar_ayuda(self, clave=None):
        """Abre la ventana de ayuda en el tema indicado (por defecto, primeros pasos)."""
        if self._ayuda_dialog is None:
            self._ayuda_dialog = AyudaDialog(self)
        self._ayuda_dialog.mostrar_tema(clave or ayuda.TEMA_POR_DEFECTO)

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

        # Versión de la aplicación (a la derecha, junto al crédito de GitHub)
        lbl_version = QLabel(etiqueta_version())
        lbl_version.setToolTip("Versión de Italos Manager (Ayuda → Acerca de)")
        lbl_version.setStyleSheet("font-size: 11px; font-weight: normal; color: #555555; padding-right: 10px;")
        sb.addPermanentWidget(lbl_version)

        sb.addPermanentWidget(gh_widget)

        self.actualizar_info_bd()

    def actualizar_info_bd(self):
        user_display = self.auth.current_user
        if isinstance(user_display, (list, tuple)) and len(user_display) > 1:
            username = user_display[1]
        else:
            username = "Desconocido"

        ruta_bd = getattr(self.db, "db_path", "Ruta Desconocida")
        restaurante = getattr(self, "etiqueta_restaurante", "")
        self.statusBar().showMessage(
            (f"Restaurante: {restaurante}  |  " if restaurante else "")
            + f"Usuario: {username}  |  Base de Datos Activa: {ruta_bd}"
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
        self.sidebar_frame.setObjectName("sidebar")
        self.sidebar_frame.setStyleSheet(
            "QFrame#sidebar { background-color: #ffffff; border-right: 2px solid #f0e0e2; }"
        )
        sidebar_layout = QVBoxLayout(self.sidebar_frame)
        sidebar_layout.setContentsMargins(8, 12, 8, 12)
        sidebar_layout.setSpacing(4)

        # Header row: title + toggle button
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)

        self.lbl_sidebar_header = QLabel()  # logo del restaurante (aplicar_identidad)
        self.lbl_sidebar_header.setAlignment(Qt.AlignCenter)
        header_row.addWidget(self.lbl_sidebar_header)

        self.btn_toggle_sidebar = QPushButton()
        self.btn_toggle_sidebar.setIcon(icono_flecha(-1, "#a20f22"))
        self.btn_toggle_sidebar.setIconSize(QSize(14, 14))
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

        # Qué restaurante y sucursal se está viendo (de la base de datos abierta)
        self.lbl_restaurante = QLabel()
        self.lbl_restaurante.setAlignment(Qt.AlignCenter)
        self.lbl_restaurante.setWordWrap(True)
        self.lbl_restaurante.setTextFormat(Qt.RichText)
        self.lbl_restaurante.setStyleSheet(
            "color: #a20f22; font-size: 13px; background: #fff0f1; border: 1px solid #f0d0d4;"
            "border-radius: 6px; padding: 4px 6px; margin-top: 4px;")
        sidebar_layout.addWidget(self.lbl_restaurante)
        sidebar_layout.addSpacing(6)

        # Los botones del menú van en un área con scroll: en pantallas bajas el menú se desplaza en lugar
        # de obligar a la ventana a ser más alta que la pantalla. Logo y «Cerrar Sesión» quedan fijos.
        sidebar_fijo = sidebar_layout
        nav_widget = QWidget()
        nav_widget.setObjectName("sidebarNav")
        nav_widget.setStyleSheet("QWidget#sidebarNav { background: transparent; }")
        sidebar_layout = QVBoxLayout(nav_widget)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(2)
        self.nav_scroll = QScrollArea()
        self.nav_scroll.setWidgetResizable(True)
        self.nav_scroll.setFrameShape(QFrame.NoFrame)
        self.nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.nav_scroll.setStyleSheet(
            "QScrollArea { background: transparent; }"
            "QScrollBar:vertical { width: 6px; background: transparent; margin: 0; }"
            "QScrollBar::handle:vertical { background: #e0c0c3; border-radius: 3px; min-height: 30px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
        )
        self.nav_scroll.setWidget(nav_widget)

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

        self.btn_etiquetas = self.create_nav_button(
            "Etiquetas / Códigos", "assets/icons/nav_etiquetas.svg", self.show_etiquetas
        )
        sidebar_layout.addWidget(self.btn_etiquetas)

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

        self.btn_rentabilidad = self.create_nav_button(
            "Rentabilidad", "assets/icons/nav_rentabilidad.svg", self.show_rentabilidad
        )
        sidebar_layout.addWidget(self.btn_rentabilidad)

        self.btn_costo_platos = self.create_nav_button(
            "Costo de Platos", "assets/icons/nav_costo_platos.svg", self.show_costo_platos
        )
        sidebar_layout.addWidget(self.btn_costo_platos)

        self.btn_grafico_precios = self.create_nav_button(
            "Análisis de Precios", "assets/icons/nav_grafico_precios.svg", self.show_grafico_precios
        )
        sidebar_layout.addWidget(self.btn_grafico_precios)

        self.btn_planilla = self.create_nav_button(
            "Planilla", "assets/icons/nav_planilla.svg", self.show_planilla
        )
        sidebar_layout.addWidget(self.btn_planilla)

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

        # Permisos por rol: se ocultan los módulos que el rol no puede ver
        for modulo, btn in (
            ("dashboard", self.btn_inicio), ("presupuestos", self.btn_presupuestos),
            ("consolidados", self.btn_consolidados), ("rentabilidad", self.btn_rentabilidad),
            ("costo_platos", self.btn_costo_platos), ("grafico_precios", self.btn_grafico_precios),
            ("planilla", self.btn_planilla), ("sucursales", self.btn_sucursales),
        ):
            btn.setVisible(puede_ver(self.auth.rol, modulo))

        if self.auth.rol == "admin":
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

        sidebar_layout = sidebar_fijo
        sidebar_layout.addWidget(self.nav_scroll, 1)
        sidebar_layout.addSpacing(6)

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

        if puede_ver(self.auth.rol, "dashboard"):
            self.btn_inicio.setChecked(True)
            self.show_dashboard()
        else:
            self.btn_ventas.setChecked(True)
            self.show_ventas()

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
        self.btn_toggle_sidebar.setIcon(icono_flecha(1 if self.sidebar_collapsed else -1, "#a20f22"))

        # Show/hide text elements
        self.lbl_sidebar_header.setVisible(not self.sidebar_collapsed)
        self.lbl_restaurante.setVisible(not self.sidebar_collapsed)
        self.sidebar_frame.setToolTip(getattr(self, "etiqueta_restaurante", "") if self.sidebar_collapsed else "")
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
                # Los usuarios son de cada base: se vuelve al inicio de sesión de la base nueva
                self._abrir_otra_bd(path)

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
        if not puede_ver(self.auth.rol, name):
            return
        if name not in self.modules:
            instance = widget_class(self.db) if needs_db else widget_class()
            if hasattr(instance, "set_rol"):
                instance.set_rol(self.auth.rol)
            if hasattr(instance, "identidad_cambiada"):
                instance.identidad_cambiada.connect(self.aplicar_identidad)
            auto_icon_buttons(instance)
            # Cada módulo va en un área con scroll: si no cabe (laptop, escala de Windows alta) se desplaza
            # en lugar de agrandar la ventana más allá de la pantalla
            marco = QScrollArea()
            marco.setWidgetResizable(True)
            marco.setFrameShape(QFrame.NoFrame)
            marco.setWidget(instance)
            index = self.stacked_widget.addWidget(marco)
            self.modules[name] = {"instance": instance, "index": index, "title": title}

        module_data = self.modules[name]
        self._modulo_actual = name
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

    def show_etiquetas(self):
        self.load_module("etiquetas", EtiquetasView, "Etiquetas y Códigos", needs_db=True)

    def show_menu(self):
        self.load_module("menu", MenuCRUD, "Gestión de Menú", needs_db=True)

    def show_recetas(self):
        self.load_module("recetas", RecetasCRUD, "Gestión de Recetas", needs_db=True)

    def show_presupuestos(self):
        self.load_module("presupuestos", PresupuestosView, "Gestión de Presupuestos", needs_db=True)

    def show_consolidados(self):
        self.load_module("consolidados", ConsolidadosView, "Módulo de Consolidados", needs_db=True)

    def show_rentabilidad(self):
        self.load_module("rentabilidad", RentabilidadView, "Análisis de Rentabilidad", needs_db=True)

    def show_costo_platos(self):
        self.load_module("costo_platos", CostoPlatosView, "Costo de Platos", needs_db=True)

    def show_grafico_precios(self):
        self.load_module("grafico_precios", GraficoPreciosView, "Análisis de Precios", needs_db=True)

    def show_planilla(self):
        self.load_module("planilla", PlanillaView, "Módulo de Planilla", needs_db=True)

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

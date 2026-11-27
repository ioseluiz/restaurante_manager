import sys
import os
import ctypes
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFrame,
    QComboBox,
    QFileDialog,
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QIcon, QPainter, QBrush, QPen, QPainterPath, QPixmap, QColor

from app.styles import COLORS
from app.controllers.restaurante_controller import RestauranteController
from app.database.config import agregar_reciente, get_recientes

_ABRIR_OTRA = "__abrir_otra__"

# #a20f22 en formato COLORREF Windows (0x00BBGGRR): R=0xA2, G=0x0F, B=0x22
_RED_COLORREF = ctypes.c_uint(0x220FA2)
_WHITE_COLORREF = ctypes.c_uint(0xFFFFFF)
_DWMWA_CAPTION_COLOR = 35
_DWMWA_TEXT_COLOR = 36


def _apply_dwm_colors(hwnd):
    try:
        dwm = ctypes.windll.dwmapi
        dwm.DwmSetWindowAttribute(hwnd, _DWMWA_CAPTION_COLOR, ctypes.byref(_RED_COLORREF), ctypes.sizeof(_RED_COLORREF))
        dwm.DwmSetWindowAttribute(hwnd, _DWMWA_TEXT_COLOR, ctypes.byref(_WHITE_COLORREF), ctypes.sizeof(_WHITE_COLORREF))
    except Exception:
        pass


def ruta_recurso(ruta_relativa):
    # Detecta si la aplicacion esta congelada por PyInstaller
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, ruta_relativa)
    return os.path.join(os.path.abspath("."), ruta_relativa)


class CircularImageLabel(QLabel):
    def __init__(self, image_path, size=160, border_width=6, border_color=COLORS["primary"], bg_color=COLORS["background"]):
        super().__init__()
        self._size = size
        self._border_width = border_width
        self._border_color = QColor(border_color)
        self._bg_color = QColor(bg_color)
        self._pixmap = QPixmap(image_path)
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        s = self._size
        bw = self._border_width

        painter.setBrush(QBrush(self._bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, s, s)

        inner = s - 2 * bw
        clip_path = QPainterPath()
        clip_path.addEllipse(bw, bw, inner, inner)
        painter.setClipPath(clip_path)

        if not self._pixmap.isNull():
            scaled = self._pixmap.scaled(inner, inner, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x = bw + (inner - scaled.width()) // 2
            y = bw + (inner - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

        painter.setClipping(False)

        pen = QPen(self._border_color, bw)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        half = bw / 2
        painter.drawEllipse(QRectF(half, half, s - bw, s - bw))


def alto_libre_pantalla():
    pantalla = QApplication.primaryScreen()
    return pantalla.availableGeometry().height() if pantalla else 900


class LoginWindow(QDialog):
    def __init__(self, auth_controller):
        super().__init__()
        self.auth = auth_controller
        self.setWindowIcon(QIcon(ruta_recurso("assets/icons/app.ico")))
        # Pantallas bajas (laptops, escala de Windows alta): imagen y márgenes más chicos
        self._compacto = alto_libre_pantalla() < 760
        self.init_ui()
        self.mostrar_restaurante()
        # El alto se ajusta al contenido (antes era fijo y el contenido no cabía)
        self.setFixedSize(420, self.layout().sizeHint().height())

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 16 if self._compacto else 30, 50, 16 if self._compacto else 30)
        layout.setSpacing(6 if self._compacto else 12)

        img_label = CircularImageLabel(
            ruta_recurso("assets/imgs/restaurant.png"),
            size=80 if self._compacto else 150,
            border_color="#a20f22",
            bg_color="#000000",
        )
        layout.addWidget(img_label, alignment=Qt.AlignCenter)

        # Nombre del restaurante de la base abierta (mostrar_restaurante)
        self.lbl_titulo = QLabel()
        self.lbl_titulo.setAlignment(Qt.AlignCenter)
        self.lbl_titulo.setWordWrap(True)
        self.lbl_titulo.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {COLORS['text']}; margin: 8px 0 0 0;"
        )
        layout.addWidget(self.lbl_titulo)
        self.lbl_sucursal = QLabel()
        self.lbl_sucursal.setAlignment(Qt.AlignCenter)
        self.lbl_sucursal.setStyleSheet("font-size: 13px; color: #a20f22; margin: 0 0 10px 0;")
        layout.addWidget(self.lbl_sucursal)

        layout.addWidget(QLabel("Restaurante:"))
        self.cmb_restaurante = QComboBox()
        self.cmb_restaurante.setToolTip("Restaurantes abiertos antes en este equipo. Cada uno tiene su propia "
                                        "base de datos y sus propios usuarios.")
        self.cmb_restaurante.activated.connect(self._elegir_restaurante)
        layout.addWidget(self.cmb_restaurante)

        layout.addWidget(QLabel("Usuario:"))
        self.txt_user = QLineEdit()
        self.txt_user.setPlaceholderText("Ingrese su usuario")
        self.txt_user.returnPressed.connect(self.txt_pass_focus)
        layout.addWidget(self.txt_user)

        layout.addWidget(QLabel("Contraseña:"))
        self.txt_pass = QLineEdit()
        self.txt_pass.setEchoMode(QLineEdit.Password)
        self.txt_pass.setPlaceholderText("Ingrese su contraseña")
        self.txt_pass.returnPressed.connect(self.attempt_login)
        layout.addWidget(self.txt_pass)

        layout.addSpacing(8)

        self.btn_login = QPushButton("Ingresar")
        self.btn_login.setProperty("skip-auto-icon", True)
        self.btn_login.setFixedHeight(46)
        self.btn_login.setStyleSheet(
            "QPushButton { background-color: #a20f22; color: white; border-radius: 6px; }"
            "QPushButton:hover { background-color: #7d0b1a; }"
            "QPushButton:pressed { background-color: #5e0814; }"
        )
        self.btn_login.clicked.connect(self.attempt_login)
        layout.addWidget(self.btn_login)

        layout.addStretch()

        # --- FOOTER ---
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(sep)

        footer_row = QHBoxLayout()
        footer_row.setContentsMargins(0, 4, 0, 0)
        footer_row.setSpacing(6)
        footer_row.addStretch()

        gh_icon = QLabel()
        gh_px = QPixmap(ruta_recurso("assets/icons/github.svg"))
        if not gh_px.isNull():
            gh_px = gh_px.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        gh_icon.setPixmap(gh_px)
        footer_row.addWidget(gh_icon)

        lbl_gh = QLabel('<a href="https://github.com/ioseluiz" style="color:#555555; text-decoration:none;">ioseluiz</a>')
        lbl_gh.setOpenExternalLinks(True)
        lbl_gh.setStyleSheet("font-size: 11px; color: #555555;")
        footer_row.addWidget(lbl_gh)

        layout.addLayout(footer_row)

        self.setLayout(layout)

    def mostrar_restaurante(self):
        """Título, sucursal y selector según la base de datos abierta."""
        db = self.auth.db
        ctrl = RestauranteController(db)
        ident = ctrl.identidad()
        etiqueta = ctrl.etiqueta(ident)
        self.setWindowTitle(f"Iniciar sesión — {etiqueta}")
        self.lbl_titulo.setText(ident["nombre"])
        self.lbl_sucursal.setText(ident["sucursal"])
        self.lbl_sucursal.setVisible(bool(ident["sucursal"]))
        try:
            agregar_reciente(db.db_path, etiqueta)
        except OSError:
            pass
        self.cmb_restaurante.blockSignals(True)
        self.cmb_restaurante.clear()
        for r in get_recientes():
            self.cmb_restaurante.addItem(r["nombre"], r["ruta"])
            self.cmb_restaurante.setItemData(self.cmb_restaurante.count() - 1, r["ruta"], Qt.ToolTipRole)
        if self.cmb_restaurante.count() == 0:  # sin config escribible: al menos la base abierta
            self.cmb_restaurante.addItem(etiqueta, db.db_path)
        self.cmb_restaurante.addItem("Abrir otra base de datos…", _ABRIR_OTRA)
        self.cmb_restaurante.setCurrentIndex(0)
        self.cmb_restaurante.blockSignals(False)

    def _elegir_restaurante(self, indice):
        ruta = self.cmb_restaurante.itemData(indice)
        if ruta == _ABRIR_OTRA:
            ruta, _ = QFileDialog.getOpenFileName(self, "Abrir base de datos de otro restaurante", "",
                                                  "SQLite Files (*.db)")
        if ruta and os.path.normcase(os.path.abspath(ruta)) != os.path.normcase(os.path.abspath(self.auth.db.db_path)):
            try:
                self.auth.db.switch_database(ruta)
            except ValueError as e:
                QMessageBox.warning(self, "No se cambió la base de datos",
                                    f"{e}\n\nSe sigue usando la base de datos anterior.")
        self.mostrar_restaurante()
        self.txt_user.setFocus()

    def showEvent(self, event):
        super().showEvent(event)
        _apply_dwm_colors(int(self.winId()))

    def txt_pass_focus(self):
        self.txt_pass.setFocus()

    def attempt_login(self):
        user = self.txt_user.text()
        pwd = self.txt_pass.text()

        if self.auth.login(user, pwd):
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Credenciales incorrectas")

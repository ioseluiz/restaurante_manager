"""Datos del restaurante (nombre, sucursal de esta instalación, logo, RUC...) y asistente de primer arranque."""

from PyQt5.QtCore import QBuffer, QByteArray, QIODevice, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QVBoxLayout,
)

from app.controllers.restaurante_controller import RestauranteController
from app.utils.button_icons import ruta_recurso

LOGO_POR_DEFECTO = "assets/imgs/italos_horizontal_transparente.png"
LOGO_MAX_W, LOGO_MAX_H = 336, 92  # el doble del tamaño en el menú lateral (168×46), para pantallas HiDPI


def preparar_logo(ruta):
    """Lee una imagen, la reduce a LOGO_MAX_W×LOGO_MAX_H como máximo y la devuelve como bytes PNG."""
    img = QImage(ruta)
    if img.isNull():
        raise ValueError("No se pudo leer la imagen. Use un archivo PNG, JPG o BMP.")
    if img.width() > LOGO_MAX_W or img.height() > LOGO_MAX_H:
        img = img.scaled(LOGO_MAX_W, LOGO_MAX_H, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    datos = QByteArray()
    buf = QBuffer(datos)
    buf.open(QIODevice.WriteOnly)
    img.save(buf, "PNG")
    buf.close()
    return bytes(datos)


def pixmap_logo(datos, ancho, alto):
    """Pixmap del logo propio (bytes) o, si no hay, el de Italos, escalado a ancho×alto."""
    px = QPixmap()
    if not (datos and px.loadFromData(datos)):
        px = QPixmap(ruta_recurso(LOGO_POR_DEFECTO))
    if not px.isNull():
        px = px.scaled(ancho, alto, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return px


class RestauranteDialog(QDialog):
    """Edita la identidad del restaurante. En el primer arranque se presenta como asistente («Más tarde»)."""

    def __init__(self, db, parent=None, primer_arranque=False):
        super().__init__(parent)
        self.db = db
        self.ctrl = RestauranteController(db)
        self._logo = None
        self.setWindowTitle("Configurar este restaurante" if primer_arranque else "Datos del restaurante")
        self.setMinimumWidth(460)
        self._build(primer_arranque)
        self._cargar()

    def _build(self, primer_arranque):
        lay = QVBoxLayout(self)
        if primer_arranque:
            intro = QLabel(
                "<b>Bienvenido.</b> Indique qué restaurante y qué sucursal usa esta instalación. El nombre se "
                "muestra en la ventana, el inicio de sesión y los reportes, para saber siempre qué restaurante "
                "está viendo. Puede cambiarlo después en <i>Sucursales → Datos del restaurante</i>.")
            intro.setWordWrap(True)
            lay.addWidget(intro)

        form = QFormLayout()
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej.: Italos, Pizzería Roma…")
        self.cmb_sucursal = QComboBox()
        self.cmb_sucursal.setEditable(True)
        self.cmb_sucursal.setToolTip("Elija una sucursal registrada o escriba una nueva. Queda marcada como la "
                                     "sucursal de ESTA instalación.")
        self.txt_ruc = QLineEdit()
        self.txt_direccion = QLineEdit()
        self.txt_telefono = QLineEdit()
        form.addRow("Nombre del restaurante:", self.txt_nombre)
        form.addRow("Sucursal de esta instalación:", self.cmb_sucursal)
        form.addRow("RUC (opcional):", self.txt_ruc)
        form.addRow("Dirección (opcional):", self.txt_direccion)
        form.addRow("Teléfono (opcional):", self.txt_telefono)

        self.lbl_logo = QLabel()
        self.lbl_logo.setFixedSize(176, 54)
        self.lbl_logo.setAlignment(Qt.AlignCenter)
        self.lbl_logo.setStyleSheet("border: 1px dashed #ccc; background: white;")
        btn_cargar = QPushButton("Cargar logo…")
        btn_cargar.clicked.connect(self._elegir_logo)
        self.btn_quitar = QPushButton("Usar el de Italos")
        self.btn_quitar.setToolTip("Quita el logo propio y vuelve al logo de Italos")
        self.btn_quitar.clicked.connect(self._quitar_logo)
        fila_logo = QHBoxLayout()
        fila_logo.addWidget(self.lbl_logo)
        col = QVBoxLayout()
        col.addWidget(btn_cargar)
        col.addWidget(self.btn_quitar)
        fila_logo.addLayout(col)
        fila_logo.addStretch()
        form.addRow("Logo:", fila_logo)
        lay.addLayout(form)

        botones = QHBoxLayout()
        botones.addStretch()
        btn_guardar = QPushButton("Guardar")
        btn_guardar.setProperty("class", "btn-success")
        btn_guardar.clicked.connect(self.guardar)
        btn_cancelar = QPushButton("Más tarde" if primer_arranque else "Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        botones.addWidget(btn_guardar)
        botones.addWidget(btn_cancelar)
        lay.addLayout(botones)

    def _cargar(self):
        ident = self.ctrl.identidad()
        self.txt_nombre.setText(ident["nombre"] if ident["configurado"] else "")
        nombres = [r[0] for r in self.db.fetch_all("SELECT nombre FROM sucursales ORDER BY nombre")]
        self.cmb_sucursal.addItems(nombres)
        self.cmb_sucursal.setCurrentText(ident["sucursal"])
        self.txt_ruc.setText(ident["ruc"])
        self.txt_direccion.setText(ident["direccion"])
        self.txt_telefono.setText(ident["telefono"])
        self._logo = ident["logo"]
        self._refrescar_logo()

    def _refrescar_logo(self):
        self.lbl_logo.setPixmap(pixmap_logo(self._logo, 168, 46))
        self.btn_quitar.setEnabled(self._logo is not None)

    def _elegir_logo(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Elegir logo", "", "Imágenes (*.png *.jpg *.jpeg *.bmp)")
        if not ruta:
            return
        try:
            self._logo = preparar_logo(ruta)
        except ValueError as e:
            QMessageBox.warning(self, "Logo", str(e))
            return
        self._refrescar_logo()

    def _quitar_logo(self):
        self._logo = None
        self._refrescar_logo()

    def guardar(self):
        try:
            self.ctrl.guardar(self.txt_nombre.text(), self.txt_ruc.text(), self.txt_direccion.text(),
                              self.txt_telefono.text(), sucursal=self.cmb_sucursal.currentText())
        except ValueError as e:
            QMessageBox.warning(self, "Datos del restaurante", str(e))
            return
        self.ctrl.guardar_logo(self._logo)
        self.accept()


def asistente_si_falta(db, rol, parent=None):
    """Abre el asistente si esta base aún no tiene nombre de restaurante y quien entra es administrador.

    Devuelve True si se guardaron datos."""
    if rol != "admin" or RestauranteController(db).identidad()["configurado"]:
        return False
    return RestauranteDialog(db, parent, primer_arranque=True).exec_() == QDialog.Accepted

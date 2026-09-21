# [FILE: app/views/ayuda_dialog.py]
"""Ventana de ayuda: índice de módulos con buscador a la izquierda y el tema en Markdown a la derecha."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.utils import ayuda

_CSS = """
h1 { color: #a20f22; }
h2 { color: #2c3e50; margin-top: 18px; }
h3 { color: #a20f22; }
a  { color: #2980b9; }
blockquote { color: #7f8c8d; }
"""


class AyudaDialog(QDialog):
    """No modal: el usuario puede tener la ayuda abierta mientras trabaja en el módulo."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ayuda — Italos Manager")
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
        self.resize(1000, 680)

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(10, 10, 10, 10)

        izq = QWidget()
        izq_lay = QVBoxLayout(izq)
        izq_lay.setContentsMargins(0, 0, 6, 0)
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar en la ayuda…")
        self.txt_buscar.setClearButtonEnabled(True)
        self.txt_buscar.textChanged.connect(self._filtrar)
        self.lista = QListWidget()
        self.lista.currentItemChanged.connect(self._al_elegir)
        self.lbl_vacio = QLabel("Sin resultados")
        self.lbl_vacio.setStyleSheet("color:#7f8c8d; padding:6px;")
        self.lbl_vacio.hide()
        izq_lay.addWidget(self.txt_buscar)
        izq_lay.addWidget(self.lista, 1)
        izq_lay.addWidget(self.lbl_vacio)

        self.visor = QTextBrowser()
        self.visor.setOpenLinks(False)  # los enlaces ayuda:<tema> se manejan aquí
        self.visor.anchorClicked.connect(self._al_hacer_clic_enlace)
        self.visor.document().setDefaultStyleSheet(_CSS)
        self.visor.setStyleSheet("QTextBrowser { background:#ffffff; color:#2c3e50; padding:8px; }")

        split = QSplitter(Qt.Horizontal)
        split.addWidget(izq)
        split.addWidget(self.visor)
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setSizes([260, 740])
        raiz.addWidget(split, 1)

        self._poblar(ayuda.buscar(""))

    # ------------------------------------------------------------------ API
    def mostrar_tema(self, clave):
        """Selecciona el tema (limpiando el buscador si lo tenía oculto) y trae la ventana al frente."""
        if not ayuda.existe(clave):
            clave = ayuda.TEMA_POR_DEFECTO
        if self._fila_de(clave) is None:
            self.txt_buscar.clear()
        fila = self._fila_de(clave)
        if fila is not None:
            self.lista.setCurrentRow(fila)
        self.show()
        self.raise_()
        self.activateWindow()

    # ------------------------------------------------------------ internos
    def _fila_de(self, clave):
        for i in range(self.lista.count()):
            if self.lista.item(i).data(Qt.UserRole) == clave:
                return i
        return None

    def _poblar(self, claves, seleccionar=None):
        self.lista.blockSignals(True)
        self.lista.clear()
        for c in claves:
            it = QListWidgetItem(ayuda.titulo(c))
            it.setData(Qt.UserRole, c)
            self.lista.addItem(it)
        self.lista.blockSignals(False)
        self.lbl_vacio.setVisible(not claves)
        if not claves:
            self.visor.clear()
            return
        fila = self._fila_de(seleccionar) if seleccionar else None
        self.lista.setCurrentRow(fila if fila is not None else 0)

    def _filtrar(self, texto):
        actual = self.lista.currentItem().data(Qt.UserRole) if self.lista.currentItem() else None
        self._poblar(ayuda.buscar(texto), seleccionar=actual)

    def _al_elegir(self, item, _previo=None):
        if item is None:
            return
        self.visor.setMarkdown(ayuda.leer(item.data(Qt.UserRole)))
        self.visor.verticalScrollBar().setValue(0)

    def _al_hacer_clic_enlace(self, url):
        if url.scheme() == "ayuda":
            self.mostrar_tema(url.path() or url.host())
        else:
            from PyQt5.QtGui import QDesktopServices
            QDesktopServices.openUrl(url)

# [FILE: app/views/widgets.py]
"""Widgets reutilizables de la interfaz."""

from PyQt5.QtWidgets import QComboBox, QCompleter
from PyQt5.QtCore import Qt


class SearchableComboBox(QComboBox):
    """QComboBox editable con filtrado 'contiene' e insensible a mayúsculas.

    Reemplazo directo de QComboBox: conserva addItem/currentData/setCurrentIndex.
    No inserta ítems nuevos al escribir (NoInsert) y restaura el texto válido al
    perder foco si lo tecleado no corresponde a ninguna opción.
    """

    def __init__(self, parent=None, placeholder="Escriba para buscar…", start_empty=True):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.lineEdit().setPlaceholderText(placeholder)

        comp = self.completer()
        comp.setCompletionMode(QCompleter.PopupCompletion)
        comp.setFilterMode(Qt.MatchContains)
        comp.setCaseSensitivity(Qt.CaseInsensitive)

        # Arrancar sin selección para que el usuario escriba y filtre desde vacío.
        # Al poblar con addItem, Qt seleccionaría el primer ítem; lo evitamos.
        # (La carga en modo edición hace setCurrentIndex() después de poblar.)
        self._start_empty = start_empty
        if start_empty:
            self.model().rowsInserted.connect(self._reset_seleccion)

    def _reset_seleccion(self, *args):
        self.setCurrentIndex(-1)
        self.setEditText("")

    def focusOutEvent(self, e):
        # Si el texto tecleado no coincide con un ítem, restaurar el del índice actual
        if self.findText(self.currentText(), Qt.MatchFixedString) < 0:
            idx = self.currentIndex()
            self.setEditText(self.itemText(idx) if idx >= 0 else "")
        super().focusOutEvent(e)

import os
import sys

from PyQt5.QtCore import QEvent, QObject, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QMessageBox, QPushButton

_ICON_SIZE = QSize(16, 16)
_ICON_DIR = "assets/icons"


def ruta_recurso(ruta_relativa):
    # Detecta si la aplicacion esta congelada por PyInstaller
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, ruta_relativa)
    return os.path.join(os.path.abspath("."), ruta_relativa)


def _icon(name):
    return QIcon(ruta_recurso(os.path.join(_ICON_DIR, name)))


def _style(bg, hov, prs):
    return (
        f"QPushButton{{background-color:{bg};color:white;border-radius:6px;"
        f"padding:8px 14px;font-weight:bold;border:none;}}"
        f"QPushButton:hover{{background-color:{hov};}}"
        f"QPushButton:pressed{{background-color:{prs};}}"
        f"QPushButton:disabled{{background-color:#cccccc;color:#999999;}}"
    )


# (icon_file, bg, hover, pressed)
_TYPES = {
    "delete":    ("btn_delete.svg",    "#a20f22", "#7d0b1a", "#5e0814"),
    "cancel":    ("btn_cancel.svg",    "#6c757d", "#5a6268", "#495057"),
    "close":     ("btn_close.svg",     "#6c757d", "#5a6268", "#495057"),
    "receive":   ("btn_receive.svg",   "#d0741d", "#b05f16", "#8a4910"),
    "export":    ("btn_export.svg",    "#5a6475", "#454e5c", "#303844"),
    "import_":   ("btn_import.svg",    "#5a6475", "#454e5c", "#303844"),
    "load":      ("btn_load.svg",      "#5a6475", "#454e5c", "#303844"),
    "edit":      ("btn_edit.svg",      "#db9930", "#b8801f", "#8a5f0f"),
    "view":      ("btn_view.svg",      "#a20f22", "#7d0b1a", "#5e0814"),
    "calculate": ("btn_calculate.svg", "#d0741d", "#b05f16", "#8a4910"),
    "save":      ("btn_save.svg",      "#d0741d", "#b05f16", "#8a4910"),
    "new":       ("btn_new.svg",       "#d0741d", "#b05f16", "#8a4910"),
    "refresh":   ("btn_refresh.svg",   "#a20f22", "#7d0b1a", "#5e0814"),
    "confirm":   ("btn_save.svg",      "#d0741d", "#b05f16", "#8a4910"),
    "settings":  ("btn_settings.svg",  "#a20f22", "#7d0b1a", "#5e0814"),
}


def _classify(text: str):
    t = text.lower().strip().lstrip("+- ").strip()
    if not t:
        return None

    # Destructive first — unambiguous
    if any(k in t for k in ("eliminar", "borrar", "remover", "delete")):
        return "delete"
    if any(k in t for k in ("cancelar", "cancel", "limpiar")):
        return "cancel"
    if any(k in t for k in ("cerrar", "close", "salir")):
        return "close"

    # State-change / positive process
    if any(k in t for k in ("recibir", "recibido", "procesar inventario", "marcar como")):
        return "receive"

    # File operations
    if any(k in t for k in ("exportar", "export", "csv", "excel")):
        return "export"
    if any(k in t for k in ("importar", "import")):
        return "import_"
    if any(k in t for k in ("seleccionar archivo", "cargar archivo", "load")):
        return "load"

    # Edit before view so "ver/editar" → edit
    if any(k in t for k in ("editar", "modificar", "edit")):
        return "edit"

    # View / read
    if any(k in t for k in ("detalle", "kardex", "control presup", "ver mov", "ver /", "ver/", "visualiz")):
        return "view"

    # Calculation / generation
    if any(k in t for k in ("calcular", "recalcular", "generar", "ajustar", "llenar", "replicar")):
        return "calculate"

    # Save before new — "guardar y añadir" → save
    if any(k in t for k in ("guardar", "save", "grabar")):
        return "save"

    # New / add
    if any(k in t for k in ("nuevo", "nueva", "agregar", "añadir", "añad", "crear", "definir", "+")):
        return "new"

    # Refresh
    if any(k in t for k in ("actualizar", "refresh", "recargar")):
        return "refresh"

    # Confirm / accept
    if any(k in t for k in ("aplicar", "confirmar", "aceptar", "ingresar")):
        return "confirm"

    # Settings / management
    if any(k in t for k in ("configurar", "gestionar", "gesti")):
        return "settings"

    return None


def auto_icon_buttons(widget, icon_size: QSize = _ICON_SIZE):
    for btn in widget.findChildren(QPushButton):
        if btn.property("skip-auto-icon"):
            continue
        text = btn.text()
        if len(text.strip()) <= 1:  # skip "X", "◀", "▶", etc.
            continue
        kind = _classify(text)
        if kind is None:
            continue
        icon_file, bg, hov, prs = _TYPES[kind]
        btn.setIcon(_icon(icon_file))
        btn.setIconSize(icon_size)
        btn.setStyleSheet(_style(bg, hov, prs))


class ButtonIconFilter(QObject):
    """Intercepts QDialog.Show to auto-apply action button icons on every dialog."""

    def eventFilter(self, obj, event):
        if (
            event.type() == QEvent.Show
            and isinstance(obj, QDialog)
            and not isinstance(obj, QMessageBox)
            and not obj.property("auto-icons-applied")
        ):
            obj.setProperty("auto-icons-applied", True)
            auto_icon_buttons(obj)
        return super().eventFilter(obj, event)

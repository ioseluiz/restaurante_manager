"""Diferencias entre Windows y macOS en un solo lugar: recursos, abrir archivos y apariencia."""

import os
import sys

ES_WINDOWS = sys.platform == "win32"
ES_MAC = sys.platform == "darwin"

# Raíz del proyecto (dos niveles arriba de app/utils), para no depender de la carpeta actual
_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def ruta_recurso(ruta_relativa):
    """Ruta absoluta de un archivo de assets/, tanto desde el código como en el ejecutable de PyInstaller."""
    base = getattr(sys, "_MEIPASS", _RAIZ)
    return os.path.join(base, ruta_relativa)


def abrir_archivo(ruta):
    """Abre un archivo (Excel, PDF...) con la aplicación predeterminada del sistema. Devuelve True si pudo."""
    from PyQt5.QtCore import QUrl
    from PyQt5.QtGui import QDesktopServices

    return bool(QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(ruta))))


def preparar_proceso():
    """Ajustes previos a crear la QApplication."""
    if ES_WINDOWS:
        # Para que la barra de tareas muestre el ícono de la app y no el del intérprete de Python
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("italos.restaurante_manager")
        except (AttributeError, OSError):
            pass


def configurar_app(app):
    """Apariencia uniforme. En macOS fija el estilo Fusion con paleta clara: las hojas de estilo de la app
    son claras y, con el modo oscuro del sistema, Qt mezclaba texto claro sobre fondos blancos."""
    if not ES_MAC:
        return
    from PyQt5.QtGui import QColor, QPalette
    from PyQt5.QtWidgets import QStyleFactory

    app.setStyle(QStyleFactory.create("Fusion"))
    pal = QPalette()
    for rol, color in (
        (QPalette.Window, "#f5f5f5"), (QPalette.WindowText, "#2c3e50"), (QPalette.Base, "#ffffff"),
        (QPalette.AlternateBase, "#f7f7f7"), (QPalette.Text, "#2c3e50"), (QPalette.Button, "#f0f0f0"),
        (QPalette.ButtonText, "#2c3e50"), (QPalette.ToolTipBase, "#ffffdc"), (QPalette.ToolTipText, "#000000"),
        (QPalette.Highlight, "#a20f22"), (QPalette.HighlightedText, "#ffffff"), (QPalette.Link, "#a20f22"),
        (QPalette.PlaceholderText, "#999999"),
    ):
        pal.setColor(rol, QColor(color))
    pal.setColor(QPalette.Disabled, QPalette.Text, QColor("#aaaaaa"))
    pal.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#aaaaaa"))
    pal.setColor(QPalette.Disabled, QPalette.WindowText, QColor("#aaaaaa"))
    app.setPalette(pal)

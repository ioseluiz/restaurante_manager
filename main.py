# main.py
import sys
import os
import ctypes
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtGui import QIcon
from app.database.connection import DatabaseManager
from app.controllers.auth_controller import AuthController
from app.views.login_window import LoginWindow
from app.views.main_window import MainWindow

# IMPORTAMOS LOS ESTILOS
from app.styles import GLOBAL_STYLES
from app.utils.button_icons import ButtonIconFilter


def ruta_recurso(ruta_relativa):
    # Detecta si la aplicacion esta congelada por PyInstaller
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, ruta_relativa)
    return os.path.join(os.path.abspath("."), ruta_relativa)


def main():
    # Necesario para que Windows muestre el ícono de la app en la barra de tareas
    # en lugar del ícono del intérprete de Python
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("italos.restaurante_manager")

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(ruta_recurso("assets/icons/app.ico")))

    # APLICAR TEMA GLOBAL
    app.setStyleSheet(GLOBAL_STYLES)

    # Aplica iconos de acción automáticamente a todos los QDialog
    _btn_icon_filter = ButtonIconFilter(app)
    app.installEventFilter(_btn_icon_filter)

    # 1 Backend setup
    db = DatabaseManager()
    auth = AuthController(db)

    # 2. Flujo de Login con bucle para permitir Cerrar Sesión
    while True:
        login = LoginWindow(auth)

        # Si el login es exitoso
        if login.exec_() == QDialog.Accepted:
            window = MainWindow(db, auth)
            window.show()

            # Ejecuta la aplicación hasta que se cierre la ventana principal
            app.exec_()

            # Al cerrarse la ventana, verificamos si fue por logout
            if getattr(window, "logout_requested", False):
                # Si fue logout, el bucle continúa y vuelve a mostrar el Login
                continue
            else:
                # Si se cerró normalmente (X), rompemos el bucle para salir
                break
        else:
            # Si cancela el login, salimos
            break

    sys.exit()


if __name__ == "__main__":
    main()

# main.py
import sys
from PyQt5.QtWidgets import QApplication, QDialog
from app.database.connection import DatabaseManager
from app.controllers.auth_controller import AuthController
from app.views.login_window import LoginWindow
from app.views.main_window import MainWindow

# IMPORTAMOS LOS ESTILOS
from app.styles import GLOBAL_STYLES


def main():
    app = QApplication(sys.argv)

    # APLICAR TEMA GLOBAL
    app.setStyleSheet(GLOBAL_STYLES)

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

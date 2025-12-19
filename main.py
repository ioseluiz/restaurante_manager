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

    # 2. Flujo de Login
    login = LoginWindow(auth)
    if login.exec_() == QDialog.Accepted:
        window = MainWindow(db, auth)
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit()


if __name__ == "__main__":
    main()

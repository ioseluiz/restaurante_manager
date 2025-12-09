import sys
from PyQt5.QtWidgets import QApplication, QDialog
from app.database.connection import DatabaseManager
from app.controllers.auth_controller import AuthController
from app.views.login_window import LoginWindow
from app.views.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    # 1 Backend setup
    db = DatabaseManager()
    auth = AuthController(db)

    # 2. Flujo de Login
    login = LoginWindow(auth)
    if login.exec_() == QDialog.Accepted:
        # Si el login es exitoso, abrimos la ventana principal
        window = MainWindow(db, auth)
        window.show()
        sys.exit(app.exec_())
    else:
        # Si cierra la ventana de login sin ingresar
        sys.exit()


if __name__ == "__main__":
    main()

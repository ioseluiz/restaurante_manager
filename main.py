# main.py
import sys
import os
from PyQt5 import sip
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtGui import QIcon
from app.views.db_recovery import abrir_base_de_datos
from app.controllers.auth_controller import AuthController
from app.views.login_window import LoginWindow
from app.views.main_window import MainWindow
from app.views.restaurante_dialog import asistente_si_falta

# IMPORTAMOS LOS ESTILOS
from app.styles import GLOBAL_STYLES
from app.utils.button_icons import ButtonIconFilter
from app.utils.plataforma import configurar_app, preparar_proceso, ruta_recurso


def prueba_de_humo(app):
    """`--smoke`: abre login y ventana principal (todos los módulos) sobre una base temporal y sale.

    La usa el CI para comprobar que el ejecutable empaquetado arranca e incluye todo (Qt, matplotlib,
    reportlab, assets). No toca la configuración ni la base del usuario. Código de salida 0 = correcto.

    El ejecutable de Windows no tiene consola: el resultado (y un volcado si se cae) queda también en el
    archivo de ITALOS_SMOKE_LOG o, si no se indica, en <temp>/italos_smoke.log."""
    import faulthandler
    import tempfile
    import traceback

    log = open(os.environ.get("ITALOS_SMOKE_LOG") or os.path.join(tempfile.gettempdir(), "italos_smoke.log"),
               "w", encoding="utf-8")
    faulthandler.enable(file=log, all_threads=True)

    def informar(texto):
        log.write(texto + "\n")
        log.flush()
        if sys.stdout:
            print(texto, flush=True)

    from app.database import config
    from app.database.connection import DatabaseManager

    carpeta = tempfile.mkdtemp(prefix="italos_smoke_")
    config.CONFIG_FILE = os.path.join(carpeta, "config.json")
    try:
        informar(f"inicio (carpeta {carpeta})")
        db = DatabaseManager(os.path.join(carpeta, "smoke.db"))
        auth = AuthController(db)
        LoginWindow(auth)
        assert auth.login("admin", "admin123"), "no entra el admin por defecto"
        window = MainWindow(db, auth)
        for nombre in ("dashboard", "ventas", "compras", "inventario", "conteo", "insumos", "etiquetas",
                       "menu", "recetas", "presupuestos", "consolidados", "rentabilidad", "costo_platos",
                       "grafico_precios", "planilla", "unidades", "sucursales", "usuarios"):
            informar(f"módulo {nombre}")
            getattr(window, f"show_{nombre}")()
        app.processEvents()
        assert ruta_recurso("assets/icons/app.ico") and os.path.exists(ruta_recurso("assets/ayuda/general.md"))
        import reportlab.graphics.barcode.code128  # noqa: F401  (se importa con exec() en reportlab)
        window.close()
        db.conn.close()
    except Exception:
        informar(traceback.format_exc())
        return 1
    informar("SMOKE OK")
    return 0


def salir(app, codigo=0):
    """Cierra la aplicación en orden.

    Al terminar Python, PyQt destruía los objetos de Qt en un orden cualquiera y a veces borraba la
    QApplication antes que sus ventanas: «access violation» / segfault (código 139) DESPUÉS de cerrar, de
    forma intermitente. Se cierran y eliminan las ventanas mientras la QApplication sigue viva y no se
    dejan destructores de C++ para la salida del intérprete."""
    for w in app.topLevelWidgets():
        w.close()
        w.deleteLater()
    app.processEvents()
    sys.stdout and sys.stdout.flush()
    sys.exit(codigo)


def main():
    preparar_proceso()  # Windows: ícono propio en la barra de tareas

    sip.setdestroyonexit(False)  # ver salir(): evita el segfault intermitente al cerrar
    app = QApplication(sys.argv)
    configurar_app(app)  # macOS: estilo y paleta clara aunque el sistema esté en modo oscuro
    app.setWindowIcon(QIcon(ruta_recurso("assets/icons/app.ico")))

    # APLICAR TEMA GLOBAL
    app.setStyleSheet(GLOBAL_STYLES)

    # Aplica iconos de acción automáticamente a todos los QDialog
    _btn_icon_filter = ButtonIconFilter(app)
    app.installEventFilter(_btn_icon_filter)

    if "--smoke" in sys.argv:
        salir(app, prueba_de_humo(app))

    # 1 Backend setup
    db = abrir_base_de_datos()
    if db is None:  # el usuario eligió salir
        salir(app)
    auth = AuthController(db)

    # 2. Flujo de Login con bucle para permitir Cerrar Sesión
    while True:
        login = LoginWindow(auth)

        # Si el login es exitoso
        if login.exec_() == QDialog.Accepted:
            # Base sin nombre de restaurante: el administrador lo configura (o lo deja para más tarde)
            asistente_si_falta(db, auth.rol)
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

    salir(app)


if __name__ == "__main__":
    main()

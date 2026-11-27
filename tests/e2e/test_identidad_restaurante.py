"""La interfaz indica qué restaurante se está viendo, y cambiar de restaurante vuelve a pedir el login."""
import os

from app.controllers.auth_controller import AuthController
from app.controllers.restaurante_controller import RestauranteController
from app.database import config
from app.database.connection import DatabaseManager


def _ventana(db):
    from app.views.main_window import MainWindow

    auth = AuthController(db)
    assert auth.login("admin", "admin123")
    return MainWindow(db, auth)


def test_ventana_y_login_muestran_el_restaurante(db, esc, sin_dialogos):
    from app.views.login_window import LoginWindow

    RestauranteController(db).guardar("Pizzería Roma")  # la sucursal marcada del escenario es «Centro»
    win = _ventana(db)
    try:
        assert win.windowTitle().startswith("Pizzería Roma · Centro — Italos Manager")
        assert "Pizzería Roma" in win.lbl_restaurante.text() and "Centro" in win.lbl_restaurante.text()
        assert "Restaurante: Pizzería Roma · Centro" in win.statusBar().currentMessage()
        assert config.get_recientes()[0]["nombre"] == "Pizzería Roma · Centro"

        # Cambiar el nombre desde Sucursales actualiza la ventana
        win.show_sucursales()
        suc = win.modules["sucursales"]["instance"]
        assert not suc.btn_restaurante.isHidden()  # admin: puede editar
        RestauranteController(db).guardar("Roma Express", sucursal="Norte")
        suc.identidad_cambiada.emit()
        assert win.windowTitle().startswith("Roma Express · Norte")
    finally:
        win.close()

    login = LoginWindow(AuthController(db))
    assert login.lbl_titulo.text() == "Roma Express" and login.lbl_sucursal.text() == "Norte"
    assert login.cmb_restaurante.itemText(0) == "Roma Express · Norte"


def test_gerente_ve_los_datos_del_restaurante_sin_editarlos(db, esc, sin_dialogos):
    from app.controllers.auth_controller import hash_password
    from app.views.main_window import MainWindow

    db.execute_query("INSERT INTO usuarios (username, password_hash, rol) VALUES ('ger', ?, 'gerente')",
                     (hash_password("x"),))
    auth = AuthController(db)
    assert auth.login("ger", "x")
    win = MainWindow(db, auth)
    try:
        win.show_sucursales()
        suc = win.modules["sucursales"]["instance"]
        assert suc.btn_restaurante.isHidden() and "Italos" in suc.lbl_identidad.text()
    finally:
        win.close()


def test_cambiar_de_restaurante_cierra_la_sesion_y_abre_la_otra_base(db, esc, sin_dialogos, tmp_path):
    otra_ruta = str(tmp_path / "otro.db")
    otra = DatabaseManager(otra_ruta)
    RestauranteController(otra).guardar("Sushi Bar", sucursal="Obarrio")
    otra.conn.close()

    win = _ventana(db)
    win.cambiar_de_restaurante(otra_ruta)  # sin_dialogos responde «Sí» a la confirmación
    assert win.logout_requested
    assert os.path.samefile(db.db_path, otra_ruta)
    assert RestauranteController(db).etiqueta() == "Sushi Bar · Obarrio"
    assert config.get_db_path() == otra_ruta


def test_login_cambia_de_restaurante_desde_la_lista(db, esc, sin_dialogos, tmp_path):
    from app.views.login_window import LoginWindow

    otra_ruta = str(tmp_path / "otro.db")
    otra = DatabaseManager(otra_ruta)
    RestauranteController(otra).guardar("Sushi Bar")
    otra.conn.close()
    config.agregar_reciente(otra_ruta, "Sushi Bar")

    login = LoginWindow(AuthController(db))
    idx = login.cmb_restaurante.findText("Sushi Bar")
    assert idx >= 0
    login._elegir_restaurante(idx)
    assert login.lbl_titulo.text() == "Sushi Bar" and os.path.samefile(db.db_path, otra_ruta)
    assert login.cmb_restaurante.itemText(0) == "Sushi Bar"  # la elegida queda primera


def test_logo_grande_se_reduce_y_se_muestra(db, qapp, tmp_path):
    from PyQt5.QtGui import QColor, QImage

    from app.views.restaurante_dialog import LOGO_MAX_H, LOGO_MAX_W, pixmap_logo, preparar_logo

    ruta = str(tmp_path / "logo.png")
    img = QImage(1200, 400, QImage.Format_ARGB32)
    img.fill(QColor("#336699"))
    img.save(ruta)
    datos = preparar_logo(ruta)
    chico = QImage.fromData(datos)
    assert chico.width() <= LOGO_MAX_W and chico.height() <= LOGO_MAX_H and chico.width() == 276
    assert not pixmap_logo(datos, 168, 46).isNull() and not pixmap_logo(None, 168, 46).isNull()

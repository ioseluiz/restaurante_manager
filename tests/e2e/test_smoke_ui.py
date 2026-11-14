"""Humo de la interfaz: la ventana principal abre cada módulo sobre el escenario sin errores."""
import pytest

from app.controllers.auth_controller import AuthController

MODULOS = [
    "dashboard", "ventas", "compras", "inventario", "conteo", "insumos", "etiquetas", "menu", "recetas",
    "presupuestos", "consolidados", "rentabilidad", "costo_platos", "grafico_precios", "planilla",
    "unidades", "sucursales", "usuarios",
]


@pytest.fixture
def ventana(db, esc, sin_dialogos):
    from app.views.main_window import MainWindow

    auth = AuthController(db)
    assert auth.login("admin", "admin123")
    win = MainWindow(db, auth)
    yield win
    win.close()


@pytest.mark.parametrize("modulo", MODULOS)
def test_abre_modulo(ventana, sin_dialogos, modulo):
    getattr(ventana, f"show_{modulo}")()
    assert ventana._modulo_actual is not None
    assert not [m for m in sin_dialogos if m[0] == "critical"]


def _ventana_como(db, usuario, rol):
    from app.controllers.auth_controller import hash_password
    from app.views.main_window import MainWindow

    db.execute_query("INSERT INTO usuarios (username, password_hash, rol) VALUES (?,?,?)",
                     (usuario, hash_password("x"), rol))
    auth = AuthController(db)
    assert auth.login(usuario, "x")
    return MainWindow(db, auth)


def test_empleado_solo_ve_lo_operativo(db, esc, sin_dialogos):
    win = _ventana_como(db, "emp", "empleado")
    try:
        assert win._modulo_actual == "ventas"  # arranca en Ventas, no en el Panel
        assert win.btn_planilla.isHidden() and win.btn_rentabilidad.isHidden() and win.btn_inicio.isHidden()
        assert not win.btn_ventas.isHidden() and not win.btn_conteo.isHidden()
        assert not hasattr(win, "btn_usuarios")
        win.show_planilla()
        assert "planilla" not in win.modules and win._modulo_actual == "ventas"
    finally:
        win.close()


def test_gerente_ve_finanzas_pero_no_usuarios(db, esc, sin_dialogos):
    win = _ventana_como(db, "ger", "gerente")
    try:
        assert win._modulo_actual == "dashboard"
        assert not win.btn_planilla.isHidden() and not win.btn_rentabilidad.isHidden()
        assert not hasattr(win, "btn_usuarios")
        win.show_usuarios()
        assert "usuarios" not in win.modules
    finally:
        win.close()

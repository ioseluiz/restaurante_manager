import hashlib

import pytest

from app.controllers.auth_controller import AuthController, es_hash_antiguo, hash_password, verificar_password
from app.database.connection import DatabaseManager


@pytest.fixture
def db(tmp_path):
    return DatabaseManager(str(tmp_path / "t.db"))


def _hash(db, usuario):
    return db.fetch_one("SELECT password_hash FROM usuarios WHERE username=?", (usuario,))[0]


def test_hash_con_sal_distinta_cada_vez():
    a, b = hash_password("clave"), hash_password("clave")
    assert a != b and not es_hash_antiguo(a)
    assert verificar_password("clave", a) and not verificar_password("otra", a)


def test_admin_por_defecto_entra_con_hash_nuevo(db):
    assert not es_hash_antiguo(_hash(db, "admin"))
    auth = AuthController(db)
    assert auth.login("admin", "admin123")
    assert auth.current_user[1:] == ("admin", "admin")
    assert not AuthController(db).login("admin", "mala")
    assert not AuthController(db).login("nadie", "admin123")


def test_hash_antiguo_se_migra_al_iniciar_sesion(db):
    viejo = hashlib.sha256("secreta".encode()).hexdigest()
    db.execute_query("INSERT INTO usuarios (username, password_hash, rol) VALUES ('ana', ?, 'gerente')", (viejo,))
    assert not AuthController(db).login("ana", "mala")
    assert _hash(db, "ana") == viejo
    assert AuthController(db).login("ana", "secreta")
    assert not es_hash_antiguo(_hash(db, "ana"))
    assert AuthController(db).login("ana", "secreta")


@pytest.mark.parametrize("rol, modulo, esperado", [
    ("admin", "usuarios", True), ("Administrador", "planilla", True),
    ("gerente", "planilla", True), ("gerente", "rentabilidad", True), ("gerente", "usuarios", False),
    ("empleado", "ventas", True), ("empleado", "conteo", True), ("empleado", "insumos", True),
    ("empleado", "planilla", False), ("empleado", "rentabilidad", False), ("empleado", "dashboard", False),
    ("empleado", "presupuestos", False), ("empleado", "consolidados", False), ("empleado", "costo_platos", False),
    ("empleado", "usuarios", False), ("empleado", "sucursales", False), ("gerente", "sucursales", True),
    ("", "planilla", False),
])
def test_permisos_por_rol(rol, modulo, esperado):
    from app.controllers.auth_controller import puede_ver
    assert puede_ver(rol, modulo) is esperado

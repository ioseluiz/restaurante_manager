import hashlib
import hmac
import secrets

_ALGORITMO = "pbkdf2_sha256"
_ITERACIONES = 260000


def hash_password(password):
    """Hash con sal propia: 'pbkdf2_sha256$iteraciones$sal$hash'."""
    sal = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), sal.encode(), _ITERACIONES)
    return f"{_ALGORITMO}${_ITERACIONES}${sal}${dk.hex()}"


def es_hash_antiguo(guardado):
    """True si es el SHA-256 sin sal de versiones anteriores (se migra al iniciar sesión)."""
    return not str(guardado or "").startswith(_ALGORITMO + "$")


def verificar_password(password, guardado):
    guardado = str(guardado or "")
    if es_hash_antiguo(guardado):
        return hmac.compare_digest(hashlib.sha256(password.encode()).hexdigest(), guardado)
    try:
        _alg, iteraciones, sal, esperado = guardado.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), sal.encode(), int(iteraciones))
    except ValueError:
        return False
    return hmac.compare_digest(dk.hex(), esperado)


# Módulos por rol (claves de MainWindow.load_module). El administrador ve todo; el gerente todo
# menos la administración; el empleado solo lo operativo (sin finanzas, costos ni salarios).
MODULOS_SOLO_ADMIN = {"usuarios"}
MODULOS_GERENCIA = {"dashboard", "presupuestos", "consolidados", "rentabilidad", "costo_platos",
                    "grafico_precios", "planilla", "sucursales"}


def normalizar_rol(rol):
    rol = str(rol or "").strip().lower()
    return "admin" if rol == "administrador" else rol


def puede_ver(rol, modulo):
    rol = normalizar_rol(rol)
    if rol == "admin":
        return True
    if modulo in MODULOS_SOLO_ADMIN:
        return False
    if modulo in MODULOS_GERENCIA:
        return rol == "gerente"
    return True


class AuthController:
    def __init__(self, db_manager):
        self.db = db_manager
        self.current_user = None

    def login(self, username, password):
        row = self.db.fetch_one(
            "SELECT id, username, rol, password_hash FROM usuarios WHERE username=?", (username,)
        )
        if not row or not verificar_password(password, row[3]):
            return False
        if es_hash_antiguo(row[3]):
            self.db.execute_query(
                "UPDATE usuarios SET password_hash=? WHERE id=?", (hash_password(password), row[0])
            )
        self.current_user = row[:3]  # (id, username, rol)
        return True

    @property
    def rol(self):
        user = self.current_user
        return normalizar_rol(user[2]) if isinstance(user, (list, tuple)) and len(user) > 2 else ""

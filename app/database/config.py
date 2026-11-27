import json
import os
import sqlite3
from pathlib import Path

# 1. Definimos una carpeta segura y oculta en el directorio "Home" del usuario
APP_DIR = os.path.join(str(Path.home()), ".restaurante_manager")

# 2. Nos aseguramos de que esa carpeta exista
os.makedirs(APP_DIR, exist_ok=True)

# 3. Asignamos rutas absolutas seguras
CONFIG_FILE = os.path.join(APP_DIR, "config.json")
DEFAULT_DB = os.path.join(APP_DIR, "restaurante.db")

CABECERA_SQLITE = b"SQLite format 3\x00"


MAX_RECIENTES = 10


def _leer_config():
    """Contenido de config.json como dict ({} si no existe o es ilegible)."""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            datos = json.load(f)
        return datos if isinstance(datos, dict) else {}
    except (OSError, ValueError):
        return {}


def _escribir_config(datos):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)


def get_db_path():
    # Configuración ausente o ilegible: se cae a la base predeterminada
    return _leer_config().get("db_path") or DEFAULT_DB


def save_db_path(path):
    datos = _leer_config()  # conserva las demás claves (restaurantes recientes)
    datos["db_path"] = path
    _escribir_config(datos)


def _misma_ruta(a, b):
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def get_recientes():
    """Restaurantes abiertos en este equipo: [{"ruta", "nombre"}], el más reciente primero.

    Omite las bases que ya no existen. El nombre es una copia guardada al abrir cada base, para no tener
    que abrirlas todas al armar la lista."""
    lista = _leer_config().get("recientes") or []
    return [r for r in lista
            if isinstance(r, dict) and r.get("ruta") and os.path.exists(r["ruta"])][:MAX_RECIENTES]


def agregar_reciente(ruta, nombre):
    """Pone la base al principio de la lista de recientes (o actualiza su nombre)."""
    datos = _leer_config()
    lista = [r for r in get_recientes() if not _misma_ruta(r["ruta"], ruta)]
    datos["recientes"] = [{"ruta": os.path.abspath(ruta), "nombre": nombre}] + lista[:MAX_RECIENTES - 1]
    _escribir_config(datos)


def validar_base_datos(path):
    """Comprueba que `path` sirva como base de datos ANTES de abrirla o guardarla en la configuración.

    Devuelve (True, "") si es una base SQLite válida, o un archivo vacío / inexistente en una carpeta que
    existe (se creará una base nueva). Devuelve (False, motivo) si no es utilizable; entre otros casos, los
    archivos residuales «._nombre» que macOS deja al copiar a discos no-Mac (parecen .db pero no lo son).
    """
    if not path or not str(path).strip():
        return False, "No se indicó ninguna ruta."
    path = str(path)
    nombre = os.path.basename(path)
    if nombre.startswith("._"):
        return False, (f"«{nombre}» es un archivo residual de macOS (AppleDouble), no una base de datos. "
                       f"Seleccione «{nombre[2:]}» (sin el «._»).")
    if os.path.isdir(path):
        return False, "La ruta indicada es una carpeta, no un archivo de base de datos."
    if not os.path.exists(path):
        carpeta = os.path.dirname(os.path.abspath(path))
        if not os.path.isdir(carpeta):
            return False, f"La carpeta «{carpeta}» no existe."
        return True, ""  # se creará una base nueva
    try:
        if os.path.getsize(path) == 0:
            return True, ""
        with open(path, "rb") as f:
            cabecera = f.read(16)
    except OSError as e:
        return False, f"No se puede leer el archivo: {e}"
    if cabecera != CABECERA_SQLITE:
        return False, ("El archivo no es una base de datos SQLite (puede ser un archivo residual «._» de macOS, "
                       "otro tipo de archivo o estar dañado).")
    try:
        con = sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True)
        try:
            con.execute("SELECT count(*) FROM sqlite_master").fetchone()
        finally:
            con.close()
    except sqlite3.Error as e:
        return False, f"La base de datos está dañada o no se puede abrir: {e}"
    return True, ""

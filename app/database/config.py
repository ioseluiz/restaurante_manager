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


def get_db_path():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f).get("db_path", DEFAULT_DB)
        except (OSError, ValueError):
            return DEFAULT_DB  # configuración ilegible: se cae a la base predeterminada
    return DEFAULT_DB


def save_db_path(path):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"db_path": path}, f)


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

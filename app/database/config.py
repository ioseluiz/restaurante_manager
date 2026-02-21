import json
import os
from pathlib import Path

# 1. Definimos una carpeta segura y oculta en el directorio "Home" del usuario
APP_DIR = os.path.join(str(Path.home()), ".restaurante_manager")

# 2. Nos aseguramos de que esa carpeta exista
os.makedirs(APP_DIR, exist_ok=True)

# 3. Asignamos rutas absolutas seguras
CONFIG_FILE = os.path.join(APP_DIR, "config.json")
DEFAULT_DB = os.path.join(APP_DIR, "restaurante.db")


def get_db_path():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f).get("db_path", DEFAULT_DB)
    return DEFAULT_DB


def save_db_path(path):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"db_path": path}, f)

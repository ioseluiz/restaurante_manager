import json
import os

CONFIG_FILE = "config.json"


def get_db_path():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f).get("db_path", "data/restaurante.db")
    return "data/restaurante.db"


def save_db_path(path):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"db_path": path}, f)

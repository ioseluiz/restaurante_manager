import json
import os
import sqlite3

import pytest

from app.database import config
from app.database.connection import DatabaseManager

# Cabecera real de un archivo AppleDouble («._nombre») que macOS deja al copiar a un disco no-Mac
APPLEDOUBLE = b"\x00\x05\x16\x07\x00\x02\x00\x00Mac OS X        \x00\x02" + b"\x00" * 4000


@pytest.fixture
def cfg(tmp_path, monkeypatch):
    """Aísla el archivo de configuración para no tocar el del usuario."""
    archivo = tmp_path / "config.json"
    monkeypatch.setattr(config, "CONFIG_FILE", str(archivo))
    return archivo


def _bd_valida(carpeta, nombre="ok.db"):
    ruta = carpeta / nombre
    DatabaseManager(str(ruta)).conn.close()
    return str(ruta)


def test_rechaza_el_archivo_residual_de_macos(tmp_path):
    falso = tmp_path / "._restaurante.db"
    falso.write_bytes(APPLEDOUBLE)
    ok, motivo = config.validar_base_datos(str(falso))
    assert not ok and "macOS" in motivo and "restaurante.db" in motivo


def test_rechaza_archivos_que_no_son_sqlite_aunque_se_llamen_db(tmp_path):
    for nombre, contenido in (("texto.db", b"esto no es una base de datos" * 10), ("dañado.db", b"SQLite format 3\x00" + b"\xff" * 200)):
        f = tmp_path / nombre
        f.write_bytes(contenido)
        assert not config.validar_base_datos(str(f))[0], nombre


def test_acepta_bases_validas_vacias_y_nuevas(tmp_path):
    assert config.validar_base_datos(_bd_valida(tmp_path)) == (True, "")
    vacio = tmp_path / "vacio.db"
    vacio.write_bytes(b"")
    assert config.validar_base_datos(str(vacio))[0]
    assert config.validar_base_datos(str(tmp_path / "nueva.db"))[0]          # se creará


def test_rechaza_rutas_inutilizables(tmp_path):
    assert not config.validar_base_datos("")[0]
    assert not config.validar_base_datos(None)[0]
    assert not config.validar_base_datos(str(tmp_path))[0]                    # es una carpeta
    assert not config.validar_base_datos(str(tmp_path / "no_existe" / "x.db"))[0]


def test_cambiar_a_una_base_invalida_no_toca_la_conexion_ni_la_configuracion(tmp_path, cfg):
    actual = _bd_valida(tmp_path, "actual.db")
    db = DatabaseManager(actual)
    falso = tmp_path / "._x.db"
    falso.write_bytes(APPLEDOUBLE)
    with pytest.raises(ValueError, match="macOS"):
        db.switch_database(str(falso))
    assert not cfg.exists(), "no debe guardarse la ruta inválida"
    assert db.db_path == actual
    assert db.fetch_one("SELECT COUNT(*) FROM usuarios")[0] == 1               # sigue conectada a la anterior


def test_cambiar_a_una_base_dañada_revierte_a_la_anterior(tmp_path, cfg):
    actual = _bd_valida(tmp_path, "actual.db")
    db = DatabaseManager(actual)
    rota = tmp_path / "rota.db"
    rota.write_bytes(b"SQLite format 3\x00" + b"\xff" * 200)
    with pytest.raises(ValueError):
        db.switch_database(str(rota))
    assert not cfg.exists() and db.db_path == actual
    assert db.fetch_one("SELECT COUNT(*) FROM usuarios")[0] == 1


def test_cambiar_a_una_base_valida_guarda_la_ruta(tmp_path, cfg):
    db = DatabaseManager(_bd_valida(tmp_path, "a.db"))
    otra = _bd_valida(tmp_path, "b.db")
    db.switch_database(otra)
    assert db.db_path == otra
    assert json.loads(cfg.read_text())["db_path"] == otra
    assert db.fetch_one("SELECT COUNT(*) FROM usuarios")[0] == 1


def test_get_db_path_tolera_una_configuracion_ilegible(cfg):
    cfg.write_text("{esto no es json", encoding="utf-8")
    assert config.get_db_path() == config.DEFAULT_DB

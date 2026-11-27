"""Identidad del restaurante (guardada en la BD) y lista de restaurantes recientes del equipo."""
import json

import pytest

from app.controllers.restaurante_controller import RestauranteController
from app.database import config
from app.database.connection import DatabaseManager


@pytest.fixture
def db(tmp_path):
    d = DatabaseManager(str(tmp_path / "r.db"))
    yield d
    d.conn.close()


def test_base_sin_identidad_muestra_italos_y_la_sucursal_marcada(db):
    ctrl = RestauranteController(db)
    ident = ctrl.identidad()
    assert ident["nombre"] == "Italos" and not ident["configurado"] and ident["logo"] is None
    assert ctrl.etiqueta() == "Italos"
    db.execute_query("INSERT INTO sucursales (nombre, es_principal) VALUES ('Norte', 0), ('Centro', 1)")
    assert ctrl.etiqueta() == "Italos · Centro"


def test_guardar_marca_la_sucursal_y_la_crea_si_no_existe(db):
    ctrl = RestauranteController(db)
    db.execute_query("INSERT INTO sucursales (nombre, es_principal) VALUES ('Centro', 1), ('Norte', 0)")
    ctrl.guardar("Pizzería Roma", ruc="8-123-456", direccion="Calle 50", sucursal="norte")
    ident = ctrl.identidad()
    assert ident["configurado"] and ident["sucursal"] == "Norte" and ident["ruc"] == "8-123-456"
    assert db.fetch_one("SELECT COUNT(*) FROM sucursales WHERE es_principal = 1")[0] == 1

    ctrl.guardar("Pizzería Roma", sucursal="El Dorado")
    assert ctrl.etiqueta() == "Pizzería Roma · El Dorado"
    assert ctrl.identidad()["ruc"] == ""  # se guardan todos los campos del formulario
    assert ctrl.encabezado_reporte() == ["Pizzería Roma · El Dorado"]
    ctrl.guardar("Pizzería Roma", ruc="8-1", telefono="222-3333")
    assert ctrl.encabezado_reporte() == ["Pizzería Roma · El Dorado", "RUC 8-1 · 222-3333"]

    with pytest.raises(ValueError):
        ctrl.guardar("   ")


def test_logo_se_guarda_y_se_quita(db):
    ctrl = RestauranteController(db)
    ctrl.guardar_logo(b"\x89PNG-falso")
    assert ctrl.identidad()["logo"] == b"\x89PNG-falso"
    ctrl.guardar_logo(None)
    assert ctrl.identidad()["logo"] is None


def test_la_identidad_viaja_con_la_base(tmp_path):
    ruta = str(tmp_path / "viaja.db")
    d = DatabaseManager(ruta)
    RestauranteController(d).guardar("Italos", sucursal="Costa del Este")
    d.conn.close()
    d2 = DatabaseManager(ruta)
    assert RestauranteController(d2).etiqueta() == "Italos · Costa del Este"
    d2.conn.close()


def test_recientes_conserva_la_ruta_de_la_bd_y_respeta_el_tope(tmp_path):
    archivo = tmp_path / "config_pruebas.json"
    archivo.write_text(json.dumps({"db_path": "C:/viejo.db"}))  # formato anterior
    bases = []
    for i in range(config.MAX_RECIENTES + 2):
        f = tmp_path / f"b{i}.db"
        f.write_bytes(b"")
        bases.append(str(f))
        config.agregar_reciente(str(f), f"Rest {i}")
    rec = config.get_recientes()
    assert len(rec) == config.MAX_RECIENTES and rec[0]["nombre"] == f"Rest {config.MAX_RECIENTES + 1}"
    assert config.get_db_path() == "C:/viejo.db"

    config.agregar_reciente(bases[-3], "Renombrado")       # ya estaba: sube al principio, sin duplicarse
    rec = config.get_recientes()
    assert rec[0]["nombre"] == "Renombrado" and len(rec) == config.MAX_RECIENTES

    config.save_db_path("C:/nuevo.db")                     # guardar la ruta no borra los recientes
    assert len(config.get_recientes()) == config.MAX_RECIENTES

    (tmp_path / "b11.db").unlink()                         # las bases que ya no existen no se listan
    assert all("b11.db" not in r["ruta"] for r in config.get_recientes())

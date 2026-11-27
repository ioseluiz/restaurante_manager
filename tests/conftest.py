import pytest


@pytest.fixture(autouse=True)
def _config_aislada(tmp_path, monkeypatch):
    """Ninguna prueba toca el config.json real del usuario (ruta de la BD y restaurantes recientes)."""
    from app.database import config

    monkeypatch.setattr(config, "CONFIG_FILE", str(tmp_path / "config_pruebas.json"))

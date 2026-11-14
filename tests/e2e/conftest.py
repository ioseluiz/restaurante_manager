import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from app.database.connection import DatabaseManager  # noqa: E402

import escenario_e2e  # noqa: E402


@pytest.fixture(scope="session")
def qapp():
    """QApplication sin pantalla, para la lógica que todavía vive en diálogos."""
    QtWidgets = pytest.importorskip("PyQt5.QtWidgets")
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    yield app


@pytest.fixture
def sin_dialogos(qapp, monkeypatch):
    """Silencia los QMessageBox (las preguntas responden «Sí») y guarda los mensajes mostrados."""
    from PyQt5.QtWidgets import QMessageBox

    mensajes = []

    def _registrar(tipo):
        def _f(_parent, titulo, texto, *a, **k):
            mensajes.append((tipo, titulo, texto))
            return QMessageBox.Yes if tipo == "question" else QMessageBox.Ok
        return _f

    for tipo in ("information", "warning", "critical", "question"):
        monkeypatch.setattr(QMessageBox, tipo, staticmethod(_registrar(tipo)))
    return mensajes


@pytest.fixture
def db(tmp_path):
    return DatabaseManager(str(tmp_path / "e2e.db"))


@pytest.fixture
def esc(db):
    return escenario_e2e.construir(db)


def recibir_compra(db, compra_id):
    """Recepción por el mismo diálogo que usa la app (Recibido = Pedido)."""
    from app.views.modulos.compras_crud import RecepcionDialog

    dlg = RecepcionDialog(db, compra_id)
    dlg._aplicar()
    assert dlg.aplicado
    return dlg


@pytest.fixture
def recibir(sin_dialogos):
    return recibir_compra

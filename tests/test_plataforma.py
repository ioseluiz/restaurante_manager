"""Código multiplataforma (Windows / macOS): recursos, abrir archivos y arranque sin APIs de Windows."""
import os
import sys

import pytest

from app.utils import plataforma


def test_ruta_recurso_no_depende_de_la_carpeta_actual(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # en el .app de macOS la carpeta actual es «/»
    assert os.path.exists(plataforma.ruta_recurso("assets/icons/app.ico"))
    assert os.path.exists(plataforma.ruta_recurso("assets/icons/app.icns"))
    assert os.path.exists(plataforma.ruta_recurso("assets/ayuda/general.md"))


def test_ruta_recurso_usa_la_carpeta_del_ejecutable(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert plataforma.ruta_recurso("assets/x.png") == os.path.join(str(tmp_path), "assets/x.png")


def test_abrir_archivo_usa_la_aplicacion_del_sistema(tmp_path, monkeypatch):
    pytest.importorskip("PyQt5.QtGui")
    from PyQt5.QtGui import QDesktopServices

    abiertos = []
    monkeypatch.setattr(QDesktopServices, "openUrl", staticmethod(lambda url: abiertos.append(url) or True))
    archivo = tmp_path / "reporte.pdf"
    archivo.write_bytes(b"%PDF")
    assert plataforma.abrir_archivo(str(archivo))
    assert os.path.samefile(abiertos[0].toLocalFile(), archivo)


def test_no_quedan_apis_solo_de_windows_sin_proteger():
    """os.startfile y ctypes.windll no existen en macOS: solo pueden usarse dentro de plataforma.py
    (o protegidos con try/except, como los colores de la barra de título del login)."""
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    permitidos = {os.path.join("app", "utils", "plataforma.py"), os.path.join("app", "views", "login_window.py")}
    hallados = []
    for carpeta in ("app", "."):
        base = os.path.join(raiz, carpeta)
        for dirpath, dirnames, archivos in os.walk(base):
            dirnames[:] = [] if carpeta == "." else [d for d in dirnames if d != "__pycache__"]
            for a in archivos:
                if not a.endswith(".py"):
                    continue
                ruta = os.path.join(dirpath, a)
                rel = os.path.relpath(ruta, raiz)
                texto = open(ruta, encoding="utf-8").read()
                if ("os.startfile" in texto or "windll" in texto) and rel not in permitidos:
                    hallados.append(rel)
    assert not hallados, hallados


def test_configurar_app_en_mac_fija_una_paleta_clara(monkeypatch):
    pytest.importorskip("PyQt5.QtWidgets")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt5.QtGui import QPalette
    from PyQt5.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    anterior_estilo, anterior_paleta = app.style().objectName(), app.palette()
    monkeypatch.setattr(plataforma, "ES_MAC", True)
    try:
        plataforma.configurar_app(app)
        assert app.palette().color(QPalette.Base).name() == "#ffffff"
        assert app.palette().color(QPalette.Text).lightness() < 100
    finally:
        app.setPalette(anterior_paleta)
        app.setStyle(anterior_estilo)

# [FILE: app/views/db_recovery.py]
"""Apertura de la base de datos al arrancar, con recuperación guiada si la configurada no se puede abrir."""

import os

from PyQt5.QtWidgets import QFileDialog, QMessageBox

from app.database.config import DEFAULT_DB, get_db_path, save_db_path, validar_base_datos
from app.database.connection import DatabaseManager


def _intentar_abrir(ruta):
    """(DatabaseManager|None, motivo). Valida y abre; nunca lanza."""
    ok, motivo = validar_base_datos(ruta)
    if not ok:
        return None, motivo
    try:
        return DatabaseManager(ruta), ""
    except Exception as e:  # base dañada, sin permisos, esquema incompatible…
        return None, f"No se pudo abrir la base de datos: {e}"


def abrir_base_de_datos(parent=None):
    """Abre la base configurada. Si falla, deja elegir otra, usar la predeterminada o salir.

    Devuelve un DatabaseManager, o None si el usuario decide salir. La ruta solo se guarda en la
    configuración cuando la base elegida abre correctamente.
    """
    ruta = get_db_path()
    while True:
        db, motivo = _intentar_abrir(ruta)
        if db is not None:
            if os.path.abspath(ruta) != os.path.abspath(get_db_path()):
                save_db_path(ruta)
            return db

        caja = QMessageBox(parent)
        caja.setIcon(QMessageBox.Warning)
        caja.setWindowTitle("No se pudo abrir la base de datos")
        caja.setText("El programa no puede abrir la base de datos configurada.")
        caja.setInformativeText(
            f"<b>Ruta:</b> {ruta}<br><br><b>Motivo:</b> {motivo}<br><br>"
            "Elija otra base de datos existente, o use la predeterminada "
            f"(<i>{DEFAULT_DB}</i>; si no existe se crea una vacía).")
        btn_otra = caja.addButton("Elegir otra base de datos…", QMessageBox.AcceptRole)
        btn_def = caja.addButton("Usar la predeterminada", QMessageBox.ActionRole)
        btn_salir = caja.addButton("Salir", QMessageBox.RejectRole)
        caja.setDefaultButton(btn_otra)
        caja.exec_()
        elegido = caja.clickedButton()

        if elegido == btn_otra:
            carpeta = os.path.dirname(ruta) if os.path.isdir(os.path.dirname(ruta)) else ""
            nueva, _ = QFileDialog.getOpenFileName(
                parent, "Seleccionar base de datos", carpeta,
                "Bases de datos (*.db *.sqlite *.sqlite3);;Todos los archivos (*)")
            if nueva:
                ruta = nueva
        elif elegido == btn_def:
            ruta = DEFAULT_DB
        else:
            return None

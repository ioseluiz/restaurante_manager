"""Crea una base de datos con el escenario de prueba de mayo 2026 para el checklist manual de la UI.

    python scripts/crear_bd_prueba.py                 # -> ./prueba_e2e.db
    python scripts/crear_bd_prueba.py C:/ruta/otra.db

Carga el mismo escenario que las pruebas E2E (tests/e2e/escenario_e2e.py) más un usuario por rol
(gerente/gerente123, empleado/empleado123). Deja la compra PENDIENTE y las ventas sin procesar: esos
pasos se hacen desde la app siguiendo docs/pruebas_manual_ui.md. No toca la configuración de la app;
para usarla, abra «Configurar BD» y elija el archivo.
"""

import os
import sys

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "tests", "e2e"))

from app.controllers.auth_controller import hash_password  # noqa: E402
from app.database.connection import DatabaseManager  # noqa: E402
import escenario_e2e  # noqa: E402


def main(destino):
    destino = os.path.abspath(destino)
    if os.path.exists(destino):
        sys.exit(f"Ya existe {destino}; bórrelo o indique otra ruta.")
    db = DatabaseManager(destino)
    esc = escenario_e2e.construir(db)
    escenario_e2e.dia_ventas(db, escenario_e2e.FECHA_VENTA, [(esc.p1, 10), (esc.p2, 20)])
    for usuario, clave, rol in (("gerente", "gerente123", "gerente"), ("empleado", "empleado123", "empleado")):
        db.execute_query("INSERT INTO usuarios (username, password_hash, rol) VALUES (?,?,?)",
                         (usuario, hash_password(clave), rol))
    db.conn.close()
    print(f"Base de prueba creada: {destino}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "prueba_e2e.db")

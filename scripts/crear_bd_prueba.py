"""Crea una base de datos con el escenario de prueba de mayo 2026 para el checklist manual de la UI.

    python scripts/crear_bd_prueba.py                 # -> ./prueba_e2e.db
    python scripts/crear_bd_prueba.py C:/ruta/otra.db
    python scripts/crear_bd_prueba.py C:/ruta/otra.db --agregar-junio   # solo suma junio a una base existente

Carga el mismo escenario que las pruebas E2E (tests/e2e/escenario_e2e.py) más un usuario por rol
(gerente/gerente123, empleado/empleado123), con el restaurante «Italos (prueba) · Centro». Deja la compra PENDIENTE y las ventas sin procesar: esos
pasos se hacen desde la app siguiendo docs/pruebas_manual_ui.md. No toca la configuración de la app;
para usarla, abra «Configurar BD» y elija el archivo.

Además carga **junio 2026 completo** (ventas de los 30 días, diario de caja, dos quincenas de planilla y los
egresos del mes) para ver Costo de Platos, Rentabilidad y el Panel con un volumen realista. Mayo queda igual:
los números del checklist no cambian.
"""

import os
import sys

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "tests", "e2e"))

from app.controllers.auth_controller import hash_password  # noqa: E402
from app.database.connection import DatabaseManager  # noqa: E402
from app.controllers.restaurante_controller import RestauranteController  # noqa: E402
from app.utils.diario_ventas_calc import total_ventas_diario  # noqa: E402
import escenario_e2e  # noqa: E402

NOMBRE_PRUEBA = "Italos (prueba)"  # la sucursal de esta instalación es «Centro» (del escenario)
# Platos por día de la semana (lunes = 0): (P1, P2). Promedio ≈ 198 platos/día
VENTAS_POR_DIA = {0: (90, 85), 1: (90, 85), 2: (95, 90), 3: (95, 90), 4: (110, 105), 5: (125, 115), 6: (105, 100)}
# Reparto del cobro diario por medio de pago
MEDIOS_PAGO = {"efectivo": 0.40, "visa_mastercard": 0.30, "yappy": 0.15, "pedidos_ya": 0.10, "clave": 0.05}


def agregar_junio(db):
    """Junio 2026 completo sobre una base con el escenario de mayo. Se niega si junio ya tiene ventas."""
    import datetime

    if db.fetch_one("SELECT 1 FROM registro_ventas_diarias WHERE fecha LIKE '2026-06-%'"):
        sys.exit("La base ya tiene ventas de junio 2026.")
    uno = lambda sql, *p: db.fetch_one(sql, p)[0]  # noqa: E731
    p1, p2 = (uno("SELECT id FROM menu_items WHERE codigo = ?", c) for c in ("P1", "P2"))
    precio1, precio2 = (uno("SELECT precio_venta FROM menu_items WHERE id = ?", p) for p in (p1, p2))
    ana = uno("SELECT id FROM empleados WHERE nombre = 'Ana'")
    luis = uno("SELECT id FROM empleados WHERE nombre = 'Luis'")
    tarjeta = uno("SELECT id FROM tarjetas_credito WHERE numero = '1234'")
    yappy = uno("SELECT id FROM yappy_cuentas WHERE nombre = 'Principal'")

    # Ventas diarias (sin procesar) y cierre de caja de cada día
    for dia in range(1, 31):
        fecha = datetime.date(2026, 6, dia)
        c1, c2 = VENTAS_POR_DIA[fecha.weekday()]
        escenario_e2e.dia_ventas(db, fecha.isoformat(), [(p1, c1), (p2, c2)])
        cobro = c1 * precio1 + c2 * precio2
        medios = {k: round(cobro * pct, 2) for k, pct in MEDIOS_PAGO.items()}
        medios["efectivo"] = round(cobro - sum(v for k, v in medios.items() if k != "efectivo"), 2)
        db.execute_query(
            "INSERT INTO diario_ventas (fecha, total_ventas, yappy, pedidos_ya, clave, visa_mastercard, efectivo) "
            "VALUES (?,?,?,?,?,?,?)",
            (fecha.isoformat(), total_ventas_diario(**medios), medios["yappy"], medios["pedidos_ya"],
             medios["clave"], medios["visa_mastercard"], medios["efectivo"]))

    # Planilla: dos quincenas con las mismas horas de mayo
    for nombre, ini, fin in (("1ra quincena junio", "2026-06-01", "2026-06-15"),
                             ("2da quincena junio", "2026-06-16", "2026-06-30")):
        per = db.execute_query("INSERT INTO periodos_pago (nombre, fecha_inicio, fecha_fin) VALUES (?,?,?)",
                               (nombre, ini, fin)).lastrowid
        db.execute_query("INSERT INTO horas_empleado (empleado_id, periodo_id, horas_regulares, horas_domingos, "
                         "horas_extra_diurnas) VALUES (?,?,88,8,4)", (ana, per))
        db.execute_query("INSERT INTO horas_empleado (empleado_id, periodo_id, horas_regulares) VALUES (?,?,96)",
                         (luis, per))
        db.execute_query("INSERT INTO pagos_efectivo (fecha, proveedor, total, planilla) VALUES (?,?,900,900)",
                         (fin, f"Planilla {nombre}"))

    # Gastos fijos del mes (mismos conceptos y canales que mayo, con montos de un mes completo)
    db.execute_query("INSERT INTO chequera (fecha, no_ck, nombre_cheque, monto, tipo_gasto) "
                     "VALUES ('2026-06-05','103','Inmobiliaria',3000,'Alquiler')")
    db.execute_query("INSERT INTO transacciones_tarjeta (tarjeta_id, fecha, comercio, tipo_transaccion, monto, "
                     "tipo_gasto) VALUES (?, '2026-06-12', 'Cable', 'COMPRA', 60, 'Internet / Teléfono')", (tarjeta,))
    db.execute_query("INSERT INTO transacciones_yappy (yappy_id, fecha, proveedor, monto, tipo_gasto) "
                     "VALUES (?, '2026-06-15', 'Naturgy', 850, 'Luz (electricidad)')", (yappy,))
    pe = db.execute_query("INSERT INTO pagos_efectivo (fecha, proveedor, total, otros) "
                          "VALUES ('2026-06-08','Gas del Istmo',350,350)").lastrowid
    db.execute_query("INSERT INTO detalle_pagos_efectivo (pago_efectivo_id, categoria, monto, tipo_gasto) "
                     "VALUES (?, 'otros', 350, 'Gas')", (pe,))

    # Compras de mercado semanales en efectivo (costo real del mes: 4 × 2 500 ≈ 30 % de las ventas)
    for fecha in ("2026-06-01", "2026-06-08", "2026-06-15", "2026-06-22"):
        pe = db.execute_query("INSERT INTO pagos_efectivo (fecha, proveedor, total, costo_viveres, costo_carnes) "
                              "VALUES (?, 'Mercado', 2500, 1100, 1400)", (fecha,)).lastrowid
        for cat, monto in (("costo_viveres", 1100), ("costo_carnes", 1400)):
            db.execute_query("INSERT INTO detalle_pagos_efectivo (pago_efectivo_id, categoria, monto) "
                             "VALUES (?,?,?)", (pe, cat, monto))


def main(destino, solo_junio=False):
    destino = os.path.abspath(destino)
    if solo_junio:
        if not os.path.exists(destino):
            sys.exit(f"No existe {destino}.")
        db = DatabaseManager(destino)
        agregar_junio(db)
        db.conn.close()
        print(f"Junio 2026 agregado a: {destino}")
        return
    if os.path.exists(destino):
        sys.exit(f"Ya existe {destino}; bórrelo o indique otra ruta.")
    db = DatabaseManager(destino)
    esc = escenario_e2e.construir(db)
    escenario_e2e.dia_ventas(db, escenario_e2e.FECHA_VENTA, [(esc.p1, 10), (esc.p2, 20)])
    for usuario, clave, rol in (("gerente", "gerente123", "gerente"), ("empleado", "empleado123", "empleado")):
        db.execute_query("INSERT INTO usuarios (username, password_hash, rol) VALUES (?,?,?)",
                         (usuario, hash_password(clave), rol))
    # Nombre distinto de una base real, para que la UI muestre claramente que es la de prueba
    RestauranteController(db).guardar(NOMBRE_PRUEBA)
    agregar_junio(db)
    db.conn.close()
    print(f"Base de prueba creada: {destino}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args[0] if args else "prueba_e2e.db", solo_junio="--agregar-junio" in sys.argv)

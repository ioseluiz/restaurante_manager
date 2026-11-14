"""Escenario de restaurante para las pruebas end-to-end (mayo 2026).

Todos los números están elegidos para que los resultados se puedan calcular a mano; los mismos
ejemplos aparecen en docs/calculos.md. Precios por unidad base (presentación vigente):

    Arroz   g   Saco 10 kg   $12.00  -> 0.0012 $/g   (stock previo 5 000 g a 0.0010 $/g)
    Pollo   g   Caja 5 kg    $20.00  -> 0.0040 $/g
    Tomate  g   Caja 2 kg    $ 3.00  -> 0.0015 $/g
    Aceite  ml  Botella 1 L  $ 4.00  -> 0.0040 $/ml
    Envase  und Paquete 50   $10.00  -> 0.20   $/und
    Soda    und Lata         $ 0.50  -> 0.50   $/und

Menú:
    SALSA  Salsa de tomate (componente, tanda de 1 000 g): Tomate 1 200 g + Aceite 100 ml
    ENV    Envase para llevar (componente): Envase 1 und
    SODA   Soda (componente): Soda 1 und
    P1     Pollo con arroz, receta por porción: Pollo 200 g, Arroz 150 g, Salsa 50 g;
           extra EMPAQUE Envase solo LLEVAR. Precio $6.00
    P2     Arroz con pollo, receta por tanda (rinde 4 000 g, porción 400 g):
           Arroz 1 500 g, Pollo 2 000 g, Aceite 200 ml; extra BEBIDA Soda AMBOS. Precio $5.50
"""
from types import SimpleNamespace

FECHA_VENTA = "2026-05-10"
MES, ANIO = 5, 2026


def _ins(db, sql, params=()):
    return db.execute_query(sql, params).lastrowid


def unidad(db, nombre, abrev):
    return _ins(db, "INSERT INTO unidades_medida (nombre, abreviatura) VALUES (?,?)", (nombre, abrev))


def insumo(db, nombre, unidad_id, stock=0.0, costo=0.0, categoria_id=None):
    return _ins(
        db,
        "INSERT INTO insumos (nombre, unidad_base_id, stock_actual, costo_unitario, categoria_id) "
        "VALUES (?,?,?,?,?)",
        (nombre, unidad_id, stock, costo, categoria_id),
    )


def presentacion(db, insumo_id, nombre, contenido, precio):
    return _ins(
        db,
        "INSERT INTO presentaciones_compra (insumo_id, nombre, cantidad_contenido, precio_compra, "
        "costo_unitario_calculado) VALUES (?,?,?,?,?)",
        (insumo_id, nombre, contenido, precio, precio / contenido),
    )


def plato(db, codigo, nombre, precio=0.0, **extra):
    iid = _ins(db, "INSERT INTO menu_items (codigo, nombre, precio_venta) VALUES (?,?,?)",
               (codigo, nombre, precio))
    for k, v in extra.items():
        db.execute_query(f"UPDATE menu_items SET {k}=? WHERE id=?", (v, iid))
    return iid


def receta(db, plato_id, insumo_id, cantidad):
    _ins(db, "INSERT INTO recetas (menu_item_id, insumo_id, cantidad_necesaria) VALUES (?,?,?)",
         (plato_id, insumo_id, cantidad))


def componente(db, plato_id, comp_id, cantidad, unidad_id=None):
    _ins(db, "INSERT INTO receta_componentes (menu_item_id, componente_id, cantidad, unidad_id) "
             "VALUES (?,?,?,?)", (plato_id, comp_id, cantidad, unidad_id))


def extra(db, plato_id, comp_id, tipo, canal, porciones=1.0):
    _ins(db, "INSERT INTO plato_extras (menu_item_id, componente_id, cantidad_porciones, tipo, canal) "
             "VALUES (?,?,?,?,?)", (plato_id, comp_id, porciones, tipo, canal))


def compra(db, proveedor_id, lineas, fecha="2026-05-02", presupuesto_id=None):
    """lineas: [(presentacion_id, cantidad, precio_unitario)]. Queda PENDIENTE."""
    total = sum(c * p for _pid, c, p in lineas)
    cid = _ins(db, "INSERT INTO compras (proveedor_id, fecha_compra, total, presupuesto_id) VALUES (?,?,?,?)",
               (proveedor_id, fecha, total, presupuesto_id))
    for pid, cant, precio in lineas:
        _ins(db, "INSERT INTO detalle_compras (compra_id, presentacion_id, cantidad, precio_unitario, subtotal) "
                 "VALUES (?,?,?,?,?)", (cid, pid, cant, precio, cant * precio))
    return cid


def dia_ventas(db, fecha, ventas):
    rid = _ins(db, "INSERT INTO registro_ventas_diarias (fecha) VALUES (?)", (fecha,))
    for plato_id, cant in ventas:
        _ins(db, "INSERT INTO detalle_ventas_diarias (registro_diario_id, menu_item_id, cantidad) VALUES (?,?,?)",
             (rid, plato_id, cant))
    return rid


def reporte_pos(db, pct_sugerido, filas, desde="01/04/2026", hasta="30/04/2026"):
    """filas: [(codigo, nombre, dia, cantidad, promedio, total_venta, total_costo)]."""
    rid = _ins(db, "INSERT INTO reportes_ventas (fecha_inicio_periodo, fecha_fin_periodo, porcentaje_sugerido) "
                   "VALUES (?,?,?)", (desde, hasta, pct_sugerido))
    for cod, nom, dia, cant, prom, venta, costo in filas:
        _ins(db, "INSERT INTO detalle_reportes_ventas (reporte_id, codigo_producto, nombre_producto, dia_semana, "
                 "cantidad, promedio_medida, total_venta, total_costo) VALUES (?,?,?,?,?,?,?,?)",
             (rid, cod, nom, dia, cant, prom, venta, costo))
    return rid


def construir(db):
    """Catálogo, recetas, personal y finanzas de mayo 2026. No recibe la compra ni procesa ventas:
    cada prueba ejecuta los pasos del flujo que le interesan."""
    e = SimpleNamespace()
    e.g = unidad(db, "Gramo", "g")
    e.ml = unidad(db, "Mililitro", "ml")
    e.und = unidad(db, "Unidad", "und")
    e.cat_viveres = _ins(db, "INSERT INTO categorias_insumos (codigo, nombre) VALUES ('VIV','Víveres')")
    e.cat_carnes = _ins(db, "INSERT INTO categorias_insumos (codigo, nombre) VALUES ('CAR','Carnes')")

    e.arroz = insumo(db, "Arroz", e.g, stock=5000, costo=0.0010, categoria_id=e.cat_viveres)
    e.pollo = insumo(db, "Pollo", e.g, categoria_id=e.cat_carnes)
    e.tomate = insumo(db, "Tomate", e.g, categoria_id=e.cat_viveres)
    e.aceite = insumo(db, "Aceite", e.ml, categoria_id=e.cat_viveres)
    e.envase = insumo(db, "Envase", e.und)
    e.soda = insumo(db, "Soda", e.und)
    e.stock_inicial = {e.arroz: 5000.0}

    e.p_arroz = presentacion(db, e.arroz, "Saco 10 kg", 10000, 12.00)
    e.p_pollo = presentacion(db, e.pollo, "Caja 5 kg", 5000, 20.00)
    e.p_tomate = presentacion(db, e.tomate, "Caja 2 kg", 2000, 3.00)
    e.p_aceite = presentacion(db, e.aceite, "Botella 1 L", 1000, 4.00)
    e.p_envase = presentacion(db, e.envase, "Paquete 50", 50, 10.00)
    e.p_soda = presentacion(db, e.soda, "Lata", 1, 0.50)

    e.salsa = plato(db, "SALSA", "Salsa de tomate", es_componente=1, rendimiento=1000,
                    unidad_rendimiento_id=e.g)
    receta(db, e.salsa, e.tomate, 1200)
    receta(db, e.salsa, e.aceite, 100)
    e.c_envase = plato(db, "ENV", "Envase para llevar", es_componente=1)
    receta(db, e.c_envase, e.envase, 1)
    e.c_soda = plato(db, "SODA", "Soda", es_componente=1)
    receta(db, e.c_soda, e.soda, 1)

    e.p1 = plato(db, "P1", "Pollo con arroz", 6.00)
    receta(db, e.p1, e.pollo, 200)
    receta(db, e.p1, e.arroz, 150)
    componente(db, e.p1, e.salsa, 50, e.g)
    extra(db, e.p1, e.c_envase, "EMPAQUE", "LLEVAR")

    e.p2 = plato(db, "P2", "Arroz con pollo", 5.50, rendimiento=4000, unidad_rendimiento_id=e.g,
                 porcion_servida=400, unidad_porcion_id=e.g)
    receta(db, e.p2, e.arroz, 1500)
    receta(db, e.p2, e.pollo, 2000)
    receta(db, e.p2, e.aceite, 200)
    extra(db, e.p2, e.c_soda, "BEBIDA", "AMBOS")

    e.proveedor = _ins(db, "INSERT INTO proveedores (nombre) VALUES ('Distribuidora')")
    e.compra = compra(db, e.proveedor, [
        (e.p_arroz, 2, 12.00), (e.p_pollo, 3, 20.00), (e.p_tomate, 2, 3.00),
        (e.p_aceite, 2, 4.00), (e.p_envase, 1, 10.00), (e.p_soda, 24, 0.50),
    ])

    e.suc_centro = _ins(db, "INSERT INTO sucursales (nombre, es_principal) VALUES ('Centro', 1)")
    e.suc_norte = _ins(db, "INSERT INTO sucursales (nombre, es_principal) VALUES ('Norte', 0)")

    # Personal: una quincena de mayo
    e.ana = _ins(db, "INSERT INTO empleados (nombre, apellido, salario_hora, tipo_contrato, sucursal_id) "
                     "VALUES ('Ana','Pérez',4.00,'INDEFINIDO',?)", (e.suc_centro,))
    e.luis = _ins(db, "INSERT INTO empleados (nombre, apellido, salario_hora, tipo_contrato, sucursal_id) "
                      "VALUES ('Luis','Gómez',3.00,'DEFINIDO',?)", (e.suc_centro,))
    e.periodo = _ins(db, "INSERT INTO periodos_pago (nombre, fecha_inicio, fecha_fin) "
                         "VALUES ('1ra quincena mayo','2026-05-01','2026-05-15')")
    _ins(db, "INSERT INTO horas_empleado (empleado_id, periodo_id, horas_regulares, horas_domingos, "
             "horas_extra_diurnas) VALUES (?,?,88,8,4)", (e.ana, e.periodo))
    _ins(db, "INSERT INTO horas_empleado (empleado_id, periodo_id, horas_regulares) VALUES (?,?,96)",
         (e.luis, e.periodo))

    # Egresos de mayo por canal de pago
    db.execute_query("INSERT INTO chequera (fecha, no_ck, nombre_cheque, monto, tipo_gasto) "
                     "VALUES ('2026-05-05','101','Inmobiliaria',800,'Alquiler')")
    db.execute_query("INSERT INTO chequera (fecha, no_ck, nombre_cheque, monto) "
                     "VALUES ('2026-05-20','102','Carnes del Istmo',300)")
    tarjeta = _ins(db, "INSERT INTO tarjetas_credito (numero, tipo, banco) VALUES ('1234','VISA','Banco')")
    db.execute_query("INSERT INTO transacciones_tarjeta (tarjeta_id, fecha, comercio, tipo_transaccion, monto, "
                     "tipo_gasto) VALUES (?, '2026-05-12', 'Cable', 'COMPRA', 60, 'Internet / Teléfono')",
                     (tarjeta,))
    db.execute_query("INSERT INTO transacciones_tarjeta (tarjeta_id, fecha, comercio, tipo_transaccion, monto) "
                     "VALUES (?, '2026-05-28', 'Pago', 'PAGO', 500)", (tarjeta,))
    yappy = _ins(db, "INSERT INTO yappy_cuentas (nombre, numero) VALUES ('Principal','6000-0000')")
    db.execute_query("INSERT INTO transacciones_yappy (yappy_id, fecha, proveedor, monto, tipo_gasto) "
                     "VALUES (?, '2026-05-15', 'Naturgy', 150, 'Luz (electricidad)')", (yappy,))
    pe = _ins(db, "INSERT INTO pagos_efectivo (fecha, proveedor, total, costo_viveres, costo_carnes, otros) "
                  "VALUES ('2026-05-08','Mercado',270,120,100,50)")
    for cat, monto, tipo in (("costo_viveres", 120, None), ("costo_carnes", 100, None), ("otros", 50, "Gas")):
        db.execute_query("INSERT INTO detalle_pagos_efectivo (pago_efectivo_id, categoria, monto, tipo_gasto) "
                         "VALUES (?,?,?,?)", (pe, cat, monto, tipo))
    db.execute_query("INSERT INTO pagos_efectivo (fecha, proveedor, total, planilla) "
                     "VALUES ('2026-05-30','Planilla quincena',900,900)")

    # Diario de ventas del día de venta (cierre de caja)
    from app.utils.diario_ventas_calc import total_ventas_diario
    total = total_ventas_diario(yappy=20, pedidos_ya=30, clave=40, visa_mastercard=50, efectivo=60.5,
                                sobrante=1, faltante=0.5)
    db.execute_query("INSERT INTO diario_ventas (fecha, total_ventas, yappy, pedidos_ya, clave, visa_mastercard, "
                     "efectivo, sobrante, faltante) VALUES (?,?,20,30,40,50,60.5,1,0.5)", (FECHA_VENTA, total))
    return e

# [FILE: app/controllers/kardex_controller.py]
class KardexController:
    def __init__(self, db_manager):
        self.db = db_manager

    def registrar_movimiento(
        self, insumo_id, cantidad, tipo, referencia_id=None, observacion=""
    ):
        """
        Registra un movimiento, actualiza el stock y guarda el historial.
        cantidad: Positivo (Entrada) o Negativo (Salida)
        """
        try:
            # 1. Obtener Stock Actual
            row = self.db.fetch_one(
                "SELECT stock_actual FROM insumos WHERE id=?", (insumo_id,)
            )
            if not row:
                raise Exception(f"Insumo ID {insumo_id} no encontrado.")

            stock_anterior = row[0]
            stock_nuevo = stock_anterior + cantidad

            # 2. Actualizar Tabla Insumos
            self.db.execute_query(
                "UPDATE insumos SET stock_actual=? WHERE id=?", (stock_nuevo, insumo_id)
            )

            # 3. Insertar en Kardex
            self.db.execute_query(
                """
                INSERT INTO movimientos_inventario 
                (insumo_id, tipo_movimiento, cantidad, stock_anterior, stock_nuevo, referencia_id, observacion)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    insumo_id,
                    tipo,
                    cantidad,
                    stock_anterior,
                    stock_nuevo,
                    referencia_id,
                    observacion,
                ),
            )

            return True
        except Exception as e:
            print(f"Error en Kardex: {e}")
            raise e

    # ------------------------------------------------------------------
    # Ventas diarias -> descuento de insumos
    # ------------------------------------------------------------------
    def _aplicar(self, cur, insumo_id, cantidad, tipo, referencia_id, observacion):
        """Mueve el stock y registra el Kardex SIN confirmar (lo confirma quien llama)."""
        row = cur.execute("SELECT stock_actual FROM insumos WHERE id=?", (insumo_id,)).fetchone()
        if not row:
            raise Exception(f"Insumo ID {insumo_id} no encontrado.")
        anterior = row[0] or 0.0
        nuevo = round(anterior + cantidad, 6)
        cur.execute("UPDATE insumos SET stock_actual=? WHERE id=?", (nuevo, insumo_id))
        cur.execute(
            "INSERT INTO movimientos_inventario "
            "(insumo_id, tipo_movimiento, cantidad, stock_anterior, stock_nuevo, referencia_id, observacion) "
            "VALUES (?,?,?,?,?,?,?)",
            (insumo_id, tipo, cantidad, anterior, nuevo, referencia_id, observacion),
        )
        return nuevo

    def procesar_ventas_diarias(self, registro_id):
        """Descuenta del stock los insumos consumidos por las ventas de un día.

        Por cada plato vendido usa v_recetas_explotadas (receta por porción o por tanda, con los
        insumos de sus sub-recetas) × unidades vendidas, y suma por insumo: un movimiento `VENTA`
        por insumo, con referencia_id = id del registro diario. Todo en una transacción.

        Devuelve {"fecha", "movimientos", "sin_receta": [nombres], "negativos": [nombres]}.
        Lanza ValueError si el día no existe o ya estaba procesado.
        """
        reg = self.db.fetch_one(
            "SELECT fecha, inventario_descontado FROM registro_ventas_diarias WHERE id=?", (registro_id,)
        )
        if not reg:
            raise ValueError("El registro de ventas del día no existe.")
        fecha, ya = reg
        if ya:
            raise ValueError("Este día ya fue procesado. Use «Reabrir Día» si necesita corregirlo.")

        platos = self.db.fetch_all(
            "SELECT d.menu_item_id, m.nombre, SUM(d.cantidad) FROM detalle_ventas_diarias d "
            "JOIN menu_items m ON m.id = d.menu_item_id WHERE d.registro_diario_id=? AND d.cantidad > 0 "
            "GROUP BY d.menu_item_id, m.nombre",
            (registro_id,),
        )
        consumo, sin_receta = {}, []
        for item_id, nombre, unidades in platos:
            insumos = self.db.fetch_all(
                "SELECT insumo_id, cantidad_necesaria FROM v_recetas_explotadas WHERE menu_item_id=?", (item_id,)
            )
            if not insumos:
                sin_receta.append(nombre)
                continue
            for insumo_id, por_porcion in insumos:
                consumo[insumo_id] = consumo.get(insumo_id, 0.0) + (por_porcion or 0.0) * unidades

        cur = self.db.conn.cursor()
        try:
            negativos = []
            for insumo_id, cant in consumo.items():
                if cant <= 0:
                    continue
                nuevo = self._aplicar(cur, insumo_id, -cant, "VENTA", registro_id, f"Ventas del día {fecha}")
                if nuevo < 0:
                    negativos.append(insumo_id)
            cur.execute("UPDATE registro_ventas_diarias SET inventario_descontado=1 WHERE id=?", (registro_id,))
            self.db.conn.commit()
        except Exception:
            self.db.conn.rollback()
            raise
        nombres_neg = [
            r[0] for i in negativos for r in [self.db.fetch_one("SELECT nombre FROM insumos WHERE id=?", (i,))] if r
        ]
        return {"fecha": fecha, "movimientos": len([c for c in consumo.values() if c > 0]),
                "sin_receta": sin_receta, "negativos": nombres_neg}

    def revertir_ventas_diarias(self, registro_id):
        """Reabre un día procesado devolviendo al stock lo que se descontó (movimiento `REVERSO_VENTA`).

        Se revierte el neto de VENTA + REVERSO_VENTA del día, así que sirve también si el día se reabrió y
        reprocesó antes. Un día marcado por la versión anterior (sin movimientos) solo pierde la marca.
        Devuelve la cantidad de insumos repuestos.
        """
        reg = self.db.fetch_one(
            "SELECT fecha, inventario_descontado FROM registro_ventas_diarias WHERE id=?", (registro_id,)
        )
        if not reg:
            raise ValueError("El registro de ventas del día no existe.")
        fecha, procesado = reg
        if not procesado:
            raise ValueError("Este día no está procesado.")
        netos = self.db.fetch_all(
            "SELECT insumo_id, SUM(cantidad) FROM movimientos_inventario "
            "WHERE referencia_id=? AND tipo_movimiento IN ('VENTA','REVERSO_VENTA') GROUP BY insumo_id",
            (registro_id,),
        )
        cur = self.db.conn.cursor()
        try:
            repuestos = 0
            for insumo_id, neto in netos:
                if abs(neto or 0.0) < 1e-9:
                    continue
                self._aplicar(cur, insumo_id, -neto, "REVERSO_VENTA", registro_id,
                              f"Reapertura de las ventas del día {fecha}")
                repuestos += 1
            cur.execute("UPDATE registro_ventas_diarias SET inventario_descontado=0 WHERE id=?", (registro_id,))
            self.db.conn.commit()
        except Exception:
            self.db.conn.rollback()
            raise
        return repuestos

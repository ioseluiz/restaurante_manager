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

    def procesar_baja_por_ventas(self, reporte_ids):
        """
        Recorre una lista de IDs de 'ventas_reporte_semanal', busca sus recetas
        y descuenta los insumos del inventario.
        """
        count_movimientos = 0
        errores = []

        for venta_id in reporte_ids:
            # Obtener datos de la venta
            venta = self.db.fetch_one(
                """
                SELECT codigo_producto, cantidad, nombre_producto, inventario_descontado 
                FROM ventas_reporte_semanal WHERE id=?
            """,
                (venta_id,),
            )

            if not venta:
                continue
            codigo, cantidad_vendida, nombre_prod, descontado = venta

            if descontado:
                continue  # Ya fue procesado

            # Buscar el menu_item y su receta
            menu_item = self.db.fetch_one(
                "SELECT id FROM menu_items WHERE codigo=?", (codigo,)
            )

            if menu_item:
                menu_item_id = menu_item[0]
                # Obtener ingredientes
                ingredientes = self.db.fetch_all(
                    """
                    SELECT insumo_id, cantidad_necesaria 
                    FROM recetas WHERE menu_item_id=?
                """,
                    (menu_item_id,),
                )

                if ingredientes:
                    for insumo_id, cant_receta in ingredientes:
                        # CALCULO: Cantidad Vendida * Cantidad Receta
                        # Salida es negativa
                        cantidad_baja = -1 * (cantidad_vendida * cant_receta)

                        self.registrar_movimiento(
                            insumo_id,
                            cantidad_baja,
                            "VENTA",
                            venta_id,
                            f"Venta: {nombre_prod}",
                        )
                        count_movimientos += 1

                # Marcar venta como procesada
                self.db.execute_query(
                    "UPDATE ventas_reporte_semanal SET inventario_descontado=1 WHERE id=?",
                    (venta_id,),
                )
            else:
                errores.append(f"Producto sin enlace al menú: {codigo} - {nombre_prod}")

        return count_movimientos, errores

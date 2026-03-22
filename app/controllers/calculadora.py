import math


class CalculadoraInsumos:
    def __init__(self, db_manager):
        self.db = db_manager

    def obtener_promedio_ventas_semanales(self):
        """
        Calcula el promedio de ventas por producto y día de semana
        basado en los reportes históricos.
        """
        query = """
            SELECT codigo_producto, LOWER(dia_semana), AVG(promedio_medida) 
            FROM detalle_reportes_ventas
            GROUP BY codigo_producto, LOWER(dia_semana)
        """
        rows = self.db.fetch_all(query)

        ventas_promedio = {}
        for row in rows:
            codigo = row[0]
            dia = row[1]
            cantidad_prom = row[2]

            if codigo not in ventas_promedio:
                ventas_promedio[codigo] = {}

            ventas_promedio[codigo][dia] = cantidad_prom

        return ventas_promedio

    def obtener_platos_por_grupo(self, grupo_filtro):
        """
        Retorna la lista de platos (items del menú) que utilizan insumos
        del grupo seleccionado. Sirve para pedir datos manuales solo de lo necesario.
        """
        query = """
            SELECT DISTINCT m.codigo, m.nombre
            FROM insumos i
            JOIN recetas r ON i.id = r.insumo_id
            JOIN menu_items m ON r.menu_item_id = m.id
            WHERE 1=1
        """
        params = []
        if grupo_filtro and grupo_filtro != "Todos":
            query += " AND i.grupo_calculo = ?"
            params.append(grupo_filtro)

        query += " ORDER BY m.nombre"
        return self.db.fetch_all(query, tuple(params))

    def calcular_requerimiento(
        self, grupo_filtro=None, ventas_manuales=None, porcentaje_global=0.0
    ):
        """
        Realiza el cálculo maestro usando el porcentaje sugerido global.
        :param ventas_manuales: (Opcional) Diccionario con ventas simuladas.
        :param porcentaje_global: Porcentaje sugerido a aplicar a la base.
        """

        if ventas_manuales:
            ventas_promedio = ventas_manuales
        else:
            ventas_promedio = self.obtener_promedio_ventas_semanales()

        query_insumos = """
            SELECT id, nombre, unidad_base_id 
            FROM insumos 
            WHERE 1=1
        """
        params = []
        if grupo_filtro and grupo_filtro != "Todos":
            query_insumos += " AND grupo_calculo = ?"
            params.append(grupo_filtro)

        query_insumos += " ORDER BY nombre ASC"

        insumos = self.db.fetch_all(query_insumos, tuple(params))

        reporte = []

        # --- CORRECCIÓN: Se usa el porcentaje global en lugar del factor del insumo ---
        factor_val = 1.0 + (porcentaje_global / 100.0)

        for ins in insumos:
            ins_id, ins_nombre, u_base_id = ins

            u_row = self.db.fetch_all(
                "SELECT abreviatura FROM unidades_medida WHERE id=?", (u_base_id,)
            )
            unidad_nombre = u_row[0][0] if u_row else "??"

            query_recetas = """
                SELECT m.codigo, m.nombre, r.cantidad_necesaria 
                FROM recetas r
                JOIN menu_items m ON r.menu_item_id = m.id
                WHERE r.insumo_id = ?
            """
            usos = self.db.fetch_all(query_recetas, (ins_id,))

            total_semanal_base = 0.0
            detalle_uso = []

            for uso in usos:
                cod_prod = uso[0]
                nom_prod = uso[1]
                cant_receta = uso[2]

                consumo_plato_semanal = 0.0

                if cod_prod in ventas_promedio:
                    dias_venta = ventas_promedio[cod_prod]
                    total_ventas_item_semana = sum(dias_venta.values())

                    consumo_plato_semanal = total_ventas_item_semana * cant_receta

                if consumo_plato_semanal > 0:
                    detalle_uso.append(
                        f"{nom_prod}: {consumo_plato_semanal:.2f} {unidad_nombre}"
                    )
                    total_semanal_base += consumo_plato_semanal

            if total_semanal_base == 0:
                continue

            total_semanal_ajustado = total_semanal_base * factor_val
            total_mensual = total_semanal_ajustado * 4

            compra_sugerida = self.calcular_presentacion_compra(
                ins_id, total_mensual, unidad_nombre
            )

            reporte.append(
                {
                    "insumo": ins_nombre,
                    "unidad": unidad_nombre,
                    "semanal": total_semanal_ajustado,
                    "mensual": total_mensual,
                    "compra": compra_sugerida,
                    "detalle": "\n".join(detalle_uso)
                    + f"\n(Factor aplicado: {factor_val:.2f} por {porcentaje_global}%)",
                }
            )

        return reporte

    def calcular_presentacion_compra(
        self, insumo_id, cantidad_necesaria, unidad_nombre
    ):
        pres = self.db.fetch_all(
            """
            SELECT nombre, cantidad_contenido 
            FROM presentaciones_compra 
            WHERE insumo_id = ? 
            ORDER BY cantidad_contenido DESC
        """,
            (insumo_id,),
        )

        if not pres:
            return f"{cantidad_necesaria:.2f} {unidad_nombre} (Sin presentación)"

        nombre_pres = pres[0][0]
        contenido = pres[0][1]

        if contenido <= 0:
            return "Error config"

        paquetes_compra = math.ceil(cantidad_necesaria / contenido)

        return f"{paquetes_compra} x {nombre_pres} (Total: {paquetes_compra * contenido:.2f} {unidad_nombre})"

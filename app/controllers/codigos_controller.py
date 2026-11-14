# [FILE: app/controllers/codigos_controller.py]
import sqlite3


class CodigosController:
    """Gestión de códigos de barras / QR de insumos y presentaciones.

    Un insumo puede tener varios códigos: los que traen los productos de fábrica
    ('FABRICANTE') y los que imprimimos nosotros ('INTERNO'). Cada código puede,
    opcionalmente, apuntar a una presentación de compra concreta para conocer la
    unidad de conteo y el peso estándar al escanear.
    """

    def __init__(self, db_manager):
        self.db = db_manager

    # ── Resolución (lectura del escáner) ──────────────────────────────────────

    def resolver_codigo(self, codigo):
        """Devuelve un dict con la info del insumo/presentación del código, o None.

        dict: {insumo_id, nombre, unidad_base, presentacion_id, presentacion_nombre,
               factor, tipo}
        factor = cantidad_contenido de la presentación (para convertir a unidad
        base), o 1.0 si el código está a nivel de insumo.
        """
        codigo = (codigo or "").strip()
        if not codigo:
            return None

        row = self.db.fetch_one(
            """
            SELECT cb.insumo_id,
                   i.nombre,
                   um.abreviatura,
                   cb.presentacion_id,
                   pc.nombre,
                   pc.cantidad_contenido,
                   cb.tipo
            FROM codigos_barras cb
            JOIN insumos i          ON i.id = cb.insumo_id
            LEFT JOIN unidades_medida um ON um.id = i.unidad_base_id
            LEFT JOIN presentaciones_compra pc ON pc.id = cb.presentacion_id
            WHERE cb.codigo = ?
            """,
            (codigo,),
        )
        if not row:
            return None

        insumo_id, nombre, unidad, pres_id, pres_nombre, pres_cont, tipo = row
        factor = float(pres_cont) if (pres_id and pres_cont) else 1.0
        return {
            "insumo_id": insumo_id,
            "nombre": nombre,
            "unidad_base": unidad or "unidad",
            "presentacion_id": pres_id,
            "presentacion_nombre": pres_nombre,
            "factor": factor,
            "tipo": tipo,
        }

    # ── Alta de códigos ───────────────────────────────────────────────────────

    def registrar_codigo(self, codigo, insumo_id, presentacion_id=None,
                         tipo="FABRICANTE", descripcion=None):
        """Registra un código existente (p.ej. escaneado de fábrica).

        Devuelve (True, mensaje) o (False, mensaje) si ya existe / hay error.
        """
        codigo = (codigo or "").strip()
        if not codigo:
            return False, "El código está vacío."

        existente = self.db.fetch_one(
            """
            SELECT cb.codigo, i.nombre
            FROM codigos_barras cb
            JOIN insumos i ON i.id = cb.insumo_id
            WHERE cb.codigo = ?
            """,
            (codigo,),
        )
        if existente:
            return False, f"El código '{codigo}' ya está asignado a: {existente[1]}."

        try:
            self.db.execute_query(
                """
                INSERT INTO codigos_barras (codigo, insumo_id, presentacion_id, tipo, descripcion)
                VALUES (?, ?, ?, ?, ?)
                """,
                (codigo, insumo_id, presentacion_id, tipo, descripcion),
            )
            return True, f"Código '{codigo}' registrado."
        except sqlite3.IntegrityError:
            return False, f"El código '{codigo}' ya existe."
        except Exception as e:
            return False, f"Error al registrar el código: {e}"

    def reasignar_codigo(self, codigo, insumo_id, presentacion_id=None,
                        tipo="FABRICANTE"):
        """Mueve un código existente a otro insumo/presentación.

        Útil cuando un código quedó asignado por error a otro producto.
        Devuelve (True, mensaje) o (False, mensaje).
        """
        codigo = (codigo or "").strip()
        if not codigo:
            return False, "El código está vacío."
        try:
            self.db.execute_query(
                """
                UPDATE codigos_barras
                SET insumo_id = ?, presentacion_id = ?, tipo = ?
                WHERE codigo = ?
                """,
                (insumo_id, presentacion_id, tipo, codigo),
            )
            return True, f"Código '{codigo}' reasignado a este insumo."
        except Exception as e:
            return False, f"Error al reasignar el código: {e}"

    def generar_codigo_interno(self, insumo_id, presentacion_id=None):
        """Crea un código interno único para imprimir en etiqueta y lo devuelve.

        Formato: ITL-{insumo:05d}[-P{presentacion}]. Si colisiona, añade sufijo.
        Devuelve (codigo, mensaje) o (None, mensaje_error).
        """
        base = f"ITL-{int(insumo_id):05d}"
        if presentacion_id:
            base += f"-P{int(presentacion_id)}"

        codigo = base
        sufijo = 1
        # Evitar colisión con códigos ya existentes
        while self.db.fetch_one("SELECT 1 FROM codigos_barras WHERE codigo = ?", (codigo,)):
            sufijo += 1
            codigo = f"{base}-{sufijo}"

        try:
            self.db.execute_query(
                """
                INSERT INTO codigos_barras (codigo, insumo_id, presentacion_id, tipo, descripcion)
                VALUES (?, ?, ?, 'INTERNO', ?)
                """,
                (codigo, insumo_id, presentacion_id, "Código interno generado"),
            )
            return codigo, f"Código interno '{codigo}' generado."
        except Exception as e:
            return None, f"Error al generar el código: {e}"

    # ── Consulta / borrado ────────────────────────────────────────────────────

    def listar_codigos(self, insumo_id):
        """Devuelve la lista de códigos de un insumo con su presentación (si aplica)."""
        return self.db.fetch_all(
            """
            SELECT cb.id, cb.codigo, cb.tipo, cb.presentacion_id, pc.nombre, cb.descripcion
            FROM codigos_barras cb
            LEFT JOIN presentaciones_compra pc ON pc.id = cb.presentacion_id
            WHERE cb.insumo_id = ?
            ORDER BY cb.tipo, cb.codigo
            """,
            (insumo_id,),
        )

    def contar_codigos(self, insumo_id):
        row = self.db.fetch_one(
            "SELECT COUNT(*) FROM codigos_barras WHERE insumo_id = ?", (insumo_id,)
        )
        return row[0] if row else 0

    def eliminar_codigo(self, codigo_id):
        try:
            self.db.execute_query("DELETE FROM codigos_barras WHERE id = ?", (codigo_id,))
            return True, "Código eliminado."
        except Exception as e:
            return False, f"Error al eliminar: {e}"

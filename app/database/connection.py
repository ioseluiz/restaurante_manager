# [FILE: app/database/connection.py]
import sqlite3
import os
import hashlib
import shutil
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_name=None):
        # Si no se pasa nombre, intenta cargar de la configuración o usa el default
        if db_name is None:
            from app.database.config import get_db_path

            db_name = get_db_path()

        self.db_path = db_name
        self.connect()

    def connect(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.cursor = self.conn.cursor()
        self.initialize_tables()
        self.create_default_admin()
        self._migrate_tables()

    def switch_database(self, new_path):
        """Cierra la conexión actual y abre una nueva en la ruta especificada."""
        self.conn.close()
        self.db_path = new_path
        from app.database.config import save_db_path

        save_db_path(new_path)
        self.connect()

    def create_backup(self, dest_folder):
        """Crea una copia de seguridad del archivo actual."""
        try:
            filename = (
                f"backup_restaurante_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            )
            dest_path = os.path.join(dest_folder, filename)
            shutil.copy2(self.db_path, dest_path)
            return True, dest_path
        except Exception as e:
            return False, str(e)

    def initialize_tables(self):
        """
        Inicializa las tablas de la base de datos.
        """
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS unidades_medida (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                abreviatura TEXT NOT NULL
            );
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversiones_unidades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unidad_origen_id INTEGER NOT NULL,
                unidad_destino_id INTEGER NOT NULL,
                factor_conversion REAL NOT NULL,
                FOREIGN KEY (unidad_origen_id) REFERENCES unidades_medida(id),
                FOREIGN KEY (unidad_destino_id) REFERENCES unidades_medida(id)
            );
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS insumos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                unidad_base_id INTEGER NOT NULL,
                categoria_id INTEGER, 
                stock_actual REAL DEFAULT 0.0,
                costo_unitario REAL DEFAULT 0.0,
                grupo_calculo TEXT,
                factor_calculo REAL DEFAULT 1.0,
                FOREIGN KEY (unidad_base_id) REFERENCES unidades_medida(id)
            );
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS presentaciones_compra (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                insumo_id INTEGER NOT NULL,
                nombre TEXT NOT NULL,
                cantidad_contenido REAL NOT NULL,
                precio_compra REAL NOT NULL, 
                costo_unitario_calculado REAL, 
                FOREIGN KEY (insumo_id) REFERENCES insumos(id)
            );
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS composicion_empaque (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                presentacion_id INTEGER NOT NULL,
                nombre_empaque_interno TEXT NOT NULL,
                cantidad_interna INTEGER NOT NULL,
                peso_o_volumen_unitario REAL NOT NULL,
                FOREIGN KEY (presentacion_id) REFERENCES presentaciones_compra(id) ON DELETE CASCADE
            );
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS proveedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                contacto TEXT,
                telefono TEXT,
                tipo TEXT DEFAULT 'PROVEEDOR'
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proveedor_id INTEGER NOT NULL,
                fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
                fecha_compra TEXT,
                total REAL DEFAULT 0.0,
                estado TEXT DEFAULT 'PENDIENTE',
                tipo_pago TEXT DEFAULT 'CONTADO',
                presupuesto_id INTEGER,
                FOREIGN KEY (proveedor_id) REFERENCES proveedores(id),
                FOREIGN KEY (presupuesto_id) REFERENCES presupuestos(id)
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS detalle_compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                compra_id INTEGER NOT NULL,
                presentacion_id INTEGER NOT NULL,
                cantidad REAL NOT NULL,
                precio_unitario REAL NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (compra_id) REFERENCES compras(id) ON DELETE CASCADE,
                FOREIGN KEY (presentacion_id) REFERENCES presentaciones_compra(id)
            );
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias_insumos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL UNIQUE,
                nombre TEXT NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS reportes_ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
                fecha_inicio_periodo DATE,
                fecha_fin_periodo DATE,
                mes INTEGER, 
                anio INTEGER,
                total_venta_reportada REAL DEFAULT 0.0,
                porcentaje_sugerido REAL DEFAULT 0.0,
                observaciones TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS detalle_reportes_ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporte_id INTEGER NOT NULL,
                codigo_producto TEXT,
                nombre_producto TEXT,
                dia_semana TEXT, 
                cantidad REAL DEFAULT 0.0,
                promedio_medida REAL DEFAULT 0.0,
                total_venta REAL DEFAULT 0.0,
                total_costo REAL DEFAULT 0.0,
                total_utilidad REAL DEFAULT 0.0,
                FOREIGN KEY (reporte_id) REFERENCES reportes_ventas(id) ON DELETE CASCADE
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL UNIQUE,
                nombre TEXT NOT NULL,
                precio_venta REAL NOT NULL,
                es_preparado BOOLEAN DEFAULT 1
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS recetas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                menu_item_id INTEGER,
                insumo_id INTEGER,
                cantidad_necesaria REAL,
                FOREIGN KEY(menu_item_id) REFERENCES menu_items(id),
                FOREIGN KEY(insumo_id) REFERENCES insumos(id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                total REAL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                rol TEXT DEFAULT 'empleado'
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS movimientos_inventario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                insumo_id INTEGER NOT NULL,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                tipo_movimiento TEXT NOT NULL, 
                cantidad REAL NOT NULL,
                stock_anterior REAL,
                stock_nuevo REAL,
                referencia_id INTEGER,
                observacion TEXT,
                FOREIGN KEY (insumo_id) REFERENCES insumos(id)
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS registro_ventas_diarias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATE UNIQUE NOT NULL,
                inventario_descontado BOOLEAN DEFAULT 0,
                fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS detalle_ventas_diarias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                registro_diario_id INTEGER NOT NULL,
                menu_item_id INTEGER NOT NULL,
                cantidad REAL DEFAULT 0.0,
                FOREIGN KEY (registro_diario_id) REFERENCES registro_ventas_diarias(id) ON DELETE CASCADE,
                FOREIGN KEY (menu_item_id) REFERENCES menu_items(id)
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS presupuestos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero INTEGER,
                mes INTEGER,
                anio INTEGER,
                descripcion TEXT,
                monto_total REAL DEFAULT 0.0,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS presupuesto_reportes (
                presupuesto_id INTEGER,
                reporte_id INTEGER,
                FOREIGN KEY (presupuesto_id) REFERENCES presupuestos(id) ON DELETE CASCADE,
                FOREIGN KEY (reporte_id) REFERENCES reportes_ventas(id) ON DELETE CASCADE,
                PRIMARY KEY (presupuesto_id, reporte_id)
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS detalle_presupuestos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                presupuesto_id INTEGER,
                categoria_nombre TEXT,
                insumo_nombre TEXT,
                unidad_nombre TEXT,
                cantidad_requerida REAL,
                monto_estimado REAL,
                items_menu TEXT,
                detalle_calculo TEXT,
                porcentaje_usado REAL DEFAULT 0.0,
                FOREIGN KEY (presupuesto_id) REFERENCES presupuestos(id) ON DELETE CASCADE
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS chequera (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATE NOT NULL,
                no_ck TEXT,
                nombre_cheque TEXT,
                detalle TEXT,
                deposito REAL DEFAULT 0.0,
                monto REAL DEFAULT 0.0
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tarjetas_credito (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero TEXT NOT NULL,
                tipo TEXT NOT NULL,
                banco TEXT NOT NULL
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transacciones_tarjeta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tarjeta_id INTEGER NOT NULL,
                fecha DATE NOT NULL,
                comercio TEXT,
                descripcion TEXT,
                tipo_transaccion TEXT NOT NULL,
                monto REAL DEFAULT 0.0,
                FOREIGN KEY(tarjeta_id) REFERENCES tarjetas_credito(id) ON DELETE CASCADE
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS pagos_efectivo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATE NOT NULL,
                proveedor TEXT,
                descripcion TEXT,
                total REAL DEFAULT 0.0,
                costo_viveres REAL DEFAULT 0.0,
                costo_carnes REAL DEFAULT 0.0,
                desayunos REAL DEFAULT 0.0,
                otros REAL DEFAULT 0.0,
                planilla REAL DEFAULT 0.0,
                gastos_propietarios REAL DEFAULT 0.0,
                honorarios REAL DEFAULT 0.0,
                reparaciones_mantenimiento REAL DEFAULT 0.0,
                atencion_empleados REAL DEFAULT 0.0,
                combustible REAL DEFAULT 0.0,
                medicamentos REAL DEFAULT 0.0
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS yappy_cuentas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                numero TEXT NOT NULL
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transacciones_yappy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                yappy_id INTEGER NOT NULL,
                fecha DATE NOT NULL,
                proveedor TEXT,
                descripcion TEXT,
                monto REAL DEFAULT 0.0,
                FOREIGN KEY(yappy_id) REFERENCES yappy_cuentas(id) ON DELETE CASCADE
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS diario_ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATE NOT NULL,
                total_ventas REAL DEFAULT 0.0,
                yappy REAL DEFAULT 0.0,
                pedidos_ya REAL DEFAULT 0.0,
                no_facturas INTEGER DEFAULT 0,
                sobrante REAL DEFAULT 0.0,
                faltante REAL DEFAULT 0.0,
                depositos REAL DEFAULT 0.0
            );
        """)

        self.conn.commit()
    def _migrate_tables(self):
        try:
            self.cursor.execute("ALTER TABLE insumos ADD COLUMN grupo_calculo TEXT")
        except sqlite3.OperationalError:
            pass

        try:
            self.cursor.execute(
                "ALTER TABLE insumos ADD COLUMN factor_calculo REAL DEFAULT 1.0"
            )
        except sqlite3.OperationalError:
            pass

        try:
            self.cursor.execute(
                "ALTER TABLE detalle_presupuestos ADD COLUMN unidad_nombre TEXT"
            )
        except sqlite3.OperationalError:
            pass

        try:
            self.cursor.execute(
                "ALTER TABLE detalle_presupuestos ADD COLUMN detalle_calculo TEXT"
            )
        except sqlite3.OperationalError:
            pass

        try:
            self.cursor.execute("ALTER TABLE compras ADD COLUMN presupuesto_id INTEGER")
        except sqlite3.OperationalError:
            pass

        try:
            self.cursor.execute(
                "ALTER TABLE reportes_ventas ADD COLUMN porcentaje_sugerido REAL DEFAULT 0.0"
            )
        except sqlite3.OperationalError:
            pass

        # --- NUEVO: Migración para añadir el porcentaje_usado por insumo en el presupuesto ---
        try:
            self.cursor.execute(
                "ALTER TABLE detalle_presupuestos ADD COLUMN porcentaje_usado REAL DEFAULT 0.0"
            )
        except sqlite3.OperationalError:
            pass

        self.conn.commit()

    def create_default_admin(self):
        try:
            check = self.cursor.execute(
                "SELECT * FROM usuarios WHERE username='admin'"
            ).fetchone()
            if not check:
                pwd_hash = hashlib.sha256("admin123".encode()).hexdigest()
                self.cursor.execute(
                    "INSERT INTO usuarios (username, password_hash, rol) VALUES (?,?,?)",
                    ("admin", pwd_hash, "admin"),
                )
                self.conn.commit()
        except sqlite3.OperationalError:
            pass

    def execute_query(self, query, params=()):
        self.cursor.execute(query, params)
        self.conn.commit()
        return self.cursor

    def fetch_all(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def fetch_one(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def guardar_reporte_mensual(self, metadata, records):
        try:
            fecha_inicio = metadata.get("desde", "")
            fecha_fin = metadata.get("hasta", "")
            pct_sugerido = metadata.get("pct_sugerido", 0.0)
            total_global = sum(r["total_venta"] for r in records)

            query_header = """
                INSERT INTO reportes_ventas 
                (fecha_inicio_periodo, fecha_fin_periodo, total_venta_reportada, porcentaje_sugerido, observaciones)
                VALUES (?, ?, ?, ?, ?)
            """
            self.cursor.execute(
                query_header,
                (
                    fecha_inicio,
                    fecha_fin,
                    total_global,
                    pct_sugerido,
                    "Carga desde CSV",
                ),
            )
            reporte_id = self.cursor.lastrowid

            query_detail = """
                INSERT INTO detalle_reportes_ventas 
                (reporte_id, codigo_producto, nombre_producto, dia_semana, cantidad, promedio_medida, total_venta, total_costo, total_utilidad)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            data_tuples = []
            for r in records:
                data_tuples.append(
                    (
                        reporte_id,
                        r["code"],
                        r["desc"],
                        r["day"],
                        r["qty"],
                        r.get("prom", 0.0),
                        r["total_venta"],
                        r.get("total_costo", 0.0),
                        r.get("total_utilidad", 0.0),
                    )
                )

            self.cursor.executemany(query_detail, data_tuples)
            self.conn.commit()
            return (
                True,
                f"Reporte guardado con éxito. ID: {reporte_id}. {len(records)} registros.",
            )

        except Exception as e:
            self.conn.rollback()
            return False, f"Error al guardar reporte: {str(e)}"

    def obtener_reportes_registrados(self):
        query = """
            SELECT id, fecha_inicio_periodo, fecha_fin_periodo, total_venta_reportada, porcentaje_sugerido, fecha_registro 
            FROM reportes_ventas ORDER BY id DESC
        """
        return self.fetch_all(query)

    def obtener_detalle_reporte(self, reporte_id):
        query = """
            SELECT codigo_producto, nombre_producto, dia_semana, cantidad, promedio_medida, total_venta, total_costo, total_utilidad
            FROM detalle_reportes_ventas WHERE reporte_id = ?
        """
        return self.fetch_all(query, (reporte_id,))

    def eliminar_reporte(self, reporte_id):
        try:
            self.execute_query(
                "DELETE FROM reportes_ventas WHERE id = ?", (reporte_id,)
            )
            return True, "Reporte eliminado."
        except Exception as e:
            return False, str(e)

    def obtener_todos_codigos_menu(self):
        query = "SELECT codigo FROM menu_items"
        resultados = self.fetch_all(query)
        return [r[0] for r in resultados]

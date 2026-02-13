# [FILE: app/database/connection.py]
import sqlite3
import os
import hashlib


class DatabaseManager:
    def __init__(self, db_name="data/restaurante.db"):
        os.makedirs(os.path.dirname(db_name), exist_ok=True)
        self.conn = sqlite3.connect(db_name)
        # Habilitar Foreign Keys es vital
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.cursor = self.conn.cursor()
        self.initialize_tables()
        self.create_default_admin()
        self._migrate_tables()

    def initialize_tables(self):
        """
        Inicializa las tablas de la base de datos.
        """
        # --- TABLAS EXISTENTES ---
        # 1. Unidades
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS unidades_medida (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                abreviatura TEXT NOT NULL
            );
        """)
        # 2. Conversiones
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
        # 3. Insumos
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
        # 4. Presentaciones
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
        # 5. Composicion Empaque
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
        # 6. Proveedores
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS proveedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                contacto TEXT,
                telefono TEXT,
                tipo TEXT DEFAULT 'PROVEEDOR'
            );
        """)
        # 7. Compras
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proveedor_id INTEGER NOT NULL,
                fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
                fecha_compra TEXT,
                total REAL DEFAULT 0.0,
                estado TEXT DEFAULT 'PENDIENTE',
                tipo_pago TEXT DEFAULT 'CONTADO',
                FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
            );
        """)
        # 8. Detalle Compras
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
        # Categorias Insumos
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias_insumos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL UNIQUE,
                nombre TEXT NOT NULL
            )
        """)

        # --- NUEVA ESTRUCTURA DE REPORTES DE VENTAS (MENSUAL) ---

        # Cabecera del Reporte Mensual
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS reportes_ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
                fecha_inicio_periodo DATE,
                fecha_fin_periodo DATE,
                mes INTEGER, -- 1 al 12
                anio INTEGER,
                total_venta_reportada REAL DEFAULT 0.0,
                observaciones TEXT
            )
        """)

        # Detalle del Reporte Mensual (Remplaza a ventas_reporte_semanal)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS detalle_reportes_ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporte_id INTEGER NOT NULL,
                codigo_producto TEXT,
                nombre_producto TEXT,
                dia_semana TEXT, -- Domingo, Lunes, etc.
                cantidad REAL DEFAULT 0.0,
                promedio_medida REAL DEFAULT 0.0,
                total_venta REAL DEFAULT 0.0,
                total_costo REAL DEFAULT 0.0,
                total_utilidad REAL DEFAULT 0.0,
                FOREIGN KEY (reporte_id) REFERENCES reportes_ventas(id) ON DELETE CASCADE
            )
        """)

        # Menu Items
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL UNIQUE,
                nombre TEXT NOT NULL,
                precio_venta REAL NOT NULL,
                es_preparado BOOLEAN DEFAULT 1
            )
        """)
        # Recetas
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
        # Ventas (Registro simple, puede ser depurado en el futuro)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                total REAL
            )
        """)
        # Usuarios
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                rol TEXT DEFAULT 'empleado'
            )
        """)

        # --- KARDEX (MOVIMIENTOS DE INVENTARIO) ---
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

        # Registro Diario (Cabecera)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS registro_ventas_diarias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATE UNIQUE NOT NULL,
                inventario_descontado BOOLEAN DEFAULT 0,
                fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Detalle Ventas (Solo Cantidades)
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

        self.conn.commit()

    def _migrate_tables(self):
        """
        Actualizaciones de estructura seguras
        """
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

    # --- MÉTODOS DE REPORTES ---

    def guardar_reporte_mensual(self, metadata, records):
        """
        Guarda un reporte mensual completo: Cabecera y Detalles.
        """
        try:
            fecha_inicio = metadata.get("desde", "")
            fecha_fin = metadata.get("hasta", "")
            total_global = sum(r["total_venta"] for r in records)

            query_header = """
                INSERT INTO reportes_ventas 
                (fecha_inicio_periodo, fecha_fin_periodo, total_venta_reportada, observaciones)
                VALUES (?, ?, ?, ?)
            """
            self.cursor.execute(
                query_header, (fecha_inicio, fecha_fin, total_global, "Carga desde CSV")
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
        """Devuelve la lista de reportes cargados para el historial."""
        query = """
            SELECT id, fecha_inicio_periodo, fecha_fin_periodo, total_venta_reportada, fecha_registro 
            FROM reportes_ventas 
            ORDER BY id DESC
        """
        return self.fetch_all(query)

    def obtener_detalle_reporte(self, reporte_id):
        """Devuelve los ítems de un reporte específico."""
        query = """
            SELECT codigo_producto, nombre_producto, dia_semana, cantidad, total_venta, total_costo
            FROM detalle_reportes_ventas
            WHERE reporte_id = ?
        """
        return self.fetch_all(query, (reporte_id,))

    def eliminar_reporte(self, reporte_id):
        """Elimina un reporte y sus detalles (por el ON DELETE CASCADE)."""
        try:
            self.execute_query(
                "DELETE FROM reportes_ventas WHERE id = ?", (reporte_id,)
            )
            return True, "Reporte eliminado."
        except Exception as e:
            return False, str(e)

    def obtener_todos_codigos_menu(self):
        """
        Devuelve una lista plana con todos los códigos de productos (menu_items)
        registrados en la base de datos.
        Utilizado para validaciones al cargar reportes.
        """
        query = "SELECT codigo FROM menu_items"
        resultados = self.fetch_all(query)
        # Convertir de lista de tuplas [(COD1,), (COD2,)] a lista simple [COD1, COD2]
        return [r[0] for r in resultados]

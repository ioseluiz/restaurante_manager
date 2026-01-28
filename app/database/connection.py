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
        # --- TABLAS EXISTENTES (Resumidas para brevedad, mantener tu código original) ---
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
        # Reporte Ventas Semanal
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS ventas_reporte_semanal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_producto TEXT,
                nombre_producto TEXT,
                dia_semana TEXT,
                cantidad REAL,
                promedio_medida REAL,
                total_venta REAL,
                fecha_inicio_reporte TEXT,
                fecha_fin_reporte TEXT,
                fecha_carga DATETIME DEFAULT CURRENT_TIMESTAMP,
                inventario_descontado BOOLEAN DEFAULT 0 -- NUEVO CAMPO
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
        # Ventas
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

        # --- NUEVA TABLA: KARDEX (MOVIMIENTOS DE INVENTARIO) ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS movimientos_inventario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                insumo_id INTEGER NOT NULL,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                tipo_movimiento TEXT NOT NULL, -- 'COMPRA', 'VENTA', 'MERMA', 'AJUSTE'
                cantidad REAL NOT NULL,        -- Positivo para entrada, Negativo para salida
                stock_anterior REAL,
                stock_nuevo REAL,
                referencia_id INTEGER,         -- ID de la Compra o ID del Reporte de Venta
                observacion TEXT,
                FOREIGN KEY (insumo_id) REFERENCES insumos(id)
            );
        """)

        # 12. Registro Diario (Cabecera)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS registro_ventas_diarias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATE UNIQUE NOT NULL,
                inventario_descontado BOOLEAN DEFAULT 0, -- Para saber si ya se restaron los insumos
                fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 13. Detalle Ventas (Solo Cantidades)
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

        # Nueva migración para flag de ventas
        try:
            self.cursor.execute(
                "ALTER TABLE ventas_reporte_semanal ADD COLUMN inventario_descontado BOOLEAN DEFAULT 0"
            )
        except sqlite3.OperationalError:
            pass

        self.conn.commit()

    # ... (Resto de métodos: create_default_admin, execute_query, fetch_all, insert_report_batch se mantienen igual)
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

    def insert_report_batch(self, records, fecha_inicio, fecha_fin):
        # ... (Tu código existente)
        query = """
            INSERT INTO ventas_reporte_semanal 
            (codigo_producto, nombre_producto, dia_semana, cantidad, promedio_medida, total_venta, fecha_inicio_reporte, fecha_fin_reporte, inventario_descontado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
        """
        data = []
        for r in records:
            data.append(
                (
                    r["code"],
                    r["desc"],
                    r["day"],
                    r["qty"],
                    r.get("prom", 0.0),
                    r["total"],
                    fecha_inicio,
                    fecha_fin,
                )
            )
        try:
            self.cursor.executemany(query, data)
            self.conn.commit()
            return True, f"{self.cursor.rowcount} registros insertados."
        except Exception as e:
            self.conn.rollback()
            return False, str(e)

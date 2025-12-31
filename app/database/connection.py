import sqlite3
import os
import hashlib


class DatabaseManager:
    def __init__(self, db_name="data/restaurante.db"):
        os.makedirs(os.path.dirname(db_name), exist_ok=True)
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.initialize_tables()
        self.check_schema_updates()  # Migración para DB existentes
        self.create_default_admin()

    def initialize_tables(self):
        # --- NUEVA TABLA: Categorias de Insumos ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias_insumos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL UNIQUE,
                nombre TEXT NOT NULL
            )
        """)

        # Tabla de insumos (Inventario)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS insumos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                unidad_medida TEXT NOT NULL,
                stock_actual REAL DEFAULT 0,
                costo_unitario REAL DEFAULT 0,
                categoria_id INTEGER REFERENCES categorias_insumos(id)
            )
        """)

        # --- TABLA ACTUALIZADA: Detalle de Reportes de Ventas ---
        # Ahora incluye promedio_medida
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
                fecha_carga DATETIME DEFAULT CURRENT_TIMESTAMP
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
                FOREIGN KEY(menu_item_id) REFERENCES insumos(id)
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
        self.conn.commit()

    def check_schema_updates(self):
        """Revisa y aplica actualizaciones de estructura en tablas existentes."""
        try:
            # Intentar agregar categoria_id a insumos
            self.cursor.execute(
                "ALTER TABLE insumos ADD COLUMN categoria_id INTEGER REFERENCES categorias_insumos(id)"
            )
            self.conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            # Intentar agregar promedio_medida a ventas_reporte_semanal
            self.cursor.execute(
                "ALTER TABLE ventas_reporte_semanal ADD COLUMN promedio_medida REAL"
            )
            self.conn.commit()
        except sqlite3.OperationalError:
            pass

    def create_default_admin(self):
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

    def execute_query(self, query, params=()):
        self.cursor.execute(query, params)
        self.conn.commit()
        return self.cursor

    def fetch_all(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def insert_report_batch(self, records, fecha_inicio, fecha_fin):
        """
        Inserta un lote de registros provenientes del ReportParser.
        """
        query = """
            INSERT INTO ventas_reporte_semanal 
            (codigo_producto, nombre_producto, dia_semana, cantidad, promedio_medida, total_venta, fecha_inicio_reporte, fecha_fin_reporte)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        data = []
        for r in records:
            data.append(
                (
                    r["code"],
                    r["desc"],
                    r["day"],
                    r["qty"],
                    r.get("prom", 0.0),  # Nuevo campo Promedio
                    r["total"],
                    fecha_inicio,
                    fecha_fin,
                )
            )

        try:
            self.cursor.executemany(query, data)
            self.conn.commit()
            return True, f"{self.cursor.rowcount} registros insertados correctamente."
        except Exception as e:
            self.conn.rollback()
            return False, str(e)

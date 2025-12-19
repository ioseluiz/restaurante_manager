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
        # Nota: En SQLite agregar FK a tabla existente es complejo,
        # se maneja en 'check_schema_updates' o en create para nuevas DB.
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

        # ... (Resto de tablas menu_items, recetas, ventas, usuarios igual que antes) ...
        self.cursor.execute("""
                            CREATE TABLE IF NOT EXISTS menu_items (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                codigo TEXT NOT NULL UNIQUE,
                                nombre TEXT NOT NULL,
                                precio_venta REAL NOT NULL,
                                es_preparado BOOLEAN DEFAULT 1
                            )
                            """)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS recetas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                menu_item_id INTEGER,
                insumo_id INTEGER,
                cantidad_necesaria REAL,
                FOREIGN KEY(menu_item_id) REFERENCES insumos(id)
            )
            """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                total REAL
            )
            """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                rol TEXT DEFAULT 'empleado'
            )
            """
        )
        self.conn.commit()

    def check_schema_updates(self):
        """Revisa si existen las columnas nuevas en tablas viejas"""
        try:
            # Intentamos agregar la columna categoria_id si no existe
            self.cursor.execute(
                "ALTER TABLE insumos ADD COLUMN categoria_id INTEGER REFERENCES categorias_insumos(id)"
            )
            self.conn.commit()
        except sqlite3.OperationalError:
            # La columna ya existe, ignoramos el error
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

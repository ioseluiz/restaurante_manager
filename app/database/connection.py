import sqlite3
import os
import hashlib


class DatabaseManager:
    def __init__(self, db_name="data/restaurante.db"):
        os.makedirs(os.path.dirname(db_name), exist_ok=True)
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.initialize_tables()
        self.create_default_admin()

    def initialize_tables(self):
        # Table de insumos (Inventario)
        self.cursor.execute("""
                            CREATE TABLE IF NOT EXISTS insumos (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                nombre TEXT NOT NULL,
                                unidad_medida TEXT NOT NULL, --kg litros, unidad
                                stock_actual REAL DEFAULT 0,
                                costo_unitario REAL DEFAULT 0
                            )
                            """)
        # Tabla del Menu (Platos y Bebidas)
        self.cursor.execute("""
                            CREATE TABLE IF NOT EXISTS menu_items (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                codigo TEXT NOT NULL UNIQUE,
                                nombre TEXT NOT NULL,
                                precio_venta REAL NOT NULL,
                                es_preparado BOOLEAN DEFAULT 1 -- 1=Plato (usa receta), 0=Bebida/Directo
                            )
                            """)

        # Tabla de Recetas (Relacion Menu -> Insumos )
        # Esto es lo que permite el presupuesto y descuento automatico de inventario
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

        # Tabla de Ventas (Cabecera)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                total REAL
            )
            """
        )

        # Tabla de usuarios
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

    def create_default_admin(self):
        # Crear usuario 'admin' con clave 'admin123' si no existe
        check = self.cursor.execute(
            """
            SELECT * FROM usuarios WHERE username='admin'
            """
        ).fetchone()
        if not check:
            # En produccion usa brypt, para este demo usamos sha256
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

import sqlite3
import os
import hashlib


class DatabaseManager:
    def __init__(self, db_name="data/restaurante.db"):
        os.makedirs(os.path.dirname(db_name), exist_ok=True)
        self.conn = sqlite3.connect(db_name)
        # Habilitar Foreign Keys es vital para que no queden datos huérfanos
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.cursor = self.conn.cursor()
        self.initialize_tables()
        self.create_default_admin()

    def initialize_tables(self):
        """
        Inicializa las tablas de la base de datos.
        Integra el nuevo módulo de cálculo de insumos y mantiene el historial de ventas/usuarios.
        """

        # --- 1. Unidades de Medida (NUEVO) ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS unidades_medida (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                abreviatura TEXT NOT NULL
            );
        """)

        # --- 2. Conversiones (Kilos <-> Libras <-> Unidades) (NUEVO) ---
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

        # --- 3. Insumos (ACTUALIZADO - Ahora relacional) ---
        # Nota: Se ha cambiado unidad_medida (TEXT) por unidad_base_id (INTEGER FK)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS insumos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                unidad_base_id INTEGER NOT NULL,
                categoria_id INTEGER, -- Mantenemos esto por compatibilidad si usas categorias_insumos
                FOREIGN KEY (unidad_base_id) REFERENCES unidades_medida(id)
            );
        """)

        # --- 4. Presentaciones de Compra (NUEVO) ---
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

        # --- 5. Composición Empaque (NUEVO) ---
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

        # --- MÓDULOS EXISTENTES (COMPATIBILIDAD) ---

        # Categorías de Insumos (Opcional, mantenida de tu versión anterior)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias_insumos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL UNIQUE,
                nombre TEXT NOT NULL
            )
        """)

        # Detalle de Reportes de Ventas
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

        # Items del Menú
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL UNIQUE,
                nombre TEXT NOT NULL,
                precio_venta REAL NOT NULL,
                es_preparado BOOLEAN DEFAULT 1
            )
        """)

        # Recetas (Podría requerir actualización futura para usar unidades_medida)
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

        # Ventas Generales
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                total REAL
            )
        """)

        # Usuarios y Autenticación
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                rol TEXT DEFAULT 'empleado'
            )
        """)

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
            # Manejo de error si la tabla usuarios no está lista
            pass

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
                    r.get("prom", 0.0),  # Campo Promedio
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

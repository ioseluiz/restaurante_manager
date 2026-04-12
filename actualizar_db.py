# [FILE: actualizar_db.py]
import sqlite3
import os

# Apuntamos a la carpeta data explícitamente
DB_NAME = "data/restaurante.db"


def migrar_db():
    # Verificamos que el archivo exista antes de intentar conectar
    if not os.path.exists(DB_NAME):
        print(f"ERROR: No se encuentra la base de datos en '{DB_NAME}'")
        print(
            "Verifica que estás ejecutando el script desde la carpeta raíz del proyecto."
        )
        return

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        print(f"Conectado a: {DB_NAME}")

        # Migración anterior
        try:
            print("Verificando/Agregando columna 'tipo_pago'...")
            cursor.execute(
                "ALTER TABLE compras ADD COLUMN tipo_pago TEXT DEFAULT 'CONTADO'"
            )
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(" -> La columna 'tipo_pago' ya existía.")

        # --- NUEVA MIGRACIÓN: Enlace de Compras a Presupuestos ---
        try:
            print("Agregando columna 'presupuesto_id' a la tabla 'compras'...")
            cursor.execute("ALTER TABLE compras ADD COLUMN presupuesto_id INTEGER")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(" -> La columna 'presupuesto_id' ya existía.")
            else:
                print(f"Error SQL: {e}")

        # --- NUEVA MIGRACIÓN: Tarjetas de Crédito ---
        try:
            print("Agregando columna 'fecha_corte' a la tabla 'tarjetas_credito'...")
            cursor.execute("ALTER TABLE tarjetas_credito ADD COLUMN fecha_corte TEXT")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(" -> La columna 'fecha_corte' ya existía.")
            else:
                print(f"Error SQL: {e}")

        try:
            print("Agregando columna 'fecha_pago' a la tabla 'tarjetas_credito'...")
            cursor.execute("ALTER TABLE tarjetas_credito ADD COLUMN fecha_pago TEXT")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(" -> La columna 'fecha_pago' ya existía.")
            else:
                print(f"Error SQL: {e}")

        try:
            print("Agregando columna 'tasa_interes' a la tabla 'tarjetas_credito'...")
            cursor.execute("ALTER TABLE tarjetas_credito ADD COLUMN tasa_interes REAL")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(" -> La columna 'tasa_interes' ya existía.")
            else:
                print(f"Error SQL: {e}")

        # --- NUEVA MIGRACIÓN: Eliminar depósito de chequera ---
        try:
            print("Eliminando columna 'deposito' de la tabla 'chequera'...")
            cursor.execute("ALTER TABLE chequera DROP COLUMN deposito")
        except sqlite3.OperationalError as e:
            if "no such column" in str(e).lower():
                print(" -> La columna 'deposito' ya fue eliminada o no existe.")
            else:
                print(f"Error SQL al eliminar 'deposito': {e}")

        # --- NUEVA MIGRACIÓN: Diario de Ventas ---
        try:
            print("Agregando columna 'clave' a la tabla 'diario_ventas'...")
            cursor.execute("ALTER TABLE diario_ventas ADD COLUMN clave REAL DEFAULT 0.0")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(" -> La columna 'clave' ya existía.")
            else:
                print(f"Error SQL al agregar 'clave': {e}")

        try:
            print("Agregando columna 'visa_mastercard' a la tabla 'diario_ventas'...")
            cursor.execute("ALTER TABLE diario_ventas ADD COLUMN visa_mastercard REAL DEFAULT 0.0")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(" -> La columna 'visa_mastercard' ya existía.")
            else:
                print(f"Error SQL al agregar 'visa_mastercard': {e}")

        try:
            print("Agregando columna 'vale' a la tabla 'diario_ventas'...")
            cursor.execute("ALTER TABLE diario_ventas ADD COLUMN vale REAL DEFAULT 0.0")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(" -> La columna 'vale' ya existía.")
            else:
                print(f"Error SQL al agregar 'vale': {e}")

        try:
            print("Agregando columna 'vale_descripcion' a la tabla 'diario_ventas'...")
            cursor.execute("ALTER TABLE diario_ventas ADD COLUMN vale_descripcion TEXT")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(" -> La columna 'vale_descripcion' ya existía.")
            else:
                print(f"Error SQL al agregar 'vale_descripcion': {e}")

        # --- NUEVA MIGRACIÓN: Configuracion de Comisiones ---
        try:
            print("Creando tabla 'configuracion_comisiones'...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS configuracion_comisiones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metodo TEXT UNIQUE,
                    porcentaje REAL DEFAULT 0.0,
                    frecuencia TEXT DEFAULT 'Mensual'
                )
            """)
        except sqlite3.OperationalError as e:
            print(f"Error SQL al crear tabla 'configuracion_comisiones': {e}")

        # --- NUEVA MIGRACIÓN: Sucursales y Abastecimiento Interno ---
        try:
            print("Creando tabla 'sucursales'...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sucursales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    direccion TEXT,
                    telefono TEXT,
                    es_principal INTEGER DEFAULT 0
                )
            """)
        except sqlite3.OperationalError as e:
            print(f"Error SQL al crear tabla 'sucursales': {e}")

        try:
            print("Creando tabla 'abastecimiento_interno'...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS abastecimiento_interno (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha DATE NOT NULL,
                    sucursal_origen_id INTEGER NOT NULL,
                    sucursal_destino_id INTEGER NOT NULL,
                    estado TEXT DEFAULT 'COMPLETADO',
                    FOREIGN KEY(sucursal_origen_id) REFERENCES sucursales(id),
                    FOREIGN KEY(sucursal_destino_id) REFERENCES sucursales(id)
                )
            """)
        except sqlite3.OperationalError as e:
            print(f"Error SQL al crear tabla 'abastecimiento_interno': {e}")

        try:
            print("Creando tabla 'detalle_abastecimiento'...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detalle_abastecimiento (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    abastecimiento_id INTEGER NOT NULL,
                    insumo_id INTEGER NOT NULL,
                    cantidad REAL NOT NULL,
                    unidad_id INTEGER NOT NULL,
                    FOREIGN KEY(abastecimiento_id) REFERENCES abastecimiento_interno(id) ON DELETE CASCADE,
                    FOREIGN KEY(insumo_id) REFERENCES insumos(id),
                    FOREIGN KEY(unidad_id) REFERENCES unidades_medida(id)
                )
            """)
        except sqlite3.OperationalError as e:
            print(f"Error SQL al crear tabla 'detalle_abastecimiento': {e}")

        conn.commit()
        print("¡Éxito! Base de datos actualizada correctamente.")
        conn.close()
    except Exception as e:
        print(f"Error general: {e}")


if __name__ == "__main__":
    migrar_db()

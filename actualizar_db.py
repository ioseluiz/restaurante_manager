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

        conn.commit()
        print("¡Éxito! Base de datos actualizada correctamente.")
        conn.close()
    except Exception as e:
        print(f"Error general: {e}")


if __name__ == "__main__":
    migrar_db()

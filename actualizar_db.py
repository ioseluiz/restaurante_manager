import sqlite3
import os

# --- CORRECCIÓN AQUÍ ---
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
        print("Agregando columna 'tipo_pago' a la tabla 'compras'...")

        # Agregamos la columna
        cursor.execute(
            "ALTER TABLE compras ADD COLUMN tipo_pago TEXT DEFAULT 'CONTADO'"
        )

        conn.commit()
        print("¡Éxito! Base de datos actualizada correctamente.")
        conn.close()
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("AVISO: La columna 'tipo_pago' ya existía. No se hicieron cambios.")
        else:
            print(f"Error SQL: {e}")


if __name__ == "__main__":
    migrar_db()

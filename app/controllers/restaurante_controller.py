"""Identidad del restaurante de esta base de datos: nombre, logo, RUC, dirección y teléfono.

El cliente tiene varios restaurantes, cada uno con su propia instalación y su propia base de datos (sin
conexión entre ellas). La identidad se guarda en la tabla `restaurante_config` de la base, así viaja con el
archivo .db: si se abre la base de otro restaurante, la app muestra el nombre correcto.

La sucursal no se duplica aquí: es la marcada en Sucursales como «de esta instalación»
(`sucursales.es_principal`). Una base sin nombre configurado muestra «Italos» y el logo de Italos.
"""

NOMBRE_POR_DEFECTO = "Italos"
CAMPOS_TEXTO = ("nombre", "ruc", "direccion", "telefono")


class RestauranteController:
    def __init__(self, db):
        self.db = db

    # ---------------------------------------------------------------- lectura
    def _valores(self):
        filas = self.db.fetch_all("SELECT clave, valor, blob FROM restaurante_config")
        return {clave: (valor, blob) for clave, valor, blob in filas}

    def sucursal_local(self):
        """(id, nombre) de la sucursal de esta instalación, o None si no está marcada."""
        row = self.db.fetch_one("SELECT id, nombre FROM sucursales WHERE es_principal = 1 ORDER BY id LIMIT 1")
        return (row[0], row[1]) if row else None

    def identidad(self):
        """{nombre, sucursal, ruc, direccion, telefono, logo (bytes o None), configurado}."""
        valores = self._valores()
        texto = {c: ((valores.get(c) or (None, None))[0] or "").strip() for c in CAMPOS_TEXTO}
        local = self.sucursal_local()
        logo = (valores.get("logo") or (None, None))[1]
        return {
            **texto,
            "nombre": texto["nombre"] or NOMBRE_POR_DEFECTO,
            "sucursal": local[1] if local else "",
            "logo": bytes(logo) if logo else None,
            "configurado": bool(texto["nombre"]),
        }

    def etiqueta(self, ident=None):
        """«Restaurante · Sucursal» (o solo el restaurante si no hay sucursal marcada)."""
        ident = ident or self.identidad()
        return " · ".join(p for p in (ident["nombre"], ident["sucursal"]) if p)

    def encabezado_reporte(self):
        """Líneas para el encabezado de reportes PDF/Excel: título y, si hay, RUC / dirección / teléfono."""
        ident = self.identidad()
        detalle = " · ".join(p for p in (f"RUC {ident['ruc']}" if ident["ruc"] else "",
                                         ident["direccion"], ident["telefono"]) if p)
        return [self.etiqueta(ident)] + ([detalle] if detalle else [])

    # ---------------------------------------------------------------- escritura
    def guardar(self, nombre, ruc="", direccion="", telefono="", sucursal=None):
        """Guarda los datos de texto. `sucursal` (nombre) se marca como la de esta instalación."""
        nombre = (nombre or "").strip()
        if not nombre:
            raise ValueError("El nombre del restaurante es obligatorio.")
        for clave, valor in zip(CAMPOS_TEXTO, (nombre, ruc, direccion, telefono)):
            self.db.cursor.execute(
                "INSERT INTO restaurante_config (clave, valor) VALUES (?, ?) "
                "ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor",
                (clave, (valor or "").strip()))
        if sucursal is not None and sucursal.strip():
            self._fijar_sucursal_local(sucursal.strip())
        self.db.conn.commit()

    def _fijar_sucursal_local(self, nombre):
        """Marca la sucursal `nombre` como la de esta instalación; la crea si no existe."""
        row = self.db.fetch_one("SELECT id FROM sucursales WHERE nombre = ? COLLATE NOCASE ORDER BY id LIMIT 1",
                                (nombre,))
        self.db.cursor.execute("UPDATE sucursales SET es_principal = 0")
        if row:
            self.db.cursor.execute("UPDATE sucursales SET es_principal = 1 WHERE id = ?", (row[0],))
        else:
            self.db.cursor.execute("INSERT INTO sucursales (nombre, es_principal) VALUES (?, 1)", (nombre,))

    def guardar_logo(self, datos):
        """Guarda el logo (bytes PNG, ya redimensionado) o lo quita si `datos` es None."""
        if datos:
            self.db.cursor.execute(
                "INSERT INTO restaurante_config (clave, blob) VALUES ('logo', ?) "
                "ON CONFLICT(clave) DO UPDATE SET blob = excluded.blob", (datos,))
        else:
            self.db.cursor.execute("DELETE FROM restaurante_config WHERE clave = 'logo'")
        self.db.conn.commit()

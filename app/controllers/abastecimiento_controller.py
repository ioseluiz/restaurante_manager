# [FILE: app/controllers/abastecimiento_controller.py]
"""Abastecimiento interno (traslados de insumos entre sucursales).

Modelo: cada sucursal tiene el programa instalado por separado y lleva su propio inventario, sin conexión
entre instalaciones. Por eso cada traslado se registra en las DOS instalaciones y cada una aplica su lado:

  - esta sucursal es el ORIGEN   -> el stock baja   (Kardex: TRASLADO_SALIDA)
  - esta sucursal es el DESTINO  -> el stock sube   (Kardex: TRASLADO_ENTRADA)
  - ninguna de las dos           -> se rechaza (no afectaría este inventario)

«Esta sucursal» es la marcada en Sucursales (columna sucursales.es_principal, que ahora significa
«sucursal de esta instalación»). El costo del insumo no se modifica al recibir un traslado.
Anular un traslado repone el stock con un movimiento REVERSO_TRASLADO (no se borra el registro).
"""

from app.controllers.kardex_controller import KardexController

TIPO_SALIDA = "TRASLADO_SALIDA"
TIPO_ENTRADA = "TRASLADO_ENTRADA"
TIPO_REVERSO = "REVERSO_TRASLADO"
ESTADO_ANULADO = "ANULADO"


class AbastecimientoController:
    def __init__(self, db):
        self.db = db
        self._kardex = KardexController(db)

    # ---------------------------------------------------------------- sucursal local
    def sucursal_local(self):
        """(id, nombre) de la sucursal de esta instalación, o None si no está configurada."""
        row = self.db.fetch_one("SELECT id, nombre FROM sucursales WHERE es_principal = 1 ORDER BY id LIMIT 1")
        return (row[0], row[1]) if row else None

    def efecto(self, origen_id, destino_id):
        """'SALIDA' / 'ENTRADA' sobre esta instalación, o None si el traslado no la involucra."""
        local = self.sucursal_local()
        if not local:
            return None
        if origen_id == local[0]:
            return "SALIDA"
        if destino_id == local[0]:
            return "ENTRADA"
        return None

    # ---------------------------------------------------------------- registrar
    def revisar_stock(self, origen_id, destino_id, detalles):
        """Insumos que quedarían en negativo si esta sucursal ENVÍA: [(nombre, stock, cantidad)]."""
        if self.efecto(origen_id, destino_id) != "SALIDA":
            return []
        faltan = []
        for insumo_id, cantidad, _unidad in detalles:
            row = self.db.fetch_one("SELECT nombre, stock_actual FROM insumos WHERE id = ?", (insumo_id,))
            if row and (row[1] or 0.0) - float(cantidad) < 0:
                faltan.append((row[0], row[1] or 0.0, float(cantidad)))
        return faltan

    def registrar(self, fecha, origen_id, destino_id, detalles):
        """Guarda el traslado y mueve el stock de esta sucursal en una sola transacción.

        detalles: lista de (insumo_id, cantidad, unidad_id). No bloquea el stock negativo (lo avisa la
        vista con revisar_stock). Lanza ValueError con un mensaje claro si el traslado no es válido.
        Devuelve {"id", "efecto", "negativos": [nombres]}.
        """
        if origen_id == destino_id:
            raise ValueError("La sucursal de origen y destino no pueden ser la misma.")
        if not detalles:
            raise ValueError("Debe agregar al menos un insumo al abastecimiento.")
        if any(float(c) <= 0 for _i, c, _u in detalles):
            raise ValueError("Todas las cantidades deben ser mayores a 0.")
        local = self.sucursal_local()
        if not local:
            raise ValueError(
                "No hay una sucursal marcada como «esta sucursal». Vaya a Sucursales, edite la de esta "
                "instalación y marque la casilla correspondiente.")
        efecto = self.efecto(origen_id, destino_id)
        if efecto is None:
            raise ValueError(
                f"Este traslado no involucra a esta sucursal ({local[1]}): no afectaría su inventario. "
                "Regístrelo en la instalación de la sucursal de origen o de destino.")

        nombres = {r[0]: r[1] for r in self.db.fetch_all("SELECT id, nombre FROM sucursales")}
        cur = self.db.conn.cursor()
        try:
            cur.execute(
                "INSERT INTO abastecimiento_interno (fecha, sucursal_origen_id, sucursal_destino_id) VALUES (?,?,?)",
                (fecha, origen_id, destino_id))
            abast_id = cur.lastrowid
            negativos = []
            for insumo_id, cantidad, unidad_id in detalles:
                cantidad = float(cantidad)
                cur.execute(
                    "INSERT INTO detalle_abastecimiento (abastecimiento_id, insumo_id, cantidad, unidad_id) "
                    "VALUES (?,?,?,?)", (abast_id, insumo_id, cantidad, unidad_id))
                if efecto == "SALIDA":
                    nuevo = self._kardex._aplicar(cur, insumo_id, -cantidad, TIPO_SALIDA, abast_id,
                                                  f"Traslado a {nombres.get(destino_id, destino_id)}")
                    if nuevo < 0:
                        negativos.append(insumo_id)
                else:
                    self._kardex._aplicar(cur, insumo_id, cantidad, TIPO_ENTRADA, abast_id,
                                          f"Traslado desde {nombres.get(origen_id, origen_id)}")
            self.db.conn.commit()
        except Exception:
            self.db.conn.rollback()
            raise
        nombres_neg = [r[0] for i in negativos
                       for r in [self.db.fetch_one("SELECT nombre FROM insumos WHERE id=?", (i,))] if r]
        return {"id": abast_id, "efecto": efecto, "negativos": nombres_neg}

    # ---------------------------------------------------------------- anular
    def anular(self, abastecimiento_id):
        """Anula un traslado: repone el stock con REVERSO_TRASLADO y lo marca ANULADO.

        Revierte el neto de los movimientos del traslado. Un traslado registrado antes de esta versión no
        tiene movimientos en el Kardex: se revierte según lo que aplicó la versión anterior (baja si esta
        sucursal era el origen, suba si era el destino). Devuelve la cantidad de insumos repuestos.
        """
        reg = self.db.fetch_one(
            "SELECT estado, sucursal_origen_id, sucursal_destino_id FROM abastecimiento_interno WHERE id=?",
            (abastecimiento_id,))
        if not reg:
            raise ValueError("El abastecimiento no existe.")
        estado, origen_id, destino_id = reg
        if estado == ESTADO_ANULADO:
            raise ValueError("Este abastecimiento ya está anulado.")

        netos = self.db.fetch_all(
            "SELECT insumo_id, SUM(cantidad) FROM movimientos_inventario WHERE referencia_id=? "
            "AND tipo_movimiento IN (?,?,?) GROUP BY insumo_id",
            (abastecimiento_id, TIPO_SALIDA, TIPO_ENTRADA, TIPO_REVERSO))
        if not netos:  # registrado por la versión anterior: sin movimientos en el Kardex
            efecto = self.efecto(origen_id, destino_id)
            signo = {"SALIDA": -1.0, "ENTRADA": 1.0}.get(efecto)
            if signo is not None:
                netos = [(i, signo * c) for i, c in self.db.fetch_all(
                    "SELECT insumo_id, cantidad FROM detalle_abastecimiento WHERE abastecimiento_id=?",
                    (abastecimiento_id,))]

        cur = self.db.conn.cursor()
        try:
            repuestos = 0
            for insumo_id, neto in netos:
                if abs(neto or 0.0) < 1e-9:
                    continue
                self._kardex._aplicar(cur, insumo_id, -neto, TIPO_REVERSO, abastecimiento_id,
                                      f"Anulación del abastecimiento #{abastecimiento_id}")
                repuestos += 1
            cur.execute("UPDATE abastecimiento_interno SET estado=?, anulado_en=CURRENT_TIMESTAMP WHERE id=?",
                        (ESTADO_ANULADO, abastecimiento_id))
            self.db.conn.commit()
        except Exception:
            self.db.conn.rollback()
            raise
        return repuestos

    # ---------------------------------------------------------------- consultas
    def listar(self):
        """[(id, fecha, origen, destino, efecto o None, estado)] del más reciente al más antiguo."""
        filas = self.db.fetch_all(
            "SELECT a.id, a.fecha, so.nombre, sd.nombre, a.estado, a.sucursal_origen_id, a.sucursal_destino_id "
            "FROM abastecimiento_interno a "
            "JOIN sucursales so ON so.id = a.sucursal_origen_id "
            "JOIN sucursales sd ON sd.id = a.sucursal_destino_id "
            "ORDER BY a.fecha DESC, a.id DESC")
        return [(i, f, o, d, self.efecto(oi, di), e) for i, f, o, d, e, oi, di in filas]

    def detalle(self, abastecimiento_id):
        """[(insumo, cantidad, unidad)] del traslado."""
        return self.db.fetch_all(
            "SELECT i.nombre, d.cantidad, COALESCE(u.abreviatura, '') FROM detalle_abastecimiento d "
            "JOIN insumos i ON i.id = d.insumo_id LEFT JOIN unidades_medida u ON u.id = d.unidad_id "
            "WHERE d.abastecimiento_id = ? ORDER BY i.nombre", (abastecimiento_id,))

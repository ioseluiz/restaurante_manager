from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QDialog,
    QHeaderView,
    QMessageBox,
    QDateEdit,
    QComboBox,
    QDoubleSpinBox,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor

from app.controllers.abastecimiento_controller import AbastecimientoController, ESTADO_ANULADO
from app.views.widgets import SearchableComboBox


class NumericItem(QTableWidgetItem):
    def __lt__(self, other):
        try:
            return float(self.text()) < float(other.text())
        except ValueError:
            return super().__lt__(other)


class NuevoAbastecimientoDialog(QDialog):
    """Registra un traslado de insumos entre sucursales.

    Cada sucursal tiene su propio programa: el traslado se registra en las dos instalaciones y aquí solo
    se aplica el lado de ESTA sucursal (envío = baja el stock; recepción = sube el stock).
    """

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.ctrl = AbastecimientoController(db_manager)
        self.setWindowTitle("Nuevo Abastecimiento Interno")
        self.resize(800, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.lbl_local = QLabel()
        self.lbl_local.setWordWrap(True)
        layout.addWidget(self.lbl_local)

        form_layout = QHBoxLayout()

        layout_fecha = QVBoxLayout()
        layout_fecha.addWidget(QLabel("Fecha:"))
        self.fecha_input = QDateEdit()
        self.fecha_input.setCalendarPopup(True)
        self.fecha_input.setDisplayFormat("yyyy-MM-dd")
        self.fecha_input.setDate(QDate.currentDate())
        layout_fecha.addWidget(self.fecha_input)
        form_layout.addLayout(layout_fecha)

        layout_origen = QVBoxLayout()
        layout_origen.addWidget(QLabel("Sucursal Origen (envía):"))
        self.origen_combo = QComboBox()
        layout_origen.addWidget(self.origen_combo)
        form_layout.addLayout(layout_origen)

        layout_destino = QVBoxLayout()
        layout_destino.addWidget(QLabel("Sucursal Destino (recibe):"))
        self.destino_combo = QComboBox()
        layout_destino.addWidget(self.destino_combo)
        form_layout.addLayout(layout_destino)

        layout.addLayout(form_layout)

        self.lbl_efecto = QLabel()
        self.lbl_efecto.setWordWrap(True)
        layout.addWidget(self.lbl_efecto)

        self.cargar_sucursales()
        self.origen_combo.currentIndexChanged.connect(self._actualizar_efecto)
        self.destino_combo.currentIndexChanged.connect(self._actualizar_efecto)
        self._actualizar_efecto()

        layout.addWidget(QLabel("<h3>Insumos a Transferir</h3>"))

        add_item_layout = QHBoxLayout()
        self.insumo_combo = SearchableComboBox(placeholder="Escriba para buscar insumo…")
        self.insumo_combo.setMinimumWidth(200)
        add_item_layout.addWidget(QLabel("Insumo:"))
        add_item_layout.addWidget(self.insumo_combo)

        self.cantidad_input = QDoubleSpinBox()
        self.cantidad_input.setDecimals(4)
        self.cantidad_input.setMaximum(999999.9999)
        add_item_layout.addWidget(QLabel("Cantidad:"))
        add_item_layout.addWidget(self.cantidad_input)

        btn_add_detalle = QPushButton("Agregar Insumo")
        btn_add_detalle.clicked.connect(self.agregar_detalle)
        add_item_layout.addWidget(btn_add_detalle)
        layout.addLayout(add_item_layout)

        self.cargar_insumos()

        self.table_detalles = QTableWidget()
        self.table_detalles.setColumnCount(5)
        self.table_detalles.setHorizontalHeaderLabels(["ID Insumo", "Insumo", "Cantidad", "Unidad", "Acción"])
        self.table_detalles.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_detalles)

        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Guardar Abastecimiento")
        btn_save.setProperty("class", "btn-success")
        btn_save.clicked.connect(self.guardar_abastecimiento)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    # ------------------------------------------------------------------ datos
    def cargar_sucursales(self):
        local = self.ctrl.sucursal_local()
        if local:
            self.lbl_local.setText(f"<b>Esta instalación es la sucursal:</b> {local[1]}")
        else:
            self.lbl_local.setText(
                "<span style='color:#c0392b'><b>No hay una sucursal marcada como «esta sucursal».</b> "
                "Vaya a <b>Sucursales</b>, edite la de esta instalación y marque la casilla; sin eso no se "
                "puede registrar un abastecimiento.</span>")
        for sid, nombre in self.db.fetch_all("SELECT id, nombre FROM sucursales ORDER BY nombre"):
            texto = f"{nombre} (esta sucursal)" if local and sid == local[0] else nombre
            self.origen_combo.addItem(texto, sid)
            self.destino_combo.addItem(texto, sid)
        if local:  # lo más común: esta sucursal envía
            self.origen_combo.setCurrentIndex(self.origen_combo.findData(local[0]))
            for i in range(self.destino_combo.count()):
                if self.destino_combo.itemData(i) != local[0]:
                    self.destino_combo.setCurrentIndex(i)
                    break

    def _actualizar_efecto(self):
        o, d = self.origen_combo.currentData(), self.destino_combo.currentData()
        efecto = self.ctrl.efecto(o, d) if o != d else None
        if not self.ctrl.sucursal_local():
            texto = ""
        elif o == d:
            texto = "<span style='color:#c0392b'>El origen y el destino no pueden ser la misma sucursal.</span>"
        elif efecto == "SALIDA":
            texto = "Esta sucursal <b>envía</b>: el stock de los insumos <b>baja</b>."
        elif efecto == "ENTRADA":
            texto = "Esta sucursal <b>recibe</b>: el stock de los insumos <b>sube</b> (el costo no cambia)."
        else:
            texto = ("<span style='color:#c0392b'>Este traslado no involucra a esta sucursal: no se puede "
                     "registrar aquí. Hágalo en la instalación de la sucursal de origen o de destino.</span>")
        self.lbl_efecto.setText(texto)

    def cargar_insumos(self):
        rows = self.db.fetch_all("""
            SELECT i.id, i.nombre, u.abreviatura, u.id
            FROM insumos i
            LEFT JOIN unidades_medida u ON i.unidad_base_id = u.id
            ORDER BY i.nombre
        """)
        for r in rows:
            self.insumo_combo.addItem(f"{r[1]} ({r[2]})",
                                      {"id": r[0], "unidad_str": r[2], "unidad_id": r[3], "nombre": r[1]})

    def agregar_detalle(self):
        if self.insumo_combo.currentIndex() < 0:
            return
        data = self.insumo_combo.currentData()
        if not data:
            return
        cantidad = self.cantidad_input.value()
        if cantidad <= 0:
            QMessageBox.warning(self, "Aviso", "La cantidad debe ser mayor a 0.")
            return
        for i in range(self.table_detalles.rowCount()):
            if self.table_detalles.item(i, 0).text() == str(data["id"]):
                QMessageBox.warning(self, "Aviso", "El insumo ya está en la lista.")
                return

        row = self.table_detalles.rowCount()
        self.table_detalles.insertRow(row)
        self.table_detalles.setItem(row, 0, QTableWidgetItem(str(data["id"])))
        self.table_detalles.setItem(row, 1, QTableWidgetItem(data["nombre"]))
        self.table_detalles.setItem(row, 2, QTableWidgetItem(str(cantidad)))
        item_unidad = QTableWidgetItem(data["unidad_str"])
        item_unidad.setData(Qt.UserRole, data["unidad_id"])
        self.table_detalles.setItem(row, 3, item_unidad)

        btn_eliminar = QPushButton("X")
        btn_eliminar.setStyleSheet("color: red; font-weight: bold;")
        btn_eliminar.clicked.connect(self._quitar_fila_del_boton)
        self.table_detalles.setCellWidget(row, 4, btn_eliminar)
        self.cantidad_input.setValue(0.0)

    def _quitar_fila_del_boton(self):
        boton = self.sender()
        for r in range(self.table_detalles.rowCount()):
            if self.table_detalles.cellWidget(r, 4) is boton:
                self.table_detalles.removeRow(r)
                return

    def _detalles(self):
        return [
            (int(self.table_detalles.item(i, 0).text()),
             float(self.table_detalles.item(i, 2).text()),
             int(self.table_detalles.item(i, 3).data(Qt.UserRole)))
            for i in range(self.table_detalles.rowCount())
        ]

    def guardar_abastecimiento(self):
        origen_id = self.origen_combo.currentData()
        destino_id = self.destino_combo.currentData()
        fecha = self.fecha_input.date().toString("yyyy-MM-dd")
        detalles = self._detalles()

        # Avisa (sin bloquear) si esta sucursal enviaría más de lo que tiene registrado
        try:
            faltan = self.ctrl.revisar_stock(origen_id, destino_id, detalles)
        except Exception:
            faltan = []
        if faltan:
            lista = "\n".join(f"• {n}: hay {s:g}, se envían {c:g}" for n, s, c in faltan)
            resp = QMessageBox.question(
                self, "Stock insuficiente",
                "Estos insumos quedarían con stock NEGATIVO en el sistema:\n\n" + lista +
                "\n\nEsto suele indicar compras sin registrar o un stock desactualizado. ¿Desea continuar?",
                QMessageBox.Yes | QMessageBox.No)
            if resp != QMessageBox.Yes:
                return

        try:
            res = self.ctrl.registrar(fecha, origen_id, destino_id, detalles)
        except ValueError as e:
            QMessageBox.warning(self, "Aviso", str(e))
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar abastecimiento: {e}")
            return

        que = "descontó del" if res["efecto"] == "SALIDA" else "sumó al"
        QMessageBox.information(
            self, "Éxito",
            f"Abastecimiento registrado: se {que} inventario de esta sucursal.\n\n"
            "Recuerde que la otra sucursal debe registrar el mismo traslado en su programa.")
        self.accept()


class DetalleAbastecimientoDialog(QDialog):
    def __init__(self, ctrl, abastecimiento_id, titulo, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Abastecimiento — {titulo}")
        self.resize(520, 380)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(f"<b>{titulo}</b>"))
        tabla = QTableWidget()
        tabla.setColumnCount(3)
        tabla.setHorizontalHeaderLabels(["Insumo", "Cantidad", "Unidad"])
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        for i, (nombre, cantidad, unidad) in enumerate(ctrl.detalle(abastecimiento_id)):
            tabla.insertRow(i)
            tabla.setItem(i, 0, QTableWidgetItem(nombre))
            tabla.setItem(i, 1, NumericItem(f"{cantidad:g}"))
            tabla.setItem(i, 2, QTableWidgetItem(unidad))
        lay.addWidget(tabla)
        cerrar = QPushButton("Cerrar")
        cerrar.clicked.connect(self.accept)
        lay.addWidget(cerrar, alignment=Qt.AlignRight)


class TabAbastecimientoInterno(QWidget):
    _EFECTO = {"SALIDA": "Envío (baja stock)", "ENTRADA": "Recepción (sube stock)", None: "—"}

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.ctrl = AbastecimientoController(db_manager)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<h3>Registro de Abastecimiento Interno</h3>"))
        header_layout.addStretch()

        btn_add = QPushButton(" + Nuevo Abastecimiento")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setProperty("class", "btn-success")
        btn_add.clicked.connect(self.abrir_crear)
        header_layout.addWidget(btn_add)

        btn_detalle = QPushButton("Ver Detalle")
        btn_detalle.clicked.connect(self.ver_detalle)
        header_layout.addWidget(btn_detalle)

        btn_anular = QPushButton("Anular")
        btn_anular.setProperty("class", "btn-danger")
        btn_anular.clicked.connect(self.anular_abastecimiento)
        header_layout.addWidget(btn_anular)
        layout.addLayout(header_layout)

        self.lbl_local = QLabel()
        layout.addWidget(self.lbl_local)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Fecha", "Origen", "Destino", "Efecto en esta sucursal", "Estado"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.hideColumn(0)
        self.table.cellDoubleClicked.connect(lambda *_: self.ver_detalle())
        layout.addWidget(self.table)
        self.setLayout(layout)

    def cargar_datos(self):
        local = self.ctrl.sucursal_local()
        self.lbl_local.setText(
            f"Esta instalación es la sucursal: <b>{local[1]}</b>" if local else
            "<span style='color:#c0392b'>Sin sucursal configurada: marque «esta sucursal» en el módulo "
            "Sucursales para poder registrar abastecimientos.</span>")
        self.table.setRowCount(0)
        for r_idx, (aid, fecha, origen, destino, efecto, estado) in enumerate(self.ctrl.listar()):
            self.table.insertRow(r_idx)
            valores = [str(aid), fecha, origen, destino, self._EFECTO[efecto], estado]
            for c, v in enumerate(valores):
                it = QTableWidgetItem(v)
                if estado == ESTADO_ANULADO:
                    it.setForeground(QColor("#95a5a6"))
                self.table.setItem(r_idx, c, it)

    def abrir_crear(self):
        dlg = NuevoAbastecimientoDialog(self.db, parent=self)
        if dlg.exec_():
            self.cargar_datos()

    def _seleccionado(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Seleccione un abastecimiento.")
            return None
        aid = int(self.table.item(row, 0).text())
        titulo = (f"{self.table.item(row, 1).text()} · {self.table.item(row, 2).text()} → "
                  f"{self.table.item(row, 3).text()}")
        return aid, titulo, self.table.item(row, 5).text()

    def ver_detalle(self):
        sel = self._seleccionado()
        if sel:
            DetalleAbastecimientoDialog(self.ctrl, sel[0], sel[1], self).exec_()

    def anular_abastecimiento(self):
        sel = self._seleccionado()
        if not sel:
            return
        aid, titulo, estado = sel
        if estado == ESTADO_ANULADO:
            QMessageBox.information(self, "Aviso", "Este abastecimiento ya está anulado.")
            return
        reply = QMessageBox.question(
            self, "Anular abastecimiento",
            f"Se anulará el traslado {titulo} y se repondrá al inventario de esta sucursal lo que movió. "
            "El registro se conserva como ANULADO.\n\nRecuerde anularlo también en la otra sucursal.\n\n¿Continuar?",
            QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        try:
            repuestos = self.ctrl.anular(aid)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo anular: {e}")
            return
        self.cargar_datos()
        QMessageBox.information(
            self, "Anulado",
            f"Abastecimiento anulado. Se ajustaron {repuestos} insumo(s) del inventario." if repuestos
            else "Abastecimiento anulado. No involucraba a esta sucursal, así que no había inventario que ajustar.")

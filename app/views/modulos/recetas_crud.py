"""Recetas (Fichas): consulta de las recetas de cada plato.

Se edita en un solo lugar: Costo de Platos → Recetas de costeo (rendimiento, porción, ingredientes, sub-recetas).
Este módulo muestra la receta completa —por porción o por tanda, con sus sub-recetas— y lo que descuenta del
inventario por plato. Antes tenía un editor propio que solo veía las líneas de insumos y no sabía de tandas ni
sub-recetas: «corregir» desde aquí una cantidad de tanda creyendo que era por plato descuadraba costos y stock.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox, QDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from app.controllers.auth_controller import puede_ver

TIPO_PORCION = "Por porción"
TIPO_TANDA = "Por tanda"
TIPO_USA_TANDA = "Usa tanda / sub-receta"
TIPO_SUBRECETA = "Sub-receta / tanda"
SIN_RECETA = "Sin receta"


class NumericItem(QTableWidgetItem):
    """Ordena como número (1, 2, 10) aunque se muestre como texto."""

    def __lt__(self, other):
        try:
            return float(self.data(Qt.UserRole)) < float(other.data(Qt.UserRole))
        except (TypeError, ValueError):
            return super().__lt__(other)


def _num(valor, texto=None):
    it = NumericItem(texto if texto is not None else f"{valor:g}")
    it.setData(Qt.UserRole, valor)
    it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
    return it


def tipo_receta(es_componente, rendimiento, n_insumos, n_componentes):
    if not n_insumos and not n_componentes:
        return SIN_RECETA
    if es_componente:
        return TIPO_SUBRECETA
    if rendimiento:
        return TIPO_TANDA
    if n_componentes and not n_insumos:
        return TIPO_USA_TANDA
    return TIPO_PORCION


class RecetasCRUD(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self._rol = ""
        self.init_ui()

    def set_rol(self, rol):
        """Gerente y administrador pueden saltar al editor de Costo de Platos; el empleado solo consulta."""
        self._rol = rol

    @property
    def puede_editar(self):
        return puede_ver(self._rol, "costo_platos")

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Recetas (Fichas Técnicas)")
        title.setProperty("class", "header-title")
        btn_ver = QPushButton(" Ver receta")
        btn_ver.setCursor(Qt.PointingHandCursor)
        btn_ver.setProperty("class", "btn-primary")
        btn_ver.clicked.connect(self.abrir_detalle)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(btn_ver)
        layout.addLayout(header)

        nota = QLabel("Consulta de recetas. Para crearlas o modificarlas use <b>Costo de Platos → Recetas de "
                      "costeo</b> (o «Editar en Costo de Platos» en el detalle).")
        nota.setWordWrap(True)
        nota.setStyleSheet("color: #555;")
        layout.addWidget(nota)

        filtros = QHBoxLayout()
        self.input_filtro_codigo = QLineEdit()
        self.input_filtro_codigo.setPlaceholderText("Filtrar por Código...")
        self.input_filtro_codigo.textChanged.connect(self.aplicar_filtros)
        self.input_filtro_nombre = QLineEdit()
        self.input_filtro_nombre.setPlaceholderText("Filtrar por Nombre del Plato...")
        self.input_filtro_nombre.textChanged.connect(self.aplicar_filtros)
        self.chk_internas = QCheckBox("Mostrar sub-recetas y tandas")
        self.chk_internas.setToolTip("Preparaciones que no se venden solas: guisos, salsas, tandas compartidas…")
        self.chk_internas.toggled.connect(self.cargar_datos)
        filtros.addWidget(self.input_filtro_codigo)
        filtros.addWidget(self.input_filtro_nombre)
        filtros.addWidget(self.chk_internas)
        layout.addLayout(filtros)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Código", "Nombre", "Tipo de receta", "Líneas"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.hideColumn(0)
        self.table.doubleClicked.connect(lambda _i: self.abrir_detalle())
        layout.addWidget(self.table)

        self.cargar_datos()

    def cargar_datos(self):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        internas = "" if self.chk_internas.isChecked() else "AND COALESCE(m.es_componente, 0) = 0"
        rows = self.db.fetch_all(f"""
            SELECT m.id, m.codigo, m.nombre, COALESCE(m.es_componente, 0), m.rendimiento,
                   (SELECT COUNT(*) FROM recetas r WHERE r.menu_item_id = m.id),
                   (SELECT COUNT(*) FROM receta_componentes rc WHERE rc.menu_item_id = m.id)
            FROM menu_items m
            WHERE m.es_preparado = 1 {internas}
            ORDER BY m.nombre ASC
        """)
        for i, (mid, codigo, nombre, es_comp, rend, n_ins, n_comp) in enumerate(rows):
            self.table.insertRow(i)
            self.table.setItem(i, 0, _num(mid, str(mid)))
            self.table.setItem(i, 1, QTableWidgetItem(str(codigo)))
            self.table.setItem(i, 2, QTableWidgetItem(str(nombre)))
            tipo = tipo_receta(es_comp, rend, n_ins, n_comp)
            it_tipo = QTableWidgetItem(tipo)
            it_tipo.setForeground(Qt.red if tipo == SIN_RECETA else Qt.darkGreen)
            self.table.setItem(i, 3, it_tipo)
            detalle = f"{n_ins} insumo(s)" + (f" + {n_comp} sub-receta(s)" if n_comp else "")
            self.table.setItem(i, 4, _num(n_ins + n_comp, detalle if n_ins or n_comp else "—"))
        self.table.setSortingEnabled(True)
        self.aplicar_filtros()

    def aplicar_filtros(self):
        txt_code = self.input_filtro_codigo.text().lower()
        txt_name = self.input_filtro_nombre.text().lower()
        for row in range(self.table.rowCount()):
            ok = (txt_code in self.table.item(row, 1).text().lower()
                  and txt_name in self.table.item(row, 2).text().lower())
            self.table.setRowHidden(row, not ok)

    def abrir_detalle(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atención", "Seleccione un plato para ver su receta.")
            return
        mid = int(self.table.item(row, 0).text())
        dlg = RecetaDetalleDialog(self.db, mid, self.table.item(row, 2).text(), self.puede_editar, self)
        dlg.exec_()
        if dlg.editado:
            self.cargar_datos()


class RecetaDetalleDialog(QDialog):
    """Receta completa en solo lectura: tanda/porción, líneas con cantidad por tanda y por porción, y lo que
    descuenta del inventario un plato (insumos de las sub-recetas incluidos)."""

    def __init__(self, db, menu_item_id, nombre, puede_editar=False, parent=None):
        super().__init__(parent)
        from app.controllers.costeo_controller import CosteoController

        self.db, self.mid, self.nombre = db, menu_item_id, nombre
        self.ctrl = CosteoController(db)
        self.editado = False
        self.setWindowTitle(f"Receta: {nombre}")
        self.resize(820, 620)

        lay = QVBoxLayout(self)
        self.lbl_resumen = QLabel()
        self.lbl_resumen.setWordWrap(True)
        self.lbl_resumen.setTextFormat(Qt.RichText)
        lay.addWidget(self.lbl_resumen)

        lay.addWidget(QLabel("<b>Ingredientes de la receta</b>"))
        self.tbl_lineas = self._tabla(["Tipo", "Ingrediente", "Cantidad receta", "Por porción", "Unidad"])
        lay.addWidget(self.tbl_lineas, 3)

        self.lbl_inventario = QLabel("<b>Lo que descuenta del inventario cada plato vendido</b> "
                                     "(incluye los insumos de las sub-recetas)")
        lay.addWidget(self.lbl_inventario)
        self.tbl_inventario = self._tabla(["Insumo", "Cantidad por plato", "Unidad"])
        lay.addWidget(self.tbl_inventario, 2)

        botones = QHBoxLayout()
        self.btn_editar = QPushButton("Editar en Costo de Platos…")
        self.btn_editar.setVisible(puede_editar)
        self.btn_editar.setToolTip("Abre el editor de recetas de costeo (rendimiento, porción, ingredientes y "
                                   "sub-recetas)")
        self.btn_editar.clicked.connect(self._editar)
        botones.addWidget(self.btn_editar)
        botones.addStretch()
        b_cerrar = QPushButton("Cerrar")
        b_cerrar.clicked.connect(self.accept)
        botones.addWidget(b_cerrar)
        lay.addLayout(botones)
        self.cargar()

    @staticmethod
    def _tabla(columnas):
        t = QTableWidget()
        t.setColumnCount(len(columnas))
        t.setHorizontalHeaderLabels(columnas)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        t.horizontalHeader().setSectionResizeMode(1 if len(columnas) > 3 else 0, QHeaderView.Stretch)
        t.verticalHeader().setVisible(False)
        t.setEditTriggers(QTableWidget.NoEditTriggers)
        t.setAlternatingRowColors(True)
        return t

    def _abrev(self, unidad_id):
        r = self.db.fetch_one("SELECT abreviatura FROM unidades_medida WHERE id=?", (unidad_id,)) if unidad_id else None
        return r[0] if r else ""

    def cargar(self):
        self.ctrl.limpiar_cache()
        it = self.db.fetch_one(
            "SELECT codigo, COALESCE(es_componente,0), rendimiento, unidad_rendimiento_id, porcion_servida, "
            "unidad_porcion_id FROM menu_items WHERE id=?", (self.mid,))
        codigo, es_comp, rend, u_rend, porcion, u_por = it
        factor = self.ctrl.factor_por_porcion(self.mid)
        insumos = self.db.fetch_all(
            "SELECT i.nombre, r.cantidad_necesaria, COALESCE(r.unidad_id, i.unidad_base_id) FROM recetas r "
            "JOIN insumos i ON i.id = r.insumo_id WHERE r.menu_item_id=? ORDER BY i.nombre", (self.mid,))
        comps = self.db.fetch_all(
            "SELECT m.nombre, rc.cantidad, rc.unidad_id FROM receta_componentes rc "
            "JOIN menu_items m ON m.id = rc.componente_id WHERE rc.menu_item_id=? ORDER BY m.nombre", (self.mid,))
        tipo = tipo_receta(es_comp, rend, len(insumos), len(comps))

        if tipo == TIPO_TANDA:
            n_porc = (1 / factor) if factor and factor != 1 else None  # factor = porción / rendimiento
            resumen = (f"<b>Receta por tanda.</b> La tanda rinde <b>{rend:g} {self._abrev(u_rend)}</b> y la porción "
                       f"servida es <b>{(porcion or 0):g} {self._abrev(u_por)}</b>"
                       + (f" → salen unas <b>{n_porc:.1f} porciones</b> por tanda." if n_porc else ".")
                       + "<br>Las cantidades de la receta son de la <b>tanda completa</b>; «Por porción» es lo que "
                         "lleva un plato.")
        elif tipo == TIPO_SUBRECETA:
            resumen = ("<b>Sub-receta o tanda</b> (no se vende sola; la usan otros platos)"
                       + (f". Rinde <b>{rend:g} {self._abrev(u_rend)}</b>." if rend else "."))
        elif tipo == TIPO_USA_TANDA:
            resumen = ("<b>Se sirve de una tanda o sub-receta.</b> La línea indica cuánto de ella lleva cada plato; "
                       "abajo, lo que eso descuenta del inventario.")
        elif tipo == TIPO_PORCION:
            resumen = "<b>Receta por porción:</b> las cantidades son las de un plato."
        else:
            resumen = "<span style='color:#a20f22'><b>Sin receta.</b> Este plato no descuenta inventario ni tiene costo.</span>"
        self.lbl_resumen.setText(f"Código <b>{codigo}</b> · {resumen}")

        self.tbl_lineas.setRowCount(0)
        lineas = [("Insumo", n, q, u) for n, q, u in insumos] + [("Sub-receta", n, q, u) for n, q, u in comps]
        for i, (t, nombre, q, u) in enumerate(lineas):
            q = float(q or 0)
            self.tbl_lineas.insertRow(i)
            self.tbl_lineas.setItem(i, 0, QTableWidgetItem(t))
            self.tbl_lineas.setItem(i, 1, QTableWidgetItem(nombre))
            self.tbl_lineas.setItem(i, 2, _num(q, f"{q:,.3f}".rstrip("0").rstrip(".")))
            pp = q * factor
            self.tbl_lineas.setItem(i, 3, _num(pp, f"{pp:,.3f}".rstrip("0").rstrip(".")))
            self.tbl_lineas.setItem(i, 4, QTableWidgetItem(self._abrev(u)))

        expl = self.db.fetch_all(
            "SELECT i.nombre, v.cantidad_necesaria, u.abreviatura FROM v_recetas_explotadas v "
            "JOIN insumos i ON i.id = v.insumo_id LEFT JOIN unidades_medida u ON u.id = i.unidad_base_id "
            "WHERE v.menu_item_id=? ORDER BY i.nombre", (self.mid,))
        self.tbl_inventario.setRowCount(0)
        for i, (nombre, q, u) in enumerate(expl):
            q = float(q or 0)
            self.tbl_inventario.insertRow(i)
            self.tbl_inventario.setItem(i, 0, QTableWidgetItem(nombre))
            self.tbl_inventario.setItem(i, 1, _num(q, f"{q:,.3f}".rstrip("0").rstrip(".")))
            self.tbl_inventario.setItem(i, 2, QTableWidgetItem(u or ""))
        visible = not es_comp
        self.lbl_inventario.setVisible(visible)
        self.tbl_inventario.setVisible(visible)

    def _editar(self):
        from app.views.modulos.costo_platos import RecetaCosteoDialog

        RecetaCosteoDialog(self.db, self.ctrl, self.mid, self.nombre, self).exec_()
        self.editado = True
        self.cargar()

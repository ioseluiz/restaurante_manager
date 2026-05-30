# [FILE: app/views/modulos/insumos_crud.py]
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QMessageBox,
    QLabel,
    QDoubleSpinBox,
    QCheckBox,
    QGroupBox,
    QSpinBox,
    QDateEdit,
    QFrame,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QSizePolicy
import datetime
import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates


# --- CLASE PERSONALIZADA PARA ORDENAR NÚMEROS ---
class NumericItem(QTableWidgetItem):
    def __lt__(self, other):
        try:
            # Intenta limpiar el texto de signos de dólar si es un precio
            val_self = self.text().replace("$", "").replace(",", "").strip()
            val_other = other.text().replace("$", "").replace(",", "").strip()
            return float(val_self) < float(val_other)
        except ValueError:
            return super().__lt__(other)


class InsumosCRUD(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Título General
        header = QLabel("<h2>Gestión de Insumos y Costos</h2>")
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        # Contenedor de Pestañas
        self.tabs = QTabWidget()

        # Inicializar las pestañas
        self.tab_insumos = TabInsumos(self.db)
        self.tab_presentaciones = TabPresentaciones(self.db)
        self.tab_categorias = TabCategorias(self.db)

        # Añadir pestañas
        self.tabs.addTab(self.tab_insumos, "1. Catálogo de Insumos")
        self.tabs.addTab(self.tab_presentaciones, "2. Presentaciones de Compra")
        self.tabs.addTab(self.tab_categorias, "3. Categorías")

        # Conectar cambio de pestaña
        self.tabs.currentChanged.connect(self.on_tab_change)

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def cargar_datos(self):
        self.on_tab_change(self.tabs.currentIndex())

    def on_tab_change(self, index):
        if index == 0:
            self.tab_insumos.cargar_datos()
        elif index == 1:
            self.tab_presentaciones.cargar_datos()
        elif index == 2:
            self.tab_categorias.cargar_datos()


# =============================================================================
# PESTAÑA 1: INSUMOS (Catálogo Base)
# =============================================================================
class TabInsumos(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.filtros = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Toolbar
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Nuevo Insumo")
        btn_add.setProperty("class", "btn-success")
        btn_add.clicked.connect(self.abrir_crear)

        btn_edit = QPushButton("Editar Seleccionado")
        btn_edit.clicked.connect(self.abrir_editar)

        btn_del = QPushButton("Eliminar")
        btn_del.setProperty("class", "btn-danger")
        btn_del.clicked.connect(self.eliminar)

        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_del)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # --- FILTROS DE BÚSQUEDA ---
        filter_layout = QHBoxLayout()
        config_filtros = [
            (0, "Filtrar ID"),
            (1, "Filtrar Nombre"),
            (3, "Filtrar Categoría"),
            (6, "Filtrar Presentación"),
        ]

        for col_idx, placeholder in config_filtros:
            inp = QLineEdit()
            inp.setPlaceholderText(placeholder)
            inp.setClearButtonEnabled(True)
            inp.textChanged.connect(self.aplicar_filtros)
            self.filtros[col_idx] = inp
            filter_layout.addWidget(inp)

        layout.addLayout(filter_layout)

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Nombre",
                "Unidad Base",
                "Categoría",
                "Grupo Calc.",
                "Factor",
                "Presentación",
            ]
        )

        # --- CORRECCIÓN DE ANCHO DE COLUMNAS Y TEXT WRAP ---
        self.table.setWordWrap(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(
            QHeaderView.Interactive
        )  # Permite al usuario modificar el ancho
        header.setStretchLastSection(True)
        self.table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )  # Altura automática

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)

        layout.addWidget(self.table)
        self.setLayout(layout)
        self.cargar_datos()

    def cargar_datos(self):
        self.table.setSortingEnabled(False)

        # Se agrega validación para saber si tiene presentación de compra definida
        query = """
            SELECT i.id, i.nombre, u.nombre, c.nombre, i.grupo_calculo, i.factor_calculo,
                   CASE WHEN (SELECT COUNT(p.id) FROM presentaciones_compra p WHERE p.insumo_id = i.id) > 0 
                        THEN 'Definida' ELSE 'Sin definir' END as estado_presentacion
            FROM insumos i
            LEFT JOIN unidades_medida u ON i.unidad_base_id = u.id
            LEFT JOIN categorias_insumos c ON i.categoria_id = c.id
            ORDER BY i.nombre ASC
        """
        rows = self.db.fetch_all(query)
        self.table.setRowCount(0)
        for r_idx, row in enumerate(rows):
            self.table.insertRow(r_idx)

            self.table.setItem(r_idx, 0, NumericItem(str(row[0])))
            self.table.setItem(
                r_idx, 1, QTableWidgetItem(str(row[1]) if row[1] else "-")
            )
            self.table.setItem(
                r_idx, 2, QTableWidgetItem(str(row[2]) if row[2] else "-")
            )
            self.table.setItem(
                r_idx, 3, QTableWidgetItem(str(row[3]) if row[3] else "-")
            )

            # Grupo
            self.table.setItem(
                r_idx, 4, QTableWidgetItem(str(row[4]) if row[4] else "General")
            )

            # Factor
            val_factor = row[5] if row[5] else 1.0
            self.table.setItem(r_idx, 5, NumericItem(str(val_factor)))

            # Estado Presentación
            self.table.setItem(r_idx, 6, QTableWidgetItem(str(row[6])))

        # Ajuste inicial de columnas
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().resizeSection(
            1, 200
        )  # Dar buen espacio al nombre inicial

        self.table.setSortingEnabled(True)
        self.aplicar_filtros()

    def aplicar_filtros(self):
        rows = self.table.rowCount()
        for row in range(rows):
            mostrar = True
            for col, inp in self.filtros.items():
                texto_filtro = inp.text().lower().strip()
                if not texto_filtro:
                    continue
                item = self.table.item(row, col)
                if item:
                    if texto_filtro not in item.text().lower():
                        mostrar = False
                        break
            self.table.setRowHidden(row, not mostrar)

    def abrir_crear(self):
        dlg = InsumoDialog(self.db, parent=self)
        if dlg.exec_():
            self.cargar_datos()

    def abrir_editar(self):
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(
                self, "Aviso", "Seleccione un insumo para editar."
            )

        id_insumo = int(self.table.item(row, 0).text())
        dlg = InsumoDialog(self.db, insumo_id=id_insumo, parent=self)
        if dlg.exec_():
            self.cargar_datos()

    def eliminar(self):
        row = self.table.currentRow()
        if row < 0:
            return
        id_insumo = self.table.item(row, 0).text()

        if (
            QMessageBox.question(self, "Confirmar", "¿Eliminar este insumo?")
            == QMessageBox.Yes
        ):
            try:
                self.db.execute_query("DELETE FROM insumos WHERE id=?", (id_insumo,))
                self.cargar_datos()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"No se puede eliminar (¿Tiene compras asociadas?)\n{e}",
                )


# --- DIÁLOGO DE EDICIÓN ---
class InsumoDialog(QDialog):
    def __init__(self, db, insumo_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.insumo_id = insumo_id
        self.setWindowTitle("Detalle de Insumo")
        self.setMinimumWidth(400)

        layout = QFormLayout()

        self.txt_nombre = QLineEdit()
        self.cmb_unidad = QComboBox()
        self.cmb_categoria = QComboBox()

        self.cmb_grupo_calc = QComboBox()
        self.cmb_grupo_calc.addItems(["General", "COMBOS", "DESAYUNO", "CRIOLLA"])
        self.cmb_grupo_calc.setEditable(True)

        self.spin_factor = QDoubleSpinBox()
        self.spin_factor.setRange(0.1, 10.0)
        self.spin_factor.setSingleStep(0.1)
        self.spin_factor.setValue(1.0)
        self.spin_factor.setToolTip(
            "Factor multiplicador para el cálculo (Ej: 1.0 = exacto, 1.1 = +10% seguridad)"
        )

        # Cargar Combos BD
        unidades = self.db.fetch_all(
            "SELECT id, nombre, abreviatura FROM unidades_medida"
        )
        for u in unidades:
            self.cmb_unidad.addItem(f"{u[1]} ({u[2]})", u[0])

        categorias = self.db.fetch_all("SELECT id, nombre FROM categorias_insumos")
        self.cmb_categoria.addItem("Sin Categoría", None)
        for c in categorias:
            self.cmb_categoria.addItem(c[1], c[0])

        layout.addRow("Nombre Insumo:", self.txt_nombre)
        layout.addRow("Unidad de Inventario:", self.cmb_unidad)
        layout.addRow("Categoría:", self.cmb_categoria)
        layout.addRow("Grupo de Cálculo:", self.cmb_grupo_calc)
        layout.addRow("Factor Cálculo:", self.spin_factor)

        btn_save = QPushButton("Guardar")
        btn_save.setProperty("class", "btn-success")
        btn_save.clicked.connect(self.guardar)
        layout.addRow(btn_save)
        self.setLayout(layout)

        if self.insumo_id:
            self.cargar_datos_edicion()

    def cargar_datos_edicion(self):
        query = "SELECT nombre, unidad_base_id, categoria_id, grupo_calculo, factor_calculo FROM insumos WHERE id=?"
        rows = self.db.fetch_all(query, (self.insumo_id,))
        if rows:
            row = rows[0]
            self.txt_nombre.setText(row[0])

            idx_u = self.cmb_unidad.findData(row[1])
            if idx_u >= 0:
                self.cmb_unidad.setCurrentIndex(idx_u)

            idx_c = self.cmb_categoria.findData(row[2])
            if idx_c >= 0:
                self.cmb_categoria.setCurrentIndex(idx_c)

            grupo = row[3]
            idx_g = self.cmb_grupo_calc.findText(grupo) if grupo else 0
            if idx_g >= 0:
                self.cmb_grupo_calc.setCurrentIndex(idx_g)
            else:
                self.cmb_grupo_calc.setCurrentText(grupo)

            factor = row[4]
            if factor:
                self.spin_factor.setValue(factor)

    def guardar(self):
        nom = self.txt_nombre.text().strip()
        uid = self.cmb_unidad.currentData()
        cid = self.cmb_categoria.currentData()
        grupo = self.cmb_grupo_calc.currentText()
        factor = self.spin_factor.value()

        if not nom or not uid:
            return QMessageBox.warning(
                self, "Error", "Nombre y Unidad son obligatorios"
            )

        try:
            if self.insumo_id:
                query = """
                    UPDATE insumos 
                    SET nombre=?, unidad_base_id=?, categoria_id=?, grupo_calculo=?, factor_calculo=? 
                    WHERE id=?
                """
                self.db.execute_query(
                    query, (nom, uid, cid, grupo, factor, self.insumo_id)
                )
            else:
                query = """
                    INSERT INTO insumos (nombre, unidad_base_id, categoria_id, grupo_calculo, factor_calculo) 
                    VALUES (?,?,?,?,?)
                """
                self.db.execute_query(query, (nom, uid, cid, grupo, factor))
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


# =============================================================================
# PESTAÑA 2: PRESENTACIONES
# =============================================================================
class TabPresentaciones(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.filtros = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        btn_layout = QHBoxLayout()

        btn_add = QPushButton("Definir Presentación")
        btn_add.setProperty("class", "btn-success")
        btn_add.clicked.connect(self.add)

        btn_edit = QPushButton("Editar Seleccionado")
        btn_edit.clicked.connect(self.edit)

        btn_del = QPushButton("Eliminar")
        btn_del.setProperty("class", "btn-danger")
        btn_del.clicked.connect(self.delete)

        btn_historial = QPushButton("Historial de Precios")
        btn_historial.clicked.connect(self.ver_historial)

        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_del)
        btn_layout.addWidget(btn_historial)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # --- FILTROS DE BÚSQUEDA ---
        filter_layout = QHBoxLayout()
        config_filtros = [
            (0, "Filtrar ID"),
            (1, "Filtrar Insumo Base"),
            (2, "Filtrar Presentación"),
        ]

        for col_idx, placeholder in config_filtros:
            inp = QLineEdit()
            inp.setPlaceholderText(placeholder)
            inp.setClearButtonEnabled(True)
            inp.textChanged.connect(self.aplicar_filtros)
            self.filtros[col_idx] = inp
            filter_layout.addWidget(inp)

        layout.addLayout(filter_layout)

        # --- TABLA ---
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Insumo Base",
                "Nombre Presentación",
                "Precio Ref.",
                "Contenido",
                "Unidad",
                "Costo Calc.",
            ]
        )

        # --- CORRECCIÓN DE ANCHO DE COLUMNAS Y TEXT WRAP ---
        self.table.setWordWrap(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)

        layout.addWidget(self.table)
        self.setLayout(layout)
        self.cargar_datos()

    def cargar_datos(self):
        self.table.setSortingEnabled(False)
        query = """
            SELECT p.id, i.nombre, p.nombre, p.precio_compra, p.cantidad_contenido, u.abreviatura, p.costo_unitario_calculado
            FROM presentaciones_compra p
            JOIN insumos i ON p.insumo_id = i.id
            JOIN unidades_medida u ON i.unidad_base_id = u.id
            ORDER BY i.nombre
        """
        rows = self.db.fetch_all(query)
        self.table.setRowCount(0)
        for r, row in enumerate(rows):
            self.table.insertRow(r)
            self.table.setItem(r, 0, NumericItem(str(row[0])))
            self.table.setItem(r, 1, QTableWidgetItem(row[1]))
            self.table.setItem(r, 2, QTableWidgetItem(row[2]))
            self.table.setItem(r, 3, NumericItem(f"${row[3]:.2f}"))
            self.table.setItem(r, 4, NumericItem(str(row[4])))
            self.table.setItem(r, 5, QTableWidgetItem(row[5]))
            self.table.setItem(r, 6, NumericItem(f"${row[6]:.4f}"))

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().resizeSection(1, 150)
        self.table.horizontalHeader().resizeSection(2, 150)

        self.table.setSortingEnabled(True)
        self.aplicar_filtros()

    def aplicar_filtros(self):
        rows = self.table.rowCount()
        for row in range(rows):
            mostrar = True
            for col, inp in self.filtros.items():
                texto_filtro = inp.text().lower().strip()
                if not texto_filtro:
                    continue
                item = self.table.item(row, col)
                if item:
                    if texto_filtro not in item.text().lower():
                        mostrar = False
                        break
            self.table.setRowHidden(row, not mostrar)

    def add(self):
        if PresentacionDialog(self.db, parent=self).exec_():
            self.cargar_datos()

    def edit(self):
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(
                self, "Aviso", "Seleccione una presentación para editar."
            )

        id_pres = int(self.table.item(row, 0).text())
        if PresentacionDialog(self.db, presentacion_id=id_pres, parent=self).exec_():
            self.cargar_datos()

    def delete(self):
        row = self.table.currentRow()
        if row < 0:
            return
        pid = self.table.item(row, 0).text()
        if (
            QMessageBox.question(self, "Eliminar", "¿Borrar esta presentación?")
            == QMessageBox.Yes
        ):
            self.db.execute_query(
                "DELETE FROM presentaciones_compra WHERE id=?", (pid,)
            )
            self.cargar_datos()

    def ver_historial(self):
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(
                self, "Aviso", "Seleccione una presentación para ver su historial de precios."
            )
        pid = int(self.table.item(row, 0).text())
        insumo_nombre = self.table.item(row, 1).text()
        pres_nombre   = self.table.item(row, 2).text()
        dlg = HistorialPreciosDialog(self.db, pid, insumo_nombre, pres_nombre, parent=self)
        dlg.exec_()
        self.cargar_datos()


class PresentacionDialog(QDialog):
    def __init__(self, db, presentacion_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.presentacion_id = presentacion_id
        self._precio_original = None  # para detectar cambio de precio en edición

        titulo = (
            "Editar Presentación de Compra"
            if self.presentacion_id
            else "Nueva Presentación de Compra"
        )
        self.setWindowTitle(titulo)
        self.resize(500, 450)

        layout = QVBoxLayout()
        form = QFormLayout()

        self.cmb_insumo = QComboBox()
        self.cargar_insumos()
        self.cmb_insumo.currentIndexChanged.connect(self.update_labels)

        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: Caja x12, Bulto 50lb")

        self.spin_precio = QDoubleSpinBox()
        self.spin_precio.setMaximum(99999.99)
        self.spin_precio.setPrefix("$ ")

        form.addRow("Insumo Base:", self.cmb_insumo)
        form.addRow("Nombre Empaque:", self.txt_nombre)
        form.addRow("Precio Compra:", self.spin_precio)
        layout.addLayout(form)

        self.chk_detalle = QCheckBox("Es un empaque compuesto (Ej: Caja con botellas)")
        self.chk_detalle.toggled.connect(self.toggle_detalle)
        layout.addWidget(self.chk_detalle)

        self.grp_det = QGroupBox("Contenido Interno")
        f_det = QFormLayout()
        self.txt_sub_nom = QLineEdit()
        self.spin_cant = QSpinBox()
        self.spin_cant.setRange(1, 1000)
        self.spin_cant.valueChanged.connect(self.calc_total)
        self.spin_peso_uni = QDoubleSpinBox()
        self.spin_peso_uni.setRange(0.001, 9999)
        self.spin_peso_uni.setDecimals(3)
        self.spin_peso_uni.valueChanged.connect(self.calc_total)
        self.lbl_u1 = QLabel("Peso/Vol Unitario:")

        f_det.addRow("Nombre Unidad Interna:", self.txt_sub_nom)
        f_det.addRow("Cantidad:", self.spin_cant)
        f_det.addRow(self.lbl_u1, self.spin_peso_uni)
        self.grp_det.setLayout(f_det)
        layout.addWidget(self.grp_det)

        self.grp_tot = QGroupBox("Total para Inventario")
        f_tot = QFormLayout()
        self.spin_total = QDoubleSpinBox()
        self.spin_total.setRange(0.01, 99999)
        self.spin_total.setDecimals(3)
        self.lbl_u2 = QLabel("Contenido Neto Total:")
        f_tot.addRow(self.lbl_u2, self.spin_total)
        self.grp_tot.setLayout(f_tot)
        layout.addWidget(self.grp_tot)

        btn = QPushButton("Guardar Definición")
        btn.setProperty("class", "btn-success")
        btn.clicked.connect(self.guardar)
        layout.addWidget(btn)

        self.setLayout(layout)
        self.toggle_detalle(False)
        self.update_labels()

        if self.presentacion_id:
            self.cargar_datos_edicion()

    def cargar_insumos(self):
        query = "SELECT i.id, i.nombre, u.abreviatura FROM insumos i JOIN unidades_medida u ON i.unidad_base_id = u.id ORDER BY i.nombre"
        rows = self.db.fetch_all(query)
        for r in rows:
            self.cmb_insumo.addItem(f"{r[1]} ({r[2]})", {"id": r[0], "u": r[2]})

    def update_labels(self):
        data = self.cmb_insumo.currentData()
        if data:
            u = data["u"]
            self.lbl_u1.setText(f"Peso/Vol Unitario ({u}):")
            self.lbl_u2.setText(f"Contenido Neto Total ({u}):")

    def toggle_detalle(self, checked):
        self.grp_det.setVisible(checked)
        self.spin_total.setReadOnly(checked)
        if checked:
            self.calc_total()

    def calc_total(self):
        if self.chk_detalle.isChecked():
            total = self.spin_cant.value() * self.spin_peso_uni.value()
            self.spin_total.setValue(total)

    def cargar_datos_edicion(self):
        # Cargar tabla principal de presentación
        query = "SELECT insumo_id, nombre, precio_compra, cantidad_contenido FROM presentaciones_compra WHERE id=?"
        rows = self.db.fetch_all(query, (self.presentacion_id,))
        if rows:
            row = rows[0]

            # Buscar el insumo en el combobox
            insumo_id = row[0]
            for i in range(self.cmb_insumo.count()):
                data = self.cmb_insumo.itemData(i)
                if data and data["id"] == insumo_id:
                    self.cmb_insumo.setCurrentIndex(i)
                    break

            self.txt_nombre.setText(row[1])
            self.spin_precio.setValue(row[2])
            self._precio_original = row[2]  # guardar para detectar cambio
            self.spin_total.setValue(row[3])

            # Verificar si tiene composición (empaque compuesto)
            comp_query = "SELECT nombre_empaque_interno, cantidad_interna, peso_o_volumen_unitario FROM composicion_empaque WHERE presentacion_id=?"
            comp_rows = self.db.fetch_all(comp_query, (self.presentacion_id,))

            if comp_rows:
                c_row = comp_rows[0]
                self.chk_detalle.setChecked(True)
                self.txt_sub_nom.setText(c_row[0])
                self.spin_cant.setValue(c_row[1])
                self.spin_peso_uni.setValue(c_row[2])
            else:
                self.chk_detalle.setChecked(False)

    def guardar(self):
        data_ins = self.cmb_insumo.currentData()
        if not data_ins:
            return

        ins_id = data_ins["id"]
        nom = self.txt_nombre.text().strip()
        precio = self.spin_precio.value()
        total = self.spin_total.value()

        if total <= 0:
            return QMessageBox.warning(
                self, "Error", "El contenido total debe ser mayor a 0"
            )
        if not nom:
            return QMessageBox.warning(
                self, "Error", "Debe proporcionar un nombre para el empaque"
            )

        costo_u = precio / total
        hoy = QDate.currentDate().toString("yyyy-MM-dd")

        try:
            if self.presentacion_id:
                # Update presentación
                self.db.execute_query(
                    """UPDATE presentaciones_compra
                       SET insumo_id=?, nombre=?, cantidad_contenido=?, precio_compra=?, costo_unitario_calculado=?
                       WHERE id=?""",
                    (ins_id, nom, total, precio, costo_u, self.presentacion_id),
                )
                pid = self.presentacion_id

                # Si el precio cambió, registrar en historial
                if self._precio_original is not None and round(precio, 4) != round(self._precio_original, 4):
                    self.db.execute_query(
                        "UPDATE historial_precios_presentacion SET es_precio_actual=0 WHERE presentacion_id=?",
                        (pid,),
                    )
                    self.db.execute_query(
                        """INSERT INTO historial_precios_presentacion
                           (presentacion_id, precio_compra, costo_unitario_calculado, fecha_registro, es_precio_actual)
                           VALUES (?,?,?,?,1)""",
                        (pid, precio, costo_u, hoy),
                    )

                self.db.execute_query(
                    "DELETE FROM composicion_empaque WHERE presentacion_id=?", (pid,)
                )
            else:
                # Insert presentación nueva
                cur = self.db.execute_query(
                    """INSERT INTO presentaciones_compra
                       (insumo_id, nombre, cantidad_contenido, precio_compra, costo_unitario_calculado)
                       VALUES (?,?,?,?,?)""",
                    (ins_id, nom, total, precio, costo_u),
                )
                pid = cur.lastrowid

                # Registrar precio inicial en historial
                self.db.execute_query(
                    """INSERT INTO historial_precios_presentacion
                       (presentacion_id, precio_compra, costo_unitario_calculado, fecha_registro, es_precio_actual)
                       VALUES (?,?,?,?,1)""",
                    (pid, precio, costo_u, hoy),
                )

            # Insertar composición si aplica
            if self.chk_detalle.isChecked():
                self.db.execute_query(
                    """INSERT INTO composicion_empaque
                       (presentacion_id, nombre_empaque_interno, cantidad_interna, peso_o_volumen_unitario)
                       VALUES (?,?,?,?)""",
                    (
                        pid,
                        self.txt_sub_nom.text(),
                        self.spin_cant.value(),
                        self.spin_peso_uni.value(),
                    ),
                )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


# =============================================================================
# HISTORIAL DE PRECIOS
# =============================================================================

class NuevoPrecioDialog(QDialog):
    """Sub-dialog para registrar un nuevo precio como precio actual."""

    def __init__(self, db, presentacion_id, cantidad_contenido, parent=None):
        super().__init__(parent)
        self.db = db
        self.presentacion_id = presentacion_id
        self.cantidad_contenido = cantidad_contenido
        self.setWindowTitle("Registrar Nuevo Precio")
        self.setMinimumWidth(380)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Fecha:", self.date_edit)

        self.cmb_proveedor = QComboBox()
        self.cmb_proveedor.addItem("— Sin proveedor —", None)
        proveedores = self.db.fetch_all("SELECT id, nombre FROM proveedores ORDER BY nombre")
        for p in proveedores:
            self.cmb_proveedor.addItem(p[1], p[0])
        form.addRow("Proveedor:", self.cmb_proveedor)

        self.spin_precio = QDoubleSpinBox()
        self.spin_precio.setMaximum(999999.99)
        self.spin_precio.setDecimals(2)
        self.spin_precio.setPrefix("$ ")
        self.spin_precio.valueChanged.connect(self._actualizar_costo)
        form.addRow("Precio de Compra:", self.spin_precio)

        self.lbl_costo = QLabel("$ 0.0000 por unidad base")
        self.lbl_costo.setStyleSheet("color:#2e7d32; font-size:11px;")
        form.addRow("Costo unitario calc.:", self.lbl_costo)

        self.txt_obs = QLineEdit()
        self.txt_obs.setPlaceholderText("Observación opcional…")
        form.addRow("Observación:", self.txt_obs)

        layout.addLayout(form)

        nota = QLabel("Este precio reemplazará al precio actual de la presentación.")
        nota.setStyleSheet("color:#666666; font-size:10px; font-style:italic;")
        nota.setWordWrap(True)
        layout.addWidget(nota)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#dddddd;")
        layout.addWidget(sep)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Guardar como Precio Actual")
        btns.accepted.connect(self._guardar)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _actualizar_costo(self, precio):
        if self.cantidad_contenido and self.cantidad_contenido > 0:
            costo = precio / self.cantidad_contenido
            self.lbl_costo.setText(f"$ {costo:.4f} por unidad base")

    def _guardar(self):
        precio = self.spin_precio.value()
        if precio <= 0:
            return QMessageBox.warning(self, "Error", "El precio debe ser mayor a cero.")

        proveedor_id = self.cmb_proveedor.currentData()
        fecha = self.date_edit.date().toString("yyyy-MM-dd")
        obs = self.txt_obs.text().strip() or None
        costo_u = precio / self.cantidad_contenido if self.cantidad_contenido > 0 else 0.0

        try:
            # Desactivar precio actual anterior
            self.db.execute_query(
                "UPDATE historial_precios_presentacion SET es_precio_actual=0 WHERE presentacion_id=?",
                (self.presentacion_id,),
            )
            # Insertar nuevo registro de precio
            self.db.execute_query(
                """INSERT INTO historial_precios_presentacion
                   (presentacion_id, proveedor_id, precio_compra, costo_unitario_calculado,
                    fecha_registro, es_precio_actual, observacion)
                   VALUES (?,?,?,?,?,1,?)""",
                (self.presentacion_id, proveedor_id, precio, costo_u, fecha, obs),
            )
            # Actualizar precio vigente en presentaciones_compra
            self.db.execute_query(
                "UPDATE presentaciones_compra SET precio_compra=?, costo_unitario_calculado=? WHERE id=?",
                (precio, costo_u, self.presentacion_id),
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class _MiniPriceChart(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(6, 2.2), dpi=96, facecolor="white")
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(170)

    def refresh(self, dates, prices):
        self.ax.clear()
        self.fig.set_facecolor("white")
        self.ax.set_facecolor("#fafafa")

        if not dates:
            self.ax.text(0.5, 0.5, "Sin datos de precios",
                         ha="center", va="center",
                         transform=self.ax.transAxes, color="#aaaaaa", fontsize=9)
            self.ax.axis("off")
            self.fig.tight_layout()
            self.draw()
            return

        color = "#a20f22"
        if len(dates) == 1:
            self.ax.scatter(dates, prices, color=color, zorder=5, s=60)
            self.ax.annotate(f"${prices[0]:,.2f}", (dates[0], prices[0]),
                             textcoords="offset points", xytext=(5, 5),
                             fontsize=8, color=color)
        else:
            self.ax.plot(dates, prices, marker="o", markersize=5,
                         linewidth=1.8, color=color)
            for d, p in zip(dates, prices):
                self.ax.annotate(f"${p:,.2f}", (d, p),
                                 textcoords="offset points", xytext=(3, 5),
                                 fontsize=7, color=color)

        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%y"))
        self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        self.fig.autofmt_xdate(rotation=30, ha="right")
        self.ax.yaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, _: f"${x:,.2f}")
        )
        self.ax.tick_params(labelsize=7)
        self.ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.6)
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.ax.set_title("Evolución del Precio", fontsize=9,
                          fontweight="bold", color="#2c3e50", pad=5)
        self.fig.tight_layout()
        self.draw()


class HistorialPreciosDialog(QDialog):
    """Dialog principal para consultar y gestionar el historial de precios de una presentación."""

    def __init__(self, db, presentacion_id, insumo_nombre, pres_nombre, parent=None):
        super().__init__(parent)
        self.db = db
        self.presentacion_id = presentacion_id
        self.setWindowTitle(f"Historial de Precios — {insumo_nombre}")
        self.setMinimumSize(750, 600)
        self._build_ui(insumo_nombre, pres_nombre)
        self._cargar_datos()

    def _build_ui(self, insumo_nombre, pres_nombre):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Encabezado
        lbl_titulo = QLabel(f"<b>{insumo_nombre}</b> — {pres_nombre}")
        lbl_titulo.setStyleSheet("font-size:13px; color:#a20f22;")
        layout.addWidget(lbl_titulo)

        # Toolbar
        toolbar = QHBoxLayout()
        btn_nuevo = QPushButton("+ Registrar Nuevo Precio")
        btn_nuevo.setProperty("class", "btn-success")
        btn_nuevo.clicked.connect(self._registrar_precio)
        toolbar.addWidget(btn_nuevo)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Mini chart
        self.chart = _MiniPriceChart(self)
        layout.addWidget(self.chart)

        # Tabla de historial
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Fecha", "Proveedor", "Precio Compra", "Costo Unit.", "Observación", "Estado"
        ])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.Stretch)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

        btns = QDialogButtonBox(QDialogButtonBox.Close)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _cargar_datos(self):
        rows = self.db.fetch_all(
            """SELECT h.fecha_registro, p.nombre, h.precio_compra,
                      h.costo_unitario_calculado, h.observacion, h.es_precio_actual
               FROM historial_precios_presentacion h
               LEFT JOIN proveedores p ON p.id = h.proveedor_id
               WHERE h.presentacion_id = ?
               ORDER BY h.fecha_registro DESC, h.id DESC""",
            (self.presentacion_id,),
        )
        self.table.setRowCount(len(rows))
        chart_dates = []
        chart_prices = []
        for r, row in enumerate(rows):
            fecha, proveedor, precio, costo, obs, es_actual = row

            self.table.setItem(r, 0, QTableWidgetItem(str(fecha or "")))
            self.table.setItem(r, 1, QTableWidgetItem(proveedor or "—"))
            self.table.setItem(r, 2, QTableWidgetItem(f"$ {float(precio):.2f}"))
            self.table.setItem(r, 3, QTableWidgetItem(f"$ {float(costo):.4f}"))
            self.table.setItem(r, 4, QTableWidgetItem(obs or ""))

            if es_actual:
                estado_item = QTableWidgetItem("ACTUAL")
                estado_item.setForeground(QColor("#2e7d32"))
                estado_item.setBackground(QColor("#e8f5e9"))
                font = estado_item.font()
                font.setBold(True)
                estado_item.setFont(font)
                for col in range(5):
                    item = self.table.item(r, col)
                    if item:
                        item.setBackground(QColor("#e8f5e9"))
            else:
                estado_item = QTableWidgetItem("Histórico")
                estado_item.setForeground(QColor("#9e9e9e"))

            estado_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 5, estado_item)

            try:
                chart_dates.append(datetime.date.fromisoformat(str(fecha)))
                chart_prices.append(float(precio))
            except (ValueError, TypeError):
                pass

        chart_dates.reverse()
        chart_prices.reverse()
        self.chart.refresh(chart_dates, chart_prices)

    def _registrar_precio(self):
        row = self.db.fetch_one(
            "SELECT cantidad_contenido FROM presentaciones_compra WHERE id=?",
            (self.presentacion_id,),
        )
        cantidad_contenido = row[0] if row else 1.0
        dlg = NuevoPrecioDialog(self.db, self.presentacion_id, cantidad_contenido, parent=self)
        if dlg.exec_():
            self._cargar_datos()


# =============================================================================
# PESTAÑA 3: CATEGORÍAS
# =============================================================================
class TabCategorias(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        action_layout = QHBoxLayout()

        btn_add = QPushButton("Nueva Categoría")
        btn_add.setProperty("class", "btn-success")
        btn_add.clicked.connect(self.abrir_form_crear)

        btn_del = QPushButton("Eliminar")
        btn_del.setProperty("class", "btn-danger")
        btn_del.clicked.connect(self.eliminar_registro)

        action_layout.addWidget(btn_add)
        action_layout.addWidget(btn_del)
        action_layout.addStretch()
        layout.addLayout(action_layout)

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Código", "Nombre Categoría"])

        # Aplicamos la misma lógica interactiva y de envoltura
        self.table.setWordWrap(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.cargar_datos()

    def cargar_datos(self):
        rows = self.db.fetch_all("SELECT id, codigo, nombre FROM categorias_insumos")
        self.table.setRowCount(0)
        for row_idx, row_data in enumerate(rows):
            self.table.insertRow(row_idx)
            for col_idx, data in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))

        self.table.resizeColumnsToContents()

    def abrir_form_crear(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Nueva Categoría")
        form = QFormLayout(dialog)
        dialog.setMinimumWidth(300)

        inp_code = QLineEdit()
        inp_name = QLineEdit()

        form.addRow("Código (ej. 5008):", inp_code)
        form.addRow("Nombre (ej. CARNES):", inp_name)

        btn_save = QPushButton("Guardar")
        btn_save.clicked.connect(dialog.accept)
        form.addRow(btn_save)

        if dialog.exec_() == QDialog.Accepted:
            codigo = inp_code.text().strip()
            nombre = inp_name.text().strip()
            if codigo and nombre:
                try:
                    self.db.execute_query(
                        "INSERT INTO categorias_insumos (codigo, nombre) VALUES (?,?)",
                        (codigo, nombre),
                    )
                    self.cargar_datos()
                except Exception as e:
                    QMessageBox.warning(
                        self, "Error", f"Error (probablemente código duplicado): {e}"
                    )

    def eliminar_registro(self):
        row = self.table.currentRow()
        if row < 0:
            return
        id_cat = self.table.item(row, 0).text()

        uso = self.db.fetch_all(
            "SELECT COUNT(*) FROM insumos WHERE categoria_id=?", (id_cat,)
        )
        if uso and uso[0][0] > 0:
            QMessageBox.warning(
                self,
                "No permitido",
                "No puedes eliminar una categoría que tiene insumos asociados.",
            )
            return

        if (
            QMessageBox.question(self, "Confirmar", "¿Eliminar categoría?")
            == QMessageBox.Yes
        ):
            try:
                self.db.execute_query(
                    "DELETE FROM categorias_insumos WHERE id=?", (id_cat,)
                )
                self.cargar_datos()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

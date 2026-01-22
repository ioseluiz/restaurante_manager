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
    QFormLayout,
    QLineEdit,
    QComboBox,
    QMessageBox,
    QLabel,
    QDoubleSpinBox,
    QCheckBox,
    QGroupBox,
    QSpinBox,
)
from PyQt5.QtCore import Qt


# --- CLASE PERSONALIZADA PARA ORDENAR NÚMEROS ---
class NumericItem(QTableWidgetItem):
    """
    Permite que la tabla ordene la columna por valor numérico
    y no por orden alfabético (ej. para que 10 no vaya antes que 2).
    """

    def __lt__(self, other):
        try:
            return float(self.text()) < float(other.text())
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
        # NOTA: Se eliminó TabUnidades, ahora se gestiona en su propio módulo.
        self.tab_insumos = TabInsumos(self.db)
        self.tab_presentaciones = TabPresentaciones(self.db)

        # Añadir pestañas
        self.tabs.addTab(self.tab_insumos, "1. Catálogo de Insumos")
        self.tabs.addTab(self.tab_presentaciones, "2. Presentaciones de Compra")

        # Conectar cambio de pestaña
        self.tabs.currentChanged.connect(self.on_tab_change)

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def cargar_datos(self):
        """
        Método 'puente' para compatibilidad con MainWindow.
        Recarga los datos de la pestaña que esté activa en ese momento.
        """
        self.on_tab_change(self.tabs.currentIndex())

    def on_tab_change(self, index):
        # Recargar datos de la pestaña activa
        if index == 0:
            self.tab_insumos.cargar_datos()
        elif index == 1:
            self.tab_presentaciones.cargar_datos()


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
        # Configuración: (Índice Columna, Placeholder)
        config_filtros = [
            (0, "Filtrar ID"),
            (1, "Filtrar Nombre"),
            (2, "Filtrar Unidad"),
            (3, "Filtrar Categoría"),
            (4, "Filtrar Stock"),
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
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Nombre", "Unidad Base", "Categoría", "Stock"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Habilitar Ordenamiento
        self.table.setSortingEnabled(True)

        layout.addWidget(self.table)

        self.setLayout(layout)
        self.cargar_datos()

    def cargar_datos(self):
        # Desactivar sorting durante la carga para evitar errores de redibujado
        self.table.setSortingEnabled(False)

        query = """
            SELECT i.id, i.nombre, u.nombre, c.nombre, i.stock_actual
            FROM insumos i
            LEFT JOIN unidades_medida u ON i.unidad_base_id = u.id
            LEFT JOIN categorias_insumos c ON i.categoria_id = c.id
            ORDER BY i.nombre ASC
        """
        rows = self.db.fetch_all(query)
        self.table.setRowCount(0)
        for r_idx, row in enumerate(rows):
            self.table.insertRow(r_idx)

            # Col 0: ID (Numérico)
            self.table.setItem(r_idx, 0, NumericItem(str(row[0])))

            # Col 1: Nombre
            val_nombre = str(row[1]) if row[1] is not None else "-"
            self.table.setItem(r_idx, 1, QTableWidgetItem(val_nombre))

            # Col 2: Unidad
            val_unidad = str(row[2]) if row[2] is not None else "-"
            self.table.setItem(r_idx, 2, QTableWidgetItem(val_unidad))

            # Col 3: Categoría
            val_cat = str(row[3]) if row[3] is not None else "-"
            self.table.setItem(r_idx, 3, QTableWidgetItem(val_cat))

            # Col 4: Stock (Numérico)
            val_stock = row[4] if row[4] is not None else 0.0
            self.table.setItem(r_idx, 4, NumericItem(str(val_stock)))

        # Reactivar sorting y aplicar filtros si hay texto escrito
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


# Dialogo Formulario Insumo
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

        # Cargar Combos
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

        btn_save = QPushButton("Guardar")
        btn_save.setProperty("class", "btn-success")
        btn_save.clicked.connect(self.guardar)
        layout.addRow(btn_save)
        self.setLayout(layout)

        if self.insumo_id:
            self.cargar_datos_edicion()

    def cargar_datos_edicion(self):
        rows = self.db.fetch_all(
            "SELECT nombre, unidad_base_id, categoria_id FROM insumos WHERE id=?",
            (self.insumo_id,),
        )
        if rows:
            row = rows[0]
            self.txt_nombre.setText(row[0])
            idx_u = self.cmb_unidad.findData(row[1])
            if idx_u >= 0:
                self.cmb_unidad.setCurrentIndex(idx_u)
            idx_c = self.cmb_categoria.findData(row[2])
            if idx_c >= 0:
                self.cmb_categoria.setCurrentIndex(idx_c)

    def guardar(self):
        nom = self.txt_nombre.text().strip()
        uid = self.cmb_unidad.currentData()
        cid = self.cmb_categoria.currentData()

        if not nom or not uid:
            return QMessageBox.warning(
                self, "Error", "Nombre y Unidad son obligatorios"
            )

        try:
            if self.insumo_id:
                self.db.execute_query(
                    "UPDATE insumos SET nombre=?, unidad_base_id=?, categoria_id=? WHERE id=?",
                    (nom, uid, cid, self.insumo_id),
                )
            else:
                self.db.execute_query(
                    "INSERT INTO insumos (nombre, unidad_base_id, categoria_id) VALUES (?,?,?)",
                    (nom, uid, cid),
                )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


# =============================================================================
# PESTAÑA 2: PRESENTACIONES (Cajas, Bultos, etc.)
# =============================================================================
class TabPresentaciones(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Definir Presentación")
        btn_add.clicked.connect(self.add)
        btn_del = QPushButton("Eliminar")
        btn_del.setProperty("class", "btn-danger")
        btn_del.clicked.connect(self.delete)
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_del)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

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
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)  # Por defecto, estirar todas
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.cargar_datos()

    def cargar_datos(self):
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
            self.table.setItem(r, 0, QTableWidgetItem(str(row[0])))
            self.table.setItem(r, 1, QTableWidgetItem(row[1]))
            self.table.setItem(r, 2, QTableWidgetItem(row[2]))
            self.table.setItem(r, 3, QTableWidgetItem(f"${row[3]:.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(str(row[4])))
            self.table.setItem(r, 5, QTableWidgetItem(row[5]))
            self.table.setItem(r, 6, QTableWidgetItem(f"${row[6]:.4f}"))

    def add(self):
        if PresentacionDialog(self.db, parent=self).exec_():
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


class PresentacionDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Nueva Presentación de Compra")
        self.resize(500, 450)

        layout = QVBoxLayout()

        # Formulario Básico
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

        # Detalle Composición
        self.chk_detalle = QCheckBox("Es un empaque compuesto (Ej: Caja con botellas)")
        self.chk_detalle.toggled.connect(self.toggle_detalle)
        layout.addWidget(self.chk_detalle)

        self.grp_det = QGroupBox("Contenido Interno")
        f_det = QFormLayout()
        self.txt_sub_nom = QLineEdit()
        self.txt_sub_nom.setPlaceholderText("Ej: Botella")
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

        # Totales
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
        btn.clicked.connect(self.guardar)
        layout.addWidget(btn)

        self.setLayout(layout)
        self.toggle_detalle(False)
        self.update_labels()  # Update labels on init

    def cargar_insumos(self):
        # Cargar insumo y su unidad de medida
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

    def guardar(self):
        data_ins = self.cmb_insumo.currentData()
        if not data_ins:
            return

        ins_id = data_ins["id"]
        nom = self.txt_nombre.text()
        precio = self.spin_precio.value()
        total = self.spin_total.value()

        if total <= 0:
            return QMessageBox.warning(
                self, "Error", "El contenido total debe ser mayor a 0"
            )

        costo_u = precio / total

        try:
            # Insertar Presentación
            cur = self.db.execute_query(
                "INSERT INTO presentaciones_compra (insumo_id, nombre, cantidad_contenido, precio_compra, costo_unitario_calculado) VALUES (?,?,?,?,?)",
                (ins_id, nom, total, precio, costo_u),
            )
            pid = cur.lastrowid

            # Insertar Detalle si aplica
            if self.chk_detalle.isChecked():
                self.db.execute_query(
                    "INSERT INTO composicion_empaque (presentacion_id, nombre_empaque_interno, cantidad_interna, peso_o_volumen_unitario) VALUES (?,?,?,?)",
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

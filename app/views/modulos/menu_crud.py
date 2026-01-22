from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QLineEdit,
    QDialog,
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QHeaderView,
    QMessageBox,
    QFileDialog,
    QTextEdit,
)
from PyQt5.QtCore import Qt
import sqlite3
import csv


# --- CLASE PERSONALIZADA PARA ORDENAR NÚMEROS ---
class NumericItem(QTableWidgetItem):
    """
    Permite que la tabla ordene la columna por valor numérico
    y no por orden alfabético.
    """

    def __lt__(self, other):
        try:
            return float(self.text()) < float(other.text())
        except ValueError:
            return super().__lt__(other)


class MenuCRUD(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.filtros = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # --- 1. HEADER Y BOTONES ---
        action_layout = QHBoxLayout()

        title = QLabel("Gestión del Menú")
        title.setProperty("class", "header-title")

        # Botones
        btn_import = QPushButton(" Importar CSV")
        btn_import.setCursor(Qt.PointingHandCursor)
        btn_import.setStyleSheet(
            "background-color: #3498db; color: white; font-weight: bold;"
        )
        btn_import.clicked.connect(self.importar_csv)

        btn_add = QPushButton(" + Nuevo Item")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setProperty("class", "btn-success")
        btn_add.clicked.connect(self.abrir_form_crear)

        btn_edit = QPushButton("Editar Item")
        btn_edit.setCursor(Qt.PointingHandCursor)
        btn_edit.clicked.connect(self.abrir_form_editar)

        btn_del = QPushButton("Eliminar Item")
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setProperty("class", "btn-danger")
        btn_del.clicked.connect(self.eliminar_registro)

        action_layout.addWidget(title)
        action_layout.addStretch()
        action_layout.addWidget(btn_import)
        action_layout.addWidget(btn_add)
        action_layout.addWidget(btn_edit)
        action_layout.addWidget(btn_del)

        layout.addLayout(action_layout)

        # --- 2. FILTROS DE BÚSQUEDA ---
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(5)

        # CAMBIO: Placeholders ajustados a nombres de BD
        config_filtros = [
            (0, "Filtro id"),
            (1, "Filtro codigo"),
            (2, "Filtro nombre"),
            (3, "Filtro precio_venta"),
            (4, "Filtro es_preparado"),
        ]

        for col_idx, placeholder in config_filtros:
            inp = QLineEdit()
            inp.setPlaceholderText(placeholder)
            inp.setClearButtonEnabled(True)
            inp.textChanged.connect(self.aplicar_filtros)

            self.filtros[col_idx] = inp
            filter_layout.addWidget(inp)

        layout.addLayout(filter_layout)

        # --- 3. TABLA ---
        self.table = QTableWidget()
        self.table.setColumnCount(5)

        # CAMBIO SOLICITADO: Nombres exactos de la base de datos
        headers = ["id", "codigo", "nombre", "precio_venta", "es_preparado"]
        self.table.setHorizontalHeaderLabels(headers)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setSortingEnabled(True)

        layout.addWidget(self.table)

        self.setLayout(layout)
        self.cargar_datos()

    def cargar_datos(self):
        """Consulta la BD y rellena la tabla"""
        self.table.setSortingEnabled(False)

        query = "SELECT id, codigo, nombre, precio_venta, es_preparado FROM menu_items"
        rows = self.db.fetch_all(query)

        self.table.setRowCount(0)
        for row_idx, row_data in enumerate(rows):
            self.table.insertRow(row_idx)

            # 0. id
            self.table.setItem(row_idx, 0, NumericItem(str(row_data[0])))

            # 1. codigo
            codigo = row_data[1] if row_data[1] else ""
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(codigo)))

            # 2. nombre
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(row_data[2])))

            # 3. precio_venta
            precio_fmt = f"{row_data[3]:.2f}"
            self.table.setItem(row_idx, 3, NumericItem(precio_fmt))

            # 4. es_preparado (CAMBIO SOLICITADO: Valor crudo de BD)
            # Mostramos 1 o 0 (o True/False según devuelva el driver, generalmente 1/0 en SQLite)
            es_preparado_val = row_data[4]
            item_es_preparado = QTableWidgetItem(str(es_preparado_val))

            # Guardamos el dato como UserRole por si acaso se necesita lógica interna,
            # pero el texto visible es el valor directo.
            item_es_preparado.setData(Qt.UserRole, es_preparado_val)
            self.table.setItem(row_idx, 4, item_es_preparado)

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
                    texto_celda = item.text().lower()
                    if texto_filtro not in texto_celda:
                        mostrar = False
                        break
            self.table.setRowHidden(row, not mostrar)

    # --- Lógica CRUD ---

    def abrir_form_crear(self):
        self.mostrar_formulario()

    def abrir_form_editar(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Alerta", "Selecciona un item para editar")
            return

        id_item = self.table.item(row, 0).text()
        codigo = self.table.item(row, 1).text()
        nombre = self.table.item(row, 2).text()

        try:
            precio = float(self.table.item(row, 3).text())
        except ValueError:
            precio = 0.0

        es_preparado = self.table.item(row, 4).data(Qt.UserRole)

        data = {
            "id": id_item,
            "codigo": codigo,
            "nombre": nombre,
            "precio": precio,
            "es_preparado": es_preparado,
        }
        self.mostrar_formulario(data)

    def eliminar_registro(self):
        row = self.table.currentRow()
        if row < 0:
            return

        id_item = self.table.item(row, 0).text()

        confirm = QMessageBox.question(
            self,
            "Confirmar",
            "¿Eliminar este item permanentemente?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            self.db.execute_query(
                "DELETE FROM recetas WHERE menu_item_id=?", (id_item,)
            )
            self.db.execute_query("DELETE FROM menu_items WHERE id=?", (id_item,))
            self.cargar_datos()

    def mostrar_formulario(self, data=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Detalle del Item")
        dialog.setFixedSize(400, 300)

        form = QFormLayout(dialog)
        form.setSpacing(15)

        inp_codigo = QLineEdit(data["codigo"] if data else "")
        inp_nombre = QLineEdit(data["nombre"] if data else "")

        inp_precio = QDoubleSpinBox()
        inp_precio.setPrefix("$ ")
        inp_precio.setMaximum(10000.00)
        inp_precio.setDecimals(2)
        if data:
            inp_precio.setValue(data["precio"])

        # Mantenemos el CheckBox en el formulario para que sea amigable editar,
        # aunque la tabla muestre el valor crudo.
        chk_preparado = QCheckBox("es_preparado (1=Sí, 0=No)")
        if data:
            chk_preparado.setChecked(bool(data["es_preparado"]))
        else:
            chk_preparado.setChecked(True)

        form.addRow("codigo:", inp_codigo)
        form.addRow("nombre:", inp_nombre)
        form.addRow("precio_venta:", inp_precio)
        form.addRow("", chk_preparado)

        def guardar():
            codigo = inp_codigo.text().strip()
            nombre = inp_nombre.text().strip()

            if not codigo or not nombre:
                QMessageBox.warning(
                    dialog, "Error", "Código y Nombre son obligatorios."
                )
                return
            dialog.accept()

        btn_save = QPushButton("Guardar")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setProperty("class", "btn-success")
        btn_save.clicked.connect(guardar)

        form.addRow(QLabel(""))
        form.addRow(btn_save)

        if dialog.exec_() == QDialog.Accepted:
            codigo_val = inp_codigo.text().strip()
            nombre_val = inp_nombre.text().strip()
            precio_val = inp_precio.value()
            es_preparado_val = 1 if chk_preparado.isChecked() else 0

            try:
                if data:
                    query = "UPDATE menu_items SET codigo=?, nombre=?, precio_venta=?, es_preparado=? WHERE id=?"
                    params = (
                        codigo_val,
                        nombre_val,
                        precio_val,
                        es_preparado_val,
                        data["id"],
                    )
                else:
                    query = "INSERT INTO menu_items (codigo, nombre, precio_venta, es_preparado) VALUES (?,?,?,?)"
                    params = (codigo_val, nombre_val, precio_val, es_preparado_val)

                self.db.execute_query(query, params)
                self.cargar_datos()

            except sqlite3.IntegrityError:
                QMessageBox.critical(
                    self, "Error", f"El código '{codigo_val}' ya existe."
                )
            except Exception as e:
                QMessageBox.critical(self, "Error BD", str(e))

    def importar_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Importar Menú CSV", "", "Archivos CSV (*.csv);;Todos (*.*)"
        )

        if not file_path:
            return

        agregados = 0
        omitidos = []

        try:
            with open(file_path, mode="r", encoding="utf-8-sig", newline="") as f:
                reader = csv.reader(f)
                rows = list(reader)

                if not rows:
                    return

                start = 0
                try:
                    float(rows[0][2].replace("$", "").replace(",", ""))
                except:
                    start = 1

                for i in range(start, len(rows)):
                    row = rows[i]
                    if len(row) < 3:
                        continue

                    codigo = row[0].strip()
                    nombre = row[1].strip()
                    precio_str = row[2].strip().replace("$", "").replace(",", "")

                    try:
                        precio = float(precio_str)
                    except ValueError:
                        omitidos.append((codigo, nombre, "Precio inválido"))
                        continue

                    existe = self.db.fetch_all(
                        "SELECT 1 FROM menu_items WHERE codigo=?", (codigo,)
                    )
                    if existe:
                        omitidos.append((codigo, nombre, "Código duplicado"))
                        continue

                    es_prep = 1
                    if len(row) > 3 and row[3].strip().lower() in [
                        "0",
                        "no",
                        "false",
                        "f",
                    ]:
                        es_prep = 0

                    try:
                        self.db.execute_query(
                            "INSERT INTO menu_items (codigo, nombre, precio_venta, es_preparado) VALUES (?,?,?,?)",
                            (codigo, nombre, precio, es_prep),
                        )
                        agregados += 1
                    except Exception as e:
                        omitidos.append((codigo, nombre, str(e)))

            self.cargar_datos()

            msg = f"Importación finalizada.\nAgregados: {agregados}\nOmitidos: {len(omitidos)}"
            if omitidos:
                dialog = QDialog(self)
                dialog.setWindowTitle("Reporte de Errores")
                dialog.resize(400, 300)
                vbox = QVBoxLayout(dialog)
                vbox.addWidget(QLabel(msg))
                txt = QTextEdit()
                txt.setPlainText("\n".join([f"{c} - {n}: {r}" for c, n, r in omitidos]))
                vbox.addWidget(txt)
                dialog.exec_()
            else:
                QMessageBox.information(self, "Éxito", msg)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error leyendo archivo:\n{e}")

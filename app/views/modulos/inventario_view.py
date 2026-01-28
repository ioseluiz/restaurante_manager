# [FILE: app/views/modulos/inventario_view.py]
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QDialog,
    QMessageBox,
)
from PyQt5.QtCore import Qt


class InventarioView(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # --- Cabecera y Filtros ---
        header = QHBoxLayout()
        title = QLabel("<h2>Monitor de Inventario Actual</h2>")
        header.addWidget(title)

        header.addStretch()

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar insumo...")
        self.txt_buscar.textChanged.connect(self.cargar_inventario)
        header.addWidget(self.txt_buscar)

        btn_refresh = QPushButton("Actualizar")
        btn_refresh.clicked.connect(self.cargar_inventario)
        header.addWidget(btn_refresh)

        layout.addLayout(header)

        # --- Tabla de Stock ---
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Insumo",
                "Categoría",
                "Unidad",
                "Stock Actual",
                "Costo Unit.",
                "Valor Total",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(
            self.abrir_kardex
        )  # Doble click para ver detalle

        layout.addWidget(self.table)

        # --- Botones de Acción ---
        actions = QHBoxLayout()
        btn_kardex = QPushButton("Ver Movimientos (Kardex)")
        btn_kardex.setStyleSheet(
            "background-color: #3498db; color: white; padding: 5px;"
        )
        btn_kardex.clicked.connect(self.abrir_kardex)

        self.lbl_valor_inventario = QLabel("Valor Total Inventario: $0.00")
        self.lbl_valor_inventario.setStyleSheet("font-weight: bold; font-size: 14px;")

        actions.addWidget(btn_kardex)
        actions.addStretch()
        actions.addWidget(self.lbl_valor_inventario)

        layout.addLayout(actions)
        self.setLayout(layout)

        self.cargar_inventario()

    def cargar_inventario(self):
        filtro = self.txt_buscar.text().lower()

        query = """
            SELECT i.id, i.nombre, c.nombre, u.abreviatura, i.stock_actual, i.costo_unitario
            FROM insumos i
            LEFT JOIN categorias_insumos c ON i.categoria_id = c.id
            LEFT JOIN unidades_medida u ON i.unidad_base_id = u.id
            ORDER BY i.nombre ASC
        """
        rows = self.db.fetch_all(query)

        self.table.setRowCount(0)
        total_inventario = 0

        for r, row in enumerate(rows):
            # Filtrado simple en memoria
            if filtro and (filtro not in row[1].lower()):
                continue

            self.table.insertRow(r)

            # Datos
            stock = row[4]
            costo = row[5]
            valor_total = stock * costo
            total_inventario += valor_total

            self.table.setItem(r, 0, QTableWidgetItem(str(row[0])))
            self.table.setItem(r, 1, QTableWidgetItem(row[1]))
            self.table.setItem(r, 2, QTableWidgetItem(row[2] if row[2] else "-"))
            self.table.setItem(r, 3, QTableWidgetItem(row[3] if row[3] else ""))

            # Columna Stock (Colorear si es bajo o negativo)
            item_stock = QTableWidgetItem(f"{stock:.2f}")
            item_stock.setTextAlignment(Qt.AlignCenter)
            if stock <= 0:
                item_stock.setForeground(Qt.red)
                item_stock.setBackground(Qt.yellow)
            self.table.setItem(r, 4, item_stock)

            self.table.setItem(r, 5, QTableWidgetItem(f"${costo:.2f}"))
            self.table.setItem(r, 6, QTableWidgetItem(f"${valor_total:.2f}"))

        self.lbl_valor_inventario.setText(
            f"Valor Total Inventario: ${total_inventario:,.2f}"
        )

    def abrir_kardex(self):
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(
                self, "Aviso", "Selecciona un insumo para ver su historial."
            )

        insumo_id = self.table.item(row, 0).text()
        nombre_insumo = self.table.item(row, 1).text()

        dialog = KardexDialog(self.db, insumo_id, nombre_insumo, self)
        dialog.exec_()


# --- SUB-VENTANA: DIALOGO DE KARDEX ---
class KardexDialog(QDialog):
    def __init__(self, db, insumo_id, nombre_insumo, parent=None):
        super().__init__(parent)
        self.db = db
        self.insumo_id = insumo_id
        self.setWindowTitle(f"Kardex: {nombre_insumo}")
        self.resize(800, 500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            [
                "Fecha",
                "Movimiento",
                "Cant.",
                "Stock Previo",
                "Stock Nuevo",
                "Detalle / Referencia",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.cargar_datos()
        self.setLayout(layout)

    def cargar_datos(self):
        query = """
            SELECT fecha, tipo_movimiento, cantidad, stock_anterior, stock_nuevo, observacion 
            FROM movimientos_inventario 
            WHERE insumo_id = ? 
            ORDER BY id DESC
        """
        rows = self.db.fetch_all(query, (self.insumo_id,))
        self.table.setRowCount(0)

        for r, row in enumerate(rows):
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(row[0])))
            self.table.setItem(r, 1, QTableWidgetItem(row[1]))

            # Cantidad con color
            cant = row[2]
            item_cant = QTableWidgetItem(f"{cant:+.2f}")
            if cant > 0:
                item_cant.setForeground(Qt.darkGreen)
            else:
                item_cant.setForeground(Qt.red)
            self.table.setItem(r, 2, item_cant)

            self.table.setItem(r, 3, QTableWidgetItem(f"{row[3]:.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"{row[4]:.2f}"))
            self.table.setItem(r, 5, QTableWidgetItem(row[5]))

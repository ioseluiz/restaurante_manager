import sys
import csv

# ### CORRECCIÓN 1: Agregamos Qt a los imports de QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QHeaderView,
    QMessageBox,
)


class ReportParser:
    """Clase encargada de la logica de extraccion de datos del reporte."""

    @staticmethod
    def parse_csv(file_path):
        metadata = {"desde": "N/A", "hasta": "N/A"}
        records = []
        lines = []

        # ### CORRECCIÓN 2: Blindaje de lectura del archivo
        # Esto asegura que 'lines' siempre tenga algo o que si falla, retornemos vacío en vez de None
        try:
            with open(file_path, "r", encoding="latin-1") as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            except Exception:
                return metadata, records  # Retornar vacio si falla la codificacion
        except Exception as e:
            print(f"Error leyendo archivo: {e}")
            return (
                metadata,
                records,
            )  # Retornar vacio si hay otro error (ej. archivo bloqueado)

        # Variables de estado
        current_code = ""
        current_desc = ""
        header_found = False

        for line_idx, line in enumerate(lines):
            # ### CORRECCIÓN 3: El delimitador del archivo es punto y coma (;), no coma (,)
            cells = [c.strip() for c in line.split(";")]

            # -- 1. Extraccion de Metadatos ---
            if line_idx < 20:
                # El archivo original usa "Desde" (sin dos puntos) en una celda separada
                if "Desde" in cells:
                    metadata["desde"] = ReportParser._find_next_value(cells, "Desde")
                if "Hasta" in cells:
                    metadata["hasta"] = ReportParser._find_next_value(cells, "Hasta")

            # -- 2. Deteccion de Inicio de Datos ---
            if "Código" in cells and "Descripción" in cells:
                header_found = True
                continue

            if not header_found:
                continue

            # -- 3. Logica de Extraccion ---
            val_code_1 = cells[1] if len(cells) > 1 else ""
            val_code_2 = cells[2] if len(cells) > 2 else ""
            val_desc_5 = (
                cells[5] if len(cells) > 5 else ""
            )  # Corregido índice para seguridad
            val_desc_6 = cells[6] if len(cells) > 6 else ""

            val_day = cells[7] if len(cells) > 7 else ""
            val_qty = cells[10] if len(cells) > 10 else ""
            val_sales = cells[24] if len(cells) > 24 else ""

            # Actualizar contexto
            if val_code_1:
                current_code = val_code_1
            if val_code_2:
                current_code = val_code_2
            if val_desc_5:
                current_desc = val_desc_5
            if val_desc_6:
                current_desc = val_desc_6

            # Identificar filas de total
            # El criterio es: NO tiene día, SI tiene cantidad y ventas
            is_total_row = (
                not val_day
                and val_qty
                and val_sales
                and not val_code_1
                and not val_code_2
            )

            if is_total_row:
                try:
                    qty_clean = val_qty.replace(",", "")
                    sales_clean = (
                        val_sales.replace("B/.", "")
                        .replace("B/", "")
                        .replace(",", "")
                        .strip()
                    )

                    records.append(
                        {
                            "code": current_code,
                            "desc": current_desc,
                            "qty": qty_clean,
                            "sales": sales_clean,
                        }
                    )
                except ValueError:
                    continue

        # ### CORRECCIÓN 4: El return debe estar ALINEADO con el 'try' inicial (fuera del for)
        return metadata, records

    @staticmethod
    def _find_next_value(cells, key):
        try:
            idx = cells.index(key)
            for i in range(idx + 1, len(cells)):
                if cells[i].strip():
                    return cells[i].strip()
        except ValueError:
            pass
        return "N/A"


class SalesReportApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visor de Reportes de Ventas - Italos")
        self.resize(1000, 600)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        top_layout = QHBoxLayout()
        self.btn_load = QPushButton("Cargar CSV")
        self.btn_load.setFixedWidth(150)
        self.btn_load.setStyleSheet(
            "background-color: #2196F3; color: white; font-weight: bold; padding: 5px;"
        )
        self.btn_load.clicked.connect(self.load_file)

        self.lbl_desde = QLabel("Fecha Desde: --")
        self.lbl_hasta = QLabel("Fecha Hasta: --")
        self.lbl_desde.setStyleSheet("font-weight: bold; margin-left: 20px;")
        self.lbl_hasta.setStyleSheet("font-weight: bold; margin-left: 10px;")

        top_layout.addWidget(self.btn_load)
        top_layout.addWidget(self.lbl_desde)
        top_layout.addWidget(self.lbl_hasta)
        top_layout.addStretch()

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Código", "Descripción", "Cantidad", "Total Ventas"]
        )

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)

        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.table)

    def load_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir Reporte CSV",
            "",
            "Archivos CSV (*.csv);;Todos los archivos (*)",
            options=options,
        )
        if file_path:
            self.process_and_display(file_path)

    def process_and_display(self, file_path):
        try:
            metadata, records = ReportParser.parse_csv(file_path)

            self.lbl_desde.setText(f"Fecha Desde: {metadata['desde']}")
            self.lbl_hasta.setText(f"Fecha Hasta: {metadata['hasta']}")
            self.populate_table(records)
            QMessageBox.information(
                self, "Éxito", f"Se cargaron {len(records)} registros correctamente."
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error: {str(e)}")

    def populate_table(self, records):
        self.table.setRowCount(0)
        self.table.setRowCount(len(records))

        for row_idx, record in enumerate(records):
            item_code = QTableWidgetItem(record["code"])
            item_desc = QTableWidgetItem(record["desc"])
            item_qty = QTableWidgetItem(record["qty"])
            item_sales = QTableWidgetItem(record["sales"])

            item_qty.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_sales.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.table.setItem(row_idx, 0, item_code)
            self.table.setItem(row_idx, 1, item_desc)
            self.table.setItem(row_idx, 2, item_qty)
            self.table.setItem(row_idx, 3, item_sales)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = SalesReportApp()
    window.show()
    sys.exit(app.exec_())

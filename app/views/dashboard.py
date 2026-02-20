from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFrame,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PyQt5.QtCore import Qt
import datetime


class DashboardView(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(20)

        # Título principal
        lbl_titulo = QLabel("Panel de Control (Dashboard)")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        self.layout.addWidget(lbl_titulo)

        # --- 1. FILA DE TARJETAS (KPIs) ---
        kpi_layout = QHBoxLayout()

        self.card_ventas_hoy = self.crear_tarjeta("Ventas de Hoy", "$ 0.00", "#27ae60")
        self.card_ventas_mes = self.crear_tarjeta("Ventas del Mes", "$ 0.00", "#2980b9")
        self.card_cuentas_pagar = self.crear_tarjeta(
            "Cuentas por Pagar", "$ 0.00", "#c0392b"
        )

        kpi_layout.addWidget(self.card_ventas_hoy)
        kpi_layout.addWidget(self.card_ventas_mes)
        kpi_layout.addWidget(self.card_cuentas_pagar)
        self.layout.addLayout(kpi_layout)

        # --- 2. FILA DE TABLAS (Alertas y Top) ---
        tablas_layout = QHBoxLayout()

        # Tabla de Inventario Crítico
        self.tabla_stock = self.crear_tabla(
            "Alerta de Stock (Top 5 más bajos)", ["Insumo", "Stock Actual"]
        )
        tablas_layout.addWidget(self.tabla_stock)

        # Tabla de Platos más vendidos
        self.tabla_top_platos = self.crear_tabla(
            "Platos Más Vendidos", ["Plato", "Cant. Vendida"]
        )
        tablas_layout.addWidget(self.tabla_top_platos)

        self.layout.addLayout(tablas_layout)

        # Cargar los datos inmediatamente
        self.cargar_datos()

    def crear_tarjeta(self, titulo, valor_inicial, color_borde):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 8px;
                border-top: 4px solid {color_borde};
            }}
            QLabel {{ border: none; }}
        """)
        layout = QVBoxLayout(frame)

        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet("color: #7f8c8d; font-size: 14px; font-weight: bold;")
        lbl_titulo.setAlignment(Qt.AlignCenter)

        lbl_valor = QLabel(valor_inicial)
        lbl_valor.setStyleSheet(f"color: #2c3e50; font-size: 22px; font-weight: bold;")
        lbl_valor.setAlignment(Qt.AlignCenter)

        # Guardamos la referencia al label del valor como atributo del frame para actualizarlo después
        frame.lbl_valor = lbl_valor

        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_valor)
        return frame

    def crear_tabla(self, titulo, cabeceras):
        container = QFrame()
        layout = QVBoxLayout(container)

        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #34495e; margin-bottom: 5px;"
        )
        layout.addWidget(lbl_titulo)

        tabla = QTableWidget()
        tabla.setColumnCount(len(cabeceras))
        tabla.setHorizontalHeaderLabels(cabeceras)
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        tabla.setSelectionMode(QTableWidget.NoSelection)
        layout.addWidget(tabla)

        # Guardamos referencia a la tabla
        container.tabla = tabla
        return container

    def cargar_datos(self):
        """Actualiza los datos visuales consultando la base de datos."""
        hoy = datetime.date.today().strftime("%Y-%m-%d")
        mes_actual = datetime.date.today().month

        # 1. Cuentas por Pagar (Compras pendientes)
        res_pagar = self.db.fetch_one(
            "SELECT SUM(total) FROM compras WHERE estado = 'PENDIENTE'"
        )
        total_pagar = res_pagar[0] if res_pagar and res_pagar[0] else 0.0
        self.card_cuentas_pagar.lbl_valor.setText(f"$ {total_pagar:,.2f}")

        # 2. Ventas del Mes
        res_mes = self.db.fetch_one(
            "SELECT SUM(total_venta_reportada) FROM reportes_ventas WHERE mes = ?",
            (mes_actual,),
        )
        total_mes = res_mes[0] if res_mes and res_mes[0] else 0.0
        self.card_ventas_mes.lbl_valor.setText(f"$ {total_mes:,.2f}")

        # 3. Alerta de Stock (Top 5)
        stock_bajo = self.db.fetch_all(
            "SELECT nombre, stock_actual FROM insumos ORDER BY stock_actual ASC LIMIT 5"
        )
        tabla_s = self.tabla_stock.tabla
        tabla_s.setRowCount(len(stock_bajo))
        for row_idx, row_data in enumerate(stock_bajo):
            tabla_s.setItem(row_idx, 0, QTableWidgetItem(str(row_data[0])))
            tabla_s.setItem(row_idx, 1, QTableWidgetItem(f"{row_data[1]:.2f}"))

        # 4. Platos más vendidos (Top 5)
        query_top = """
            SELECT m.nombre, SUM(d.cantidad) as total_vendido
            FROM detalle_ventas_diarias d
            JOIN menu_items m ON d.menu_item_id = m.id
            GROUP BY m.id
            ORDER BY total_vendido DESC LIMIT 5
        """
        top_platos = self.db.fetch_all(query_top)
        tabla_p = self.tabla_top_platos.tabla
        tabla_p.setRowCount(len(top_platos))
        for row_idx, row_data in enumerate(top_platos):
            tabla_p.setItem(row_idx, 0, QTableWidgetItem(str(row_data[0])))
            tabla_p.setItem(row_idx, 1, QTableWidgetItem(f"{row_data[1]:.2f}"))

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QHeaderView,
    QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

class NumericItem(QTableWidgetItem):
    """Permite ordenar columnas numéricas correctamente."""
    def __lt__(self, other):
        try:
            return float(self.text()) < float(other.text())
        except ValueError:
            return super().__lt__(other)

class ResumenConsolidadosView(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- HEADER ---
        header_layout = QHBoxLayout()
        title = QLabel("<h2>Resumen General Mensual</h2>")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        btn_refresh = QPushButton("Actualizar Datos")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setProperty("class", "btn-primary")
        btn_refresh.clicked.connect(self.cargar_datos)
        header_layout.addWidget(btn_refresh)
        
        layout.addLayout(header_layout)
        
        info = QLabel("Vista consolidada de todos los ingresos (Ventas) y los gastos/pagos realizados por mes.")
        info.setStyleSheet("color: #7f8c8d; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(info)

        # --- TABLA ---
        self.table = QTableWidget()
        
        self.columnas = [
            "Mes / Año", 
            "Total Ventas (+)", 
            "Efectivo (-)", 
            "Cheques (-)", 
            "Yappy (-)", 
            "Tarjetas (-)", 
            "Total Gastos (-)", 
            "Balance General"
        ]
        
        self.table.setColumnCount(len(self.columnas))
        self.table.setHorizontalHeaderLabels(self.columnas)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
            
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)
        
        layout.addWidget(self.table)
        self.setLayout(layout)

    def cargar_datos(self):
        self.table.setSortingEnabled(False)
        
        # Diccionario para agrupar por mes: { 'YYYY-MM': { 'ventas': 0, 'efectivo': 0, ... } }
        datos_mensuales = {}
        
        def inicializar_mes(mes):
            if mes not in datos_mensuales:
                datos_mensuales[mes] = {
                    'ventas': 0.0,
                    'efectivo': 0.0,
                    'cheques': 0.0,
                    'yappy': 0.0,
                    'tarjetas': 0.0
                }

        # 1. Obtener Ventas (Diario de Ventas)
        self.db.cursor.execute("""
            SELECT strftime('%Y-%m', fecha) as mes, SUM(total_ventas) 
            FROM diario_ventas GROUP BY mes
        """)
        for row in self.db.cursor.fetchall():
            mes = row[0]
            if not mes: continue
            inicializar_mes(mes)
            datos_mensuales[mes]['ventas'] += float(row[1] or 0.0)

        # 2. Obtener Gastos en Efectivo
        self.db.cursor.execute("""
            SELECT strftime('%Y-%m', fecha) as mes, SUM(total) 
            FROM pagos_efectivo GROUP BY mes
        """)
        for row in self.db.cursor.fetchall():
            mes = row[0]
            if not mes: continue
            inicializar_mes(mes)
            datos_mensuales[mes]['efectivo'] += float(row[1] or 0.0)

        # 3. Obtener Gastos por Cheque (monto)
        self.db.cursor.execute("""
            SELECT strftime('%Y-%m', fecha) as mes, SUM(monto) 
            FROM chequera GROUP BY mes
        """)
        for row in self.db.cursor.fetchall():
            mes = row[0]
            if not mes: continue
            inicializar_mes(mes)
            datos_mensuales[mes]['cheques'] += float(row[1] or 0.0)

        # 4. Obtener Gastos por Yappy (monto)
        self.db.cursor.execute("""
            SELECT strftime('%Y-%m', fecha) as mes, SUM(monto) 
            FROM transacciones_yappy GROUP BY mes
        """)
        for row in self.db.cursor.fetchall():
            mes = row[0]
            if not mes: continue
            inicializar_mes(mes)
            datos_mensuales[mes]['yappy'] += float(row[1] or 0.0)

        # 5. Obtener Gastos por Tarjeta (Solo tipo COMPRA, es decir, pagos realizados a terceros)
        self.db.cursor.execute("""
            SELECT strftime('%Y-%m', fecha) as mes, SUM(monto) 
            FROM transacciones_tarjeta 
            WHERE tipo_transaccion = 'COMPRA'
            GROUP BY mes
        """)
        for row in self.db.cursor.fetchall():
            mes = row[0]
            if not mes: continue
            inicializar_mes(mes)
            datos_mensuales[mes]['tarjetas'] += float(row[1] or 0.0)

        # Llenar la tabla
        self.table.setRowCount(0)
        
        # Ordenar meses de más reciente a más antiguo
        meses_ordenados = sorted(datos_mensuales.keys(), reverse=True)
        
        for r_idx, mes in enumerate(meses_ordenados):
            data = datos_mensuales[mes]
            ventas = data['ventas']
            efectivo = data['efectivo']
            cheques = data['cheques']
            yappy = data['yappy']
            tarjetas = data['tarjetas']
            
            total_gastos = efectivo + cheques + yappy + tarjetas
            balance = ventas - total_gastos
            
            self.table.insertRow(r_idx)
            
            # Mes / Año
            self.table.setItem(r_idx, 0, QTableWidgetItem(mes))
            
            # Ventas (+)
            it_ventas = NumericItem(f"{ventas:.2f}")
            it_ventas.setForeground(QColor("#2ecc71")) # Verde
            self.table.setItem(r_idx, 1, it_ventas)
            
            # Efectivo (-)
            self.table.setItem(r_idx, 2, NumericItem(f"{efectivo:.2f}"))
            
            # Cheques (-)
            self.table.setItem(r_idx, 3, NumericItem(f"{cheques:.2f}"))
            
            # Yappy (-)
            self.table.setItem(r_idx, 4, NumericItem(f"{yappy:.2f}"))
            
            # Tarjetas (-)
            self.table.setItem(r_idx, 5, NumericItem(f"{tarjetas:.2f}"))
            
            # Total Gastos (-)
            it_gastos = NumericItem(f"{total_gastos:.2f}")
            it_gastos.setForeground(QColor("#e74c3c")) # Rojo
            font = it_gastos.font()
            font.setBold(True)
            it_gastos.setFont(font)
            self.table.setItem(r_idx, 6, it_gastos)
            
            # Balance
            it_balance = NumericItem(f"{balance:.2f}")
            font_bal = it_balance.font()
            font_bal.setBold(True)
            it_balance.setFont(font_bal)
            if balance > 0:
                it_balance.setForeground(QColor("#2ecc71")) # Verde (Ganancia)
            elif balance < 0:
                it_balance.setForeground(QColor("#e74c3c")) # Rojo (Pérdida)
                
            self.table.setItem(r_idx, 7, it_balance)

        self.table.setSortingEnabled(True)

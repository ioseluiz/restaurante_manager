from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QComboBox,
    QHeaderView,
    QMessageBox,
    QCheckBox,
    QDialog,
    QDoubleSpinBox,
)
from PyQt5.QtCore import Qt
from app.controllers.calculadora import CalculadoraInsumos


class CalculoInsumosView(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.calculadora = CalculadoraInsumos(db_manager)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        # --- Header ---
        header = QLabel("<h2>Cálculo de Necesidad de Insumos (Mensual)</h2>")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # --- Controles ---
        controls_layout = QHBoxLayout()

        lbl_grupo = QLabel("Filtrar por Grupo:")
        self.cmb_grupo = QComboBox()
        self.cmb_grupo.addItems(["Todos", "COMBOS", "DESAYUNO", "CRIOLLA"])
        self.cmb_grupo.setMinimumWidth(150)

        # Checkbox para modo manual
        self.chk_manual = QCheckBox("Simulación Manual (Sin datos históricos)")
        self.chk_manual.setToolTip(
            "Activa esto para ingresar manualmente las ventas por día de la semana."
        )

        btn_calc = QPushButton(" Calcular Necesidad")
        btn_calc.setProperty("class", "btn-primary")
        btn_calc.clicked.connect(self.preparar_calculo)

        controls_layout.addWidget(lbl_grupo)
        controls_layout.addWidget(self.cmb_grupo)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(self.chk_manual)
        controls_layout.addStretch()
        controls_layout.addWidget(btn_calc)

        layout.addLayout(controls_layout)

        # --- Tabla Resultados ---
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Insumo", "Unidad", "Semanal (Est)", "Mensual (x4)", "Sugerencia Compra"]
        )

        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(QHeaderView.Stretch)
        header_view.setSectionResizeMode(0, QHeaderView.ResizeToContents)

        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        lbl_nota = QLabel(
            "Nota: Pase el mouse sobre el nombre del insumo para ver el detalle."
        )
        lbl_nota.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(lbl_nota)

        self.setLayout(layout)

    def preparar_calculo(self):
        grupo = self.cmb_grupo.currentText()
        ventas_manuales = None

        # Si está activado el modo manual, abrimos el diálogo de simulación detallado
        if self.chk_manual.isChecked():
            # 1. Obtener qué platos necesitamos preguntar
            platos = self.calculadora.obtener_platos_por_grupo(grupo)
            if not platos:
                return QMessageBox.information(
                    self,
                    "Aviso",
                    "No hay platos con recetas configuradas para este grupo.",
                )

            # 2. Abrir Dialogo
            dlg = SimulacionVentasDialog(platos, parent=self)
            if dlg.exec_():
                # 3. Obtener datos (Diccionario detallado por días)
                ventas_manuales = dlg.obtener_datos_semanales()
            else:
                return  # Usuario canceló

        self.realizar_calculo(grupo, ventas_manuales)

    def realizar_calculo(self, grupo, ventas_manuales=None):
        self.table.setRowCount(0)
        try:
            resultados = self.calculadora.calcular_requerimiento(grupo, ventas_manuales)
            self.mostrar_resultados(resultados)
        except Exception as e:
            QMessageBox.critical(self, "Error de Cálculo", str(e))

    def mostrar_resultados(self, datos):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        for r_idx, fila in enumerate(datos):
            self.table.insertRow(r_idx)

            item_nom = QTableWidgetItem(fila["insumo"])
            item_nom.setToolTip(fila["detalle"])
            self.table.setItem(r_idx, 0, item_nom)
            self.table.setItem(r_idx, 1, QTableWidgetItem(fila["unidad"]))
            self.table.setItem(r_idx, 2, QTableWidgetItem(f"{fila['semanal']:.2f}"))

            item_mes = QTableWidgetItem(f"{fila['mensual']:.2f}")
            item_mes.setTextAlignment(Qt.AlignCenter)
            item_mes.setBackground(Qt.cyan)
            item_mes.setFlags(item_mes.flags() ^ Qt.ItemIsEditable)
            self.table.setItem(r_idx, 3, item_mes)

            self.table.setItem(r_idx, 4, QTableWidgetItem(fila["compra"]))

        self.table.setSortingEnabled(True)
        if not datos:
            QMessageBox.information(
                self,
                "Resultado",
                "No se encontraron datos. Verifique Filtros, Recetas o Ventas.",
            )


# --- DIÁLOGO PARA INGRESAR VENTAS MANUALES (DETALLADO POR DÍA) ---
class SimulacionVentasDialog(QDialog):
    def __init__(self, lista_platos, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Simulación de Ventas Semanales")
        self.resize(900, 600)  # Más ancho para caber los 7 días
        self.lista_platos = lista_platos  # [(codigo, nombre), ...]

        # Estructura para guardar referencias a los inputs:
        # self.inputs[codigo_plato] = [spin_lun, spin_mar, ..., spin_dom]
        self.inputs = {}

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        lbl_info = QLabel(
            "Ingrese la venta estimada <b>por día de la semana</b> para cada plato."
        )
        layout.addWidget(lbl_info)

        # Botones de ayuda
        btn_layout = QHBoxLayout()
        btn_fill_all = QPushButton("Llenar Todo con 10 (Prueba)")
        btn_fill_all.clicked.connect(self.llenar_todo)

        btn_replicate = QPushButton("Copiar valor del Lunes al resto de la semana")
        btn_replicate.clicked.connect(self.replicar_lunes)

        btn_layout.addWidget(btn_fill_all)
        btn_layout.addWidget(btn_replicate)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Tabla de entradas
        self.table = QTableWidget()
        # Columna 0: Nombre, Columnas 1-7: Días
        dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        self.table.setColumnCount(1 + len(dias))
        headers = ["Plato / Producto"] + dias
        self.table.setHorizontalHeaderLabels(headers)

        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )  # Nombre estirado
        # Ajustar ancho de columnas de días
        for i in range(1, 8):
            self.table.setColumnWidth(i, 60)

        self.table.setRowCount(len(self.lista_platos))

        for idx, (codigo, nombre) in enumerate(self.lista_platos):
            # Nombre del plato (no editable)
            item_nom = QTableWidgetItem(f"{nombre} ({codigo})")
            item_nom.setFlags(Qt.ItemIsEnabled)  # Solo lectura
            self.table.setItem(idx, 0, item_nom)

            # Crear 7 SpinBoxes
            row_spins = []
            for col_dia in range(7):
                spin = QDoubleSpinBox()
                spin.setRange(0, 9999)
                spin.setDecimals(
                    0
                )  # Generalmente las ventas son enteras, pero dejamos double por si acaso
                spin.setValue(0)
                # Ocultar botones de flecha para ahorrar espacio visual si se prefiere, o dejarlos
                spin.setButtonSymbols(QDoubleSpinBox.NoButtons)

                self.table.setCellWidget(idx, col_dia + 1, spin)
                row_spins.append(spin)

            self.inputs[codigo] = row_spins

        layout.addWidget(self.table)

        # Botones Acción
        btns_action = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("Calcular Insumos")
        btn_ok.setProperty("class", "btn-success")
        btn_ok.clicked.connect(self.accept)

        btns_action.addStretch()
        btns_action.addWidget(btn_cancel)
        btns_action.addWidget(btn_ok)
        layout.addLayout(btns_action)

        self.setLayout(layout)

    def llenar_todo(self):
        for lista_spins in self.inputs.values():
            for spin in lista_spins:
                spin.setValue(10)

    def replicar_lunes(self):
        """Toma el valor de la columna Lunes y lo pega en Mar-Dom para cada fila"""
        for lista_spins in self.inputs.values():
            val_lun = lista_spins[0].value()
            for i in range(1, 7):
                lista_spins[i].setValue(val_lun)

    def obtener_datos_semanales(self):
        """
        Retorna la estructura compatible con el controlador:
        { 'CODIGO': {'Lunes': 10, 'Martes': 5, ...} }
        """
        datos = {}
        dias_key = [
            "Lunes",
            "Martes",
            "Miercoles",
            "Jueves",
            "Viernes",
            "Sabado",
            "Domingo",
        ]

        for codigo, lista_spins in self.inputs.items():
            ventas_por_dia = {}
            total_fila = 0

            for i, spin in enumerate(lista_spins):
                val = spin.value()
                if val > 0:
                    ventas_por_dia[dias_key[i]] = val
                    total_fila += val

            if total_fila > 0:
                datos[codigo] = ventas_por_dia

        return datos

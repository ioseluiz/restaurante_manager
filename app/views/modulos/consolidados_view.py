from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from app.views.modulos.resumen_consolidados import ResumenConsolidadosView
from app.views.modulos.chequera import ChequeraCRUD
from app.views.modulos.tarjetas_credito import TarjetasCreditoView
from app.views.modulos.pagos_efectivo import PagosEfectivoView
from app.views.modulos.pagos_yappy import PagosYappyView
from app.views.modulos.diario_ventas import DiarioVentasView

class ConsolidadosView(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        
        # Instantiate sub-views
        self.tab_resumen = ResumenConsolidadosView(self.db)
        self.tab_chequera = ChequeraCRUD(self.db)
        self.tab_tarjetas = TarjetasCreditoView(self.db)
        self.tab_efectivo = PagosEfectivoView(self.db)
        self.tab_yappy = PagosYappyView(self.db)
        self.tab_diario_ventas = DiarioVentasView(self.db)
        
        self.tabs.addTab(self.tab_resumen, "Resumen General")
        self.tabs.addTab(self.tab_chequera, "Chequera")
        self.tabs.addTab(self.tab_tarjetas, "Tarjetas de Crédito")
        self.tabs.addTab(self.tab_efectivo, "Pagos en Efectivo")
        self.tabs.addTab(self.tab_yappy, "Pagos con Yappy")
        self.tabs.addTab(self.tab_diario_ventas, "Diario de Ventas")
        
        # Connect tab change to data reload
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def cargar_datos(self):
        # Called when the module is loaded
        self.on_tab_changed(self.tabs.currentIndex())

    def on_tab_changed(self, index):
        if index == 0:
            if hasattr(self.tab_resumen, "cargar_datos"):
                self.tab_resumen.cargar_datos()
        elif index == 1:
            if hasattr(self.tab_chequera, "cargar_datos"):
                self.tab_chequera.cargar_datos()
        elif index == 2:
            if hasattr(self.tab_tarjetas, "cargar_datos"):
                self.tab_tarjetas.cargar_datos()
        elif index == 3:
            if hasattr(self.tab_efectivo, "cargar_datos"):
                self.tab_efectivo.cargar_datos()
        elif index == 4:
            if hasattr(self.tab_yappy, "cargar_datos"):
                self.tab_yappy.cargar_datos()
        elif index == 5:
            if hasattr(self.tab_diario_ventas, "cargar_datos"):
                self.tab_diario_ventas.cargar_datos()
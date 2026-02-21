# app/views/modulos/ventas.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget

# Importaciones con los nombres CORRECTOS de las clases de tus archivos
from app.views.modulos.carga_reportes import CargaReportesWidget
from app.views.modulos.ventas_diarias import VentasDiariasView


class VentasModulo(QWidget):
    """
    Módulo consolidado de Ventas.
    Agrupa las pestañas de carga de reportes y el registro de ventas diarias.
    """

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db  # Recibimos y guardamos la conexión a la base de datos
        self.setup_ui()

    def setup_ui(self):
        # Layout principal de la pantalla consolidada
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # TabWidget principal que contendrá las 3 pestañas
        self.tabs_principales = QTabWidget()
        self.layout.addWidget(self.tabs_principales)

        # 1. Instanciar las vistas originales PASÁNDOLE LA BASE DE DATOS (self.db)
        self.vista_carga_reportes = CargaReportesWidget(self.db)
        self.vista_ventas_diarias = VentasDiariasView(self.db)

        # 2. Agregar las pestañas en el orden solicitado
        # Extraemos las propiedades internas de tu CargaReportesWidget y las añadimos
        self.tabs_principales.addTab(
            self.vista_carga_reportes.tab_carga, "📥 Cargar Nuevo Reporte"
        )
        self.tabs_principales.addTab(
            self.vista_carga_reportes.tab_historial, "📋 Historial y Consultas"
        )

        # 3. Agregamos la vista de Ventas Diarias como la tercera pestaña
        self.tabs_principales.addTab(
            self.vista_ventas_diarias, "Registro Ventas Diarias"
        )

        # 4. Conectar el evento de cambio de pestaña
        # Esto asegura que el historial se actualice si haces clic en esa pestaña
        self.tabs_principales.currentChanged.connect(self.al_cambiar_pestana)

    def al_cambiar_pestana(self, index):
        # El índice 1 corresponde a la pestaña de "Historial y Consultas"
        if index == 1:
            self.vista_carga_reportes.tab_historial.cargar_lista_reportes()

# app/styles.py

# Paleta de colores "Clean Professional"
COLORS = {
    "primary": "#3498db",  # Azul corporativo
    "primary_hover": "#2980b9",
    "success": "#2ecc71",  # Verde acción positiva
    "success_hover": "#27ae60",
    "danger": "#e74c3c",  # Rojo peligro/eliminar
    "danger_hover": "#c0392b",
    "background": "#ecf0f1",  # Gris muy claro para fondo de ventana
    "surface": "#ffffff",  # Blanco para tarjetas/tablas
    "text": "#2c3e50",  # Gris oscuro para texto (no negro puro)
    "border": "#bdc3c7",
}

# Hoja de estilos QSS global
GLOBAL_STYLES = f"""
    /* --- GENERAL --- */
    QWidget {{
        font-family: 'Segoe UI', 'Roboto', sans-serif;
        font-size: 14px;
        color: {COLORS["text"]};
    }}

    QMainWindow, QDialog {{
        background-color: {COLORS["background"]};
    }}

    /* --- BOTONES ESTÁNDAR --- */
    QPushButton {{
        background-color: {COLORS["primary"]};
        color: white;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: bold;
        border: none;
    }}
    QPushButton:hover {{
        background-color: {COLORS["primary_hover"]};
    }}
    QPushButton:pressed {{
        background-color: #1abc9c;
    }}
    
    /* Botones específicos usando Propiedades Dinámicas */
    QPushButton[class="btn-primary"] {{
        background-color: {COLORS["primary"]};
    }}
    QPushButton[class="btn-primary"]:hover {{
        background-color: {COLORS["primary_hover"]};
    }}

    QPushButton[class="btn-success"] {{
        background-color: {COLORS["success"]};
    }}
    QPushButton[class="btn-success"]:hover {{
        background-color: {COLORS["success_hover"]};
    }}

    QPushButton[class="btn-danger"] {{
        background-color: {COLORS["danger"]};
    }}
    QPushButton[class="btn-danger"]:hover {{
        background-color: {COLORS["danger_hover"]};
    }}
    
    /* Botones del Dashboard (Tarjetas Grandes) */
    QPushButton[class="btn-dashboard"] {{
        background-color: {COLORS["surface"]};
        color: {COLORS["primary"]};
        border: 1px solid {COLORS["border"]};
        font-size: 16px;
        border-radius: 10px;
        padding: 20px;
    }}
    QPushButton[class="btn-dashboard"]:hover {{
        background-color: {COLORS["primary"]};
        color: white;
        border: 1px solid {COLORS["primary"]};
    }}

    /* --- TOOLBAR & NAVEGACIÓN --- */
    QToolBar {{
        background-color: {COLORS["surface"]};
        border-bottom: 1px solid {COLORS["border"]};
        padding: 8px; 
        spacing: 10px;
    }}
    
    /* Botón de "Volver al Inicio" */
    QPushButton[class="btn-navbar"] {{
        background-color: {COLORS["text"]}; 
        color: white;
        border: none;
        border-radius: 5px;
        padding: 8px 20px;
        font-weight: bold;
        font-size: 14px;
        min-width: 120px;
    }}
    
    QPushButton[class="btn-navbar"]:hover {{
        background-color: #34495e; 
    }}
    
    QPushButton[class="btn-navbar"]:pressed {{
        background-color: #1a252f;
    }}

    /* --- TABLAS --- */
    QTableWidget {{
        background-color: {COLORS["surface"]};
        alternate-background-color: #f9f9f9;
        gridline-color: {COLORS["background"]};
        selection-background-color: {COLORS["primary"]};
        selection-color: white;
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
    }}
    
    QHeaderView::section {{
        background-color: {COLORS["background"]}; 
        color: {COLORS["text"]};                  
        padding: 8px;
        border: 1px solid {COLORS["border"]};     
        font-weight: bold;
    }}

    /* --- INPUTS --- */
    QLineEdit, QComboBox, QDoubleSpinBox, QDateEdit {{
        padding: 6px;
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
        background-color: white;
        color: {COLORS["text"]}; 
    }}
    QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {{
        border: 2px solid {COLORS["primary"]};
    }}

    /* --- CORRECCIÓN LISTAS DESPLEGABLES (COMBOBOX) --- */
    /* Fuerza el fondo blanco en la lista que se despliega */
    QComboBox QAbstractItemView {{
        background-color: white;
        color: {COLORS["text"]};
        selection-background-color: {COLORS["primary"]};
        selection-color: white;
        border: 1px solid {COLORS["border"]};
        outline: none;
    }}

    /* --- LABELS HEADER --- */
    QLabel[class="header-title"] {{
        font-size: 22px;
        font-weight: bold;
        color: {COLORS["text"]};
        margin-bottom: 10px;
    }}

    /* --- CORRECCIÓN CALENDARIO (QDateEdit Popup) --- */
    QCalendarWidget QWidget {{
        background-color: white;
        color: {COLORS["text"]};
    }}
    
    QCalendarWidget QWidget#qt_calendar_navigationbar {{
        background-color: {COLORS["background"]};
        border-bottom: 1px solid {COLORS["border"]};
    }}

    QCalendarWidget QToolButton {{
        color: {COLORS["text"]};
        background-color: transparent;
        icon-size: 20px;
        border: none;
        font-weight: bold;
        margin: 2px;
    }}
    QCalendarWidget QToolButton:hover {{
        background-color: #bdc3c7;
        border-radius: 4px;
    }}
    
    QCalendarWidget QMenu {{
        background-color: white;
        color: {COLORS["text"]};
    }}

    QCalendarWidget QSpinBox {{
        background-color: white;
        color: {COLORS["text"]};
        selection-background-color: {COLORS["primary"]};
        selection-color: white;
    }}
    
    QCalendarWidget QAbstractItemView:enabled {{
        background-color: white;
        color: {COLORS["text"]};
        selection-background-color: {COLORS["primary"]};
        selection-color: white;
        outline: none;
    }}
    QCalendarWidget QAbstractItemView:disabled {{
        color: #bdc3c7;
    }}
"""

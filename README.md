# Restaurante Italos Manager 🍽️

**Restaurante Manager** es una aplicación de escritorio robusta desarrollada en Python, diseñada para la gestión integral y operativa de un restaurante. Permite administrar inventarios, recetas, finanzas, ventas y personal a través de una interfaz gráfica moderna e intuitiva.

## 📋 Características Principales

El sistema está organizado en módulos especializados para cubrir todas las áreas del negocio:

### 📦 Gestión de Inventario y Abastecimiento
*   **📉 Inventario en Tiempo Real:** Control de stock, movimientos de entrada/salida y ajustes automáticos.
*   **🚜 Insumos y Unidades:** Gestión detallada de insumos, categorías y conversiones de unidades de medida.
*   **🚚 Abastecimiento Interno:** Control de transferencia de insumos entre diferentes áreas o sucursales.
*   **🛒 Compras y Proveedores:** Registro de facturas vinculadas a presupuestos, con actualización automática de costos.

### 🍲 Gestión Gastronómica
*   **🍳 Recetas (Escandallo):** Definición técnica de platos para calcular costos precisos y descarga automática de stock.
*   **📜 Gestión de Menú:** Administración dinámica de los platos ofrecidos al público.

### 💰 Finanzas y Pagos
*   **💵 Control de Caja:** Módulos específicos para pagos en **Efectivo**, **Yappy** y **Tarjetas de Crédito**.
*   **📓 Chequera:** Gestión y seguimiento de pagos realizados mediante cheques.
*   **📊 Presupuestos:** Proyección de compras mensuales y comparativa contra el gasto real.

### 📈 Ventas y Reportes
*   **📅 Diario de Ventas:** Registro detallado de la operación diaria.
*   **📥 Carga de Reportes:** Importación masiva de datos desde archivos externos (CSV/Excel).
*   **📂 Consolidados:** Resúmenes operativos para la toma de decisiones gerenciales.

### 🔐 Seguridad y Configuración
*   **👤 Usuarios y Roles:** Control de acceso basado en permisos (Admin/Empleado).
*   **⚙️ Gestión de DB:** Herramientas integradas para respaldos, cambio de base de datos y migraciones.

## 🗂️ Estructura del Proyecto

```text
restaurante_manager/
├── app/
│   ├── controllers/       # Lógica de negocio (Reportes, Kardex, Autenticación)
│   ├── database/          # Conexión, configuración y modelos de SQLite
│   ├── reports/           # Generación de reportes PDF y documentos
│   ├── utils/             # Funciones auxiliares e iconos de botones
│   ├── views/             # Ventanas principales (Login, Dashboard)
│   │   └── modulos/       # Todos los módulos funcionales (Ventas, CRUDs, etc.)
│   └── styles.py          # Definición visual y estilos de la aplicación
├── assets/                # Recursos (Iconos, imágenes y datos de ejemplo)
├── data/                  # Almacenamiento local de Base de Datos
├── docs/                  # Documentación técnica adicional por módulo
├── main.py                # Punto de entrada principal
└── requirements.txt       # Dependencias del sistema
```

## 🚀 Instalación y Configuración

### 1. Prerrequisitos
*   **Python 3.8+** instalado.
*   Git (opcional, para clonar).

### 2. Configuración del Entorno
Clona el repositorio o descarga el código y navega a la carpeta:
```bash
cd restaurante_manager
```

Crea y activa un entorno virtual:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configuración Inicial
La aplicación utiliza un archivo `config.json` para localizar la base de datos. Si es la primera vez que se ejecuta, el sistema intentará crear una base de datos por defecto en `data/restaurante.db`.

## 💻 Ejecución

Para iniciar la aplicación, simplemente ejecuta:
```bash
python main.py
```

**Credenciales por defecto:**
*   **Usuario:** `admin`
*   **Contraseña:** `admin123` (Se recomienda cambiarla tras el primer acceso).

## 🛠️ Tecnologías Utilizadas
*   **Lenguaje:** Python 3
*   **Interfaz Gráfica:** PyQt5 (Modernizada con estilos personalizados)
*   **Base de Datos:** SQLite
*   **Análisis de Datos:** Pandas
*   **Generación de Documentos:** ReportLab (para PDFs)
*   **Empaquetado:** PyInstaller

---
Desarrollado para optimizar la eficiencia operativa de **Italos Manager**.

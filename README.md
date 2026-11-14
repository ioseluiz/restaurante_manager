# Restaurante Italos Manager 🍽️

**Italos Manager** es una aplicación de escritorio desarrollada en Python (PyQt5 + SQLite) para la gestión operativa y financiera de un restaurante: insumos, compras, inventario, recetas, presupuestos, pagos, planilla, rentabilidad y costo de platos.

## 📋 Módulos

El menú lateral da acceso a los siguientes módulos:

### 📦 Insumos, compras e inventario
*   **Catálogo de Insumos:** insumos con unidad base y categoría, **presentaciones de compra** con precio e historial de precios, categorías y tipos de empaque.
*   **Compras y Proveedores:** pedidos y compras (pendientes → recibidas), proveedores, resúmenes semanal y mensual y **abastecimiento interno** entre sucursales (cada sucursal lleva su propio inventario: el traslado se registra en ambas y cada una aplica su lado, con Kardex y anulación). Al recibir una compra sube el stock y se actualiza el costo (promedio ponderado). Las compras se pueden vincular a un presupuesto.
*   **Inventario:** stock actual, valor del inventario y **Kardex** por insumo (compras recibidas, ventas diarias y ajustes por conteo).
*   **Toma de Inventario:** sesiones de conteo físico (formato en Excel), revisión línea por línea y ajuste del stock.
*   **Etiquetas y Códigos:** códigos de barras/QR de insumos y presentaciones, escaneo e impresión de etiquetas en PDF.
*   **Unidades de Medida** y **Sucursales**.

### 🍲 Menú, recetas y costos
*   **Gestión de Menú:** platos con código (el del POS) y precio, con importación desde CSV.
*   **Recetas (Fichas):** insumos y cantidades de cada plato.
*   **Costo de Platos:** costo de producir cada plato (ingredientes, acompañamientos, bebida, empaque e indirectos), recetas por tanda, sub-recetas, precio sugerido por canal e importación del Excel de costeo del cliente.
*   **Análisis de Precios:** evolución de los precios de compra de los insumos.

### 📈 Ventas, presupuestos y finanzas
*   **Ventas:** carga de reportes del POS (**CSV**), historial y registro de ventas diarias por plato, que descuenta los insumos del inventario.
*   **Presupuestos:** proyección de compras mensuales a partir de los reportes de ventas y las recetas, bloques de **planilla** y **gastos fijos**, y control de ejecución (presupuestado vs. real).
*   **Consolidados:** Diario de Ventas (cierre diario), Chequera, Tarjetas de Crédito, Pagos en Efectivo (con desglose por categoría), Pagos con Yappy y Resumen General mensual.
*   **Rentabilidad:** estado de resultados mensual y anual (ventas, costo de ventas real y teórico, gastos y utilidad).
*   **Panel de Control:** resumen del negocio (valor del inventario, ventas y utilidad del mes).

### 👥 Personal
*   **Planilla:** empleados, períodos de pago con horas y recargos, vales, resumen con reglas de Panamá (seguro social, seguro educativo, riesgo profesional, ISR) y provisiones laborales. Su costo completo es el que usan los presupuestos y el costo de platos.

### 🔐 Seguridad, configuración y ayuda
*   **Usuarios:** roles `admin`, `gerente` y `empleado`. Solo el rol administrador ve la gestión de usuarios y la configuración de la base de datos.
*   **Configurar BD** (administrador): cambiar la base de datos en uso y crear copias de respaldo.
*   **Ayuda en pantalla:** menú **Ayuda** (o **F1**) con la guía de cada módulo.

> **Inventario:** el stock cambia por compras recibidas, **ventas diarias** (al pulsar «Actualizar Inventario (Kardex)» se descuentan los insumos según las recetas, con recetas por tanda y sub-recetas; «Reabrir Día» lo revierte), abastecimientos internos (envío baja, recepción sube) y ajustes por toma de inventario.

## 🗂️ Estructura del Proyecto

```text
restaurante_manager/
├── app/
│   ├── controllers/       # Lógica de negocio (Kardex, costeo, rentabilidad, códigos, reportes…)
│   ├── database/          # Conexión SQLite, migraciones y SQL compartido
│   ├── reports/           # Generación de reportes PDF y Excel
│   ├── utils/             # Utilidades (planilla, gastos, importador, ayuda…)
│   ├── views/             # Ventana principal, login, ayuda
│   │   └── modulos/       # Los módulos funcionales
│   └── styles.py          # Estilos de la aplicación
├── assets/                # Iconos, imágenes y la ayuda en pantalla (assets/ayuda/*.md)
├── docs/                  # Guías técnicas por módulo y manual de usuario en PDF
├── generar_manual.py      # Genera el manual PDF desde assets/ayuda/
├── tests/                 # Pruebas automáticas (pytest)
├── main.py                # Punto de entrada
└── requirements.txt       # Dependencias
```

## 🚀 Instalación y Configuración

### 1. Prerrequisitos
*   **Python 3.10 o superior** (el instalador se compila con 3.11).
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
La ubicación de la base de datos se guarda en `~/.restaurante_manager/config.json`. Si no existe, la aplicación crea una base de datos por defecto en `~/.restaurante_manager/restaurante.db`. Las tablas y migraciones se crean o actualizan automáticamente al abrir la aplicación.

## 💻 Ejecución

Para iniciar la aplicación, simplemente ejecuta:
```bash
python main.py
```

**Credenciales por defecto:**
*   **Usuario:** `admin`
*   **Contraseña:** `admin123` (Se recomienda cambiarla tras el primer acceso).

## 🏷️ Versiones

La versión aparece en el título de la ventana, en la barra de estado y en **Ayuda → Acerca de**. Vive en `app/version.py`; el CI la reemplaza con la del tag al compilar. Un tag con sufijo (`v1.3.0-beta.1`) publica el instalador como **pre-release** y uno sin sufijo (`v1.3.0`) como release oficial. Detalles en `docs/versiones.md`.

## 🧪 Pruebas

```bash
pip install pytest
python -m pytest tests
```

## 🛠️ Tecnologías Utilizadas
*   **Lenguaje:** Python 3
*   **Interfaz Gráfica:** PyQt5 (con estilos personalizados)
*   **Base de Datos:** SQLite
*   **Gráficos:** Matplotlib
*   **Excel:** openpyxl
*   **PDF:** ReportLab
*   **Empaquetado:** PyInstaller

## 📚 Documentación
*   **Ayuda en pantalla:** menú **Ayuda** o tecla **F1** (contenido en `assets/ayuda/`).
*   **Manual de usuario (PDF):** `docs/Manual_de_Usuario_ItalosManager.pdf`, generado desde la ayuda en pantalla con `python generar_manual.py`.
*   **Guías técnicas:** carpeta `docs/` (ventas, inventario, presupuestos, consolidados, costo de platos, mantenimiento de la ayuda y versiones).

---
Desarrollado para optimizar la eficiencia operativa de **Italos Manager**.

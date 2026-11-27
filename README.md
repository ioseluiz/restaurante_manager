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
*   **Recetas (Fichas):** consulta de la receta de cada plato (por porción o por tanda, sub-recetas y lo que descuenta del inventario por plato); se editan en Costo de Platos.
*   **Costo de Platos:** costo de producir cada plato (ingredientes, acompañamientos, bebida, empaque e indirectos), recetas por tanda, sub-recetas, precio sugerido por canal e **importación de recetas** desde una plantilla estándar (con convertidor de las fichas del cliente, modos «solo nuevas» / «actualizar», insumos por código o nombre y reporte de insumos faltantes importable) o desde el Excel de costeo del cliente. Los insumos tienen **código** propio y **gramos por ml** para convertir recetas medidas en volumen.
*   **Análisis de Precios:** evolución de los precios de compra de los insumos.

### 📈 Ventas, presupuestos y finanzas
*   **Ventas:** carga de reportes del POS (**CSV**), historial y registro de ventas diarias por plato, que descuenta los insumos del inventario.
*   **Presupuestos:** proyección de compras mensuales a partir de los reportes de ventas y las recetas, bloques de **planilla** y **gastos fijos**, y control de ejecución (presupuestado vs. real).
*   **Consolidados:** Diario de Ventas (cierre diario), Chequera, Tarjetas de Crédito, Pagos en Efectivo (con desglose por categoría), Pagos con Yappy y Resumen General mensual.
*   **Rentabilidad:** estado de resultados mensual y anual (ventas, costo de ventas real y teórico, gastos y utilidad).
*   **Panel de Control:** resumen del negocio (valor del inventario, ventas y utilidad del mes), con navegación a meses anteriores.

### 👥 Personal
*   **Planilla:** empleados, períodos de pago con horas y recargos, vales, resumen con reglas de Panamá (seguro social, seguro educativo, riesgo profesional, ISR) y provisiones laborales. Su costo completo es el que usan los presupuestos y el costo de platos.

### 🔐 Seguridad, configuración y ayuda
*   **Usuarios:** roles `admin` (todo), `gerente` (todo menos usuarios y configuración de la base de datos) y `empleado` (solo la operación diaria: sin Panel, Presupuestos, Consolidados, Rentabilidad, Costo de Platos, Análisis de Precios, Planilla ni Sucursales). Contraseñas cifradas con sal (PBKDF2).
*   **Configurar BD** (administrador): cambiar la base de datos en uso y crear copias de respaldo.
*   **Varios restaurantes:** cada instalación usa su propia base de datos, y la identidad del restaurante (nombre, sucursal de esta instalación, logo propio opcional, RUC, dirección y teléfono) se guarda **dentro de la base**. La interfaz la muestra en el título, el menú lateral, la barra de estado, el login y los encabezados de reportes. El login y el menú **Restaurante** permiten cambiar entre los restaurantes recientes del equipo (guardados en `config.json`); cambiar de restaurante cierra la sesión porque los usuarios son de cada base. Una base sin nombre muestra «Italos» y, al entrar un administrador, se abre un asistente para configurarla.
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

## 📥 Instalar la aplicación (usuarios)

Los instaladores están en la página de **Releases** del repositorio (la versión de desarrollo, en `latest-dev`):

*   **Windows:** `ItalosManager_Setup.exe` → ejecutarlo y seguir el asistente.
*   **macOS (Apple Silicon, M1 o posterior; macOS 11 o superior):** `ItalosManager_mac_arm64.dmg` → abrirlo y arrastrar **Italos Manager** a **Aplicaciones**.
    *   **Primera apertura:** la app todavía **no está firmada por Apple**, así que macOS la bloquea la primera vez. Abra *Aplicaciones*, haga **clic derecho (o Control + clic) sobre Italos Manager → Abrir** y confirme con **Abrir**. Si macOS solo ofrece «Trasladar a la papelera», vaya a **Ajustes del Sistema → Privacidad y seguridad** y pulse **Abrir igualmente** junto al aviso de Italos Manager. Solo hace falta la primera vez.
    *   Alternativa desde Terminal: `xattr -dr com.apple.quarantine "/Applications/Italos Manager.app"`.
    *   La base y la configuración quedan en `~/.restaurante_manager` (carpeta oculta de su usuario), igual que en Windows.

## 🚀 Instalación y Configuración (desarrollo)

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

## 📦 Compilar los instaladores

*   **Windows:** `pyinstaller main.spec` y luego Inno Setup con `installer.iss` (lo hace el CI).
*   **macOS (en una Mac con Apple Silicon):** `pip install -r requirements-build.txt` y `./compilar_mac.sh` → `dist/Italos Manager.app` e `installer_output/ItalosManager_mac_arm64.dmg`.
*   Ambos usan el mismo `main.spec`. El ícono de macOS (`assets/icons/app.icns`) se genera desde `app.ico` con `python scripts/generar_icns.py`.
*   `python main.py --smoke` (o el ejecutable con `--smoke`) abre todos los módulos sobre una base temporal y termina con código 0 si todo carga: el CI lo usa para comprobar el ejecutable empaquetado.
*   Lo propio de cada sistema operativo (abrir archivos, recursos, apariencia) está en `app/utils/plataforma.py`.

## 🩺 Solución de problemas

**El programa no abre por la base de datos.** La ubicación de la base se guarda en `~/.restaurante_manager/config.json`. Si apunta a un archivo inválido, el programa lo detecta, explica el motivo y permite elegir otra base o usar la predeterminada. Un caso típico es seleccionar un archivo `._nombre.db`: son residuos de macOS, no bases de datos. Detalles en la ayuda (F1 → Primeros pasos). Para corregirlo a mano, edite o borre `config.json`.

## 🏷️ Versiones

La versión aparece en el título de la ventana, en la barra de estado y en **Ayuda → Acerca de**. Vive en `app/version.py`; el CI la reemplaza con la del tag al compilar. Un tag con sufijo (`v1.3.0-beta.1`) publica el instalador como **pre-release** y uno sin sufijo (`v1.3.0`) como release oficial. Detalles en `docs/versiones.md`.

## 🧪 Pruebas

```bash
pip install pytest
python -m pytest tests
```

Ejecútelas con el Python del entorno virtual (el que tiene PyQt5); sin PyQt5, las pruebas de los diálogos se omiten.
`tests/e2e/` recorre el flujo completo (compra → inventario → ventas → costeo → presupuesto → rentabilidad) sobre un
escenario con resultados calculados a mano. Las marcadas `xfail` son hallazgos pendientes (`docs/revision_hallazgos.md`).
Para probar a mano en la app: `python scripts/crear_bd_prueba.py C:/temp/prueba_e2e.db` y seguir `docs/pruebas_manual_ui.md`.

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
*   **Cálculos y revisión:** `docs/calculos.md` (cada fórmula con un ejemplo resuelto), `docs/revision_hallazgos.md` (hallazgos de la revisión end-to-end y conciliación con los Excel del cliente) y `docs/pruebas_manual_ui.md` (checklist manual).

---
Desarrollado para optimizar la eficiencia operativa de **Italos Manager**.

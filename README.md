# Restaurante Manager 🍽️

**Restaurante Manager** es una aplicación de escritorio desarrollada en Python diseñada para optimizar la gestión operativa de un restaurante. Permite administrar inventarios, recetas, costos, menús y analizar reportes de ventas, todo integrado en una interfaz gráfica intuitiva.

## 📋 Características Principales

El sistema cuenta con los siguientes módulos:

* **🔐 Autenticación:** Sistema de login seguro para usuarios (Administradores y Empleados).
* **📦 Gestión de Insumos:** Control de stock, costos unitarios, unidades de medida y conversiones.
* **🍲 Recetas y Menú:** Creación de platos y definición de recetas (escandallo) para calcular costos precisos.
* **📊 Reportes de Ventas:** Importación y análisis de reportes de ventas (soporte para CSV/Excel).
* **🛒 Compras:** Gestión de presentaciones de compra y proveedores.

## 🗂️ Estructura del Proyecto

El proyecto sigue una arquitectura organizada separando la lógica de negocio (controladores), la interfaz (vistas) y los datos.

```text
restaurante_manager/
├── app/
│   ├── controllers/       # Lógica de negocio y autenticación
│   ├── database/          # Conexión a SQLite y creación de tablas
│   ├── views/             # Interfaz gráfica (Ventanas y Widgets)
│   │   ├── modulos/       # Módulos específicos (CRUDs, Reportes, etc.)
│   │   ├── main_window.py # Ventana principal
│   │   └── login_window.py# Ventana de acceso
│   └── styles.py          # Estilos visuales de la aplicación
├── assets/                # Iconos y archivos de datos (Excel/CSV)
├── data/                  # Base de datos SQLite (generada automáticamente)
├── diagrama_ER.svg        # Diagrama Entidad-Relación de la BDD
├── main.py                # Punto de entrada de la aplicación
├── requirements.txt       # Dependencias del proyecto
└── README.md              # Documentación del proyecto


```
## 🗃️ Modelo de Base de Datos
El sistema utiliza SQLite como motor de base de datos. A continuación se presenta el Diagrama Entidad-Relación (ER) que describe las tablas y sus relaciones:

![Diagrama ER de la Base de Datos](./diagrama_ER.svg)

Nota: El diagrama muestra las relaciones clave entre Insumos, Recetas, Menús y las tablas de conversiones de unidades.

## 🚀 Instalación y Requisitos
Para ejecutar este proyecto en tu máquina local, sigue estos pasos:

1. Prerrequisitos
Asegúrate de tener instalado Python 3.8 o superior.

2. Clonar el repositorio
Descarga el código fuente o clona el repositorio:

```
Bash

git clone <URL_DE_TU_REPOSITORIO>
cd restaurante_manager
```
3. Crear un entorno virtual (Recomendado)
```
Bash

### En Windows
python -m venv venv
venv\Scripts\activate

### En macOS/Linux
python3 -m venv venv
source venv/bin/activate
```
4. Instalar dependencias
Instala las librerías necesarias listadas en requirements.txt:

```Bash

pip install -r requirements.txt
```
💻 Ejecución
Para iniciar la aplicación, ejecuta el archivo principal desde la raíz del proyecto:

```Bash

python main.py
```
Al iniciar por primera vez:

Se creará automáticamente la carpeta data/ y la base de datos restaurante.db.

Se creará un usuario administrador por defecto (si así está configurado):

Usuario: admin

Contraseña: admin123 (Se recomienda cambiarla en producción)

## 🛠️ Tecnologías Utilizadas
Lenguaje: Python 3

Interfaz Gráfica (GUI): PyQt5

Base de Datos: SQLite

Manipulación de Datos: Pandas

Desarrollado para la gestión eficiente de restaurantes.
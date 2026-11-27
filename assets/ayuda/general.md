# Primeros pasos y navegación

Esta ayuda explica **cómo usar cada módulo** y **qué debe estar listo antes**. Puede consultarla en cualquier momento:

- **F1**: abre la ayuda del módulo que tiene a la vista.
- **Ctrl + F1** o menú **Ayuda → Índice de ayuda**: abre esta guía con la lista de módulos.
- El **buscador** de la izquierda encuentra palabras en todos los temas (no distingue tildes).
- **Ayuda → Acerca de Italos Manager…** muestra la **versión** de la aplicación y la base de datos en uso. La versión también aparece en el título de la ventana y en la barra de estado (abajo a la derecha); indíquela cuando reporte un problema.

La ventana de ayuda puede quedar abierta mientras trabaja.

## Cómo se organiza el programa

El **menú lateral** da acceso a los módulos. El botón de la parte superior del menú lo contrae para ganar espacio. En pantallas pequeñas (laptops o Windows con escala alta) el menú lateral y el contenido de cada módulo se desplazan con la rueda del mouse o la barra de desplazamiento, y la ventana abre maximizada. Cada módulo se abre en el área principal; muchos tienen **pestañas** con pasos numerados.

Los módulos están conectados: lo que registra en uno alimenta a otros. Por eso conviene cargar los datos en orden.

## En Mac

El programa funciona igual en macOS. Diferencias:

- Los atajos con **Ctrl** se usan con **Cmd** (por ejemplo **Cmd + F1** para el índice de ayuda). Para **F1** puede hacer falta mantener **fn**.
- **Acerca de Italos Manager** está en el menú con el nombre de la aplicación (arriba a la izquierda).
- La base de datos y la configuración quedan en la carpeta oculta `.restaurante_manager` de su usuario. En el Finder, **Cmd + Mayús + .** muestra las carpetas ocultas.
- La primera vez que se abre, macOS puede bloquearla porque aún no está firmada por Apple: **clic derecho sobre Italos Manager → Abrir**.

## Varios restaurantes

Cada restaurante (o sucursal) tiene **su propia base de datos** con sus propios usuarios. El nombre del restaurante abierto se ve siempre en el título de la ventana, debajo del logo del menú lateral y en la barra de estado.

- **Al iniciar sesión**, la lista **Restaurante** muestra los restaurantes abiertos antes en este equipo. Elija uno (o **Abrir otra base de datos…**) y luego ingrese con un usuario **de ese** restaurante.
- **Con la sesión abierta**, use el menú **Restaurante → Cambiar de restaurante**: se cierra la sesión y vuelve al inicio de sesión del restaurante elegido.
- El nombre, la sucursal y el logo se configuran en **[Sucursales](ayuda:sucursales) → Datos del restaurante…** (administrador).

## Puesta en marcha recomendada

1. **[Unidades de Medida](ayuda:unidades)**: g, kg, lb, ml, l, unidad…
2. **[Sucursales](ayuda:sucursales)**: nombre y logo del restaurante y la sucursal de esta instalación (cada sucursal usa su propio programa e inventario), y **[Usuarios](ayuda:usuarios)**.
3. **[Catálogo de Insumos](ayuda:insumos)**: categorías, insumos y sus presentaciones de compra con precio.
4. **[Menú](ayuda:menu)**: platos y precios de venta (con el mismo código que usa el POS).
5. **[Recetas](ayuda:recetas)**: qué insumos lleva cada plato.
6. **[Compras](ayuda:compras)**: proveedores y compras; al recibirlas suben el stock y se actualiza el costo.
7. **[Toma de Inventario](ayuda:conteo)** inicial para partir de existencias reales.
8. **[Ventas](ayuda:ventas)**: reportes del POS y ventas diarias (al actualizar el inventario descuentan los insumos según las recetas).
9. **[Consolidados](ayuda:consolidados)**, **[Planilla](ayuda:planilla)** y **[Presupuestos](ayuda:presupuestos)**.
10. Análisis: **[Rentabilidad](ayuda:rentabilidad)**, **[Costo de Platos](ayuda:costo_platos)** y **[Análisis de Precios](ayuda:grafico_precios)**.

## Consejos generales

- Los botones **Nuevo / Editar / Eliminar** de cada módulo actúan sobre la fila seleccionada; seleccione primero.
- Las tablas se pueden **ordenar** haciendo clic en el encabezado de una columna.
- Antes de cambios grandes (importaciones, borrados masivos) haga una **copia de seguridad** de la base de datos.
- El módulo **Usuarios** y la configuración de la base de datos solo aparecen para el rol administrador.
- **Cerrar sesión** está al final del menú lateral.

Si un dato no aparece donde lo espera, revise la sección **«Antes de empezar»** del módulo correspondiente: casi siempre falta cargar algo previo.

## Si el programa no abre por la base de datos

Si al iniciar aparece **«No se pudo abrir la base de datos»**, el programa no encontró o no pudo leer el archivo configurado. El mensaje explica el motivo y ofrece:

- **Elegir otra base de datos…**: seleccione el archivo `.db` con sus datos (por ejemplo `restaurante.db`).
- **Usar la predeterminada**: abre (o crea, vacía) la base en la carpeta `.restaurante_manager` de su usuario. **Sus datos no se borran**: la base anterior sigue en su carpeta y puede volver a elegirla.
- **Salir**.

Causas frecuentes:
- Se seleccionó un archivo que **empieza con «._»** (por ejemplo `._restaurante.db`). Son archivos residuales que macOS crea al copiar a otro disco: **no son bases de datos**. Elija el que tiene el mismo nombre **sin** el «._».
- El archivo o la carpeta se movió, se borró o está en un disco que no está conectado.
- El archivo está dañado: restaure una copia de respaldo.

Desde **Configurar BD** (administrador) el cambio de base también se valida antes de guardarse: si el archivo elegido no sirve, se avisa y **se sigue usando la base anterior**. Haga **copias de respaldo** con «Crear Respaldo (Copia)» antes de mover o cambiar bases.

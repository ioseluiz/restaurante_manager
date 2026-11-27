# Sucursales

Registro de los **locales** o puntos de operación del restaurante. Se usan para asignar empleados en [Planilla](ayuda:planilla) y para los traslados de [Abastecimiento interno](ayuda:compras).

> **Importante:** cada sucursal tiene el programa instalado por separado y lleva su propio inventario. En cada instalación, marque la casilla **«Es la sucursal de ESTA instalación»** en la sucursal donde se usa ese programa (solo una puede estar marcada). Con eso el sistema sabe si un abastecimiento interno **envía** (baja el stock) o **recibe** (sube el stock) en esa instalación. Sin esa marca no se pueden registrar abastecimientos.

## Este restaurante

El recuadro superior muestra **qué restaurante es esta base de datos**: nombre, sucursal de esta instalación, logo y, si los tiene, RUC, dirección y teléfono. Ese nombre aparece en el título de la ventana, en el menú lateral (debajo del logo), en la barra de estado, en el inicio de sesión y en el encabezado de los reportes (toma de inventario, planilla). Así siempre sabe qué restaurante está viendo.

- **Datos del restaurante…** (solo administrador; también en el menú **Restaurante**): cambie el nombre, elija o escriba la sucursal de esta instalación, cargue un **logo propio** (PNG o JPG; se reduce automáticamente) o vuelva al de Italos con **Usar el de Italos**. El gerente ve los datos pero no puede cambiarlos.
- Los datos se guardan **dentro de la base de datos**: si copia la base a otro equipo, el nombre y el logo viajan con ella.
- Una base sin nombre configurado muestra «Italos». La primera vez que un administrador entra a una base así, el programa le pide estos datos (puede elegir **Más tarde**).

## Tareas

| Quiero… | Cómo |
|---|---|
| Agregar una sucursal | **+ Nueva Sucursal** → complete los datos → **Guardar** (o **Cancelar**) |
| Modificar una sucursal | Seleccione la fila → **Editar** |
| Quitar una sucursal | Seleccione la fila → **Eliminar** |
| Cambiar el nombre o el logo del restaurante | **Datos del restaurante…** → **Guardar** |

## Consejos

- Si trabaja con un solo local, con una sucursal es suficiente (márquela como la de esta instalación si usa abastecimientos).
- Cada instalación marca **su propia** sucursal; no marque la de otra instalación.
- Antes de eliminar una sucursal, verifique que no tenga empleados ni abastecimientos asociados.

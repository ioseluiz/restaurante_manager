# Ventas

Reúne **toda la información de lo que se vende**. Tiene tres pestañas y dos tipos de datos distintos:

| Pestaña | Para qué sirve |
|---|---|
| **Cargar Nuevo Reporte** | Importar el reporte periódico del POS (archivo CSV) |
| **Historial y Consultas** | Ver y gestionar los reportes ya cargados |
| **Registro Ventas Diarias** | Anotar a mano cuántas unidades de cada plato se vendieron en un día |

> **Diferencia clave:** los *reportes del POS* sirven para **planificar compras y presupuestos** (promedios por día de la semana). Las *ventas diarias* registran lo **realmente vendido** cada día y alimentan el costo teórico de [Rentabilidad](ayuda:rentabilidad).

## Antes de empezar

- El **[Menú](ayuda:menu)** debe tener cada producto con el **mismo código** que usa el POS.
- Las **[Recetas](ayuda:recetas)** de los platos deben estar definidas.

## Cargar un reporte del POS

1. Pulse **Seleccionar Archivo CSV…** y elija el archivo exportado del POS.
2. Revise la vista previa: el sistema detecta el **período**, el **% sugerido** y el número de **registros**.
3. Las filas en **rojo claro** son productos cuyo código **no existe en el Menú**. Puede guardar igual, pero esas líneas no se tendrán en cuenta en los presupuestos. Para corregirlo, cree ese código en [Menú](ayuda:menu) y vuelva a cargar el archivo.
4. Pulse **Guardar en Base de Datos** y confirme.

## Historial y Consultas

Lista los reportes guardados (período, total, % sugerido, fecha de carga). Al seleccionar uno se ve su detalle línea por línea.

**Eliminar Reporte Seleccionado** borra el reporte y su detalle. No elimine reportes usados como base de un [presupuesto](ayuda:presupuestos): ese presupuesto ya no podría recalcularse bien.

## Registro de Ventas Diarias

1. Elija la **fecha**.
2. Escriba la cantidad vendida de cada plato del menú (los que no vendió quedan en 0).
3. Pulse **Guardar Cantidades**. El día queda en **BORRADOR**.
4. Pulse **Actualizar Inventario (Kardex)** para **descontar del stock los insumos** consumidos: el sistema usa la receta de cada plato (con recetas por tanda y sub-recetas) × las unidades vendidas y registra un movimiento `VENTA` por insumo en el Kardex. El día queda **INVENTARIO ACTUALIZADO** y bloqueado.

Al terminar, el sistema avisa qué **platos no tenían receta** (no descuentan nada) y qué **insumos quedaron en negativo**.

**¿Se equivocó en las cantidades?** Pulse **Reabrir Día (Revertir Inventario)**: repone al stock exactamente lo descontado y deja el día editable. Corrija, guarde y vuelva a actualizar el inventario.

Las cantidades de cada día también las usan [Rentabilidad](ayuda:rentabilidad) (costo teórico) y el promedio de platos vendidos de [Costo de Platos](ayuda:costo_platos).

> **Días antiguos:** antes el botón solo marcaba el día («Simulación») y no descontaba nada. Esos días figuran como actualizados pero sin movimientos; para descontarlos use **Reabrir Día** (solo quita la marca) y luego **Actualizar Inventario (Kardex)**.

## Errores frecuentes

- **«Código no existe» (fila roja):** falta el producto en el Menú, o el código está escrito distinto.
- **Presupuesto sin ventas:** no hay reportes del POS cargados para ese período.
- **Botón «Actualizar Inventario» deshabilitado:** el día es nuevo (guárdelo primero) o ya está actualizado (use «Reabrir Día»). Si hay cantidades sin guardar, el sistema pide guardarlas antes.
- **«Platos vendidos SIN receta»:** cree la receta del plato en [Recetas](ayuda:recetas), reabra el día y vuelva a actualizar.

# Presupuestos

Un presupuesto mensual tiene **tres bloques separados** (las recetas por tanda y las sub-recetas de [Costo de Platos](ayuda:costo_platos) se tienen en cuenta en el cálculo de compras):

- **Compras**: cuánto comprar (insumos y monto), calculado desde las ventas y las recetas.
- **Planilla**: costo laboral completo del personal (salario bruto + carga patronal + provisiones), igual que el Resumen de Planilla.
- **Gastos fijos**: alquiler, luz, agua, etc.

Después se compara lo presupuestado con lo **realmente ejecutado**.

## Antes de empezar

Para que el bloque de compras salga completo debe existir:

1. **Insumos** con sus **presentaciones de compra y precio** ([Catálogo](ayuda:insumos)).
2. **Menú** y **Recetas** de los platos ([Menú](ayuda:menu), [Recetas](ayuda:recetas)).
3. **Reportes de ventas del POS** cargados ([Ventas](ayuda:ventas)): son la base de la proyección.

Para el bloque de planilla, [Planilla](ayuda:planilla) con sus períodos.

## Generar el presupuesto

1. Cree un presupuesto: número, mes, año y descripción.
2. Seleccione los **reportes de ventas base** (uno o varios períodos).
3. Pulse calcular. El sistema proyecta las ventas por producto, multiplica por la receta, aplica el **% sugerido** del reporte como margen de seguridad y lo convierte a **unidades de compra** con su costo.

En el resultado, cada fila es un insumo con la cantidad a comprar y el monto estimado. Puede abrir el **detalle de cálculo** de un insumo para ver cómo se obtuvo.

## Ajustar

- Cambiar el **porcentaje** de un insumo (más margen o menos).
- Editar a mano **cantidad y monto**.
- **Agregar** insumos que no están en recetas (limpieza, desechables).
- **Eliminar** una línea.
- **Recalcular** con los precios y recetas actuales si cambiaron.

## Planilla y gastos fijos

Cada bloque se edita por separado. La planilla puede basarse en los meses anteriores; los gastos fijos se eligen de un catálogo reutilizable y recuerdan el historial.

## Control de ejecución

Vincule las [compras](ayuda:compras) reales al presupuesto para ver **presupuestado vs. ejecutado**. Los gastos fijos y la planilla ejecutados salen de [Consolidados](ayuda:consolidados) (según el «tipo de gasto» de cada pago) y de [Planilla](ayuda:planilla).

## Problemas frecuentes

- **Presupuesto en cero:** no hay reportes de ventas cargados o los productos no tienen receta.
- **Insumo con monto 0:** le falta presentación o precio.
- **Ventas no consideradas:** el código del POS no existe en el [Menú](ayuda:menu).

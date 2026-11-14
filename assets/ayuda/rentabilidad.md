# Rentabilidad

Estado de resultados (P&L) del negocio: **Ventas − Costo de ventas − Gastos = Utilidad neta**. Elija **mes y año** arriba a la derecha (**Mes Actual** vuelve al mes en curso). Tiene tres pestañas:

1. **Estado de Resultados**: el P&L del mes con el **% sobre ventas** de cada línea, tarjetas de resumen, y la variación **vs. el mes anterior** y **vs. el año anterior**. Se puede exportar a CSV.
2. **Desglose de Gastos**: los gastos del mes por categoría (tabla y gráfico) y las compras por categoría de insumo (solo como referencia, no se suman).
3. **Comparativo Anual**: los 12 meses en columnas, con gráfico de la utilidad neta.

## De dónde salen los números

| Concepto | Fuente |
|---|---|
| **Ventas** | Diario de Ventas ([Consolidados](ayuda:consolidados)) |
| **Costo real de ventas** | Pagos en efectivo de víveres, carnes y desayunos ([Consolidados](ayuda:consolidados)) |
| **Costo teórico** | Ventas por plato × costo de los **ingredientes** del plato, calculado igual que en [Costo de Platos](ayuda:costo_platos) (misma fuente de costo de Parámetros, sub-recetas y tandas). Usa las ventas diarias de [Ventas](ayuda:ventas); si no hay, el costo del reporte del POS |
| *Ref.: teórico con extras del plato* | Referencia en gris: suma además acompañamientos y bebida de cada plato, como la pantalla de Costo de Platos. Si la caja también los registra como líneas propias, se cuentan dos veces; por eso la merma usa el teórico sin extras |
| **Gastos** | Pagos por categoría: planilla, honorarios, mantenimiento… |

## Cómo interpretarlo

Comparar el **costo real** con el **teórico** indica la **merma**: si el real es mucho mayor, se está gastando más de lo que las recetas justifican (desperdicio, porciones excesivas, faltantes o recetas desactualizadas).

## Antes de empezar

- Registre el **Diario de Ventas** y los **pagos** del mes en Consolidados.
- Para el costo teórico necesita [recetas](ayuda:recetas), insumos con costo y **ventas diarias** por plato.

## Problemas frecuentes

- **Ventas en cero:** falta el Diario de Ventas de ese mes.
- **Costo teórico vacío o muy bajo:** platos sin receta o insumos sin costo.
- **Gastos que no aparecen:** el pago no tiene categoría o tipo de gasto.

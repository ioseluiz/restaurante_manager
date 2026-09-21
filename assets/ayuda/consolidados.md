# Consolidados

Concentra **por dónde entra y sale el dinero**: cheques, tarjetas, efectivo, Yappy y el cierre diario de ventas. Tiene seis pestañas:

| Pestaña | Qué registra |
|---|---|
| **Resumen General** | Vista global de ingresos y egresos por mes; se puede exportar |
| **Chequera** | Cheques emitidos |
| **Tarjetas de Crédito** | Compras y pagos por cada tarjeta (con balance mensual) |
| **Pagos en Efectivo** | Gastos pagados en efectivo, con desglose por categoría |
| **Pagos con Yappy** | Transacciones por cuenta Yappy |
| **Diario de Ventas** | Cierre de cada día: ventas por método de pago, sobrante (suma) y faltante (resta) de caja, y depósitos |

## Por qué es importante

Alimenta a otros módulos:

- El **Diario de Ventas** es la fuente de las ventas en el [Panel de Control](ayuda:dashboard) y en [Rentabilidad](ayuda:rentabilidad). Su **TOTAL VENTAS** se calcula solo (suma Yappy, Pedidos Ya, Clave, Visa/MC, efectivo, vale y sobrante, y **resta el faltante**) y no se edita.
- Los pagos con **tipo de gasto** (alquiler, luz, gas…) son el «ejecutado» de los [Presupuestos](ayuda:presupuestos) y los gastos indirectos de [Costo de Platos](ayuda:costo_platos).

**Consejo:** elija siempre el *tipo de gasto* correcto al registrar un pago; de eso depende que el gasto llegue al lugar correcto.

## Rutina recomendada

**Al cierre de cada día:** registre el **Diario de Ventas** (total, Yappy, PedidosYa, Clave, Visa/Mastercard, vales, depósitos, efectivo…). Las comisiones de cada método se configuran una vez desde esa pestaña.

**Al pagar algo:** regístrelo en la pestaña del medio de pago usado (cheque, tarjeta, efectivo o Yappy), con fecha, monto y, si corresponde, el **tipo de gasto**.

**Al cerrar el mes:** revise el **Resumen General** y los resúmenes mensuales de cada pestaña.

## Tarjetas y cuentas Yappy

Primero cree la **tarjeta** o **cuenta Yappy** y selecciónela como activa; luego registre sus transacciones (las tarjetas distinguen compras y pagos, y muestran el balance mensual).

## Pagos en efectivo

Cada pago se **desglosa por categorías** (víveres, carnes, desayunos, planilla, honorarios, mantenimiento, etc.) y **la suma del desglose debe ser igual al total del pago**: si no cuadra, el sistema no deja guardar. Estas categorías alimentan el costo real de ventas en [Rentabilidad](ayuda:rentabilidad). El tipo de gasto se elige por línea del desglose.

## Filtros y exportar

Las listas se pueden filtrar por columna. Todas las pestañas tienen **Exportar CSV**, que pide el mes (o «Todos»). El **Resumen General** incluye además dos gráficos del mes elegido (ventas por método de cobro y gastos por método de pago).

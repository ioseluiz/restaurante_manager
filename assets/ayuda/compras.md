# Compras

Registra lo que se le compra a los proveedores. **Al recibir una compra sube el stock** de los insumos y se **actualiza su costo** (promedio ponderado). Tiene cinco pestañas:

1. **Registro de Compras**: pedidos y compras.
2. **Proveedores**: catálogo de proveedores.
3. **Resumen Semanal** y 4. **Resumen Mensual**: cuánto se compró, por período.
5. **Abastecimiento Interno**: traslados de insumos entre sucursales.

## Antes de empezar

- Los insumos deben tener al menos una **presentación de compra** (ej. «Caja 12 latas») en el [Catálogo de Insumos](ayuda:insumos). Las compras se registran por presentación.
- Cree el **proveedor** en la pestaña 2.

## Registrar una compra

1. Pulse **Nueva Compra / Pedido**.
2. Elija proveedor y fecha, y agregue las líneas (presentación, cantidad, precio).
3. Pulse **Guardar Compra**. Queda como **PENDIENTE**: aún no afecta el stock.

## Recibir la mercancía

1. Seleccione la compra y pulse **Marcar como RECIBIDO (Sumar a Stock)**.
2. Indique lo realmente recibido de cada línea. **Recibido = Pedido** copia lo pedido en todas las líneas.
3. Pulse **Aplicar Recepción y Sumar a Stock**.

Solo lo recibido suma al inventario y actualiza el costo del insumo. Puede ver el resultado en [Inventario](ayuda:inventario).

## Editar o corregir

- **Ver Detalle** muestra las líneas de una compra.
- Mientras arma una compra, **Editar Línea Seleccionada** y **Borrar Línea** corrigen las líneas ya agregadas.

## Abastecimiento interno

Use la pestaña 5 para trasladar insumos entre sucursales sin comprarlos. **Cada sucursal tiene su propio programa**, así que el traslado se registra **en las dos** y cada una aplica su lado:

- Si **esta sucursal envía**, el stock **baja**. Si **recibe**, **sube** (el costo del insumo no cambia).
- Un traslado que no involucra a esta sucursal no se puede registrar aquí.
- Si envía más de lo que hay en el sistema, avisa y le deja continuar.

**Pasos:** **+ Nuevo Abastecimiento** → elija fecha, origen y destino → **Agregar Insumo** con su cantidad → **Guardar Abastecimiento**. Con **Ver Detalle** (o doble clic) revisa los insumos de un traslado y con **Anular** lo deshace (repone el stock y lo deja como ANULADO; anúlelo también en la otra sucursal).

**Antes de empezar:** en [Sucursales](ayuda:sucursales) debe estar marcada la sucursal de esta instalación.

## Consejos

- Vincular las compras a un [presupuesto](ayuda:presupuestos) permite comparar lo presupuestado con lo ejecutado.
- Un precio mal digitado cambia el **costo promedio** del insumo al recibir la compra: afecta el valor del inventario y el costo teórico de [Rentabilidad](ayuda:rentabilidad) (y el de [Costo de Platos](ayuda:costo_platos) si allí eligió «costo promedio»). Revíselo antes de recibir.

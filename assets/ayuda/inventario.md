# Inventario

Muestra el **stock actual estimado** de cada insumo y su valor. Es un inventario *perpetuo estimado*: se calcula a partir de los movimientos registrados, no de un conteo automático.

## Cómo sube y baja el stock

| Sube por | Baja por |
|---|---|
| [Compras](ayuda:compras) marcadas como recibidas | **Ventas diarias** actualizadas con «Actualizar Inventario (Kardex)» ([Ventas](ayuda:ventas)): consumo según las recetas |
| Abastecimiento interno: esta sucursal **recibe** | Abastecimiento interno: esta sucursal **envía** |
| Ajustes por Toma de Inventario (sobrantes) | Ajustes por [Toma de Inventario](ayuda:conteo) (faltantes, mermas) |
| **Reabrir Día** de ventas o **anular** un abastecimiento (reponen lo movido) | |

> El descuento por ventas es **estimado**: usa las recetas, así que no captura mermas ni porciones distintas. Por eso conviene hacer conteos físicos periódicos.

## Qué puede hacer aquí

- Consultar el stock, la unidad y el costo de cada insumo (**Actualizar** recarga los datos).
- Seleccionar un insumo (o hacer doble clic) y pulsar **Ver Movimientos (Kardex)** para ver su historial: fecha, tipo (`COMPRA`, `VENTA`, `REVERSO_VENTA`, `TRASLADO_SALIDA`, `TRASLADO_ENTRADA`, `REVERSO_TRASLADO`, `AJUSTE_INVENTARIO`), cantidad, stock anterior y nuevo.

## Antes de empezar

- Cargue los insumos en el [Catálogo](ayuda:insumos).
- Para partir de existencias reales haga una [Toma de Inventario](ayuda:conteo) inicial (recomendado) o registre las compras históricas.

## Consejos

- Un stock **negativo** indica que hubo salidas (por ejemplo ventas) sin entradas registradas: revise compras no recibidas, el stock inicial o haga un conteo.
- Un insumo sin costo hace que el **valor del inventario** salga incompleto: se define al recibir compras o en sus presentaciones.

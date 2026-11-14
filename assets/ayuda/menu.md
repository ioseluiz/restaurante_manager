# Menú

El catálogo de **lo que se vende**: cada plato o producto con su **código**, nombre y **precio de venta**.

## Muy importante: el código

El **código** debe ser **el mismo que usa el POS**. Con él se enlazan los reportes de [Ventas](ayuda:ventas) con las [recetas](ayuda:recetas) y los presupuestos. Un código distinto o faltante deja ventas sin costear.

## Tareas

| Quiero… | Cómo |
|---|---|
| Agregar un producto | **+ Nuevo Item**: código, nombre y precio |
| Cambiar precio o nombre | Seleccione la fila → **Editar Item** |
| Quitar un producto | Seleccione la fila → **Eliminar Item** (también borra su receta) |
| Cargar muchos de una vez | **Importar CSV** |

## Importar CSV

El archivo debe tener las columnas **código, nombre y precio** (en ese orden), con o sin fila de títulos, y una cuarta columna **opcional** para marcar si es preparado (`0`, `no` o `false` = no preparado; vacía = preparado). Se **omiten** las filas con código repetido o precio inválido y al terminar se informa cuáles fueron. Guarde el CSV desde Excel como «CSV (delimitado por comas)».

## Campo «preparado»

- **Preparado**: se cocina con ingredientes → necesita [receta](ayuda:recetas).
- **No preparado**: se vende tal cual (una soda embotellada).

## Consejos

- Los **componentes** de costeo (salsas, sazonadores…) que se crean en [Costo de Platos](ayuda:costo_platos) no se venden y **no aparecen** en esta lista.
- Actualice aquí el precio cuando cambie: el margen de [Costo de Platos](ayuda:costo_platos) lo compara con el precio sugerido.

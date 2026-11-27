# Recetas (Fichas)

Muestra **qué lleva cada plato y cuánto**: la receta completa, por porción o por tanda, con sus sub-recetas, y lo que **descuenta del inventario** cada plato vendido. Esas recetas alimentan los **presupuestos de compras**, el **costo teórico** ([Rentabilidad](ayuda:rentabilidad)) y el **[costo de platos](ayuda:costo_platos)**.

> **Este módulo es de consulta.** Las recetas se crean y se modifican en un solo lugar: **[Costo de Platos](ayuda:costo_platos) → Recetas de costeo**, donde están también el rendimiento, la porción y las sub-recetas. Así no se «corrige» por error una cantidad de tanda creyendo que es por plato.

## La lista

- Filtre por **código** o **nombre**. Doble clic (o **Ver receta**) abre el detalle.
- **Tipo de receta**:
  - **Por porción**: las cantidades son las de un plato.
  - **Por tanda**: las cantidades son de la olla o tanda completa, con su rendimiento y porción servida.
  - **Usa tanda / sub-receta**: el plato se sirve de una tanda compartida (por ejemplo un plato normal y su versión *eco*) o solo de sub-recetas.
  - **Sin receta** (en rojo): el plato no descuenta inventario ni tiene costo.
- **Mostrar sub-recetas y tandas** agrega las preparaciones que no se venden solas (guisos, salsas, tandas compartidas).

## El detalle

- Arriba, el tipo de receta y, si es por tanda, cuánto rinde, la porción y cuántas porciones salen.
- **Ingredientes de la receta**: insumos y sub-recetas con la **cantidad de la receta** y la cantidad **por porción**.
- **Lo que descuenta del inventario cada plato vendido**: todos los insumos, incluidos los de las sub-recetas, ya calculados por plato.
- **Editar en Costo de Platos…** (gerente y administrador) abre el editor de la receta.

## Antes de empezar

- El plato debe existir en el [Menú](ayuda:menu) y estar marcado como **preparado**.
- Los ingredientes deben estar en el [Catálogo de Insumos](ayuda:insumos).

## Cargar muchas recetas desde Excel

Use **[Costo de Platos](ayuda:costo_platos) → Recetas de costeo → Importar recetas…** (plantilla estándar o fichas del cliente).

## Consejos

- Cuanto más completas las recetas, más exactos los presupuestos y costos. La receta es la que se usa para **descontar el stock** cuando actualiza el inventario con las [ventas diarias](ayuda:ventas); un plato sin receta no descuenta nada.
- Revise la tabla de inventario del detalle: si un plato descuenta cantidades raras (por ejemplo 900 g de arroz por plato), probablemente falta el rendimiento de la tanda.

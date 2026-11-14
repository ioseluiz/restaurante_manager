# Catálogo de Insumos

Aquí se define **todo lo que el restaurante compra y usa**: ingredientes, empaques y desechables. Es la base de Compras, Recetas, Inventario y de todos los costos. Tiene cuatro pestañas:

1. **Catálogo de Insumos**: el insumo y su **unidad base** (g, ml, unidad…).
2. **Presentaciones de Compra**: cómo se compra cada insumo y a qué precio.
3. **Categorías**: para agrupar (carnes, vegetales, empaques…).
4. **Tipos de Empaque**: caja, bolsa, lata… para describir las presentaciones.

## Antes de empezar

Cargue primero las **[Unidades de Medida](ayuda:unidades)**.

## Crear un insumo

1. Pestaña 1 → **Nuevo Insumo**.
2. Escriba el **nombre**, elija la **unidad de inventario** (unidad base) y la **categoría**. Use la unidad más pequeña con la que se mide en las recetas (por ejemplo, gramos para la carne).
3. Guarde. **Editar Seleccionado** y **Eliminar** actúan sobre la fila elegida. Si el insumo ya se usó (por ejemplo en compras), el sistema puede negarse a eliminarlo.

## Definir cómo se compra (presentación)

1. Pestaña 2 → seleccione el insumo → **Definir Presentación**.
2. Indique el **nombre del empaque** (ej. «Saco 100 lb») y el **precio de compra**.
3. Defina el **contenido**:
   - **Empaque simple:** escriba el **Contenido Neto Total** en la unidad base del insumo.
   - **Empaque compuesto** (ej. una caja con botellas): marque *Es un empaque compuesto* y complete **Unidad Interna** (de los Tipos de Empaque), **Cantidad** y **Peso/Vol Unitario**; el total se calcula solo.
4. **Guardar Definición**. El sistema calcula el **costo por unidad base** (precio ÷ contenido).

**Historial de Precios** muestra los precios anteriores; **+ Registrar Nuevo Precio** anota un cambio de precio conservando el historial. Ese historial alimenta el [Análisis de Precios](ayuda:grafico_precios).

## Códigos de barras y QR

El botón **Códigos de barras / QR…** vincula códigos al insumo o a una presentación. Detalles en [Etiquetas y Códigos](ayuda:etiquetas).

## Consejos

- El **costo** de un insumo se actualiza al **recibir compras** ([Compras](ayuda:compras)) y con las presentaciones vigentes. Sin ninguno de los dos, el insumo queda «sin costo» y sus platos salen con costo incompleto.
- Evite duplicar insumos con nombres parecidos («Aceite» y «Aceite Veg»): dificultan las recetas y la importación de datos.
- No elimine insumos que ya se usan en recetas o compras.

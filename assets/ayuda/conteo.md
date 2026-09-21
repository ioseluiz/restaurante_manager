# Toma de Inventario

Sirve para **contar físicamente** las existencias y **corregir el sistema** con la diferencia. Se trabaja por *sesiones* de conteo y tiene dos pestañas:

1. **Ingreso de Cantidades**
2. **Revisión y Aprobación**

## Flujo completo

1. **Nueva Sesión de Conteo**: elija la fecha y las **categorías a incluir** (el contador muestra cuántos insumos entran), escriba una descripción opcional y pulse **Crear y Generar Excel**.
2. Al crear la sesión se genera y abre una **hoja de Excel** para imprimir y contar en papel (botón **Crear y Generar Excel**). **Volver a Generar Excel** la regenera si la perdió.
3. Con la sesión abierta, pulse **Ingresar Conteo** y registre lo contado de cada insumo. Puede escribir la cantidad o **escanear** el código (📷 Escanear). Al terminar, **Guardar Cantidades**.
4. En **Revisión y Aprobación** compare *sistema vs. contado* y revise las diferencias.
5. Para cada diferencia que quiera corregir, escriba el **motivo** y marque **Aprobar**. Pulse **Aplicar Ajustes y Cerrar Sesión**: solo las líneas aprobadas (con diferencia distinta de cero) ajustan el stock y quedan en el Kardex.

## Antes de empezar

- Los insumos deben estar en el [Catálogo](ayuda:insumos) y clasificados por **categoría**.
- Para escanear, los insumos necesitan códigos de barras/QR ([Etiquetas y Códigos](ayuda:etiquetas)).

## Consejos

- Cuente por categorías (carnes, secos, bebidas…) para que cada sesión sea corta.
- **Ver Detalle** aparece solo en sesiones **cerradas** y muestra qué se ajustó. **Eliminar** y **Ingresar Conteo** aparecen solo en sesiones abiertas (*En proceso*); eliminar una sesión abierta no modifica el inventario.
- Una vez aplicados los ajustes, el cambio no se deshace desde este módulo: revise antes de confirmar.
- Hacer el conteo con el local cerrado evita que las compras y ventas del día lo desajusten.

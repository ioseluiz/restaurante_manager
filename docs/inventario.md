# Sistema de Inventario — Restaurante Italos

> Documento de referencia para explicar al cliente cómo funciona el control de
> inventario, qué registra el sistema automáticamente y cómo realizar la primera
> carga de existencias.

---

## 1. Concepto general: inventario perpetuo estimado

El sistema mantiene un **inventario perpetuo**: el stock de cada insumo se
actualiza automáticamente cada vez que ocurre un movimiento (compra, venta,
ajuste). No es necesario parar operaciones para saber cuánto hay en bodega; el
sistema lo calcula en tiempo real.

La palabra **"estimado"** es importante: el descuento por ventas se calcula
usando las **recetas** del menú. Si se vendieron 10 platos de pasta, el sistema
descuenta exactamente los ingredientes que dice la receta de ese plato. Si en la
práctica se usó más o menos insumo que la receta, esa diferencia no se captura
automáticamente — de ahí la necesidad de hacer conteos físicos periódicos.

---

## 2. Los bloques del sistema de inventario

### 2.1 Catálogo de Insumos

Es la base de todo. Cada insumo tiene:

| Campo | Descripción |
|---|---|
| Nombre | Identificador del insumo (ej. "Arroz") |
| Unidad base | La unidad mínima en que se mide (ej. kg, ml, unidad) |
| Categoría | Agrupación (Carnes, Viveres, Bebidas…) |
| Stock actual | Existencia actual calculada por el sistema |
| Costo unitario | Costo por unidad base, actualizado con cada compra |

Cada insumo puede tener una o varias **presentaciones de compra** (ej. Saco de
25 kg, Caja de 24 latas de 355 ml). Las presentaciones definen cuántas unidades
base contiene cada empaque y cuánto cuesta, permitiendo que el sistema calcule
el costo unitario automáticamente.

### 2.2 Recetas

Cada ítem del menú tiene una receta que lista los insumos y las cantidades
necesarias para preparar **una** porción. Esta receta es el puente entre las
ventas y el descuento de inventario.

---

## 3. Cómo sube el inventario (entradas)

### 3.1 Registro de Compras

Módulo: **Compras y Proveedores**

Al registrar una compra y marcarla como recibida:

1. El usuario selecciona el proveedor y la fecha.
2. Agrega los productos comprados (presentación de compra + cantidad).
3. El sistema calcula el subtotal y el costo unitario de cada insumo.
4. Al confirmar, el **Kardex** registra un movimiento de tipo `COMPRA` y suma
   las unidades al stock de cada insumo.

> **Resultado:** `stock_actual` sube; queda registro con stock anterior,
> stock nuevo y referencia a la compra.

### 3.2 Abastecimiento Interno

Módulo: **Abastecimiento Interno** (transferencias entre sucursales)

Cuando se transfiere un insumo de una sucursal a otra, el sistema registra la
salida de la sucursal origen y la entrada en la sucursal destino, ambas con
movimiento de tipo `TRASLADO` en el Kardex.

---

## 4. Cómo baja el inventario (salidas)

### 4.1 Descuento por ventas diarias

Módulo: **Ventas → Ventas Diarias**

El flujo es:

1. Al final del día el operador ingresa cuántas unidades de cada ítem del menú
   se vendieron.
2. Guarda el registro (queda en estado **BORRADOR**).
3. Cuando se presiona **"Actualizar Inventario (Kardex)"**, el sistema recorre
   cada producto vendido, busca su receta y descuenta los insumos
   proporcionalmente.
   - Ejemplo: se vendieron 15 Pastas Alfredo; la receta tiene 200 g de pasta,
     30 ml de crema, 10 g de queso → el sistema descuenta 3 000 g de pasta,
     450 ml de crema y 150 g de queso.
4. El día queda marcado como **procesado** y ya no se puede re-descontar.

> **Movimiento generado:** tipo `VENTA`, cantidad negativa, referencia al
> ítem del menú.

### 4.2 Ajustes manuales y mermas

No existe un módulo de mermas independiente, pero cualquier diferencia física
se corrige a través del módulo de **Toma de Inventario** (ver sección 6).

---

## 5. El Kardex

El Kardex es el **historial completo de movimientos** de cada insumo. Se accede
desde **Inventario → Monitor de Inventario** haciendo doble clic en cualquier
insumo.

Cada entrada del Kardex contiene:

| Campo | Descripción |
|---|---|
| Fecha | Cuándo ocurrió el movimiento |
| Tipo | `COMPRA`, `VENTA`, `AJUSTE_INVENTARIO`, `TRASLADO` |
| Cantidad | Positivo = entrada, Negativo = salida |
| Stock anterior | Existencia antes del movimiento |
| Stock nuevo | Existencia después del movimiento |
| Referencia | ID de la compra, ítem de menú o conteo que originó el movimiento |
| Observación | Descripción del movimiento |

El Kardex **no se edita manualmente**. Es un registro de auditoría generado
automáticamente por cada operación del sistema.

---

## 6. Monitor de Inventario

Módulo: **Inventario**

Muestra en tiempo real el stock de todos los insumos con:

- Stock actual (en rojo si es cero o negativo)
- Costo unitario
- Valor total del insumo en bodega
- Valor total del inventario completo (suma al pie)

---

## 7. Carga de inventario inicial

Cuando el sistema se usa **por primera vez**, todos los insumos parten con
`stock_actual = 0`. Es necesario cargar las existencias reales que hay en bodega
en ese momento. Hay dos formas de hacerlo:

### Opción A — Toma de Inventario (recomendada)

Es el método más limpio porque deja trazabilidad completa en el Kardex.

1. Ir a **Toma de Inventario → Nueva Sesión de Conteo**.
2. Seleccionar "Todas las categorías" y crear la sesión.
3. El sistema genera el formato PDF (con stock teórico = 0 para todos).
4. En la pestaña **"Ingreso de Cantidades"**, ingresar el stock real de cada
   insumo (contando la bodega físicamente).
5. En la pestaña **"Revisión y Aprobación"**, marcar todas las líneas como
   aprobadas (la diferencia será igual al stock real, ya que el teórico parte
   en cero).
6. Presionar **"Aplicar Ajustes y Cerrar Sesión"**.

> **Resultado:** El sistema crea un movimiento `AJUSTE_INVENTARIO` por cada
> insumo, dejando el stock correcto y el registro completo de la carga inicial
> en el Kardex.

### Opción B — Registrar las compras históricas

Si el cliente tiene facturas de las compras recientes, puede registrarlas en el
módulo de **Compras** con su fecha original. El sistema acumula el stock con
cada compra ingresada. Esta opción es útil si se quiere tener el historial de
compras completo, pero puede ser más lenta si hay muchas facturas.

### Opción C — Combinación de ambas

Registrar las compras de los últimos días (para tener el historial reciente) y
luego hacer una Toma de Inventario para corregir cualquier diferencia acumulada.

> **Nota:** La Opción A es la que recomendamos para empezar rápido. Un
> inventario físico inicial bien hecho es la mejor base para que el sistema
> refleje la realidad desde el primer día.

---

## 8. Toma de Inventario Físico

Módulo: **Toma de Inventario**

Este módulo permite reconciliar periódicamente el inventario estimado del
sistema con el inventario real contado por el personal. Se recomienda realizarlo
**mensualmente** o cuando el cliente sospeche que hay diferencias significativas.

### 8.1 ¿Por qué es necesario?

El inventario perpetuo estimado puede acumular diferencias con el tiempo por:

- Mermas y desperdicios no registrados
- Porciones servidas en cantidades distintas a la receta
- Errores de digitación en ventas
- Productos vencidos o dañados retirados sin registrar
- Robo o pérdidas

Un conteo físico periódico detecta estas diferencias y las corrige en el
Kardex.

### 8.2 Flujo completo paso a paso

```
PASO 1          PASO 2              PASO 3              PASO 4
Nueva sesión → Imprimir formato → Contar físico   → Ingresar cantidades
                   PDF              en bodega          al sistema
                                       ↓
PASO 7          PASO 6              PASO 5
Kardex         Aprobar y cerrar   Revisar
actualizado ←  ajustes         ←  diferencias
```

**Paso 1 — Crear sesión**

- Ir a **Toma de Inventario → Nueva Sesión de Conteo**.
- Seleccionar fecha, descripción opcional y categoría (o "Todas").
- Al confirmar, el sistema:
  - Registra la sesión en estado **EN_PROCESO**.
  - Toma un **snapshot del stock actual** de cada insumo (este valor queda
    guardado como "stock teórico" y no cambia aunque el sistema siga
    operando).
  - Genera y abre el formato **PDF** para imprimir.

**Paso 2 — Imprimir y entregar el formato**

El PDF contiene:

| Columna | Contenido |
|---|---|
| # | Número de línea |
| Descripción del insumo | Nombre del insumo |
| Unidad base | Unidad mínima (kg, ml, unidad…) |
| Presentaciones disponibles | Empaques de compra en que se puede contar (ej. Saco 25 kg, Caja 24 latas) |
| Cant. Física | En blanco — el empleado llena con el conteo |
| Unidad usada | En blanco — el empleado anota qué unidad usó si contó por presentación |

El empleado puede contar en la **unidad base** o en cualquier **presentación de
compra** listada; simplemente anota la cantidad y la unidad que usó.

**Paso 3 — Conteo físico**

El personal cuenta el stock real en bodega y llena el formato en papel.

**Paso 4 — Ingresar cantidades al sistema**

- Abrir la sesión con **"Ingresar Conteo"**.
- En la pestaña **"1. Ingreso de Cantidades"**:
  - Por cada insumo, seleccionar en la columna **"Contar en"** la misma unidad
    que usó el empleado (unidad base o presentación de compra).
  - Ingresar la cantidad contada en la columna **"Cantidad"**.
  - La columna **"Equiv. (base)"** muestra en tiempo real la conversión a
    unidad base (ej. 3 cajas × 8 520 ml = 25 440 ml).
- Presionar **"Guardar Cantidades"**.

El sistema pasa automáticamente a la pestaña de Revisión.

**Paso 5 — Revisar diferencias**

La pestaña **"2. Revisión y Aprobación"** muestra todas las líneas con cantidad
ingresada y calcula la diferencia:

- `Diferencia = Cantidad contada − Stock teórico`
- Diferencia **en rojo** → hay menos de lo que el sistema creía (merma, pérdida
  o consumo mayor al estimado por receta).
- Diferencia **en verde** → hay más de lo que el sistema creía (compra no
  registrada, error de digitación, o diferencia de unidad).
- Diferencia **en cero** → el físico coincide con el teórico; no requiere ajuste.

**Paso 6 — Aprobar ajustes línea por línea**

Para cada diferencia que se quiera corregir:

1. Escribir el **motivo** del ajuste (ej. "Merma por caducidad", "Derrame",
   "Error de receta").
2. Marcar la casilla **"Aprobar"**.

Las líneas sin aprobar no generan ningún movimiento. Esto permite, por ejemplo,
dejar pendiente una línea para investigar antes de ajustar.

**Paso 7 — Aplicar y cerrar sesión**

Al presionar **"Aplicar Ajustes y Cerrar Sesión"**:

- El sistema crea un movimiento `AJUSTE_INVENTARIO` en el Kardex por cada línea
  aprobada, con la diferencia calculada y el motivo ingresado.
- El `stock_actual` de cada insumo afectado se corrige.
- La sesión queda en estado **CERRADO** y no puede modificarse.

Las sesiones cerradas se pueden consultar en cualquier momento desde **"Ver
Detalle"** para auditoría.

### 8.3 Gestión de sesiones

| Estado | Significado | Acciones disponibles |
|---|---|---|
| EN_PROCESO | Sesión abierta, en espera de conteo | Ingresar conteo, Eliminar |
| CERRADO | Ajustes aplicados al kardex | Ver detalle (solo lectura) |

Las sesiones **EN_PROCESO** pueden eliminarse si fueron creadas por error, sin
ningún impacto en el inventario.

---

## 9. Resumen de tipos de movimiento en el Kardex

| Tipo | Origen | Efecto en stock |
|---|---|---|
| `COMPRA` | Registro de compra recibida | Suma |
| `VENTA` | Procesamiento de ventas diarias | Resta |
| `AJUSTE_INVENTARIO` | Toma de inventario aprobada | Suma o resta según diferencia |
| `TRASLADO` | Abastecimiento interno entre sucursales | Resta en origen, suma en destino |

---

## 10. Recomendaciones operativas

1. **Registrar todas las compras el mismo día** en que se recibe la mercancía,
   para que el stock esté siempre actualizado.
2. **Procesar las ventas diarias** antes de cerrar el día — no acumular varios
   días sin actualizar el Kardex.
3. **Realizar una Toma de Inventario físico** al menos una vez al mes, o antes
   de un período de alta demanda.
4. **Mantener las recetas actualizadas**: si una receta cambia (nueva porción,
   sustitución de ingrediente), actualizar en el sistema para que los descuentos
   por ventas sean precisos.
5. **Usar el motivo del ajuste con detalle** en cada toma de inventario — estos
   registros son valiosos para identificar patrones de pérdida.

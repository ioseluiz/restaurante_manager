# Sistema de Inventario — Restaurante Italos

> Documento de referencia para explicar al cliente cómo funciona el control de
> inventario, qué registra el sistema automáticamente y cómo realizar la primera
> carga de existencias.

---

## 1. Concepto general: inventario perpetuo estimado

El sistema mantiene el stock de cada insumo a partir de los **movimientos que
se registran**: compras recibidas, **ventas diarias procesadas**, abastecimientos
internos (envíos y recepciones de esta sucursal) y ajustes por toma de inventario.
Cada sucursal tiene el programa instalado por separado y lleva **su propio
inventario**; los sistemas no están conectados entre sí.
No es necesario parar operaciones para consultar cuánto hay: el stock se ve en el
módulo Inventario.

La palabra **"estimado"** es importante: el descuento por ventas se calcula
usando las **recetas** del menú. Si se vendieron 10 platos de pasta, el sistema
descuenta exactamente los ingredientes que dice la receta de ese plato. Si en la
práctica se usó más o menos insumo que la receta (mermas, porciones distintas), esa
diferencia no se captura automáticamente — de ahí la necesidad de hacer conteos
físicos periódicos.

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
necesarias para preparar **una** porción (o una tanda, si se define rendimiento;
ver `costo_platos.md`) y puede usar **sub-recetas** (por ejemplo chimichurri).
La receta es el puente entre las ventas y el descuento de inventario, y se usa
también para calcular **presupuestos de compras, costo teórico (Rentabilidad) y
costo de platos**.

---

## 3. Cómo sube el inventario (entradas)

### 3.1 Registro de Compras

Módulo: **Compras y Proveedores**

Una compra se guarda primero como **PENDIENTE** y no afecta el stock. Al
recibirla:

1. El usuario selecciona el proveedor y la fecha, y agrega los productos
   (presentación de compra + cantidad + precio). Guarda la compra.
2. Al llegar la mercancía usa **Marcar como RECIBIDO (Sumar a Stock)**, revisa
   las cantidades realmente recibidas (**Recibido = Pedido** las iguala a lo
   pedido) y pulsa **Aplicar Recepción y Sumar a Stock**.
3. El **Kardex** registra un movimiento de tipo `COMPRA` por cada línea recibida
   y suma las unidades (cantidad × contenido de la presentación) al stock.
4. El **costo unitario** del insumo se recalcula como **costo promedio
   ponderado** (stock anterior × costo anterior + entrada × costo de entrada).

> **Resultado:** `stock_actual` sube y `costo_unitario` se actualiza; queda
> registro con stock anterior, stock nuevo y referencia a la compra.

### 3.2 Abastecimiento Interno

Módulo: **Compras y Proveedores → 5. Abastecimiento Interno** (traslados
entre sucursales)

**Cada sucursal tiene su propio programa e inventario, sin conexión entre ellos.**
Por eso un traslado se registra **en las dos instalaciones** y cada una aplica su
propio lado:

| En esta instalación… | Efecto |
|---|---|
| esta sucursal es el **origen** (envía) | el stock **baja** (`TRASLADO_SALIDA`) |
| esta sucursal es el **destino** (recibe) | el stock **sube** (`TRASLADO_ENTRADA`) |
| no es ni origen ni destino | el sistema **no lo permite**: no afectaría este inventario |

**Configuración previa:** en el módulo **Sucursales** debe estar marcada la casilla
**«Es la sucursal de ESTA instalación»** en la sucursal donde se usa el programa
(solo una puede estar marcada). Sin ella no se pueden registrar abastecimientos.

Cada abastecimiento guarda fecha, sucursal origen, sucursal destino y los insumos
con su cantidad (en la unidad base del insumo). Al guardar, todo se hace en una
sola operación: registro, movimientos del Kardex y stock.

- Si se envía **más de lo que hay** en el sistema, avisa qué insumos quedarían en
  negativo y permite continuar (suele indicar compras sin registrar).
- Al **recibir**, el **costo** del insumo no cambia (no se conoce lo que le costó a
  la otra sucursal).
- **Ver Detalle** (o doble clic) muestra los insumos de un traslado.
- **Anular** repone el stock con un movimiento `REVERSO_TRASLADO` y deja el
  registro como **ANULADO** (no se borra). También debe anularse en la otra
  sucursal.

> **Registros anteriores:** los traslados hechos con la versión previa no generaron
> movimientos en el Kardex y, si el marcador de sucursal no era el correcto, pudieron
> mover el stock al revés. Si al configurar «esta sucursal» detecta diferencias,
> corríjalas con una **Toma de Inventario**. Anular uno de esos traslados
> repone el stock según su efecto original.

---

## 4. Cómo baja el inventario (salidas)

### 4.1 Descuento por ventas diarias

Módulo: **Ventas → Registro Ventas Diarias**

El flujo es:

1. Al final del día el operador ingresa cuántas unidades de cada ítem del menú
   se vendieron y pulsa **"Guardar Cantidades"** (el día queda en **BORRADOR**).
2. Al pulsar **"Actualizar Inventario (Kardex)"**, el sistema recorre cada plato
   vendido, toma su receta y descuenta los insumos proporcionalmente.
   - Ejemplo: se vendieron 15 Pastas Alfredo; la receta tiene 200 g de pasta,
     30 ml de crema, 10 g de queso → el sistema descuenta 3 000 g de pasta,
     450 ml de crema y 150 g de queso.
   - Si la receta es **por tanda**, se descuenta la parte que corresponde a la
     porción servida; si el plato usa **sub-recetas**, también se descuentan sus
     insumos.
3. El consumo se suma **por insumo**: queda **un movimiento `VENTA` por insumo y
   por día**, con la referencia al registro del día.
4. El día queda **INVENTARIO ACTUALIZADO**: bloqueado y sin poder re-descontarse.

Al terminar, el sistema avisa qué **platos vendidos no tenían receta** (no
descontaron nada) y qué **insumos quedaron con stock negativo**.

Si se cometió un error en las cantidades del día, **"Reabrir Día"** repone el stock
descontado (movimiento `REVERSO_VENTA`) y permite corregir y volver a procesar.

> **Movimientos generados:** tipo `VENTA` (cantidad negativa) al procesar y tipo
> `REVERSO_VENTA` (cantidad positiva) al reabrir; ambos con referencia al registro
> diario.

> **Días marcados antes de esta función:** el botón antes solo marcaba el día y no
> descontaba nada. Esos días figuran como actualizados pero sin movimientos;
> «Reabrir Día» solo les quita la marca (no cambia el stock) para poder procesarlos.

### 4.2 Ajustes manuales y mermas

No existe un módulo de mermas independiente, pero cualquier diferencia física
se corrige a través del módulo de **Toma de Inventario** (ver sección 8).

---

## 5. El Kardex

El Kardex es el **historial de movimientos** de cada insumo. Se accede desde el
módulo **Inventario**, con **doble clic** sobre un insumo o seleccionándolo y
pulsando **Ver Movimientos (Kardex)**.

La ventana del Kardex muestra:

| Campo | Descripción |
|---|---|
| Fecha | Cuándo ocurrió el movimiento |
| Tipo | `COMPRA`, `VENTA`, `REVERSO_VENTA`, `TRASLADO_SALIDA`, `TRASLADO_ENTRADA`, `REVERSO_TRASLADO` o `AJUSTE_INVENTARIO` |
| Cantidad | Positivo (verde) = entrada, negativo (rojo) = salida |
| Stock anterior | Existencia antes del movimiento |
| Stock nuevo | Existencia después del movimiento |
| Observación | Descripción del movimiento (compra y presentación, o conteo y motivo) |

En la base de datos cada movimiento también guarda la **referencia** (id de la
compra, del registro de ventas del día, del abastecimiento o del conteo), aunque la ventana no la muestre.

El Kardex **no se edita manualmente**: lo generan las compras recibidas, las
ventas diarias procesadas (y su reapertura), los abastecimientos internos (y su
anulación) y los ajustes de la toma de inventario.

---

## 6. Módulo Inventario (stock actual)

Módulo: **Inventario** (título «Inventario Actual»)

Muestra el stock de todos los insumos, con un filtro por nombre y el botón
**Actualizar**. Columnas: ID, Insumo, Categoría, Unidad, **Stock Actual**,
**Costo Unit.** y **Valor Total** (stock × costo).

- El stock en **cero o negativo** se destaca en rojo sobre fondo amarillo.
- Al pie se muestra el **Valor Total Inventario** (suma de todos los insumos
  listados).

---

## 7. Carga de inventario inicial

Cuando el sistema se usa **por primera vez**, todos los insumos parten con
`stock_actual = 0`. Es necesario cargar las existencias reales que hay en bodega
en ese momento. Hay dos formas de hacerlo:

### Opción A — Toma de Inventario (recomendada)

Es el método más limpio porque deja trazabilidad completa en el Kardex.

1. Ir a **Toma de Inventario → Nueva Sesión de Conteo**.
2. Dejar marcadas todas las categorías en **"Categorías a incluir"** y pulsar
   **"Crear y Generar Excel"**.
3. El sistema genera y abre el formato **Excel** (con stock teórico = 0 para todos).
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
                  Excel             en bodega          al sistema
                                       ↓
PASO 7          PASO 6              PASO 5
Kardex         Aprobar y cerrar   Revisar
actualizado ←  ajustes         ←  diferencias
```

**Paso 1 — Crear sesión**

- Ir a **Toma de Inventario → Nueva Sesión de Conteo**.
- Seleccionar la fecha, una descripción opcional y las **categorías a incluir**
  (el contador indica cuántos insumos entran en la sesión).
- Al pulsar **"Crear y Generar Excel"**, el sistema:
  - Registra la sesión en estado **EN_PROCESO**.
  - Toma un **snapshot del stock actual** de cada insumo (este valor queda
    guardado como "stock teórico" y no cambia aunque el sistema siga
    operando).
  - Genera y abre el formato **Excel** para imprimir (también disponible
    después con **"Volver a Generar Excel"**).

**Paso 2 — Imprimir y entregar el formato**

El Excel contiene:

| Columna | Contenido |
|---|---|
| # | Número de línea |
| Descripción del Insumo | Nombre del insumo |
| Unidad Base | Unidad mínima (kg, ml, unidad…) en la que se debe anotar el conteo |
| Presentaciones Disponibles | Empaques de compra, mostrados solo como referencia (ej. Saco 25 kg, Caja 24 latas) |
| Cant. Física | En blanco — el empleado llena con el conteo, en la unidad base |

El empleado cuenta el stock y anota el total en la **unidad base** indicada para
cada insumo. La columna de presentaciones es solo referencial.

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

Las líneas sin aprobar, o con diferencia cero, no generan ningún movimiento.
Esto permite, por ejemplo, dejar pendiente una línea para investigar antes de
ajustar.

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
| EN_PROCESO | Sesión abierta, en espera de conteo | Ingresar Conteo, Eliminar |
| BORRADOR | Estado heredado de versiones anteriores | Eliminar |
| CERRADO | Ajustes aplicados al kardex | Ver Detalle (solo lectura) |

Las sesiones abiertas (**EN_PROCESO** o **BORRADOR**) pueden eliminarse si se
crearon por error: se borran los datos del conteo y el inventario no se
modifica. Una sesión **CERRADO** no ofrece la opción de eliminar.

---

## 9. Resumen de movimientos que afectan el stock

| Origen | ¿Kardex? | Tipo | Efecto en stock |
|---|---|---|---|
| Compra recibida | Sí | `COMPRA` | Suma |
| Ventas diarias procesadas | Sí | `VENTA` | Resta (un movimiento por insumo y día) |
| Reapertura de un día de ventas | Sí | `REVERSO_VENTA` | Suma (repone lo descontado) |
| Toma de inventario aprobada | Sí | `AJUSTE_INVENTARIO` | Suma o resta según la diferencia |
| Abastecimiento interno: esta sucursal envía | Sí | `TRASLADO_SALIDA` | Resta |
| Abastecimiento interno: esta sucursal recibe | Sí | `TRASLADO_ENTRADA` | Suma (el costo del insumo no cambia) |
| Anulación de un abastecimiento | Sí | `REVERSO_TRASLADO` | Repone lo que movió el traslado |

---

## 10. Recomendaciones operativas

1. **Registrar y recibir todas las compras el mismo día** en que llega la
   mercancía: solo las compras recibidas suman al stock.
2. **Registrar las ventas diarias y pulsar «Actualizar Inventario (Kardex)»**
   antes de cerrar el día — no acumular varios días sin actualizar el Kardex.
3. **Realizar una Toma de Inventario físico** al menos una vez al mes, o antes
   de un período de alta demanda.
4. **Mantener las recetas actualizadas**: si una receta cambia (nueva porción,
   sustitución de ingrediente), actualizar en el sistema para que los descuentos
   por ventas, los presupuestos y el costo de platos sean precisos. Los platos sin
   receta no descuentan nada.
5. **Usar el motivo del ajuste con detalle** en cada toma de inventario — estos
   registros son valiosos para identificar patrones de pérdida.

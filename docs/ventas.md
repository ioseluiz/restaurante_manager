# Módulo de Ventas — Restaurante Italos

> Documento de referencia: cómo está estructurado el módulo de Ventas, qué
> información necesita, qué hace cada función y qué otros módulos se ven
> afectados por su uso.

---

## 1. Visión general

El módulo **Ventas** es el punto de entrada de toda la información de lo que el
restaurante vende. Está compuesto por **tres pestañas independientes** que
cubren dos necesidades distintas:

| Pestaña | Propósito |
|---|---|
| Cargar Nuevo Reporte | Importar el reporte periódico exportado desde el POS (CSV) |
| Historial y Consultas | Ver y gestionar los reportes ya cargados en el sistema |
| Registro Ventas Diarias | Registrar manualmente las unidades vendidas de cada plato cada día |

Estas dos funcionalidades son **independientes entre sí** — no es necesario
usar una para poder usar la otra — pero ambas alimentan otros módulos del
sistema de formas distintas.

---

## 2. Información que debe existir antes de usar el módulo

### Para los Reportes del POS (pestañas 1 y 2)

- Tener el archivo **CSV exportado desde el sistema POS** del restaurante.
- Tener los **ítems del menú** cargados en el sistema con los mismos códigos
  que aparecen en el POS. Si los códigos no coinciden, esas ventas quedan
  resaltadas en rojo y no aportan al cálculo de presupuestos.

### Para el Registro Diario de Ventas (pestaña 3)

- Tener el **catálogo del menú** cargado (módulo Gestión de Menú).
- Tener las **recetas** de cada ítem del menú definidas (módulo Recetas),
  porque con ellas se descuenta el inventario y se calcula el costo teórico de lo vendido (Rentabilidad).

---

## 3. Pestaña 1 — Cargar Nuevo Reporte

### ¿Qué es un reporte del POS?

Es un archivo CSV que el sistema de punto de venta (POS) genera al final de un
período (normalmente semanal o mensual). Contiene:

- El código y descripción de cada producto vendido.
- Las cantidades vendidas **por día de la semana** (Lunes a Domingo).
- El promedio de ventas por día.
- Los montos de venta, costo y utilidad por línea.
- El rango de fechas del período (Desde / Hasta).
- El **porcentaje sugerido** del período, que representa el margen de seguridad
  acordado con la administración para absorber variaciones en el consumo real
  versus la receta.

### Pasos para cargar un reporte

**Paso 1 — Seleccionar el archivo**

Hacer clic en **"Seleccionar Archivo CSV…"** y elegir el archivo exportado
desde el POS. El sistema intentará leerlo con distintas codificaciones
(UTF-8, Latin-1, CP1252) de forma automática.

**Paso 2 — Revisar la vista previa**

El sistema muestra una tabla con todos los registros del archivo. En la parte
superior se muestran tres indicadores detectados automáticamente:

| Indicador | Qué significa |
|---|---|
| Periodo Detectado | Rango de fechas del reporte (Desde / Hasta) |
| % Sugerido | Porcentaje de margen del período leído del encabezado del CSV |
| Registros | Cantidad de líneas de venta encontradas |

Las filas marcadas en **rojo claro** indican que el código de ese producto
**no existe en el catálogo del menú** del sistema. Esto no impide guardar el
reporte, pero esas líneas no contribuirán al cálculo de presupuestos.

**Paso 3 — Corregir códigos faltantes (si aplica)**

Si hay filas en rojo, significa que el código que usa el POS para ese producto
no está registrado en el sistema. Para corregirlo:
1. Anotar el código del POS que aparece en la columna "Código".
2. Ir a **Gestión de Menú** y crear o editar el ítem con ese código exacto.
3. Volver a **Ventas → Cargar Nuevo Reporte** y cargar el mismo archivo de
   nuevo para verificar que ya no aparece en rojo.

**Paso 4 — Guardar en la base de datos**

Hacer clic en **"Guardar en Base de Datos"** y confirmar. El reporte queda
almacenado en el historial con su período y porcentaje sugerido. Una vez
guardado, el sistema limpia el formulario listo para el próximo reporte.
Para descartar la vista previa sin guardar se usa **"Limpiar / Cancelar"**.

### Qué guarda el sistema al confirmar

- Una cabecera de reporte con: fechas de período, total de ventas del período,
  porcentaje sugerido y fecha de carga.
- El detalle de cada línea: código de producto, descripción, día de la semana,
  cantidad vendida, promedio, venta, costo y utilidad.

---

## 4. Pestaña 2 — Historial y Consultas

Muestra todos los reportes que han sido guardados en el sistema. La vista está
dividida en dos secciones:

**Sección superior — Lista de reportes**

Muestra un resumen de cada reporte:

| Columna | Contenido |
|---|---|
| ID | Identificador único del reporte |
| Inicio Periodo | Fecha de inicio del período reportado |
| Fin Periodo | Fecha de fin del período reportado |
| Total Ventas ($) | Suma total de ventas del período |
| % Sugerido | Porcentaje de margen del período |
| Fecha Carga | Cuándo se importó al sistema |

Hacer clic en cualquier reporte carga su detalle en la sección inferior.

**Sección inferior — Detalle del reporte seleccionado**

Muestra línea por línea los productos vendidos en ese período, con código,
nombre, día, cantidades, ventas, costos y utilidades.

**Eliminar un reporte**

El botón **"Eliminar Reporte Seleccionado"** borra el reporte y todo su
detalle de la base de datos. Esto también elimina el vínculo con cualquier
presupuesto que lo haya usado como base.

> **Precaución:** No eliminar reportes que fueron usados como base para
> presupuestos activos, ya que el presupuesto no podría recalcularse
> correctamente.

---

## 5. Pestaña 3 — Registro de Ventas Diarias

Esta pestaña sirve para registrar **manualmente** cuántas unidades de cada
ítem del menú se vendieron en un día específico. Es la fuente de las
**cantidades realmente vendidas**: con ellas se **descuenta el inventario** de
los insumos consumidos y las usan también Rentabilidad (costo teórico), Costo
de Platos (platos vendidos del mes) y el Panel de Control (ventas por plato).

### ¿Cómo funciona?

**Seleccionar la fecha**

Usar el selector de fecha para elegir el día que se quiere registrar. El
sistema carga automáticamente todos los ítems del menú y muestra:

- Las cantidades ya guardadas si el día tiene un registro anterior.
- Ceros si es un día nuevo.

La etiqueta de **Estado** indica la situación del registro:

| Estado | Significado |
|---|---|
| NUEVO REGISTRO | No hay datos guardados para ese día aún |
| BORRADOR (Inventario Pendiente) | Se guardaron cantidades y aún no se descontó el inventario |
| INVENTARIO ACTUALIZADO (Cerrado) | El inventario ya se descontó; el día queda **bloqueado** (no se puede guardar) hasta usar «Reabrir Día» |

El botón **"Cargar Datos"** (arriba) vuelve a leer la fecha seleccionada.

**Ingresar las cantidades**

La columna **"Cantidad Vendida"** es editable. Ingresar el número de unidades
vendidas de cada ítem. Los productos que no se vendieron ese día pueden
dejarse en cero.

**Guardar Cantidades**

Hacer clic en **"Guardar Cantidades"**. El sistema:
1. Crea el registro diario si no existía, o usa el existente.
2. Borra las cantidades anteriores del día y guarda las nuevas (solo se guardan
   los productos con cantidad mayor a 0; las cantidades pueden tener decimales).
3. Un día nuevo queda en estado **BORRADOR**.

Se puede guardar y corregir las veces que sea necesario **mientras el día esté
en BORRADOR**. Un día ya actualizado no se puede guardar: hay que reabrirlo.

**Actualizar Inventario (Kardex)**

Una vez guardadas las cantidades del día, el botón **"Actualizar Inventario
(Kardex)"** (habilitado solo en un día guardado y sin cambios pendientes) pide
confirmación y, al aceptar:

1. Para cada plato vendido calcula los insumos que consume: receta × unidades
   vendidas. Respeta las **recetas por tanda** (costo por porción) y descuenta
   también los insumos de las **sub-recetas** (por ejemplo el chimichurri).
2. Suma el consumo por insumo y registra **un movimiento `VENTA` por insumo** en el
   Kardex, con referencia al registro del día, y baja el stock.
3. Marca el día como **INVENTARIO ACTUALIZADO**, bloquea la edición y deshabilita
   el botón.
4. Muestra un resumen con los **platos vendidos sin receta** (no descuentan nada) y
   los **insumos que quedaron con stock negativo** (falta registrar compras o hacer
   un conteo).

Todo se hace en una sola operación: si algo falla, no se descuenta nada.

**Reabrir Día (Revertir Inventario)**

Si se equivocó en las cantidades de un día ya actualizado, use **"Reabrir Día"**:
el sistema **repone al stock exactamente lo que se descontó** (movimiento
`REVERSO_VENTA` en el Kardex) y devuelve el día a BORRADOR. Corrija las cantidades,
guarde y vuelva a pulsar «Actualizar Inventario (Kardex)».

> **Días marcados con la versión anterior:** antes el botón solo marcaba el día
> (mostraba «Simulación») y no descontaba nada. Esos días aparecen como
> INVENTARIO ACTUALIZADO pero **no tienen movimientos**: si desea descontarlos,
> use «Reabrir Día» (solo quita la marca, sin cambiar el stock) y luego
> «Actualizar Inventario (Kardex)».

### Regla de una sola vez

Un día no se puede descontar dos veces: una vez INVENTARIO ACTUALIZADO, el botón
queda deshabilitado y las cantidades bloqueadas. Para volver a procesarlo hay que
reabrir el día, lo que repone antes el stock.

---

## 6. Módulos que dependen del módulo de Ventas

El módulo de Ventas es uno de los más importantes del sistema porque su
información alimenta directamente a otros tres módulos:

### 6.1 → Módulo de Presupuestos

**Qué necesita:** Los reportes de ventas cargados en el historial.

Los reportes del POS (pestañas 1 y 2) son la **base de cálculo** del módulo
de Presupuestos. Al generar un presupuesto, el usuario selecciona uno o varios
reportes históricos para que el sistema proyecte cuánto se venderá el próximo
mes y calcule cuánto insumo se necesita comprar.

Sin reportes cargados en Ventas, no es posible generar presupuestos automáticos.

**Dato clave que pasa:** cantidad vendida por producto y día, porcentaje
sugerido del período.

### 6.2 → Inventario (Kardex), Rentabilidad, Costo de Platos y Panel de Control

**Qué necesita:** El registro diario de ventas (pestaña 3), con las cantidades
guardadas por día.

- **Inventario (Kardex):** al pulsar «Actualizar Inventario (Kardex)» se
  descuentan los insumos consumidos (cantidades vendidas × receta, con recetas por
  tanda y sub-recetas) con movimientos `VENTA`; «Reabrir Día» los revierte con
  `REVERSO_VENTA`.
- **Rentabilidad:** costo teórico del mes = cantidades vendidas × costo de la
  receta de cada plato.
- **Costo de Platos:** el total de platos vendidos del mes reparte los gastos
  indirectos entre los platos.
- **Panel de Control:** ventas por plato.

**Dato clave que pasa:** unidades vendidas por plato y por día.

### 6.3 → Módulo de Consolidados (Diario de Ventas)

**Qué necesita:** El módulo de Consolidados tiene su propia pestaña de "Diario
de Ventas" donde se registran los montos totales diarios de ventas por método
de pago (efectivo, Yappy, tarjeta, etc.). Esta información es independiente del
registro de cantidades por producto y se captura directamente en Consolidados,
no en Ventas.

---

## 7. Diferencia clave entre los dos tipos de datos de ventas

Es importante entender la diferencia entre las dos fuentes de datos del módulo:

| Aspecto | Reporte del POS (pestañas 1-2) | Registro Diario (pestaña 3) |
|---|---|---|
| Origen del dato | Exportado automáticamente desde el POS | Ingresado manualmente por el operador |
| Frecuencia | Periódico (semanal o mensual) | Diario |
| Granularidad | Ventas por día de semana y por período | Ventas por día calendario exacto |
| Información financiera | Sí (venta, costo, utilidad) | No (solo cantidades) |
| Uso principal | Base para presupuestos | Descuento de inventario, costo teórico, rentabilidad y platos vendidos |
| Nivel de detalle | Totales y promedios del período | Unidades exactas vendidas ese día |

---

## 8. Flujo de uso recomendado

### Flujo A — Ciclo periódico (cada vez que el POS genera un reporte)

```
POS genera el reporte CSV del período
         ↓
Ventas → Cargar Nuevo Reporte
  • Seleccionar el archivo CSV
  • Revisar filas en rojo (códigos no reconocidos)
  • Corregir en Gestión de Menú si aplica
  • Guardar en Base de Datos
         ↓
El reporte queda disponible en Historial y Consultas
         ↓
Presupuestos puede usarlo como base para el siguiente mes
```

### Flujo B — Ciclo diario (cada día de operación)

```
Fin del día operativo
         ↓
Ventas → Registro Ventas Diarias
  • Seleccionar la fecha del día
  • Ingresar cantidades vendidas de cada ítem
  • Guardar Cantidades  →  Estado: BORRADOR
  • Revisar y corregir si hay errores (se puede volver a guardar)
  • Actualizar Inventario (Kardex)  →  Estado: INVENTARIO ACTUALIZADO
         ↓
El stock baja según las recetas y el día queda bloqueado.
Si hay un error: Reabrir Día → corregir → guardar → Actualizar Inventario
```

---

## 9. Errores y advertencias comunes

**Filas en rojo al cargar un CSV**
El código del producto en el POS no existe en el catálogo del menú del sistema.
Solución: ir a Gestión de Menú y crear el ítem con el código exacto del POS.

**El botón "Actualizar Inventario" no aparece habilitado**
El día debe guardarse primero con "Guardar Cantidades" para que el botón se
active. Un día nuevo no puede procesarse sin guardar antes, y si hay cantidades
modificadas sin guardar el sistema pide guardarlas primero.

**El registro de un día aparece como INVENTARIO ACTUALIZADO pero quiero corregirlo**
Use **"Reabrir Día (Revertir Inventario)"**: repone el stock que se había
descontado y deja el día editable. Después de corregir y guardar, vuelva a
pulsar «Actualizar Inventario (Kardex)».

**Al actualizar el inventario aparece «Platos vendidos SIN receta»**
Esos platos (por ejemplo una bebida de reventa) no tienen receta y por eso no
descontaron nada. Cree su receta en el módulo Recetas si quiere controlar su
stock y reabra y vuelva a procesar el día.

**Un insumo quedó con stock negativo después de actualizar**
Se vendió más de lo que el sistema tenía registrado: falta registrar o recibir
compras, o el stock inicial no se cargó. Corrija con compras o con una Toma de
Inventario.

**El % Sugerido aparece como 0% al cargar el CSV**
El archivo CSV no tiene la línea de "Sugerido" en su encabezado, o el formato
es diferente al esperado. En ese caso, el porcentaje puede ajustarse
manualmente en el módulo de Presupuestos línea por línea usando "Ajustar %".

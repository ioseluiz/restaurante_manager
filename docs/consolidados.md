# Módulo de Consolidados — Restaurante Italos

> Documento de referencia: qué registra el módulo de Consolidados, cómo
> funciona cada pestaña, qué información produce y cómo se usa en el día a día.

---

## 1. Visión general

El módulo **Consolidados** es el centro de control financiero del restaurante.
Permite registrar y consultar tanto los **ingresos diarios** como los
**egresos** realizados por los distintos métodos de pago que maneja el negocio.

Está organizado en **seis pestañas independientes**:

| Pestaña | Propósito |
|---|---|
| Resumen General | Vista consolidada mensual: ingresos vs. egresos y balance |
| Chequera | Registro de pagos realizados con cheque |
| Tarjetas de Crédito | Gestión de tarjetas y sus transacciones (compras y pagos) |
| Pagos en Efectivo | Registro de pagos en efectivo con desglose por categoría de gasto |
| Pagos con Yappy | Registro de pagos realizados a través de Yappy |
| Diario de Ventas | Registro de los ingresos diarios del restaurante por método de cobro |

Todas las pestañas son **independientes entre sí** — se puede usar cualquiera
sin haber llenado las demás — pero el **Resumen General** consolida la
información de todas las otras para calcular el balance mensual.

---

## 2. Relación con otros módulos

El módulo de Consolidados es **autónomo**: no depende de ningún otro módulo
del sistema ni lo alimenta directamente.

> **Importante:** El **Diario de Ventas** dentro de Consolidados es distinto al
> **Registro de Ventas Diarias** del módulo de Ventas. Son dos tablas y dos
> propósitos diferentes:
>
> | | Diario de Ventas (Consolidados) | Registro Ventas Diarias (Ventas) |
> |---|---|---|
> | ¿Qué registra? | Montos totales del día por método de cobro | Unidades vendidas de cada ítem del menú |
> | Origen del dato | El cajero o administrador al cierre del día | El operador al registrar lo producido |
> | ¿Para qué sirve? | Balance financiero mensual | Descuento de inventario (Kardex) |
> | Tabla en BD | `diario_ventas` | `registro_ventas_diarias` |

---

## 3. Pestaña 1 — Resumen General

### ¿Qué muestra?

Una tabla mensual que resume en una sola fila por mes todo lo que entró y salió:

| Columna | Descripción | Fuente |
|---|---|---|
| Mes / Año | Período en formato YYYY-MM | — |
| Total Ventas (+) | Suma de ingresos registrados en el Diario de Ventas | Tabla `diario_ventas` |
| Efectivo (-) | Suma de pagos en efectivo del mes | Tabla `pagos_efectivo` |
| Cheques (-) | Suma de cheques emitidos en el mes | Tabla `chequera` |
| Yappy (-) | Suma de transacciones Yappy del mes | Tabla `transacciones_yappy` |
| Tarjetas (-) | Suma de compras pagadas con tarjeta (tipo COMPRA) | Tabla `transacciones_tarjeta` |
| Total Gastos (-) | Suma de los cuatro egresos anteriores | Calculado |
| Balance General | Total Ventas − Total Gastos | Calculado |

### Colores

- **Total Ventas** → verde (ingreso).
- **Total Gastos** → rojo en negrita (egreso total).
- **Balance General** → verde si positivo (ganancia), rojo si negativo (pérdida).

### Exportar

El botón **"Exportar CSV"** descarga la tabla completa en formato CSV con un
selector de carpeta y mes. Útil para llevar el resumen a Excel o enviarlo al
contador.

---

## 4. Pestaña 2 — Chequera

### ¿Para qué sirve?

Registrar cada cheque emitido por el restaurante para pagar a proveedores,
servicios u otros gastos. Permite llevar un historial de todos los cheques
girados y cuánto suma por mes.

### Datos de cada registro

| Campo | Descripción |
|---|---|
| Fecha | Fecha en que se emitió o registró el cheque |
| No. CK | Número del cheque (referencia del talonario) |
| Nombre Cheque | Nombre del beneficiario (a quién se le pagó) |
| Detalle | Descripción del concepto del pago |
| Monto | Valor del cheque |

### Cómo registrar un cheque

1. Hacer clic en **"+ Nuevo Registro"**.
2. Completar los campos: fecha, número de cheque, nombre del beneficiario,
   detalle y monto.
3. Hacer clic en **"Guardar"**.

Para ingresar varios cheques seguidos usar **"Guardar y Añadir Otro"**, que
limpia los campos sin cerrar la ventana.

### Resumen mensual

En la parte superior de la pestaña aparece una tabla pequeña con el total
acumulado de cheques por mes, útil para ver de un vistazo cuánto se pagó con
cheque en cada período.

### Filtros disponibles

Se puede filtrar la lista por: Fecha, No. CK, Nombre del cheque y Detalle.

---

## 5. Pestaña 3 — Tarjetas de Crédito

Esta pestaña maneja dos niveles: primero se configuran las **tarjetas** y
luego se registran las **transacciones** de cada una.

### 5.1 Gestionar tarjetas

Antes de registrar transacciones es necesario tener al menos una tarjeta
registrada. Hacer clic en **"Gestionar Tarjetas"** para:

- **Agregar** una nueva tarjeta con sus datos: número, tipo (Visa, MasterCard,
  American Express, Diners Club u Otra), banco emisor, día de corte, día de
  pago y tasa de interés.
- **Editar** o **Eliminar** tarjetas existentes.

> El número de la tarjeta se muestra enmascarado en la lista (`**** 1234`)
> para proteger la información sensible.

### 5.2 Seleccionar tarjeta activa

El selector en la parte superior de la pestaña muestra todas las tarjetas
registradas. Al elegir una se cargan automáticamente su balance mensual y su
historial de transacciones. La barra de información muestra la fecha de corte,
fecha de pago y tasa de interés de la tarjeta seleccionada.

### 5.3 Tipos de transacción

| Tipo | ¿Qué representa? |
|---|---|
| `COMPRA` | Cargo realizado con la tarjeta (pago a proveedor, gasto) |
| `PAGO` | Abono o pago realizado a la tarjeta para reducir el saldo |

> Solo las transacciones de tipo `COMPRA` se suman como egreso en el
> Resumen General. Los pagos son movimientos internos de la tarjeta.

### 5.4 Datos de cada transacción

| Campo | Descripción |
|---|---|
| Fecha | Fecha de la transacción |
| Tipo | COMPRA o PAGO |
| Comercio | Nombre del comercio o proveedor (solo para compras) |
| Descripción | Detalle del concepto |
| Monto | Valor de la transacción |

Las filas se colorean automáticamente: **rojo claro** para compras y **verde
claro** para pagos.

### 5.5 Balance mensual por tarjeta

La sección superior muestra por cada mes: total compras, total pagos y balance
(compras − pagos). Balance en rojo significa deuda pendiente; en verde significa
que se pagó más de lo que se usó.

---

## 6. Pestaña 4 — Pagos en Efectivo

### ¿Para qué sirve?

Registrar cada salida de efectivo del restaurante, ya sea para pagar
proveedores, planilla, servicios, mantenimiento u otros gastos operativos.
Incluye un **desglose por categoría** que permite saber exactamente en qué se
gastó el dinero.

### Datos de cada registro

| Campo | Descripción |
|---|---|
| Fecha | Fecha del pago |
| Proveedor | Nombre de quien recibió el pago |
| Descripción | Detalle general del pago |
| Total del Pago | Monto total pagado (obligatorio, mayor a cero) |
| Desglose de categorías | Distribución del total entre categorías de gasto |

### Categorías de desglose disponibles

| Categoría | Uso típico |
|---|---|
| Costo de Víveres | Compras de víveres pagadas en efectivo |
| Costo de Carnes | Compras de carnes pagadas en efectivo |
| Desayunos | Gastos relacionados con servicio de desayunos |
| Planilla | Pago de salarios en efectivo |
| Gastos Propietarios | Retiros o gastos personales de los propietarios |
| Honorarios | Pagos a profesionales o servicios externos |
| Reparaciones y Mantenimiento | Reparaciones de equipos, local, etc. |
| Atención Empleados | Alimentación u otros beneficios al personal |
| Combustible | Gastos de combustible |
| Medicamentos | Botiquín u otros insumos médicos |
| Otros | Cualquier gasto que no encaje en las categorías anteriores |

### Cómo registrar un pago en efectivo

1. Hacer clic en **"+ Nuevo Registro"**.
2. Completar: fecha, proveedor, descripción y **total del pago**.
3. En la sección **Desglose de Categorías**, seleccionar la categoría del gasto,
   ingresar el monto parcial y hacer clic en **"Agregar"**. Repetir por cada
   categoría que aplique.
4. Verificar que la **Suma actual** (en verde) coincida con el total ingresado
   antes de guardar. Si hay diferencia el sistema lo marcará en rojo y no
   permitirá guardar hasta que cuadren.
5. Hacer clic en **"Guardar"**.

> **Regla de validación:** la suma de todos los montos del desglose debe
> ser igual al total del pago. Esto garantiza que cada peso quede clasificado
> en una categoría.

### Vista en la tabla

La columna **Desglose** muestra en una sola línea todas las categorías con
monto mayor a cero, separadas por `|`. Ejemplo:
`Víveres: 150.00 | Planilla: 500.00 | Combustible: 45.00`

---

## 7. Pestaña 5 — Pagos con Yappy

Funciona de manera similar a la pestaña de Tarjetas de Crédito: primero se
registran las **cuentas Yappy** y luego las **transacciones** de cada una.

### 7.1 Gestionar cuentas Yappy

Hacer clic en **"Gestionar Cuentas Yappy"** para agregar, editar o eliminar
cuentas. Cada cuenta tiene:

| Campo | Descripción |
|---|---|
| Nombre | Nombre descriptivo de la cuenta (ej. "Negocio Principal") |
| Número / Celular | Número de teléfono asociado a la cuenta Yappy |

> Eliminar una cuenta borra también todas sus transacciones.

### 7.2 Seleccionar cuenta activa

El selector en la parte superior permite cambiar entre las cuentas registradas.
Al seleccionar una se carga su resumen mensual y el listado de transacciones.

### 7.3 Datos de cada transacción Yappy

| Campo | Descripción |
|---|---|
| Fecha | Fecha del pago |
| Proveedor / Comercio | A quién se le transfirió |
| Descripción | Concepto del pago |
| Monto | Valor de la transferencia |

Todas las transacciones Yappy se consideran **egresos** y se suman al Total
Gastos en el Resumen General.

---

## 8. Pestaña 6 — Diario de Ventas

### ¿Para qué sirve?

Registrar el cierre de caja de cada día: cuánto cobró el restaurante y por
qué método de pago lo recibió. Es la fuente de los **ingresos** en el Resumen
General mensual.

### Datos de cada registro

| Campo | Descripción | Notas |
|---|---|---|
| Fecha | Fecha del día de cierre | — |
| Pagos Yappy | Monto cobrado por Yappy ese día | — |
| Pagos Pedidos Ya | Monto cobrado por Pedidos Ya | — |
| Pagos Clave | Monto cobrado por sistema Clave | — |
| Pagos Visa/MC | Monto cobrado por Visa o MasterCard | — |
| Vale | Monto de vales emitidos ese día | Si > 0 aparece campo de descripción |
| No. Facturas | Cantidad de facturas emitidas en el día | Entero |
| Sobrante Caja | Dinero sobrante al cuadrar la caja | Suma al total |
| Faltante Caja | Dinero faltante al cuadrar la caja | Suma al total |
| Depósitos | Monto depositado en banco ese día | Solo informativo |
| TOTAL VENTAS | Calculado automáticamente | Campo de solo lectura |

### Cálculo del Total Ventas

El sistema calcula el total automáticamente cada vez que se modifica
cualquier campo de monto:

```
TOTAL VENTAS = Yappy + Pedidos Ya + Clave + Visa/MC + Vale + Sobrante + Faltante
```

El campo **TOTAL VENTAS** es de solo lectura — no se puede editar
directamente. Cuadra automáticamente conforme se ingresan los valores.

### Cómo registrar el diario de un día

1. Hacer clic en **"+ Nuevo Registro"**.
2. Seleccionar la fecha del día.
3. Ingresar los montos cobrados por cada método de pago.
4. Si hubo vales, ingresar el monto; aparecerá un campo adicional para
   describir el vale (ej. "Vale de alimentación empleados").
5. Registrar el número de facturas emitidas ese día.
6. Si la caja tuvo diferencia, ingresar sobrante o faltante según corresponda.
7. Si se realizó un depósito bancario, ingresar el monto en **Depósitos**.
8. Verificar que el **TOTAL VENTAS** calculado sea correcto.
9. Hacer clic en **"Guardar"**.

Para registrar varios días seguidos usar **"Guardar y Añadir Otro"**.

### Configurar comisiones por método de pago

El botón **"Configurar Comisiones"** permite registrar el porcentaje de
comisión y la frecuencia de cobro de cada método de pago electrónico:

| Método | Ejemplo de configuración |
|---|---|
| Clave | 1.50% — Mensual |
| Visa / Master Card | 2.75% — Mensual |
| Pedidos Ya | 12.00% — Semanal |
| Yappy | 1.00% — Mensual |

Esta configuración es solo de referencia informativa dentro del sistema; no
descuenta los montos automáticamente en el total.

### Resumen mensual del Diario de Ventas

Encima del listado de registros diarios aparece una tabla pequeña con el
total de ventas y depósitos acumulados por mes. Permite ver rápidamente el
rendimiento mensual sin navegar a la pestaña de Resumen General.

---

## 9. Flujo de uso recomendado

### Al cierre de cada día

```
Cuadrar la caja al final del día operativo
         ↓
Consolidados → Diario de Ventas → + Nuevo Registro
  • Ingresar montos por método de pago (Yappy, Clave, Visa/MC, Pedidos Ya)
  • Registrar vales si aplica
  • Ingresar número de facturas
  • Anotar sobrante o faltante de caja
  • Registrar depósito bancario si se realizó
  • Verificar TOTAL VENTAS calculado y guardar
```

### Al registrar un pago (en cualquier momento)

```
Identificar el método de pago del egreso
         ↓
  Cheque    → Consolidados → Chequera → + Nuevo Registro
  Efectivo  → Consolidados → Pagos en Efectivo → + Nuevo Registro + Desglose
  Yappy     → Consolidados → Pagos con Yappy → Seleccionar cuenta → + Nueva Transacción
  Tarjeta   → Consolidados → Tarjetas de Crédito → Seleccionar tarjeta → + Nueva Transacción (tipo COMPRA)
```

### Al cerrar el mes

```
Consolidados → Resumen General → Actualizar Datos
  • Revisar fila del mes cerrado
  • Verificar que Balance General sea positivo
  • Exportar CSV si es necesario para el contador
```

---

## 10. Exportación de datos

Todas las pestañas tienen un botón **"Exportar CSV"**. Al hacer clic:

1. El sistema pide seleccionar la carpeta de destino y el mes a exportar.
2. Genera un archivo CSV con todos los registros del período seleccionado.
3. El archivo se puede abrir directamente en Excel o Google Sheets.

Los nombres de archivo generados son:
- `resumen_consolidados.csv`
- `chequera.csv`
- `transacciones_tarjeta.csv`
- `pagos_efectivo.csv`
- `transacciones_yappy.csv`
- `diario_ventas.csv`

---

## 11. Errores y advertencias comunes

**El Resumen General muestra $0 en ventas**
No hay registros en el Diario de Ventas para ese mes. Registrar el cierre de
caja de los días del período.

**No puedo registrar una transacción en Tarjetas o Yappy**
Primero es necesario crear al menos una tarjeta (o cuenta Yappy) usando el
botón "Gestionar Tarjetas" / "Gestionar Cuentas Yappy".

**El sistema no me deja guardar un pago en efectivo**
La suma de las categorías del desglose no coincide con el total ingresado.
Revisar que todos los montos parciales sumen exactamente el total.

**El campo TOTAL VENTAS no se puede editar**
Es de solo lectura por diseño — el sistema lo calcula sumando todos los métodos
de cobro. Si el total no es correcto, ajustar los valores de los métodos de pago
individuales.

**Eliminar una tarjeta o cuenta Yappy borra también sus transacciones**
Esta acción es irreversible. Solo eliminar tarjetas o cuentas si se está
seguro de que no se necesita el historial de transacciones. Si la tarjeta
venció pero se quiere conservar el historial, dejarla registrada y simplemente
no usarla más.

---

## 12. Tablas en la base de datos

El módulo utiliza las siguientes tablas, todas independientes del resto del
sistema:

| Tabla | Contenido |
|---|---|
| `diario_ventas` | Registros diarios de ingresos por método de cobro |
| `chequera` | Cheques emitidos |
| `tarjetas_credito` | Catálogo de tarjetas registradas |
| `transacciones_tarjeta` | Compras y pagos por tarjeta |
| `yappy_cuentas` | Cuentas Yappy registradas |
| `transacciones_yappy` | Pagos realizados por Yappy |
| `pagos_efectivo` | Pagos en efectivo con desglose por categoría |
| `configuracion_comisiones` | Porcentajes y frecuencias de comisión por método de pago |

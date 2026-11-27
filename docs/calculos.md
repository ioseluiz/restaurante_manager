# Cálculos del sistema — Restaurante Italos

> Cada fórmula que produce un número en la app: de dónde salen los datos, cómo se calcula, dónde
> se usa y un ejemplo resuelto a mano. Los ejemplos usan el **escenario de prueba de mayo 2026**
> (`tests/e2e/escenario_e2e.py`) y cada resultado tiene una aserción en `tests/e2e/`. Si una
> fórmula cambia, se actualizan juntos este documento y la prueba.
>
> Los puntos que la revisión marcó como error o como decisión pendiente se indican con
> **⚠ Hn**, la referencia al hallazgo de `docs/revision_hallazgos.md`.

---

## 0. Flujo de los datos

```text
 Presentación de compra ──► Compra ──recepción──► Stock + costo promedio (WAC) ──► Kardex
        │                                              │
        │ (precio vigente)                             │ (costo promedio)
        ▼                                              ▼
 Costo de platos ◄── Receta (por porción o tanda + sub-recetas) ──► Costo teórico (Rentabilidad)
        ▲                       │
        │ indirectos            ▼
 Planilla + gastos ──►  Ventas diarias por plato ──► descuento de insumos (Kardex)

 Reporte POS (CSV) ──► promedio por día × 4 semanas × (1 + % sugerido) × receta ──► Presupuesto de compras
 Presupuesto (compras + planilla + gastos fijos) ──► Control: presupuestado vs. ejecutado

 Diario de ventas + pagos (efectivo, cheque, Yappy, tarjeta) ──► Estado de resultados (Rentabilidad)
```

## 1. Escenario de ejemplo

| Insumo | Unidad base | Presentación | Precio | $ por unidad base |
|---|---|---|---|---|
| Arroz | g | Saco 10 kg | 12.00 | 0.0012 (había 5 000 g a 0.0010) |
| Pollo | g | Caja 5 kg | 20.00 | 0.0040 |
| Tomate | g | Caja 2 kg | 3.00 | 0.0015 |
| Aceite | ml | Botella 1 L | 4.00 | 0.0040 |
| Envase | und | Paquete 50 | 10.00 | 0.20 |
| Soda | und | Lata | 0.50 | 0.50 |

- **Salsa de tomate** (sub-receta, tanda de 1 000 g): Tomate 1 200 g + Aceite 100 ml.
- **P1 Pollo con arroz** ($6.00, receta por porción): Pollo 200 g, Arroz 150 g, Salsa 50 g. Extra: envase solo para llevar.
- **P2 Arroz con pollo** ($5.50, receta por tanda: rinde 4 000 g, porción 400 g): Arroz 1 500 g, Pollo 2 000 g, Aceite 200 ml. Extra: soda en ambos canales.
- Ventas del 10/05/2026: 10 P1 y 20 P2.
- Personal: Ana (indefinido, $4.00/h) y Luis (definido, $3.00/h), quincena del 1 al 15 de mayo.

---

## 2. Inventario

### 2.1 Recepción de compra: stock y costo promedio ponderado

*Dónde:* `KardexController.recibir_compra` y `costo_promedio_ponderado` (`app/controllers/kardex_controller.py`),
desde el diálogo de recepción. Todo en una transacción: si falla una línea no se aplica nada.

- Entra al stock: `recibido × cantidad_contenido` de la presentación (en unidad base).
- Costo de entrada por unidad base: `precio_unitario de la compra / cantidad_contenido`.
- Nuevo costo promedio:

  `costo = (stock_anterior × costo_anterior + entrada × costo_entrada) / (stock_anterior + entrada)`

  Si no había costo anterior o el stock anterior era cero o negativo, toma el costo de entrada.
- Cada línea genera un movimiento `COMPRA` en el Kardex y la compra queda `RECIBIDO` (no se puede recibir dos veces).

*Ejemplo:* Arroz tenía 5 000 g a 0.0010 $/g; entran 2 sacos (20 000 g a 0.0012):
`(5 000 × 0.0010 + 20 000 × 0.0012) / 25 000 = 29 / 25 000 = 0.00116 $/g`.

*Stock negativo* (se vendió antes de recibir): −1 000 g a 0.004 y entran 5 000 g a 0.006 → el costo queda en **0.006**
(antes de la corrección de H5 daba 0.0065, más caro que la propia compra).

### 2.2 Receta explotada (por porción, con tandas y sub-recetas)

*Dónde:* vista SQL `v_recetas_explotadas` (`app/database/costeo_sql.py`). La usan el Kardex, el presupuesto y el costo teórico de Rentabilidad.

- Receta por porción (`rendimiento` vacío): factor 1.
- Receta por tanda: factor `porción_servida / rendimiento`.
- Sub-receta: `cantidad usada / rendimiento de la sub-receta`, multiplicado por el factor del padre (hasta 6 niveles).

*Ejemplo, insumos por porción:*
- P1: Pollo 200 g · Arroz 150 g · Tomate `50 × 1 200 / 1 000 = 60 g` · Aceite `50 × 100 / 1 000 = 5 ml`
- P2 (`400 / 4 000 = 0.1`): Arroz 150 g · Pollo 200 g · Aceite 20 ml

Los extras del plato (`plato_extras`) **no** están en esta vista: acompañamientos y bebidas se venden en la caja como
líneas propias (TAZA DE ARROZ, SODA…) con su propia receta. Los **empaques** se agregan aparte con el % de platos para
llevar (§ 2.3 y § 5.1).

### 2.3 Ventas diarias → descuento de insumos

*Dónde:* `KardexController.procesar_ventas_diarias` / `revertir_ventas_diarias`.

`consumo de cada insumo = Σ (unidades vendidas del plato × cantidad por porción)`
`+ Σ (unidades × insumos del empaque × porciones × peso del canal)`, con peso Llevar = % de platos para llevar,
Local = 1 − %, Ambos = 1 (`peso_canal_empaque`). Un movimiento `VENTA` por insumo, todo en una transacción.
«Reabrir día» devuelve el neto con `REVERSO_VENTA`.

*Ejemplo:* Pollo `10 × 200 + 20 × 200 = 6 000 g` · Arroz `1 500 + 3 000 = 4 500 g` · Tomate `600 g` · Aceite `50 + 400 = 450 ml`.
Tras la compra, el stock queda en Pollo 9 000 g, Arroz 20 500 g, Tomate 3 400 g y Aceite 1 550 ml.
Con 40 % para llevar, el envase de P1 (solo para llevar) baja `10 × 0.40 = 4` → 46; la soda de P2 no (línea propia de la caja).

### 2.4 Toma de inventario (conteo)

*Dónde:* `conteo_inventario._registrar_ajuste_kardex`. `diferencia = contado − teórico`; el stock pasa a lo contado y se registra `AJUSTE_INVENTARIO`.
*Ejemplo:* Arroz teórico 20 500 g, contado 20 400 g → ajuste −100 g.

### 2.5 Abastecimiento entre sucursales

*Dónde:* `AbastecimientoController`. Cada instalación solo mueve **su** lado: si es el origen, baja (`SALIDA`); si es el destino, sube (`ENTRADA`). Anular revierte el neto.
*Ejemplo:* Centro envía 1 000 g de pollo a Norte: 15 000 → 14 000 g; al anular vuelve a 15 000 g.

### 2.6 Valor del inventario (Panel de control)

`Σ stock_actual × costo_unitario (promedio)` de todos los insumos. Tras la compra del ejemplo:
`25 000 × 0.00116 + 15 000 × 0.004 + 4 000 × 0.0015 + 2 000 × 0.004 + 50 × 0.20 + 24 × 0.50 = 29 + 60 + 6 + 8 + 10 + 12 = 125.00`.

**Invariante que verifican las pruebas:** `stock_actual = stock inicial + Σ movimientos del Kardex`.

---

## 3. Costo de platos

*Dónde:* `app/controllers/costeo_controller.py`.

### 3.1 Costo por unidad base de un insumo

Configuración `fuente_costo_insumo`:
- `VIGENTE` (predeterminada): el `costo_unitario_calculado` de la presentación; si no hay, el costo promedio.
- `PROMEDIO`: el costo promedio del insumo; si es 0, la presentación.

«La presentación» es la marcada como **preferida** en el catálogo (una por insumo); sin ninguna, la primera creada.

Si la unidad de la línea de receta difiere de la unidad base, se convierte (tabla de conversiones o kg/g/lb/oz/l/ml/gal).

### 3.2 Costo de una porción

`ingredientes = costo de la receta (tanda o porción) × factor por porción`
`total = ingredientes + acompañamientos + bebida* + empaque* (según canal) + indirecto por plato*`

\* Opcionales: casillas «Incluir bebida», «Incluir empaque» e «Incluir indirectos» de Costo por plato (`costeo_config.incluir_bebida` / `incluir_empaque`, por defecto incluidos). Excluidos, se informan pero no suman; no afectan el descuento de empaques del Kardex, los presupuestos ni el costo teórico de Rentabilidad.

*Ejemplo:*
- Salsa: `(1 200 × 0.0015 + 100 × 0.004) / 1 000 = 0.0022 $/g`
- P1 ingredientes: `200 × 0.004 + 150 × 0.0012 + 50 × 0.0022 = 0.80 + 0.18 + 0.11 = 1.09`. Local 1.09 · Para llevar `1.09 + 0.20 = 1.29`.
- P2: `(1 500 × 0.0012 + 2 000 × 0.004 + 200 × 0.004) × 0.1 = 10.60 × 0.1 = 1.06`, más la soda 0.50 = **1.56** (sin bebida: 1.06). P1 para llevar sin empaque: 1.09.
- Con `PROMEDIO` (arroz a 0.00116): P1 ingredientes = 1.084.

### 3.3 Precio sugerido y margen

`precio sugerido = costo / (1 − % ganancia)`, con 30 % local y 50 % Pedidos Ya (configurables; 100 % o más no da precio).
`margen = precio − costo` · `food cost % = costo / precio` · `margen % = margen / precio`.

*Ejemplo P1:* sugerido local `1.09 / 0.70 = 1.557`; para llevar `1.29 / 0.50 = 2.58`; contra $6.00: margen 4.91, food cost 18.2 %.

### 3.4 Indirectos por plato

`indirecto por plato = (gastos del mes + planilla real del mes) / platos vendidos del mes`

- Gastos: lo ejecutado por tipo de gasto (§ 6.2) o, con `base_indirectos = PRESUPUESTO` («Gastos fijos del presupuesto
  del mes»), los gastos fijos del presupuesto. La planilla es siempre la real (decisión H7).
- Platos: ventas diarias del mes → si no hay, reportes del POS cuyo período se cruza con el mes
  (`cantidad del reporte / días del período × días del mes`, promediando si hay varios) → si no hay, `platos/día × días del mes` (198 × 30).

*Ejemplo:* `(1 060 + 946.2348) / 30 platos = 66.87 $/plato`. Sin ventas cargadas: `/ 5 940`.
Con un reporte del 01/04 al 31/05 con 610 platos: `610 / 61 días × 31 días de mayo = 310 platos`.

---

## 4. Planilla (Panamá)

*Dónde:* `app/utils/calculo_planilla.py`; una sola fórmula para el módulo Planilla, el bloque de planilla del presupuesto, el control presupuestal y los indirectos.

| Concepto | Fórmula (sobre el bruto) | Predeterminado |
|---|---|---|
| Salario bruto | `Σ horas × salario/hora × recargo` | regular 1.00 · festivo 2.50 · domingo 1.50 · extra diurna 1.25 · extra nocturna 1.50 |
| Deducción del colaborador | SS + SE | 9.75 % + 1.25 % |
| Aporte patronal | SS + SE | 12.25 % + 1.50 % |
| Riesgo profesional | patronal | 2.10 % |
| Provisión XIII mes | provisión | 8.33 % |
| Provisión vacaciones | provisión | 8.33 % |
| Prima de antigüedad | provisión, solo contrato **indefinido** | 1.92 % |
| **Costo laboral completo** | bruto + patronal + riesgo + provisiones | |
| ISR (retención) | tabla anual sobre `bruto × períodos al año`, dividido de vuelta | 0 % hasta 11 000 · 15 % hasta 50 000 · 5 850 + 25 % |

El ISR es deducción del colaborador: **no** forma parte del costo. El resumen del módulo Planilla anualiza con
`365 / días del período`; el presupuesto y el costo de platos con 24 (quincenal). Solo cambia el ISR mostrado.

*Ejemplo Ana* (88 h regulares, 8 de domingo, 4 extra diurnas a $4.00):
bruto `352 + 48 + 20 = 420` · patronal `57.75` · riesgo `8.82` · XIII y vacaciones `34.986` c/u · prima `8.064` →
**costo completo 564.606**. ISR 0 (`420 × 24 = 10 080` < 11 000).

*Ejemplo Luis* (96 h a $3.00, definido): bruto 288 → `288 + 39.60 + 6.048 + 2 × 23.9904` = **381.6288** (sin prima).

### 4.1 Planilla real del mes

*Dónde:* `gastos_reales.calcular_planilla_real_mes`. Suma el costo completo de las horas de los períodos cuya
**fecha de inicio** cae en el mes. Mayo del ejemplo: `564.606 + 381.6288 = 946.2348`.

⚠ **H6** (decisión): un período del 25/05 al 08/06 cuenta entero para mayo.

---

## 5. Presupuesto

*Dónde:* `app/utils/calculo_presupuesto.py` (`calcular_compras`), que usan «Calcular y Generar» y «Recalcular».

### 5.1 Compras (desde reportes del POS)

1. Por plato y día de la semana: `promedio = Σ Prom/Med de los reportes elegidos / número de reportes`
   (un plato ausente en un reporte cuenta como 0).
2. `platos del mes = Σ promedios de los 7 días × 4 semanas`. ⚠ **H4** (decisión): un mes tiene ≈4.33 semanas; el Excel del cliente también usa 4.
3. `requerido por insumo = Σ platos del mes × cantidad por porción × (1 + % sugerido / 100)`.
   El % es el promedio del % sugerido de los reportes y se puede ajustar por insumo (se conserva al recalcular).
   Los empaques del plato se suman con el peso de su canal (§ 2.3).
4. `a comprar = ⌈ requerido / contenido de la presentación ⌉` (la preferida o, sin ella, la primera creada) · `monto = a comprar × precio`.
   Sin presentación: `⌈ requerido ⌉ × costo promedio`.

*Ejemplo* (reporte con 10 %: P1 lunes 2 + martes 3; P2 lunes 4) → P1 20 y P2 16 platos/mes:

| Insumo | Requerido (× 1.1) | Presentación | A comprar | Monto |
|---|---|---|---|---|
| Pollo | `(200 × 20 + 200 × 16) × 1.1 = 7 920 g` | Caja 5 kg | ⌈1.58⌉ = 2 | 40.00 |
| Arroz | `(150 × 20 + 150 × 16) × 1.1 = 5 940 g` | Saco 10 kg | 1 | 12.00 |
| Tomate | `60 × 20 × 1.1 = 1 320 g` | Caja 2 kg | 1 | 3.00 |
| Aceite | `(5 × 20 + 20 × 16) × 1.1 = 462 ml` | Botella 1 L | 1 | 4.00 |
| **Total compras** | | | | **59.00** |

Con 40 % para llevar se agrega el envase de P1: `20 × 1 × 0.40 × 1.1 = 8.8 und` → 1 paquete de 50 = 10.00.

### 5.2 Planilla y gastos fijos

- Planilla: una fila por empleado con sus horas proyectadas → costo completo (§ 4). Ana: 564.606.
- Gastos fijos: montos por concepto del catálogo. Ejemplo: Alquiler 800 + Luz 140 = 940.
- Los tres bloques se guardan por separado (`monto_total`, `monto_planilla`, `monto_gastos`).

### 5.3 Control: presupuestado vs. ejecutado

| Bloque | Presupuestado | Ejecutado |
|---|---|---|
| Compras, por insumo | monto del presupuesto | `Σ subtotal` de las compras **vinculadas** al presupuesto (pendientes o recibidas) |
| Planilla | Σ costo de las filas | planilla real del mes (§ 4.1) |
| Gastos fijos, por concepto | monto del presupuesto | ejecutado por tipo de gasto (§ 6.2) |

*Ejemplo:* Carnes 40 vs 60 · Víveres 19 vs 38 · Sin categoría 0 vs 22 · Planilla 0 vs 946.23 · Gastos 940 vs 1 060.
Saldo global: `999.00 − 2 126.23 = −1 127.23` (alerta de exceso).

---

## 6. Finanzas

### 6.1 Total del Diario de Ventas

*Dónde:* `app/utils/diario_ventas_calc.py`.
`TOTAL = Yappy + Pedidos Ya + Clave + Visa/MC + efectivo + vale + sobrante − faltante`.
*Ejemplo:* `20 + 30 + 40 + 50 + 60.5 + 1 − 0.5 = 201.00`.

### 6.2 Gastos ejecutados por tipo de gasto

*Dónde:* `gastos_reales.ejecutado_gastos_mes`. Suma por `tipo_gasto`: cheques, tarjeta (solo `COMPRA`; los pagos a la
tarjeta no cuentan), Yappy y las líneas del desglose de pagos en efectivo. Lo que no tiene tipo de gasto no entra.
*Ejemplo:* Alquiler 800 (cheque) · Internet 60 (tarjeta) · Luz 150 (Yappy) · Gas 50 (efectivo) = **1 060**.

### 6.3 Estado de resultados (Rentabilidad)

*Dónde:* `app/controllers/rentabilidad_controller.py`.

| Renglón | Fórmula | Ejemplo mayo |
|---|---|---|
| Ventas | `Σ diario_ventas.total_ventas` | 201.00 |
| Costo real | pagos en efectivo: víveres + carnes + desayunos | 220.00 |
| Costo teórico | `Σ unidades vendidas × costo de ingredientes de una porción` (§ 3.2, misma fuente de costo de Parámetros); sin ventas por plato, el costo del reporte POS | 32.10 |
| Merma | real − teórico | 187.90 |
| *Ref.: teórico con extras* | `Σ unidades × costo total del plato` (canal local, sin indirectos) | 42.10 |
| Utilidad bruta | ventas − costo real | −19.00 |
| Gastos | efectivo (planilla, propietarios, honorarios, mantenimiento, atención, combustible, medicamentos, otros) + todos los cheques + Yappy + tarjeta (`COMPRA`) | 900 + 50 + 1 100 + 150 + 60 = 2 260 |
| Utilidad neta | utilidad bruta − gastos | −2 279.00 |

Costo teórico del ejemplo (precio vigente): `10 × 1.09 + 20 × 1.06 = 32.10`. Con extras: `10 × 1.09 + 20 × 1.56 = 42.10`;
esa cifra cuenta dos veces lo que la caja también vende como línea propia (la soda), por eso la merma usa 32.10.
Con «costo promedio» en Parámetros: P1 1.084 y P2 1.054 (arroz a 0.00116) → 31.92.

La matriz anual repite el mes para los 12 meses y suma; las variaciones comparan con el mes anterior y con el mismo
mes del año anterior (sin base, el % es 0).

⚠ **H8** (decisión): el costo real solo sale del efectivo; una compra de carne pagada con cheque cuenta como gasto
operativo, y la planilla es la pagada en efectivo, no el costo del módulo Planilla. El estado de resultados de la
contadora clasifica distinto (ver la conciliación en `docs/revision_hallazgos.md`).

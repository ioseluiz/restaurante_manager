# Revisión end-to-end — hallazgos

> Revisión de los cálculos y del flujo completo de Italos Manager (noviembre 2026, rama
> `revision/e2e-calculos`). Esta etapa **no corrige nada**: documenta cada hallazgo con su evidencia, su
> impacto y la corrección propuesta. Las fórmulas están en `docs/calculos.md` y el guion de pantalla en
> `docs/pruebas_manual_ui.md`.

## Resumen

- **Estado (actualizado):** resueltos H1, H2, H5, H7, H9, H10, H12, H13, H14, H15, H16, H18 y H19, cada uno con su
  prueba. La suite completa da 156 aprobadas y 1 omitida, sin `xfail`. Pendientes de decisión con el cliente o la
  contadora: H8, H4, H6, H11, H17 y H20.
- **Pruebas automáticas nuevas:** 40 en `tests/e2e/` sobre un escenario de mayo 2026 con resultados calculados a
  mano (más pruebas de recepción, login y humo de los 18 módulos añadidas con las correcciones). La primera corrida dio
  102 aprobadas, 1 omitida y 8 `xfail`. Cada `xfail` es un hallazgo confirmado, marcado
  `strict`: el día que se corrija, la prueba empieza a pasar y obliga a quitar la marca.
- **Lo que funciona bien:** el costo laboral de la planilla (Panamá) da el mismo resultado en Planilla, Presupuesto,
  Control e indirectos. Recepción de compras, promedio ponderado, Kardex de ventas con tandas y sub-recetas,
  reapertura de días, conteos, abastecimiento, costo de platos por canal, precio sugerido y totales del diario
  cuadran con los cálculos a mano. El invariante `stock = inicial + Σ Kardex` se cumple en todo el flujo.
- **Lo más importante para corregir:** los extras del plato (bebidas, empaques) quedan fuera del inventario y del
  presupuesto (H10). El costo teórico de Rentabilidad no coincide con el de Costo de Platos (H1). El estado de
  resultados clasifica distinto que la contadora (H8). El saldo global del Control Presupuestal no se muestra (H12).
- **Conciliación con los Excel del cliente:** el método del presupuesto es el mismo que usa el cliente; la app da
  entre +0.4 % y +3.1 % más porque redondea a presentaciones completas. Además apareció un **error en el Excel del
  cliente**: el arroz omite el 10 % de incertidumbre que la propia hoja calcula.

## Hallazgos priorizados

Severidad: **Alta** = número incorrecto que ve el cliente · **Media** = error con impacto acotado o riesgo · **Baja** = menor o de mantenimiento.
«Decisión» = no hay un único comportamiento correcto; lo define el cliente o la contadora.

| # | Sev. | Módulo | Hallazgo | Evidencia | Decisión | Estado |
|---|---|---|---|---|---|---|
| H10 | Alta | Inventario / Presupuestos | Los extras del plato (bebida, empaque, acompañamiento) no se descuentan del stock ni entran al presupuesto | `xfail` en inventario y presupuesto | Sí: el canal | **Corregido** |
| H1 | Alta | Rentabilidad | Costo teórico distinto al de Costo de Platos: 31.92 contra 42.10 para las mismas ventas | `xfail` en rentabilidad | Sí: la fuente | **Corregido** |
| H8 | Alta | Rentabilidad | El estado de resultados clasifica por canal de pago, no por naturaleza del gasto como la contadora | prueba de caracterización + conciliación | Sí | Pendiente |
| H12 | Media | Presupuestos | El resumen «Saldo Global» del Control Presupuestal nunca se muestra | `xfail` en presupuesto | No | **Corregido** |
| H5 | Media | Compras | Promedio ponderado incorrecto cuando el stock previo es negativo | `xfail` en inventario | No | **Corregido** |
| H9 | Media | Costo de platos | El reporte POS nunca se usa como fuente de platos para los indirectos | `xfail` en costeo | No | **Corregido** |
| H14 | Media | Seguridad | `gerente` y `empleado` ven exactamente lo mismo, incluidos salarios y rentabilidad | revisión de código | Sí | **Corregido** |
| H15 | Media | Compras | La recepción no es atómica: un error a mitad deja stock sumado y la compra PENDIENTE | revisión de código | No | **Corregido** |
| H16 | Media | Seguridad | Contraseñas en SHA-256 sin sal y `admin/admin123` por defecto | revisión de código | No | **Corregido** |
| H7 | Media | Costo de platos | Con base de indirectos PRESUPUESTO, la planilla sigue siendo la real | `xfail` en costeo | Sí | **Decidido: se mantiene** |
| H2 | Media | Costo de platos / Presupuestos | Se usa la presentación de menor id, no la última comprada ni la vigente | prueba de caracterización | Sí | **Corregido** |
| H11 | Baja | Presupuestos | El control cuenta como ejecutadas las compras vinculadas aún PENDIENTES | prueba del control | Sí | Pendiente |
| H4 | Baja | Presupuestos | El mes se proyecta como 4 semanas (≈4.33 reales): ~8 % menos platos | caracterización + conciliación | Sí | Pendiente |
| H6 | Baja | Planilla | Un período que cruza de mes se imputa entero al mes de inicio | prueba de caracterización | Sí | Pendiente |
| H13 | Baja | Ventas | La vista previa del CSV muestra «Estim/Med» en 0 | `xfail` con el CSV real | No | **Corregido** |
| H17 | Baja | Planilla | Las provisiones solo se registran al pulsar «Calcular Planilla» | revisión de código | No | Pendiente |
| H18 | Baja | Presupuestos | La lógica de generar y recalcular está duplicada (≈250 líneas) | prueba de igualdad | No | **Corregido** |
| H19 | Baja | Compras | `procesar_recepcion` es código muerto y no actualiza el costo promedio | revisión de código | No | **Corregido** |
| H20 | — | Presupuestos | El presupuesto no proyecta ingresos ni utilidad; el del cliente es un estado de resultados completo | conciliación | Sí | Pendiente |

Descartados tras verificar: **H3** (las recetas guardan siempre en unidad base: el editor, Recetas e importador
dejan `unidad_id` vacío, así que la vista explotada no necesita convertir) y **promediar reportes donde falta un
plato** (dividir entre todos los reportes es correcto: ausente = 0 ventas).

---

## Detalle

### H10 · Los extras del plato no tocan inventario ni presupuesto — Alta

`plato_extras` (acompañamiento, bebida, empaque) solo lo usa Costo de Platos. La vista `v_recetas_explotadas`, que
alimentan el Kardex de ventas y el presupuesto, solo lee `recetas` y `receta_componentes`.

- *Escenario:* 20 P2 llevan 20 sodas; el stock de soda sigue en 24 y el presupuesto no incluye soda.
- *Impacto:* las bebidas y los empaques nunca bajan del stock (cada conteo los ajusta de golpe) y no se presupuestan.
  En el estado de resultados de la contadora pesan 3.65 % (sodas, $1 782) y 2.15 % (envases, $1 048) de los ingresos.
- *Propuesta:* incluir los extras en la vista explotada. Para los que dependen del canal, las ventas diarias no
  registran canal: decidir si se separan local/llevar o se usa un % de llevar configurable.
- *Prueba:* `test_ventas_diarias_descuentan_extras_del_plato`, `test_presupuesto_incluye_extras_del_plato`.

*Evidencia nueva (CSV real del POS):* la caja registra acompañamientos y bebidas como **líneas propias** a precio simbólico:
TAZA DE ARROZ 5 544 u. a $0.06, ENSALADA CODITO 2 809 a $0.12, PAPITAS 3 556 a $0.22, SODA 6 055 a $0.25. Si esos ítems
tienen receta y se cargan en las ventas diarias, su consumo **ya** se descuenta y se presupuesta: sumar además los
extras del plato lo duplicaría. Lo que no aparece en el POS son los **envases** (para llevar / PedidosYa).

*Corregido (decisión: solo empaques):* parámetro «% de platos para llevar» en Costo de Platos. El Kardex de ventas y el presupuesto suman los insumos de los extras de tipo EMPAQUE con `peso_canal_empaque` (LLEVAR × %, LOCAL × (1 − %), AMBOS × 1). Acompañamientos y bebidas siguen entrando por su propia línea del POS. Con 0 % (valor inicial) no cambia nada.

### H1 · Dos costos teóricos distintos — Alta

| | Costo de Platos | Rentabilidad (costo teórico) |
|---|---|---|
| Costo del insumo | presentación vigente (configurable) | siempre el promedio ponderado |
| Extras del plato | sí | no |
| Conversión de unidades | sí | no (hoy no hace falta, ver H3) |
| Escenario (10 P1 + 20 P2) | 42.10 | 31.92 |

- *Impacto:* la **merma** (real − teórico) de Rentabilidad sale inflada: en el escenario son $10.18 (24 %) del teórico.
- *Propuesta:* que Rentabilidad calcule con `CosteoController` (una sola fuente) y que el informe diga qué fuente de costo usa.
- *Prueba:* `test_costo_teorico_coincide_con_costo_de_platos`.

*Corregido (decisión: solo ingredientes, con referencia):* `costo_teorico_mes` usa `CosteoController.costo_ingredientes` (misma fuente de costo, tandas, sub-recetas y conversión). La merma usa esa cifra (escenario 32.10). Rentabilidad muestra en gris «Ref.: teórico con extras del plato» (42.10) para discutir con el cliente el doble conteo con las líneas propias de la caja.

### H8 · Estado de resultados por canal de pago, no por naturaleza — Alta, decisión

Rentabilidad toma el **costo real** solo de tres columnas de pagos en efectivo (víveres, carnes, desayunos). Todo
cheque, Yappy o compra con tarjeta va a gastos operativos, aunque sea mercadería. La planilla es la pagada en efectivo,
no el costo del módulo Planilla.

Comparación con «INFORME E. RESULTADOS hasta sep 2025-contadora.xlsx»:

| Rubro | Contadora | App |
|---|---|---|
| Ingresos | Ventas no gravadas 42 160 + **Ingresos otros 6 663** (13.6 %) | Solo `diario_ventas.total_ventas` |
| Faltantes y sobrantes | Gasto (−752.45) | Dentro de las ventas |
| Costo de ventas | 8 rubros (carnes, pollo, mariscos, víveres, sodas, arroz, envases, **gas**) sin importar cómo se pagó | Víveres, carnes y desayunos pagados en efectivo |
| Planilla | Salarios 4 912 + CSS patronal 996; XIII, vacaciones y prima en 0 (se registran al pagarse) | Efectivo con categoría planilla (el módulo Planilla calcula con provisiones mensuales) |
| Otros | Depreciación 1 012, donación 765, ITBMS 38.71 | No existen |

- *Escenario:* el cheque de $300 a «Carnes del Istmo» es gasto operativo, no costo de ventas.
- *Propuesta:* clasificar cada egreso por **categoría contable** (las mismas cuentas de la contadora), sin importar el
  medio de pago. Registrar «otros ingresos». Definir con la contadora si la planilla del informe es la pagada o el
  costo devengado.
- *Prueba:* `test_costo_real_y_gastos_por_canal_de_pago`.

### H12 · El saldo global del Control Presupuestal no se muestra — Media

En `ControlPresupuestoDialog`, el bloque que arma el texto del saldo global quedó **después del `return`** de
`_control_gastos` (código inalcanzable desde que se agregaron los bloques de planilla y gastos). La etiqueta se queda
en «Cargando datos...».

- *Propuesta:* mover ese bloque al final de `cargar_datos_control` y asignar `self.lbl_resumen.setText(html_res)`.
- *Prueba:* `test_control_muestra_saldo_global`.

*Corregido:* el bloque se movió al final de `cargar_datos_control`; la prueba verifica los totales del resumen.

### H5 · Promedio ponderado con stock negativo — Media

`(stock_anterior × costo_anterior + entrada × costo_entrada) / stock_nuevo` con stock anterior negativo pondera
unidades que no existen. *Escenario:* −1 000 g a 0.004 + 5 000 g a 0.006 → **0.0065** (más caro que la compra).
Ocurre cuando se procesan ventas antes de registrar la compra que las abasteció, algo habitual si las recepciones se
cargan tarde.

- *Propuesta:* si el stock anterior es ≤ 0, el nuevo costo es el de entrada.
- *Prueba:* `test_promedio_ponderado_con_stock_negativo`.

*Corregido:* `costo_promedio_ponderado` en `kardex_controller.py` usa el costo de entrada si el stock previo es ≤ 0.

### H9 · Indirectos: el reporte POS nunca se usa como fuente de platos — Media

`pool_indirectos` busca los reportes por `reportes_ventas.mes/anio`, pero `guardar_reporte_mensual` no llena esas
columnas (solo las fechas del período). Sin ventas diarias, siempre cae a «promedio configurado» (198 × 30).

- *Propuesta:* al guardar, derivar mes y año de `fecha_inicio_periodo` (formato dd/mm/aaaa) o filtrar por fechas.
  Ojo: un reporte cubre varios meses (el de ejemplo va del 01/09 al 07/11); hay que prorratear o usar el promedio diario.
- *Prueba:* `test_indirectos_con_reporte_pos_cargado`.

*Corregido:* `CosteoController._platos_mes_reporte_pos` usa los reportes cuyo período se cruza con el mes: promedio diario × días del mes.

### H14 · Roles sin diferencias — Media, decisión

Solo hay dos niveles: `admin` (ve Usuarios y Configurar BD) y todos los demás. `empleado` ve Planilla (salarios),
Rentabilidad, Presupuestos y Consolidados igual que `gerente`. El README describe tres roles.
*Propuesta:* definir con el cliente qué módulos ve cada rol y aplicarlo en `main_window`.

*Corregido:* `auth_controller.puede_ver`: el gerente ve todo menos Usuarios/BD; el empleado no ve Panel, Presupuestos, Consolidados, Rentabilidad, Costo de Platos, Análisis de Precios, Planilla ni Sucursales y arranca en Ventas. `load_module` también lo bloquea.

### H15 · Recepción de compra no atómica — Media

`RecepcionDialog._aplicar` usa `KardexController.registrar_movimiento` y `execute_query`, que confirman cada sentencia.
Si falla una línea a mitad, las anteriores ya sumaron stock y la compra sigue PENDIENTE: al reintentar, se duplican.
*Propuesta:* aplicar todo en una transacción con `_aplicar(cur, …)`, como ya hacen ventas y abastecimiento.

*Corregido:* `KardexController.recibir_compra` aplica stock, Kardex, costo y estado en una transacción; la clave es la línea de detalle (una compra puede repetir presentación).

### H16 · Contraseñas — Media

SHA-256 sin sal (`auth_controller.py`) y usuario `admin/admin123` creado por defecto. *Propuesta:* `hashlib.pbkdf2_hmac`
o `scrypt` con sal por usuario, migrando al siguiente login, y forzar el cambio de la clave por defecto.

*Corregido:* PBKDF2-SHA256 con sal por usuario (`auth_controller.hash_password`); los hashes antiguos se migran en el siguiente login correcto. Queda pendiente forzar el cambio de `admin123` (decisión de UX).

### H7 · Indirectos con base PRESUPUESTO — Media, decisión

Con `base_indirectos = PRESUPUESTO` los gastos salen del presupuesto, pero la planilla sigue siendo la real.
*Propuesta:* usar también el bloque de planilla del presupuesto, o renombrar la opción a «gastos presupuestados».
*Prueba:* `test_indirectos_base_presupuesto_usa_planilla_presupuestada`.

*Decidido:* se mantiene la planilla real; la opción ahora se llama «Gastos fijos del presupuesto del mes (planilla real)».

### H2 · Presentación «vigente» = la de menor id — Media, decisión

Costo de Platos (`costo_unitario_insumo`) y el presupuesto (`ORDER BY id LIMIT 1`) toman la primera presentación
creada. Con dos presentaciones (saco de 10 kg y de 25 kg) se ignora la que realmente se compra. El historial de precios
tiene `es_precio_actual`, pero por presentación, no por insumo.
*Propuesta:* marcar una presentación **preferida** por insumo (o usar la última comprada). *Prueba:* `test_presentacion_vigente_es_la_primera_creada`.

*Corregido:* casilla «Presentación preferida» en el catálogo (una por insumo, columna ★). Costo de Platos y Presupuestos ordenan por `SQL_ORDEN_PRESENTACION`; sin preferida, la primera creada.

### H11 · Control: compras pendientes cuentan como ejecutadas — Baja, decisión

El ejecutado de compras suma las compras vinculadas al presupuesto sin mirar su estado. Puede ser lo deseado (comprometido)
o no (solo recibido). *Propuesta:* mostrar las dos columnas o filtrar por RECIBIDO.

### H4 · 4 semanas por mes — Baja, decisión

`SEMANAS_POR_MES = 4.0`. Un mes promedio tiene 52/12 ≈ 4.33 semanas: el presupuesto proyecta ~8 % menos platos.
El Excel del cliente hace lo mismo (`=B13*4`), así que hoy la app **coincide con su método**.
*Propuesta:* parámetro configurable (4.0 por defecto) o calcular con los días reales del mes. *Prueba:* `test_presupuesto_proyecta_cuatro_semanas_por_mes`.

### H6 · Período de pago que cruza de mes — Baja, decisión

`calcular_planilla_real_mes` asigna el período por el mes de `fecha_inicio`. Con quincenas 1–15 / 16–fin no ocurre;
con planillas semanales o bisemanales sí. *Propuesta:* prorratear por días si se usan períodos que cruzan.

### H13 · Vista previa del CSV con «Estim/Med» en 0 — Baja

`ReportParser` busca el estimado hasta 3 celdas después del promedio; en el CSV real está 7 celdas después. Solo afecta
a la vista previa: el presupuesto recalcula `prom × (1 + % sugerido)`, que da exactamente el estimado del POS.
*Prueba:* `test_estimado_por_medida`.

*Corregido:* el estimado se toma de su columna fija (promedio + 7); en productos con medida (papitas en gramos) la columna intermedia es el total en gramos.

### H17 · Provisiones registradas al consultar — Baja

`provisiones_laborales` se reemplaza cada vez que se pulsa «Calcular Planilla». Si nadie lo pulsa, el pasivo acumulado
no incluye ese período. *Propuesta:* registrar al cerrar el período.

### H18 · Lógica de presupuesto duplicada — Baja

`generar_presupuesto` y `recalcular_automatico` repiten el cálculo (≈250 líneas cada una). Hoy dan lo mismo
(`test_recalcular_da_lo_mismo_que_generar`); cualquier corrección de H2, H4 o H10 debe hacerse en los dos.
*Propuesta:* extraer el cálculo a una función pura en `app/utils/` antes de corregirlos.

*Corregido:* el cálculo vive en `app/utils/calculo_presupuesto.calcular_compras`, usado por generar y recalcular. La conciliación con los Excel del cliente da los mismos números.

### H19 · Código muerto en compras — Baja

`ComprasCRUD.procesar_recepcion` no se llama desde ningún lado y suma stock sin recalcular el costo promedio. *Propuesta:* eliminarlo.

*Corregido:* eliminados `procesar_recepcion` y `KardexController.registrar_movimiento` (ya sin uso).

### H20 · El presupuesto no es un estado de resultados — decisión

El «PRESUPUESTO MAYO 2024» del cliente parte de los ingresos esperados y llega a la utilidad, con costo de ventas por
rubro y unas 40 cuentas de gasto. El de la app tiene compras de insumos, planilla y gastos fijos, sin ingresos ni
utilidad. Tampoco tiene la vista semanal ni la «lista para compra» (necesidad − stock) del control de compras del cliente.
*Propuesta:* decidir con el cliente si el presupuesto debe proyectar ingresos y utilidad.

---

## Conciliación con los Excel del cliente

Los archivos de `assets/datos_presupuesto_2025/` son de períodos distintos (presupuesto de mayo 2024, CSV del POS de
sep–nov 2025, informe de la contadora hasta sep 2025) y la base de la app no tiene sus recetas. Por eso la conciliación
reproduce **líneas concretas** con los datos de la hoja del cliente, cargados en una base temporal y calculados con el
mismo diálogo de la app.

### Presupuesto de compras (hoja «produccion semanal COMBOS»)

| Producto | Cálculo del cliente | Cantidad exacta | App (redondeada) | Cliente $ | App $ | Diferencia |
|---|---|---|---|---|---|---|
| Churrasco | Σ prom. diario × 1.15 × 4 sem × 460 g, a $8.20/kg | 34.874 kg | 35 kg | 285.97 | 287.00 | +1.03 (+0.4 %) |
| Arroz | Σ g/día × 1.10 × 4 sem, bulto de 20 kg a $31.70 | 32.008 bultos | 33 bultos | 922.41 | 1 046.10 | +123.69 (+13.4 %) |
| Arroz sin el 10 % | Σ g/día × 4 sem (lo que calcula hoy la hoja) | 29.098 bultos | 30 bultos | 922.41 | 951.00 | +28.59 (+3.1 %) |

- **El método coincide**: promedio por día de la semana × 4 semanas × (1 + merma) × cantidad por porción × precio.
- **La app redondea hacia arriba** a presentaciones completas (35 kg, 30 bultos); el cliente usa la fracción. Por eso
  la app da algo más. Es lo correcto para una lista de compra, pero conviene decirlo en la ayuda.
- **Error en el Excel del cliente:** en la hoja ARROZ, la columna «insertidumbre» calcula `N4 = M4*10% + M4`, pero la
  siguiente usa `O4 = M4/1000` (sin el 10 %). El presupuesto del cliente omite la merma que la propia hoja define:
  faltan ~$92 al mes solo en arroz. Hay que avisarle.
- El cliente usa un % de merma **por producto** (15 % churrasco, 10 % arroz); la app usa el % sugerido del POS para todo,
  ajustable por insumo con «Ajustar %».

### Reporte del POS (CSV real)

- Se leen correctamente: período 01/09/2025–07/11/2025, % sugerido 12.16, 606 filas, 115 códigos, ventas B/. 100 899.98.
- «Prom/Med» del POS = cantidad / 9 en todas las filas (el POS divide por 9 semanas, aunque el período tiene 67 días)
  y «Estim/Med» = Prom × 1.1216: la app usa ese mismo criterio.
- El costo total del POS es B/. 12 464.53 (12.4 % de las ventas) con muchos productos en B/. 0.00. Como respaldo del costo
  teórico en Rentabilidad no es confiable.

### Estado de resultados

Ver la tabla de H8. Con la estructura actual, la utilidad bruta de la app no es comparable con la de la contadora.

---

## Preguntas para el cliente y la contadora

1. ¿El costo teórico y el costo de los platos se valoran al precio vigente o al costo promedio? (H1, H2)
2. ¿Qué porcentaje de las ventas es para llevar, o se registran por separado? (H10)
3. ¿Qué categorías contables se usan para clasificar los egresos y qué va a costo de ventas? ¿Dónde se registran los «Ingresos otros»? (H8)
4. En el informe, ¿la planilla es la pagada o la devengada con provisiones? ¿La retención de ISR se anualiza con 12 o con 13 salarios? (H8, § 4 de calculos.md)
5. ¿Proyectar con 4 semanas o con los días reales del mes? (H4)
6. ¿El control presupuestal debe contar las compras pendientes? (H11)
7. ¿Qué módulos debe ver cada rol? (H14)
8. ¿El presupuesto debe incluir ingresos y utilidad, como su Excel? (H20)

## Siguientes pasos sugeridos

1. ~~Correcciones sin decisión pendiente: H12, H5, H9, H13, H15, H16, H19.~~ Hechas.
2. ~~Extraer el cálculo del presupuesto a una función pura (H18) y resolver H2 y H10.~~ Hecho.
3. Reunión con el cliente y la contadora con las preguntas de arriba (quedan H8, H4, H6, H11, H17 y H20). Llevar la comparación «teórico vs. teórico con extras» de Rentabilidad (H1) y el % de platos para llevar real (H10).
4. Correr `docs/pruebas_manual_ui.md` completo antes de la próxima versión.

## Cómo reproducir

```bash
venv\Scripts\python -m pytest tests            # suite completa (Qt sin pantalla en tests/e2e)
venv\Scripts\python -m pytest tests/e2e -rx     # E2E con la lista de hallazgos (xfail)
venv\Scripts\python -m pytest tests/e2e --runxfail   # muestra dónde falla cada hallazgo
python scripts/crear_bd_prueba.py C:/temp/prueba_e2e.db   # base para el checklist manual
```

# Módulo de Costo de Platos — Restaurante Italos

> Cuánto cuesta producir cada plato y a qué precio venderlo, calculado con los
> datos que ya están en la app (insumos, recetas, gastos fijos, planilla, ventas).

---

## 1. Visión general

| Pestaña | Propósito |
|---|---|
| Costo por plato | Costo de ingredientes + acompañamientos + bebida + empaque + indirectos, precio de venta vs precio sugerido, food cost %, margen. Doble clic = desglose por línea. Exporta a Excel/CSV. |
| Recetas de costeo | Editor de recetas por porción o por tanda, sub-recetas y extras; alta de componentes; **importación desde el Excel del cliente**. |
| Parámetros | % de ganancia por canal, base de indirectos, fuente del costo de insumos, platos/día. |

## 2. Cómo se calcula

**Receta por porción o por tanda.** Un plato con *rendimiento* vacío tiene su receta por porción (comportamiento
histórico). Con rendimiento `R` y porción servida `P`, las cantidades son **por tanda** y

    costo por porción = costo de la tanda × P ÷ R

**Sub-recetas (componentes).** Chimichurri, sazonadores, salsas, acompañamientos y empaque son ítems del menú marcados
«no se vende». Su costo por unidad = costo de su tanda ÷ su rendimiento; un plato los usa indicando cuántas unidades
(g, ml…). Se admite anidar (máx. 6 niveles); los ciclos se detectan y se avisan.

**Costo del insumo.** Por defecto, el precio vigente de la presentación de compra (respaldo: costo promedio ponderado);
configurable en Parámetros. Un insumo sin costo genera una alerta ⚠.

**Indirectos por plato** = (gastos fijos del mes + planilla del mes) ÷ platos vendidos del mes. La planilla es el
**costo laboral completo** (bruto + Seguro Social/Educativo y riesgo profesional patronales + provisiones), igual que el
Resumen de Planilla y el bloque de planilla del Presupuesto. Platos vendidos: ventas
diarias → reporte del POS → *platos por día × días del mes* (Parámetros). Los gastos salen de los consolidados
(`tipo_gasto`) o del presupuesto, según la opción.

**Precio sugerido** = costo total ÷ (1 − % de ganancia). Canal *Local* y *Llevar / PedidosYa* tienen % distintos.

## 3. Importar el Excel del cliente

Recetas → **Importar desde Excel…** (hoja «PLATOS CODIGOS Y RECETAS»).

1. **Simular**: no guarda nada; muestra el reporte.
2. Corregir lo que el reporte marca (Excel o nombres de insumos) y repetir.
3. **Importar**: hace antes una copia de respaldo de la base de datos.

Reglas: rendimiento = TOTAL ÷ COST X U; porción = CANT. SERVIDA; las líneas con código numérico (`#90`, `#205`) son
sub-recetas; una receta con insumos sin resolver **no se importa a medias**; las existentes se omiten salvo «Reemplazar»;
los nombres se comparan sin acentos ni mayúsculas y por conjunto de palabras («consome pollo» = «Consome De Pollo»); un
nombre que es abreviatura de otro insumo («aceite» / «Aceite Veg») requiere decisión del usuario.

Opciones: crear insumos faltantes (con unidad y costo del Excel) y completar el costo de insumos sin costo.

### Problemas conocidos del Excel (el reporte los avisa)
- Insumos con **costos contradictorios** según la línea (referencias cruzadas a `INSUMOS BASE MADRE`); se usa el más
  frecuente y se lista el conflicto.
- Líneas **sin costo** en el Excel (p. ej. la salsa del lomo) que el Excel cuenta como $0 y la app sí costea.
- Recetas **sin cantidades** (no se importan) y códigos repetidos.
- Unidades no compatibles (`cuart`, `u` vs `lb`/`g`): se toman 1:1 y se avisa para revisión.

## 4. Impacto en otros módulos

`v_recetas_explotadas` (vista SQL) devuelve los insumos **por porción** de cada plato aplicando rendimiento/porción e
incluyendo los de sus sub-recetas. La usan los **Presupuestos** (los dos cálculos: generar y recalcular), la
**Rentabilidad (costo teórico)** y el **descuento de inventario por ventas diarias** (Kardex, movimientos `VENTA`).
Con rendimiento vacío y sin sub-recetas, el resultado es idéntico al de las recetas simples.
Los componentes no aparecen en **Menú** ni en **Ventas diarias**.

## 5. Datos

`menu_items` (+ `categoria_costeo`, `es_componente`, `rendimiento`, `unidad_rendimiento_id`, `porcion_servida`,
`unidad_porcion_id`), `recetas` (+ `unidad_id`), `receta_componentes`, `plato_extras`, `costeo_config`,
`conversiones_unidades` (factores estándar g/kg/lb/oz y ml/l/gal si esas unidades existen).
Lógica: `app/controllers/costeo_controller.py`; SQL compartido: `app/database/costeo_sql.py`;
importador: `app/utils/importar_costeo_excel.py`; vista: `app/views/modulos/costo_platos.py`.

# Módulo de Presupuestos — Restaurante Italos

> Documento de referencia completo: qué es un presupuesto en el sistema, qué
> información previa se necesita, cómo se genera, cómo se interpreta, cómo se
> ajusta y cómo se hace el seguimiento de ejecución.

---

## 1. ¿Qué es un presupuesto en este sistema?

Un presupuesto en el sistema es una **proyección de compras mensual** calculada
automáticamente. El sistema toma como base los reportes históricos de ventas
del POS, los cruza con las recetas del menú, y calcula cuánto de cada insumo
necesita comprar el restaurante para cubrir la demanda proyectada de ese mes,
expresado en unidades de compra y en costo estimado.

**El presupuesto responde a:** "Si las ventas de este mes son similares a los
períodos anteriores que seleccionamos, ¿cuánto tengo que comprar de cada cosa
y cuánto me va a costar?"

---

## 2. Qué debe estar configurado antes de generar un presupuesto

El cálculo automático depende de varias piezas de información que deben estar
cargadas en el sistema. Si alguna falta, el resultado será incompleto o incorrecto.

### 2.1 Catálogo de Insumos

Módulo: **Catálogo de Insumos → Pestaña 1**

Cada insumo debe tener:
- **Nombre** claro y único
- **Unidad base** asignada (ej. kg, ml, unidad)
- **Categoría** asignada (Carnes, Viveres, Bebidas, etc.)
- **Costo unitario** actualizado (se usa como respaldo si no hay presentación de compra)

### 2.2 Presentaciones de Compra

Módulo: **Catálogo de Insumos → Pestaña 2**

Las presentaciones de compra son la forma en que se compra cada insumo al
proveedor. Son críticas porque el presupuesto calcula **cuántos empaques comprar**
y **a qué precio**.

Cada presentación tiene:
- **Nombre** (ej. "Saco 25 kg", "Caja 24 latas 355 ml")
- **Cantidad contenido** (cuántas unidades base hay en ese empaque)
- **Precio de compra** (costo de ese empaque completo)

> **Importante:** Si un insumo no tiene presentación de compra registrada, el
> sistema cae en modo de respaldo y calcula sobre el costo unitario base. La
> cantidad será en unidad base y puede no corresponder a ningún empaque real.
> Se recomienda tener presentaciones cargadas para todos los insumos relevantes.

### 2.3 Categorías de Insumos

Módulo: **Catálogo de Insumos → Pestaña 3**

Las categorías agrupan los insumos en el presupuesto (ej. CARNES, VIVERES,
BEBIDAS). El presupuesto presenta los resultados agrupados por categoría, por
lo que categorías bien definidas facilitan la lectura y el análisis.

### 2.4 Menú

Módulo: **Gestión de Menú**

Cada ítem del menú debe tener:
- **Código** (debe coincidir exactamente con el código que reporta el POS)
- **Nombre**
- **Precio de venta**

El código es el vínculo entre las ventas reportadas por el POS y el menú del
sistema. Si hay diferencia entre el código del POS y el código en el sistema,
ese producto no entrará en el cálculo del presupuesto.

### 2.5 Recetas

Módulo: **Recetas (Fichas)**

Cada ítem del menú debe tener una receta que liste:
- Los **insumos** que lo componen
- La **cantidad** de cada insumo necesaria para preparar **una** porción

Las recetas son el corazón del cálculo: sin receta, el sistema no sabe qué
insumos se necesitan para preparar un plato y ese plato queda excluido del
presupuesto.

### 2.6 Reportes de ventas cargados

Módulo: **Ventas → Carga de Reportes**

El presupuesto necesita al menos **un reporte de ventas** histórico cargado en
el sistema. Los reportes son archivos CSV exportados desde el sistema POS y
contienen:

- Código del producto vendido
- Cantidades vendidas por día de la semana (Lunes, Martes… Domingo)
- Rango de fechas del período reportado
- Porcentaje sugerido del período

Cuantos más reportes se seleccionen para basar el cálculo, más preciso y
representativo será el promedio.

---

## 3. Cómo se carga un reporte de ventas

Antes de generar el presupuesto, los reportes del POS deben estar cargados en
el sistema.

1. Ir a **Ventas → Carga de Reportes**.
2. En la pestaña **"Cargar Nuevo Reporte"**, seleccionar el archivo CSV del POS.
3. El sistema valida y muestra una vista previa de los datos.
4. Confirmar la carga. El reporte queda guardado con su fecha de período y
   porcentaje sugerido.
5. Repetir para cada período que se desee incluir en el cálculo del presupuesto.

Los reportes cargados se pueden consultar en la pestaña **"Historial y Consultas"**.

---

## 4. Generación del presupuesto paso a paso

### Paso 1 — Abrir el módulo

Ir a **Presupuestos** en el menú lateral y hacer clic en **"Nuevo Presupuesto"**.

### Paso 2 — Configurar el encabezado

| Campo | Descripción |
|---|---|
| Mes | Mes para el que se está presupuestando (ej. 6 para junio) |
| Año | Año correspondiente |
| Descripción | Texto libre opcional para identificar el presupuesto (ej. "Temporada alta julio 2026") |

### Paso 3 — Seleccionar los reportes base

La lista muestra todos los reportes de venta cargados en el sistema, ordenados
del más reciente al más antiguo.

**Marcar con palomita** los reportes que se desean usar como base del cálculo.
Se puede seleccionar uno o varios.

> **Criterio de selección recomendado:**
> - Usar los **2 o 3 reportes más recientes** para reflejar la tendencia actual.
> - Si el mes a presupuestar tiene una temporada especial (vacaciones, fiestas),
>   incluir también reportes del mismo período del año anterior.
> - Evitar incluir reportes de períodos atípicos (pandemia, cierres, eventos
>   excepcionales) a menos que sea intencional.

### Paso 4 — Calcular y Generar

Hacer clic en **"Calcular y Generar Presupuesto"**. El sistema ejecuta el
algoritmo de cálculo automáticamente y guarda el presupuesto.

---

## 5. Cómo calcula el sistema el presupuesto

Este es el proceso interno que ejecuta el sistema al generar el presupuesto.
Entenderlo ayuda a interpretar correctamente los resultados y a saber cuándo
ajustar manualmente.

### 5.1 Porcentaje sugerido (factor de seguridad)

El sistema calcula el **promedio del porcentaje sugerido** de todos los reportes
seleccionados. Este porcentaje es un margen que se suma a la cantidad calculada
para absorber la diferencia entre lo que dice la receta y lo que realmente se
consume (mermas, porciones generosas, errores, etc.).

```
Porcentaje promedio = Promedio(%_sugerido de cada reporte seleccionado)
Factor              = 1 + (Porcentaje / 100)

Ejemplo: si el % promedio es 12%, el Factor = 1.12
→ Se compra un 12% más de lo que la receta dice como mínimo.
```

### 5.2 Ventas proyectadas por producto

Para cada producto en los reportes seleccionados:

1. Se agrupa por código de producto y día de la semana.
2. Se promedia la cantidad vendida por día entre los reportes:
   ```
   Promedio_lunes = (lunes_reporte1 + lunes_reporte2 + ...) / cantidad_reportes
   ```
3. Se suma el promedio de todos los días para obtener la **venta semanal promedio**.
4. Se multiplica por 4 para proyectar el **total mensual**:
   ```
   Total_mensual = Venta_semanal_promedio × 4 semanas
   ```

### 5.3 Cálculo de insumos por receta

Para cada producto con ventas proyectadas, el sistema busca su receta y
calcula cuánto de cada insumo se necesita:

```
Cantidad_insumo (unidad base) = Total_mensual_platos × Cantidad_receta × Factor

Ejemplo:
  Total mensual proyectado de "Pasta Alfredo": 120 platos
  Receta: 0.2 kg de crema por plato
  Factor (12%): 1.12
  → Crema necesaria = 120 × 0.2 × 1.12 = 26.88 kg
```

Si un insumo aparece en la receta de varios platos, las cantidades de todos
los platos se suman para obtener el requerimiento total de ese insumo.

### 5.4 Conversión a unidad de compra y costo

Una vez calculado el requerimiento total en unidad base, el sistema convierte
a unidades de compra usando la presentación de compra principal del insumo:

```
Unidades_a_comprar_exactas = Total_base_requerido / Cantidad_contenido_presentación
Unidades_a_comprar_final   = REDONDEAR_ARRIBA(Unidades_a_comprar_exactas)
Costo_estimado             = Unidades_a_comprar_final × Precio_presentación

Ejemplo (continuando con la crema):
  Presentación: "Caja 6 litros" (= 6 000 ml = 6 kg contenido, precio $18.50)
  Exacto: 26.88 kg / 6 kg = 4.48 cajas
  Redondeado ARRIBA: 5 cajas   ← siempre se redondea para no quedarse corto
  Costo: 5 × $18.50 = $92.50
```

> **¿Por qué redondear hacia arriba?** Porque es mejor comprar de más (el
> sobrante se usa el mes siguiente) que quedarse sin insumos a mitad de mes.

**Si el insumo no tiene presentación de compra:** el sistema usa el costo
unitario base del insumo y expresa la cantidad en unidad base. En este caso
el resultado puede no corresponder a ningún empaque real y deberá ajustarse
manualmente.

---

## 6. Interpretar los resultados del presupuesto

Después de generar el presupuesto, seleccionarlo en la lista y hacer clic en
**"Ver / Editar Insumos"** para ver el detalle.

La vista muestra un árbol agrupado por categoría:

```
▼ CARNES
     Pollo (filete)          48 Bandeja 5 kg         $432.00    Pasta Alfredo (80), Pollo Asado (160)
     Carne molida            12 Paquete 1 kg          $96.00    Lasaña (48)
▼ VIVERES
     Pasta (seco)            6 Caja 20x500g          $54.00     Pasta Alfredo (80), Lasaña (48)
     ...
```

| Columna | Qué significa |
|---|---|
| Insumo | Nombre del insumo según el catálogo |
| Cantidad a Comprar | Número de empaques (presentación de compra) redondeado hacia arriba |
| Monto Estimado | Costo total de esos empaques a precio de presentación |
| Desglose por Platos | Qué platos del menú requieren ese insumo y cuánto aportó cada uno |

### Ver el detalle de cálculo de un insumo

Hacer clic en **"Detalle"** junto a cualquier insumo para ver:
- El porcentaje sugerido aplicado y el factor resultante
- La presentación de compra usada con su precio
- La proyección de ventas por día y por plato
- La fórmula exacta de cálculo paso a paso
- La conversión final a empaques y el costo

---

## 7. Ajustar y corregir el presupuesto

El presupuesto generado es un punto de partida. El sistema ofrece varias
herramientas para ajustarlo antes de usarlo como orden de compra definitiva.

### 7.1 Ajustar el porcentaje por insumo

Botón **"Ajustar %"** junto a cada insumo.

Permite cambiar el porcentaje de seguridad para **ese insumo específico**,
sobreescribiendo el promedio global. Útil cuando:
- Un insumo tiene más merma que el promedio (subir el %).
- Un insumo se usa con alta precisión y el porcentaje global es excesivo
  (bajar el %).
- Se quiere presupuestar un extra puntual de un insumo sin afectar los demás.

Al guardar el porcentaje ajustado, el sistema recalcula automáticamente la
cantidad y el costo de esa línea.

### 7.2 Editar cantidad y monto manualmente

Botón **"Editar"** junto a cualquier insumo.

Permite sobreescribir directamente la cantidad a comprar y el monto estimado
de esa línea. Útil cuando:
- Se tiene una negociación de precio especial con el proveedor.
- Se sabe que ese mes hay una necesidad puntual que el algoritmo no captura.
- El precio de la presentación de compra cambió y aún no se actualizó en el
  catálogo.

La línea editada manualmente queda marcada como tal en su detalle de cálculo
para que quede claro que no proviene del algoritmo automático.

### 7.3 Agregar insumos que no están en recetas

Botón **"+ Agregar Insumo Manual Extra"**.

Permite agregar artículos que el restaurante compra pero que no forman parte
de ninguna receta y por lo tanto no aparecen en el cálculo automático.
Ejemplos:
- Productos de limpieza
- Empaques y bolsas para llevar
- Materiales de oficina
- Artículos de mantenimiento
- Insumos estacionales puntuales

Estos artículos se agregan con categoría (existente o nueva), nombre, unidad,
cantidad y monto manual.

### 7.4 Eliminar una línea del presupuesto

Botón **"X"** junto a cualquier insumo.

Elimina esa línea del presupuesto y recalcula el total. Útil si un insumo
no se va a comprar ese mes (hay existencia suficiente) o si fue incluido
por error.

### 7.5 Recalcular con precios y recetas actuales

Botón **"Recalcular con Precios Actuales"**.

Vuelve a ejecutar todo el algoritmo de cálculo usando los precios y recetas
**que están en el sistema en este momento**, y reemplaza los resultados
calculados. Las siguientes cosas se **conservan**:

- Los porcentajes personalizados por insumo (Ajustar %)
- Los insumos agregados manualmente (Extras)

Las siguientes cosas se **sobreescriben**:

- Las ediciones manuales a insumos calculados

Usar este botón cuando:
- Los precios de las presentaciones de compra cambiaron.
- Las recetas fueron modificadas.
- Se quiere refrescar el presupuesto sin crear uno nuevo.

### 7.6 Editar datos generales

Botón **"Editar General"** en la pantalla principal de Presupuestos.

Permite cambiar el mes, año y descripción del presupuesto sin afectar el
cálculo.

---

## 8. Vincular compras al presupuesto

Para que el sistema pueda hacer el **seguimiento de ejecución** del presupuesto,
cada compra que se realice en ese período debe vincularse al presupuesto
correspondiente.

Al registrar una compra en el módulo **Compras y Proveedores**:
1. Completar los datos de la compra normalmente (proveedor, fecha, productos).
2. En el campo **"Presupuesto asociado"**, seleccionar el presupuesto del mes
   correspondiente.
3. Guardar la compra.

Las compras sin presupuesto asociado no aparecerán en el control presupuestal.

> **Recomendación:** Vincular todas las compras del mes al presupuesto desde el
> primer día. Es mucho más difícil hacer la asociación retroactiva al final del
> mes.

---

## 9. Control de ejecución presupuestal

Una vez que hay compras vinculadas, seleccionar el presupuesto en la lista y
hacer clic en **"Control Presupuestal"**.

La vista muestra un árbol comparativo por categoría e insumo:

```
▼ CARNES                          $528.00 presup.    $492.00 ejecutado    $36.00
     Pollo (filete)               $432.00             $432.00              $0.00
     Carne molida                  $96.00              $60.00             $36.00

▼ BEBIDAS                         $185.00 presup.    $210.00 ejecutado   -$25.00  ← EXCEDIDO
     Soda                          $92.50             $111.00            -$18.50
     Agua                          $92.50              $99.00             -$6.50
```

| Columna | Qué muestra |
|---|---|
| Monto Presupuestado | Monto estimado al generar el presupuesto |
| Monto Ejecutado | Suma real de lo que se gastó en compras vinculadas a ese presupuesto |
| Saldo | Diferencia: azul = dentro del margen, rojo = excedido |

Al pie de la pantalla aparece el **resumen global**:
- Total original presupuestado
- Total real ejecutado
- Saldo global con alerta si está excedido

### Cómo interpretar el control

- **Saldo positivo (azul):** se gastó menos de lo presupuestado en ese insumo.
  Puede ser bueno (el precio bajó, se compró menos) o una señal de que faltó
  comprar algo.
- **Saldo negativo / Excedido (rojo):** se gastó más de lo presupuestado.
  Causas comunes: precio subió, se compró de más, o el presupuesto estuvo
  sub-estimado para ese insumo.
- **Ejecutado = $0 con presupuesto > $0:** ese insumo aún no se ha comprado en
  este período o las compras no fueron vinculadas al presupuesto.

---

## 10. Flujo completo de inicio a fin

```
CONFIGURACIÓN (una sola vez)
─────────────────────────────
1. Cargar unidades de medida
2. Crear categorías de insumos
3. Cargar catálogo de insumos con unidad base y categoría
4. Cargar presentaciones de compra con precio por presentación
5. Cargar ítems del menú con el código exacto del POS
6. Crear recetas (menú ↔ insumos y cantidades por porción)

CADA PERÍODO (mensual o cuando se cargue un reporte del POS)
─────────────────────────────────────────────────────────────
7. Exportar el reporte de ventas desde el POS (archivo CSV)
8. Cargarlo en el sistema: Ventas → Carga de Reportes
9. Verificar que el porcentaje sugerido del período sea correcto

GENERAR EL PRESUPUESTO
─────────────────────────────────────────────────────────────
10. Ir a Presupuestos → Nuevo Presupuesto
11. Configurar mes, año y descripción
12. Seleccionar los reportes base (2-3 períodos recientes recomendados)
13. Hacer clic en "Calcular y Generar Presupuesto"

REVISAR Y AJUSTAR
─────────────────────────────────────────────────────────────
14. Abrir el presupuesto con "Ver / Editar Insumos"
15. Revisar cada categoría e insumo
16. Ajustar porcentajes por insumo si alguno necesita margen diferente
17. Editar manualmente líneas con condiciones especiales
18. Agregar insumos extra que no están en recetas (limpieza, empaques, etc.)
19. Eliminar insumos que no se van a comprar ese mes
20. El presupuesto queda listo como guía de compras del mes

EJECUTAR Y CONTROLAR
─────────────────────────────────────────────────────────────
21. Registrar cada compra en el módulo Compras y Proveedores
22. Al registrar cada compra, vincularla al presupuesto del mes
23. En cualquier momento del mes, abrir "Control Presupuestal"
    para ver el avance: presupuestado vs. ejecutado por categoría
24. Tomar decisiones si alguna categoría está excedida o muy por debajo
```

---

## 11. Preguntas frecuentes

**¿Qué pasa si un producto del POS no tiene receta en el sistema?**
El producto se ignora en el cálculo. Su volumen de ventas no contribuye al
requerimiento de ningún insumo. Solución: crear la receta del producto en
el módulo **Recetas (Fichas)**.

**¿Qué pasa si el código del POS no coincide con el código del menú?**
El sistema no puede vincular esas ventas a ningún ítem del menú y ese producto
queda fuera del cálculo. Verificar que el código en **Gestión de Menú** sea
exactamente igual al código que exporta el POS.

**¿Se puede generar más de un presupuesto para el mismo mes?**
Sí. El sistema no impide tener varios presupuestos con el mismo mes y año. Esto
puede ser útil para comparar escenarios (pesimista vs. optimista) o para
presupuestos por sucursal.

**¿El presupuesto se actualiza automáticamente cuando cambian los precios?**
No. Una vez generado, el presupuesto queda guardado con los precios del momento.
Para actualizarlo usar el botón **"Recalcular con Precios Actuales"**.

**¿Qué significa el porcentaje sugerido del reporte?**
Es el margen de error histórico entre lo que la receta dice que se debe consumir
y lo que realmente se consumió, expresado como porcentaje. Lo define la
administración al cargar cada reporte. Un 10-15% es un valor típico para
restaurantes con buena estandarización de recetas. A mayor variabilidad en
cocina, mayor debe ser este porcentaje.

**¿Se puede presupuestar sin reportes del POS?**
No. El cálculo automático requiere al menos un reporte de ventas cargado. Si
no hay reportes, la alternativa es agregar todos los insumos manualmente uno
por uno usando **"Agregar Insumo Manual Extra"**.

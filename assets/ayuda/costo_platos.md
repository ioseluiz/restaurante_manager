# Costo de Platos

Responde: **¿cuánto cuesta producir cada plato y a qué precio debería venderse?** Calcula con los datos que ya están en el sistema (insumos, recetas, gastos fijos, planilla y ventas). Tiene tres pestañas:

| Pestaña | Para qué sirve |
|---|---|
| **Costo por plato** | Costo de cada plato, precio de venta vs. precio sugerido, margen |
| **Recetas de costeo** | Editar recetas (por porción o por tanda), sub-recetas y extras; importar del Excel |
| **Parámetros** | % de ganancia, base de indirectos, fuente del costo de insumos |

## Cómo se calcula el costo

**Costo total = ingredientes + acompañamientos + bebida + empaque + indirectos**

- **Ingredientes:** receta × costo de cada insumo. Una receta puede ser **por porción** o **por tanda** (ver abajo).
- **Acompañamientos, bebida y empaque:** los que asocie a cada plato; el empaque solo cuenta en el canal *Llevar*.
- **Indirectos por plato** = (gastos fijos del mes + planilla del mes) ÷ platos vendidos del mes. La planilla usada es el **costo laboral completo** (igual que el Resumen de Planilla: incluye aportes patronales, riesgo profesional y provisiones).
- **Precio sugerido** = costo ÷ (1 − % de ganancia). Hay un % para *Local* y otro para *Llevar / PedidosYa*.

## Costo por plato

1. Elija **mes**, **año** y **canal** arriba.
2. La tabla muestra cada plato. El precio de venta sale en **rojo** si está por debajo del sugerido y en verde si lo supera.
3. **Doble clic** en un plato abre el **desglose por línea**.
4. Las alertas **⚠** avisan de insumos sin costo, cantidades vacías o platos sin receta (pase el mouse para ver el detalle).
5. **Exportar** genera un Excel o CSV.

## Recetas de costeo

- **Editar receta / costeo:** categoría, **rendimiento** y **porción servida**, ingredientes, **sub-recetas** y **acompañamientos/empaque**.
- **Receta por porción** (sin rendimiento): las cantidades son para un plato.
- **Receta por tanda:** ponga el **rendimiento** de la tanda y la **porción servida** (misma unidad). Las cantidades son de la tanda completa y el sistema calcula el costo por porción. El botón *Rendimiento = suma de ingredientes* ayuda a llenarlo.
- **Nuevo componente:** cree preparaciones que **no se venden** (chimichurri, sazonadores, salsas, porciones de acompañamiento, fiambreras). Otros platos las usan como **sub-recetas** indicando cuántas unidades (g, ml…).
- Las cantidades se guardan en la **unidad base** del insumo; si elige otra unidad se convierte al guardar.
- Al definir rendimiento y sub-recetas, también los consideran los [Presupuestos](ayuda:presupuestos) y la [Rentabilidad](ayuda:rentabilidad) (con los insumos de las sub-recetas incluidos).

## Importar desde el Excel del cliente

**Recetas de costeo → Importar desde Excel…**

1. Elija el archivo y pulse **Simular (no guarda)**. Lea el reporte.
2. Corrija lo que se marque (nombres de insumos, códigos repetidos, recetas sin cantidades) y repita.
3. Pulse **Importar**. Se hace antes una **copia de respaldo** de la base de datos.

Opciones: *crear insumos que no existan* (con el costo que trae el Excel), *completar costos faltantes* y *reemplazar recetas existentes* (por defecto se omiten). Una receta con insumos sin resolver **nunca se importa a medias**. El reporte lista los platos nuevos con precio 0 para que los complete en [Menú](ayuda:menu).

## Parámetros

- **% de ganancia** para Local y para Llevar/PedidosYa.
- **Base de gastos indirectos:** gastos reales del mes o del presupuesto.
- **Platos por día:** se usa solo si no hay ventas registradas del mes.
- **Costo de los insumos:** precio vigente de la presentación (por defecto) o costo promedio del inventario.

## Antes de empezar

Insumos con costo ([Catálogo](ayuda:insumos) o [Compras](ayuda:compras)), platos en el [Menú](ayuda:menu), pagos del mes en [Consolidados](ayuda:consolidados) y períodos en [Planilla](ayuda:planilla) para que los indirectos no salgan en cero.

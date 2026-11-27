# Costo de Platos

Responde: **¿cuánto cuesta producir cada plato y a qué precio debería venderse?** Calcula con los datos que ya están en el sistema (insumos, recetas, gastos fijos, planilla y ventas). Tiene tres pestañas:

| Pestaña | Para qué sirve |
|---|---|
| **Costo por plato** | Costo de cada plato, precio de venta vs. precio sugerido, margen |
| **Recetas de costeo** | Editar recetas (por porción o por tanda), sub-recetas y extras; importar del Excel |
| **Parámetros** | % de ganancia, base de indirectos, fuente del costo de insumos |

## Cómo se calcula el costo

**Costo total = ingredientes + acompañamientos + bebida (opcional) + empaque (opcional) + indirectos (opcional)**

- **Ingredientes:** receta × costo de cada insumo. Una receta puede ser **por porción** o **por tanda** (ver abajo).
- **Acompañamientos, bebida y empaque:** los que asocie a cada plato; el empaque solo cuenta en el canal *Llevar*. Son para **costear el plato**: la caja registra acompañamientos y bebidas como líneas propias (TAZA DE ARROZ, SODA…), que descuentan su propio inventario. Los empaques no pasan por la caja y se descuentan con el *% de platos para llevar* (Parámetros).
- **Indirectos por plato** = (gastos fijos del mes + planilla del mes) ÷ platos vendidos del mes. La planilla usada es el **costo laboral completo** (igual que el Resumen de Planilla: incluye aportes patronales, riesgo profesional y provisiones). Los platos vendidos salen de las ventas diarias; si no hay, del reporte del POS que cubra el mes (su promedio diario × días del mes); si tampoco, de *platos por día × días del mes* (Parámetros).
- **Precio sugerido** = costo ÷ (1 − % de ganancia). Hay un % para *Local* y otro para *Llevar / PedidosYa*.

## Costo por plato

1. Elija **mes**, **año** y **canal** arriba.
2. La tabla muestra cada plato. El precio de venta sale en **rojo** si está por debajo del sugerido y en verde si lo supera.
3. **Doble clic** en un plato abre el **desglose por línea**.
4. Las alertas **⚠** avisan de insumos sin costo, cantidades vacías o platos sin receta (pase el mouse para ver el detalle).
5. **Incluir indirectos**, **Incluir bebida** e **Incluir empaque** deciden qué entra en el costo total, el food cost, el margen y el precio sugerido. La bebida y el empaque son opcionales porque no siempre forman parte del plato: desmarcados, su valor se sigue viendo en gris (como referencia) pero no se suma. La elección se recuerda. **No cambia el inventario ni los presupuestos**: los empaques se siguen descontando y comprando con el *% de platos para llevar*. El desglose marca lo «no incluido» y la exportación indica en su primera fila qué se incluyó.
6. **Exportar** genera un Excel o CSV.

## Recetas de costeo

- **Editar receta / costeo:** categoría, **rendimiento** y **porción servida**, ingredientes, **sub-recetas** y **acompañamientos/empaque**.
- **Receta por porción** (sin rendimiento): las cantidades son para un plato.
- **Receta por tanda:** ponga el **rendimiento** de la tanda y la **porción servida** (misma unidad). Las cantidades son de la tanda completa y el sistema calcula el costo por porción. El botón *Rendimiento = suma de ingredientes* ayuda a llenarlo.
- **Nuevo componente:** cree preparaciones que **no se venden** (chimichurri, sazonadores, salsas, porciones de acompañamiento, fiambreras). Otros platos las usan como **sub-recetas** indicando cuántas unidades (g, ml…).
- Las cantidades se guardan en la **unidad base** del insumo; si elige otra unidad se convierte al guardar.
- Al definir rendimiento y sub-recetas, también los consideran los [Presupuestos](ayuda:presupuestos) y la [Rentabilidad](ayuda:rentabilidad) (con los insumos de las sub-recetas incluidos).

## Importar recetas desde archivo

**Recetas de costeo → Importar recetas…**

**1. Preparar el archivo**
- **Descargar plantilla vacía…**: Excel con las hojas *Recetas* (una fila por tanda: código, nombre, tipo PLATO o SUB-RECETA, **rendimiento de la tanda** y su unidad), *Ingredientes* (cantidades de la tanda; el insumo por **código** o por nombre, o una sub-receta por su código numérico), *Platos* (cada plato del menú con su **código del POS** y su **porción**), y de referencia *Insumos* y *Unidades*. La hoja *Instrucciones* lo explica.
- **Convertir fichas del cliente…**: si las recetas vienen en fichas (una receta por hoja, como «BAÑO MARIA 1 recetas»), genera la plantilla **prellenada** con una hoja **Revisión** de lo que falta (el rendimiento de cada tanda, unidades dudosas, ingredientes sin nombre…). Las filas amarillas tienen observaciones. El archivo del cliente no se modifica.

**2. Importar**
1. Elija la plantilla y el modo: **Solo recetas nuevas** (no toca las recetas que ya existen) o **Actualizar existentes** (reemplaza las recetas que vienen en el archivo).
2. **Simular (no guarda)** y lea el reporte. **Importar** hace antes una **copia de respaldo**. **Nunca se borra** nada que no esté en el archivo.

**Reglas**
- **Sin rendimiento de la tanda** la receta queda **pendiente** y no se importa.
- Los insumos se buscan por **código** y luego por **nombre** (sin importar tildes, mayúsculas, plurales ni el orden de las palabras). Si el código es de un insumo y el nombre de otro, se avisa y se usa el del código.
- **Si falta un insumo, la receta no se importa** (nunca a medias). **Guardar reporte…** genera un Excel con la hoja **Insumos faltantes**: complete la unidad base (y los gramos por ml si hace falta) y use **Importar insumos faltantes…** para crearlos. Después póngales presentación y precio en el [Catálogo](ayuda:insumos) y vuelva a importar las recetas.
- Las cantidades se convierten a la unidad del insumo (lb → g, l → ml…). Si la receta mide en **ml** un insumo que se lleva en gramos (cebolla picada, ajo…), el insumo necesita **Gramos por ml** en el Catálogo; si no lo tiene, la receta se bloquea y el reporte lo indica.
- Una receta con **un solo plato** queda en ese plato (rendimiento + porción). Con **varios platos** (normal y *eco*, o «con arroz»), la tanda se guarda como sub-receta «R‹código› … (tanda)» y cada plato lleva su porción de ella.
- Los platos se buscan por su código del POS; si no existen se crean con **precio 0** y se avisa para que lo complete en [Menú](ayuda:menu).

**Formato anterior (COSTEO DE PLATOS)…** abre el importador del Excel de costeo del cliente (hoja «PLATOS CODIGOS Y RECETAS»), con sus opciones de crear insumos y completar costos.

## Parámetros

- **% de ganancia** para Local y para Llevar/PedidosYa.
- **Base de gastos indirectos:** gastos reales del mes (consolidados) o *gastos fijos del presupuesto del mes*. En los dos casos la planilla es la real del mes.
- **% de platos para llevar (empaques):** parte de los platos que sale para llevar. Con este % las [ventas diarias](ayuda:ventas) descuentan del inventario y los [Presupuestos](ayuda:presupuestos) compran los **empaques** del plato (extras de tipo Empaque: canal Llevar × %, Local × el resto, Ambos siempre). Con 0 % no se descuentan empaques.
- **Platos por día:** se usa solo si no hay ventas registradas del mes.
- **Costo de los insumos:** precio vigente de la presentación (por defecto) o costo promedio del inventario.

## Antes de empezar

Insumos con costo ([Catálogo](ayuda:insumos) o [Compras](ayuda:compras)), platos en el [Menú](ayuda:menu), pagos del mes en [Consolidados](ayuda:consolidados) y períodos en [Planilla](ayuda:planilla) para que los indirectos no salgan en cero.

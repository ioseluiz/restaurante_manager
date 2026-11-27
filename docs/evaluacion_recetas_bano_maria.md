# Evaluación: «BAÑO MARIA 1 recetas de ITALOS ATRIO.xlsx»

Archivo compartido por el cliente con las recetas de Baño María. Se revisó con el convertidor
(`app/utils/fichas_bano_maria.py`), que genera la plantilla estándar prellenada:
**«Plantilla recetas ITALOS ATRIO (para revisar).xlsx»**, con la hoja **Revisión**.

## Resumen

- **24 hojas → 23 recetas** («Hoja2» está vacía).
- **15 fichas en formato estándar**: se leen bien (ingredientes, cantidades de la tanda, códigos de insumo,
  códigos de plato y porción servida).
- **8 fichas con formato distinto** (plantilla copiada): hay que revisarlas a fondo antes de importarlas.
- **Ninguna ficha trae el rendimiento total de la tanda.** Es obligatorio (decisión con el cliente): sin él no se
  puede calcular cuántas porciones salen ni el costo por porción. Todas las recetas quedan **pendientes** hasta
  completarlo en la hoja «Recetas».
- Usan **55 ingredientes distintos** y **3 sub-recetas** (#200 guizos, #202 salsa, #203 salsa espesor) que deben
  existir en la app o venir en la plantilla como SUB-RECETA.

## Estado por ficha

| Ficha | Plato(s) POS · porción | Estado | Qué falta |
|---|---|---|---|
| filete de pescado | #36 · 136 g | Revisar | Rendimiento; «Ajo Molido» con código «2» (se ignoró); «1 limon» → Limón |
| puerco liso | #43 · 165 g | Revisar | Rendimiento; una fila con 60 ml sin ingrediente |
| carne guisada | — | Revisar | Rendimiento; **sin código de plato** (¿es la sub-receta que usa el arroz de combinación?) |
| sopa de carne | #69 · 592 g · #70 «con arroz» | Revisar | Rendimiento; porción del #70 (lleva arroz aparte); nombres con cantidades («2 mazorca», «16 tazas de agua») |
| sopa de pollo | #67 · 580 g · #68 «con arroz» | Revisar | Igual que sopa de carne |
| carne mechada | — | Revisar | Rendimiento; sin código de plato |
| pollo guisado (hoja «pollo guisado 1») | — | Revisar | **Duplicada** con «pollo guisado» (#46): conservar una |
| lomo | #30 · 126 g | Lista salvo rendimiento | Usa la sub-receta #202 salsa |
| pernil | #32 · 204 g | Revisar | Rendimiento; una fila con 10 ml sin ingrediente; usa #202 |
| arroz de combinacion | #38 · 287 g · #78 eco 190 g | Lista salvo rendimiento | Usa #200 guizos; la tanda se comparte entre #38 y #78 |
| pollo guisado | #46 · 292 g · #79 eco 141 g | Lista salvo rendimiento | Usa #200 y #203 |
| guacho de rabito | #41 · 603 g | Lista salvo rendimiento | Usa #200 |
| codillo | #51 · 214 g · #75 eco 106 g | Lista salvo rendimiento | Usa #200 y #203 |
| pollo al horno | #56 · 215 g | Lista salvo rendimiento | — |
| sopa de pata | #65 · 580 g · #66 «con arroz» | Revisar | Rendimiento; porción del #66 |
| Bistec Encebollado | — | **Rehacer** | Formato distinto: códigos de otra receta, cantidades en kg marcadas como «g», sin plato |
| Chuleta en Salsa | — | **Rehacer** | Ídem; la ficha dice 2.144 kg en total |
| Sancocho de Gallina | — | **Rehacer** | Ídem; 1.346 kg «un pollo entero» |
| Pechuga Salteada | — | **Rehacer** | Ídem; «salen 8 porciones» |
| Bolitas de Carne | — | **Rehacer** | Ídem; «salen 16 bolitas» |
| Filete de pechuga al Ajillo | — | **Rehacer** | Ídem |
| Hoja «Filete de Pescado al Ajillo» | — | **Rehacer** | El título interno dice «Costillitas»; «10 filetes» |
| Costillita | — | **Rehacer** | Ídem |

## Problemas generales del archivo

1. **Sólidos medidos en ml** (ajo, cebolla, ají, apio, culantro, zanahoria, ñame…), medidos con taza o
   cucharón. Para importarlos, cada insumo que se lleva en gramos necesita **Gramos por ml** en el Catálogo
   (decisión con el cliente). Si falta, la receta se bloquea y el reporte lo indica.
2. **Códigos de insumo con nombres distintos**: IC005 = «Caldo rojo» y «Caldo rojo de pollo»; C001 = «Carne para
   guisar» y «Carne guisada»; C018 = «Pollo», «Pollo entero» y «Pollos»; V017 = «Zanahoria(s)». La importación usa
   el **código** y avisa la diferencia.
3. **Ingredientes sin código** (cebolla, ají, apio, mazorca, plátano verde, pasta de tomate…): se buscan por
   nombre, sin importar tildes, plurales ni orden.
4. **Nombres con cantidades** («2 mazorca», «16 tazas de agua», «2 pollos»): el convertidor deja el nombre limpio
   y anota la observación para confirmar la cantidad.
5. **Números como texto** («4.69») y unidades `lbs`, `L`, `gal`: se normalizan solos.
6. Platos con **dos códigos**: el segundo es la versión **eco** (porción menor) o **«con arroz»**. La plantilla
   permite varios platos por receta; la versión «con arroz» debe sumar el arroz aparte.

## Pasos sugeridos con el cliente

1. Completar el **rendimiento de cada tanda** (cuánto pesa o mide la olla terminada) en la hoja «Recetas».
2. Rehacer las 8 fichas de formato distinto directamente en la plantilla (ingredientes, unidades y plato).
3. Confirmar qué fichas sin código de plato son **sub-recetas** (carne guisada, carne mechada) y cuál de las dos
   «pollo guisado» vale.
4. Cargar las sub-recetas #200, #202 y #203 (o agregarlas a la plantilla como SUB-RECETA).
5. En la app: **Simular** → **Guardar reporte** → completar e **Importar insumos faltantes** → definir **Gramos por
   ml** de los insumos medidos con taza → **Simular** de nuevo → **Importar**.

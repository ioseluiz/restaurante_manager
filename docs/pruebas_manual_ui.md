# Checklist de pruebas manuales de la UI — Italos Manager

> Guion para recorrer la app de punta a punta con datos conocidos y comparar cada pantalla con el resultado
> esperado. Los números salen del escenario de mayo 2026 explicado en `docs/calculos.md`; las pruebas
> automáticas (`tests/e2e/`) verifican los mismos valores sin interfaz. Este checklist cubre lo que solo se ve
> en pantalla: navegación, diálogos, tablas, exportaciones y permisos.

## Preparación

1. **Nunca** usar la base del cliente. Crear la base de prueba:
   `python scripts/crear_bd_prueba.py C:/temp/prueba_e2e.db`
2. `python main.py` → entrar como `admin` / `admin123` → **Configurar BD** → elegir `C:/temp/prueba_e2e.db`.
3. Usuarios de la base de prueba: `admin/admin123`, `gerente/gerente123`, `empleado/empleado123`.
4. La base trae: 6 insumos con presentación, sub-receta, 2 platos, la compra #1 **pendiente**, las ventas del
   10/05/2026 **sin procesar**, 2 empleados con una quincena, egresos de mayo y el diario de ventas del 10/05.
   También trae **junio 2026 completo** (5 870 platos en 30 días, diario de caja, dos quincenas y egresos del mes)
   para ver costos, rentabilidad y el Panel con volumen realista. Para sumarlo a una base creada antes:
   `python scripts/crear_bd_prueba.py C:/temp/prueba_e2e.db --agregar-junio`.
5. Marcar cada paso: ✅ correcto · ❌ distinto (anotar lo que se ve) · ⏭ no aplica.

Al terminar, restablecer la base original con **Configurar BD**.

---

## A. Arranque, sesión y ayuda

| # | Paso | Resultado esperado | ✓ |
|---|---|---|---|
| A1 | Abrir con `config.json` apuntando a un archivo inexistente o a un `._algo.db` | Mensaje con el motivo y opción de elegir otra base o la predeterminada; no se cierra solo | |
| A2 | Login con clave incorrecta | Rechaza el acceso | |
| A3 | Ver el título, la barra de estado y **Ayuda → Acerca de** | Misma versión (`app/version.py`) en los tres | |
| A4 | Abrir cada módulo y pulsar **F1** | Abre la guía de ese módulo; **Ctrl+F1** abre el índice | |

## B. Catálogo, unidades y sucursales

| # | Paso | Resultado esperado | ✓ |
|---|---|---|---|
| B1 | Catálogo de Insumos → lista | 6 insumos: Arroz, Pollo, Tomate, Aceite, Envase, Soda | |
| B2 | Presentaciones de Arroz | «Saco 10 kg», 10 000 g, $12.00, costo unitario 0.0012 | |
| B3 | Cambiar el precio del saco a $13.00 y volver a $12.00 | Historial de precios con dos registros; el último marcado como actual | |
| B3b | Crear «Saco 25 kg» de Arroz a $25 y marcarlo **Presentación preferida** | Columna Preferida ★ solo en el de 25 kg; Costo de Platos P1 baja a 1.06 (150 g × 0.0010). Volver a marcar el de 10 kg | |
| B4 | Unidades de Medida | g, ml, und; crear y borrar una de prueba | |
| B5 | Sucursales | Centro marcada como «esta sucursal», Norte sin marcar | |

## C. Compras e inventario

| # | Paso | Resultado esperado | ✓ |
|---|---|---|---|
| C1 | Compras → Registro: compra #1 | PENDIENTE, total $120.00 (24 + 60 + 6 + 8 + 10 + 12) | |
| C2 | **Marcar como RECIBIDO** → «Recibido = Pedido» | La columna «Entra al stock» muestra 20 000, 15 000, 4 000, 2 000, 50, 24 | |
| C3 | **Aplicar Recepción** | Compra RECIBIDO; mensaje de éxito | |
| C4 | Volver a intentar recibir la compra #1 | Aviso «ya fue recibida»; el stock no cambia | |
| C4b | Nueva compra de 1 caja de pollo a $30 con el pollo en stock negativo (procesar ventas antes de recibir) | Al recibirla, el costo del pollo queda en 0.006 (el de la compra) | |
| C5 | Inventario | Arroz 25 000 g a 0.00116 · Pollo 15 000 · Tomate 4 000 · Aceite 2 000 · Envase 50 · Soda 24 | |
| C6 | Inventario → Arroz → **Ver Movimientos (Kardex)** | Un movimiento COMPRA de +20 000 (anterior 5 000, nuevo 25 000) | |
| C7 | Panel de Control | Valor del inventario $125.00 | |
| C8 | Compras → Resumen Semanal y Mensual | La compra aparece en la semana/mes del 02/05/2026 por $120.00 | |
| C9 | Compras → Abastecimiento Interno: Centro → Norte, Pollo 1 000 g | Pollo 14 000 g; movimiento de salida en el Kardex | |
| C10 | Anular ese abastecimiento | Pollo vuelve a 15 000 g; el traslado queda ANULADO, no se borra | |
| C11 | Abastecimiento Norte → Norte | Error: origen y destino iguales | |

## D. Menú, recetas y costo de platos

| # | Paso | Resultado esperado | ✓ |
|---|---|---|---|
| D1 | Gestión de Menú | P1 $6.00 y P2 $5.50 (y los componentes si se muestran) | |
| D2 | Recetas (Fichas) → P1 | Pollo 200, Arroz 150 (la salsa está como sub-receta en Costo de Platos) | |
| D3 | Costo de Platos → Costo por plato, canal local | P1 1.09 · P2 1.56 | |
| D4 | Canal para llevar | P1 1.29 (con envase) · P2 1.56 | |
| D5 | Doble clic en P1 → desglose | Pollo 0.80 · Arroz 0.18 · Salsa 0.11; sin advertencias | |
| D6 | Precio sugerido P1 | Local 1.56 (30 %) · Para llevar 2.58 (50 %) | |
| D7 | Food cost P1 local | 18.2 %, margen $4.91 | |
| D8 | Parámetros → fuente «Promedio» → Actualizar | P1 ingredientes 1.08 (arroz a 0.00116). Volver a «Vigente» | |
| D9 | Indirectos de mayo 2026 (tras procesar las ventas, paso E3) | $66.87 por plato (2 006.23 / 30) | |
| D9b | Parámetros → Base de gastos indirectos | Opciones «Gastos reales del mes (consolidados)» y «Gastos fijos del presupuesto del mes (planilla real)» | |
| D9c | Parámetros → % de platos para llevar = 40 → Guardar; Reabrir Día 10/05 y volver a Actualizar Inventario | Envase baja de 50 a 46 (10 P1 × 40 %); la soda no cambia | |
| D10 | Exportar (Excel / CSV) | El archivo abre y trae los mismos valores de la tabla | |
| D12 | Costo de Platos → junio 2026 | Indirectos $1.05 por plato = (gastos 4 260 + planilla 1 892.47) ÷ 5 870 platos (ventas diarias). P1 local: total 2.14 · food cost 35.6 % · sugerido 3.05 | |
| D11 | Análisis de Precios → Arroz | Muestra la evolución del precio (incluye el cambio de B3) | |

## E. Ventas

| # | Paso | Resultado esperado | ✓ |
|---|---|---|---|
| E1 | Ventas → Ventas diarias → 10/05/2026 → Cargar Datos | P1 10 y P2 20 | |
| E2 | **Actualizar Inventario (Kardex)** | Mensaje con 4 movimientos, sin platos sin receta | |
| E3 | Inventario | Pollo 9 000 · Arroz 20 500 · Tomate 3 400 · Aceite 1 550 · Soda 24 y Envase 50 (con 0 % para llevar no se descuentan empaques) | |
| E4 | Pulsar otra vez «Actualizar Inventario» | Aviso «ya fue procesado»; no descuenta dos veces | |
| E5 | **Reabrir Día** | Vuelven los valores de C5; Kardex con REVERSO_VENTA | |
| E6 | Volver a procesar el día | Mismos valores de E3 | |
| E7 | Ventas → Carga de reportes: cargar `assets/datos_presupuesto_2025/REPORTE EJEMPLO PROM DE VENTAS X PLATO ITALOS (2).csv` | Desde 01/09/2025, hasta 07/11/2025, 12.16 % sugerido, 606 filas. Estim/Med = Prom × 1.1216 (ej. #IC002 jueves: .22 → .25) | |
| E8 | Guardar el reporte y abrir el historial | El reporte aparece con su período y total B/. 100 899.98 | |

## F. Toma de inventario

| # | Paso | Resultado esperado | ✓ |
|---|---|---|---|
| F1 | Nueva Sesión de Conteo (categoría Víveres) | Genera el Excel con Arroz, Tomate y Aceite y su stock teórico | |
| F2 | Ingresar Conteo: Arroz 20 400, el resto igual al teórico | Diferencia Arroz −100 | |
| F3 | Revisión y Aprobación → aprobar → **Aplicar Ajustes y Cerrar Sesión** | Arroz 20 400; Kardex AJUSTE_INVENTARIO −100; sesión CERRADO | |
| F4 | Exportar el conteo a PDF/Excel | Archivo con las mismas cifras | |

## G. Etiquetas y códigos

| # | Paso | Resultado esperado | ✓ |
|---|---|---|---|
| G1 | Generar Código Interno para «Saco 10 kg» | Código nuevo asociado a la presentación | |
| G2 | Imprimir Etiqueta(s) | PDF con el código legible por el escáner | |
| G3 | Crear una compra de Arroz y, en la recepción, escanear el código | Suma 1 saco en «Recibido» | |

## H. Presupuestos

| # | Paso | Resultado esperado | ✓ |
|---|---|---|---|
| H1 | Cargar un reporte POS de prueba con 10 % sugerido: P1 lunes Prom 2, martes 3; P2 lunes 4 (o reutilizar el de E7 y comparar con el detalle de cálculo) | — | |
| H2 | Nuevo Presupuesto mayo 2026 con ese reporte | Pollo 2 cajas $40 · Arroz 1 saco $12 · Tomate 1 caja $3 · Aceite 1 botella $4 · total $59.00 | |
| H3 | Ver / Editar Insumos → «Detalle» de Pollo | Fórmula 20 platos × 200 g × 1.10 + 16 × 200 × 1.10 = 7 920 g → 2 cajas | |
| H4 | 🔄 Recalcular con Precios Actuales | Mismo resultado que H2 | |
| H5 | Ajustar % de Arroz a 20 % → recalcular | Se conserva el 20 %; el resto igual | |
| H6 | Planilla → Copiar de período (1ra quincena mayo), solo Ana | Costo $564.61 | |
| H7 | Gastos → Alquiler 800 y Luz (electricidad) 140 | Total gastos $940.00 | |
| H8 | Vincular la compra #1 al presupuesto (Editar compra) → Control Presupuestal | Carnes 40 / 60 · Víveres 19 / 38 · Sin categoría 0 / 22 · Planilla 564.61 / 946.23 · Gastos 940 / 1 060 | |
| H9 | Resumen bajo el árbol del control | Presupuestado, ejecutado y saldo global; en rojo si está excedido | |

## I. Consolidados

| # | Paso | Resultado esperado | ✓ |
|---|---|---|---|
| I1 | Diario de Ventas 10/05/2026 | Total $201.00 (20 + 30 + 40 + 50 + 60.5 + 1 − 0.5) | |
| I2 | Editar el faltante a 1.50 y guardar | Total $200.00; volver a 0.50 | |
| I3 | Chequera mayo | Inmobiliaria 800 (Alquiler) y Carnes del Istmo 300 (sin tipo de gasto) | |
| I4 | Tarjetas de Crédito mayo | Compra 60 (Internet) y Pago 500 | |
| I5 | Pagos en Efectivo 08/05 | Total 270: víveres 120, carnes 100, otros 50 (Gas) | |
| I6 | Pagos con Yappy mayo | Naturgy 150 (Luz) | |
| I7 | Resumen General mayo 2026 | Totales por canal coherentes con I1–I6 | |

## J. Rentabilidad

| # | Paso | Resultado esperado | ✓ |
|---|---|---|---|
| J1 | Mayo 2026 | Ventas 201.00 · Costo real 220.00 · Costo teórico 32.10 · Merma 187.90 · Ref. con extras 42.10 (en gris) | |
| J2 | Gastos | Planilla 900 · Otros 50 · Cheques 1 100 · Yappy 150 · Tarjetas 60 · total 2 260 | |
| J3 | Utilidad | Bruta −19.00 · Neta −2 279.00 | |
| J4 | Comparativo anual 2026 | Mayo y junio con datos; junio: ventas 33 795 · costo real 10 000 · gastos 6 060 · utilidad neta 17 735 | |
| J5 | Compras por categoría (referencia) | Carnes 60 · Víveres 38 · Sin categoría 22 | |
| J6 | Panel de Control → ◀ hasta Mayo 2026 | Ventas del Mes $201.00 · Utilidad −2 279.00 · Top: Arroz con pollo 20, Pollo con arroz 10 · barra de mayo destacada; «Mes actual» vuelve al de hoy y ▶ queda inactivo | |

## K. Planilla

| # | Paso | Resultado esperado | ✓ |
|---|---|---|---|
| K1 | Períodos de Pago → 1ra quincena mayo → horas | Ana 88 / dom 8 / extra diurna 4 · Luis 96 | |
| K2 | Resumen de Planilla → Calcular | Ana bruto 420.00, deducciones 46.20, neto 373.80, costo total 564.61 · Luis bruto 288.00, costo total 381.63 | |
| K3 | Provisiones | Ana XIII 34.99, vacaciones 34.99, prima 8.06 · Luis sin prima | |
| K4 | Vales: vale de $20 a Ana, abono en la quincena → recalcular | Neto de Ana baja $20; el costo para la empresa no cambia | |
| K5 | Exportar Excel y PDF | Mismas cifras que la pantalla | |
| K6 | Configuración: cambiar riesgo profesional a 2.50 % → Calcular | Costo de Ana 566.29; volver a 2.10 % | |

## L. Usuarios y permisos

| # | Paso | Resultado esperado | ✓ |
|---|---|---|---|
| L1 | Entrar como `admin` | Ve «Gestión de Usuarios» y «Configurar BD» | |
| L2 | Entrar como `gerente` | No ve esos dos módulos | |
| L3 | Entrar como `empleado` | No ve esos dos módulos. Arranca en Ventas; no ve Panel, Presupuestos, Consolidados, Rentabilidad, Costo de Platos, Análisis de Precios, Planilla ni Sucursales | |
| L4 | Crear, editar y borrar un usuario de prueba | Cambios guardados; el usuario borrado no entra | |

## M. Configurar BD

| # | Paso | Resultado esperado | ✓ |
|---|---|---|---|
| M1 | Crear copia de respaldo | Archivo .db nuevo que abre con los mismos datos | |
| M2 | Elegir un archivo que no es base de datos | Rechazo con el motivo; la base en uso no cambia | |

---

## Registro de la corrida

| Fecha | Versión | Quién | ✅ | ❌ | Notas |
|---|---|---|---|---|---|
| | | | | | |

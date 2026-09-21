# Planilla

Calcula la **nómina** de los empleados por período de pago, con las reglas laborales de Panamá, y el **costo total** de la mano de obra. Tiene seis pestañas:

| Pestaña | Para qué sirve |
|---|---|
| **Empleados** | Alta y datos de cada empleado (salario por hora, sucursal, tipo de contrato) |
| **Períodos de Pago** | Crear cada quincena y registrar las horas trabajadas |
| **Vales** | Adelantos a empleados y su descuento en planilla |
| **Resumen de Planilla** | El cálculo del período: salarios, deducciones y costo total |
| **Provisiones** | Pasivo laboral acumulado (décimo tercer mes, vacaciones, prima de antigüedad) |
| **Configuración** | Recargos por tipo de hora, porcentajes de deducciones e ISR |

## Antes de empezar

1. Revise la **Configuración** (recargos, porcentajes, tabla de ISR) antes del primer cálculo.
2. Registre a los empleados en **Empleados**. El **tipo de contrato** (indefinido o definido) afecta las provisiones.

## Calcular una quincena

1. **Períodos de Pago** → cree el período con su **nombre** (ej. «Quincenal 1-15 Enero 2025»), **fecha de inicio y fin** y **sucursal**.
2. Registre las horas de cada empleado: **regulares, festivos, domingos, extra diurnas y extra nocturnas**. Haga **doble clic** en una celda de horas u observación para editarla.
3. Si hay **vales** pendientes (se registran en la pestaña Vales), anote en el período el monto a descontar (**Descuentos de Vales**, con **Guardar Abonos de Vales**). Otras deducciones se agregan con **+ Agregar Deducción**.
4. Abra el **Resumen de Planilla**, elija el período y pulse **Calcular Planilla** para ver salario bruto, deducciones del empleado, aportes patronales y **costo total**. Use **Exportar Excel** o **Exportar PDF** para sacar el reporte.

## Configuración

- **Recargos por tipo de hora:** edite el multiplicador en la columna «Recargo»; se aplica sobre (horas × salario por hora).
- **Porcentajes de deducciones:** seguro social, seguro educativo, aportes del empleador y provisiones.
- **Tabla de ISR:** tramos anuales de renta gravable, con su tasa e impuesto fijo.

## Provisiones

Son pasivos que se acumulan aunque todavía no se paguen. La pestaña permite ver lo acumulado por empleado y registrar los **pagos** (por ejemplo, el décimo tercer mes).

## Vales

Un vale puede **vincularse con el Diario de Ventas** de [Consolidados](ayuda:consolidados) (opcional) para saber en qué cierre se entregó.

## Relación con otros módulos

El **costo total** de este resumen es el mismo que usa el bloque de planilla del [Presupuesto](ayuda:presupuestos) (y su control de ejecución) y los indirectos de [Costo de Platos](ayuda:costo_platos).

# [FILE: app/utils/diario_ventas_calc.py]
"""Fórmula del TOTAL VENTAS del Diario de Ventas (Consolidados). Sin dependencias de Qt."""


def total_ventas_diario(yappy=0.0, pedidos_ya=0.0, clave=0.0, visa_mastercard=0.0, efectivo=0.0,
                        vale=0.0, sobrante=0.0, faltante=0.0):
    """TOTAL VENTAS = cobros por método (Yappy, Pedidos Ya, Clave, Visa/MC, efectivo) + vale
    + sobrante de caja - faltante de caja.

    El sobrante y el faltante se escriben como montos positivos: el sobrante aumenta lo cobrado
    y el faltante lo disminuye (cuadre de caja).
    """
    return (float(yappy or 0) + float(pedidos_ya or 0) + float(clave or 0) + float(visa_mastercard or 0)
            + float(efectivo or 0) + float(vale or 0) + float(sobrante or 0) - float(faltante or 0))

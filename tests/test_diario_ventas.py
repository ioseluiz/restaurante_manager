import pytest

from app.utils.diario_ventas_calc import total_ventas_diario


def test_suma_metodos_de_cobro_y_vale():
    assert total_ventas_diario(yappy=10, pedidos_ya=20, clave=30, visa_mastercard=40, efectivo=50,
                               vale=5) == pytest.approx(155)


def test_sobrante_suma_y_faltante_resta():
    base = dict(yappy=100, efectivo=200)
    assert total_ventas_diario(**base, sobrante=7) == pytest.approx(307)
    assert total_ventas_diario(**base, faltante=7) == pytest.approx(293)
    assert total_ventas_diario(**base, sobrante=10, faltante=4) == pytest.approx(306)


def test_valores_vacios_cuentan_como_cero():
    assert total_ventas_diario(None, None) == 0.0

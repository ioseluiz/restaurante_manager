"""La base de prueba del checklist manual: mayo como el escenario E2E y junio completo con volumen realista."""
import os
import sys

import pytest

from app.controllers.costeo_controller import CosteoController
from app.controllers.rentabilidad_controller import RentabilidadController
from app.database.connection import DatabaseManager

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
import crear_bd_prueba  # noqa: E402

approx = pytest.approx


def test_base_de_prueba_trae_junio_completo(tmp_path):
    ruta = tmp_path / "prueba.db"
    crear_bd_prueba.main(str(ruta))
    db = DatabaseManager(str(ruta))

    pool = CosteoController(db).pool_indirectos(6, 2026)
    assert pool["platos"] == 5870 and pool["fuente_platos"] == "ventas diarias"
    assert pool["por_plato"] == approx((4260 + 2 * 946.2348) / 5870)

    pyl = RentabilidadController(db).pyl_mensual(2026, 6)
    assert pyl["ventas"] == approx(33795) and pyl["costo_real"] == approx(10000)
    assert pyl["utilidad_neta"] == approx(17735)
    # Identidad propia, para no confundirla con la base de un restaurante real
    from app.controllers.restaurante_controller import RestauranteController
    assert RestauranteController(db).etiqueta() == "Italos (prueba) · Centro"
    # Mayo no cambia
    assert RentabilidadController(db).pyl_mensual(2026, 5)["utilidad_neta"] == approx(-2279)

    with pytest.raises(SystemExit):  # junio no se carga dos veces
        crear_bd_prueba.agregar_junio(db)

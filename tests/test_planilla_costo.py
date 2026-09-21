import pytest

from app.database.connection import DatabaseManager
from app.utils.calculo_planilla import calcular_costo, calcular_costo_empleado, cargar_config
from app.utils.gastos_reales import calcular_planilla_real_mes


@pytest.fixture
def db(tmp_path):
    return DatabaseManager(str(tmp_path / "t.db"))


def _empleado(db, contrato, salario=5.0):
    return db.execute_query(
        "INSERT INTO empleados (nombre, apellido, salario_hora, tipo_contrato) VALUES ('A','B',?,?)",
        (salario, contrato),
    ).lastrowid


def _periodo_con_horas(db, empleado, inicio="2026-05-01", fin="2026-05-15", regulares=80):
    pid = db.execute_query(
        "INSERT INTO periodos_pago (nombre, fecha_inicio, fecha_fin) VALUES ('Q', ?, ?)", (inicio, fin)
    ).lastrowid
    db.execute_query(
        "INSERT INTO horas_empleado (empleado_id, periodo_id, horas_regulares) VALUES (?,?,?)",
        (empleado, pid, regulares),
    )
    return pid


HORAS = {"horas_regulares": 80}


def test_costo_completo_incluye_riesgos_y_provisiones(db):
    _, pcts = cargar_config(db)
    c = calcular_costo_empleado(db, 5.0, HORAS, tipo_contrato="INDEFINIDO")
    bruto = 400.0
    esperado = bruto * (1 + (pcts["seguro_social_empleador"] + pcts["seguro_educativo_empleador"]
                             + pcts["riesgos_profesionales_empleador"] + pcts["provision_decimo"]
                             + pcts["provision_vacaciones"] + pcts["provision_prima_antiguedad"]) / 100)
    assert c["costo_total_completo"] == pytest.approx(esperado)
    # y es mayor que el cálculo simple (bruto + SS + SE patronales)
    recargos, _ = cargar_config(db)
    assert c["costo_total_completo"] > calcular_costo(5.0, HORAS, recargos, pcts)["costo_total"]


def test_prima_de_antiguedad_solo_para_contrato_indefinido(db):
    ind = calcular_costo_empleado(db, 5.0, HORAS, tipo_contrato="INDEFINIDO")
    definido = calcular_costo_empleado(db, 5.0, HORAS, tipo_contrato="DEFINIDO")
    assert definido["provision_prima"] == 0
    assert ind["costo_total_completo"] - definido["costo_total_completo"] == pytest.approx(ind["provision_prima"])


def test_el_tipo_de_contrato_se_toma_del_empleado(db):
    emp = _empleado(db, "DEFINIDO")
    c = calcular_costo_empleado(db, 5.0, HORAS, empleado_id=emp)
    assert c["provision_prima"] == 0
    assert calcular_costo_empleado(db, 5.0, HORAS)["provision_prima"] > 0   # sin empleado: INDEFINIDO


def test_planilla_real_del_mes_usa_el_costo_completo(db):
    emp = _empleado(db, "INDEFINIDO")
    _periodo_con_horas(db, emp)
    esperado = calcular_costo_empleado(db, 5.0, HORAS, tipo_contrato="INDEFINIDO")["costo_total_completo"]
    assert calcular_planilla_real_mes(db, 5, 2026) == pytest.approx(esperado)
    assert calcular_planilla_real_mes(db, 6, 2026) == 0.0


def test_planilla_real_respeta_el_contrato_de_cada_empleado(db):
    _periodo_con_horas(db, _empleado(db, "DEFINIDO"))
    definido = calcular_costo_empleado(db, 5.0, HORAS, tipo_contrato="DEFINIDO")["costo_total_completo"]
    assert calcular_planilla_real_mes(db, 5, 2026) == pytest.approx(definido)


def test_el_presupuesto_tiene_columna_provisiones(db):
    cols = [r[1] for r in db.fetch_all("PRAGMA table_info(detalle_presupuesto_planilla)")]
    assert "provisiones" in cols

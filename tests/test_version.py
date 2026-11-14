import importlib.util
import os
import re

import pytest

from app import version

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _cargar_estampador():
    spec = importlib.util.spec_from_file_location(
        "estampar_version", os.path.join(RAIZ, "scripts", "estampar_version.py"))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_la_version_del_codigo_tiene_formato_valido():
    assert re.fullmatch(r"\d+\.\d+\.\d+(-[0-9A-Za-z.]+)?|dev-[0-9A-Za-z.-]+", version.__version__)


def test_etiqueta_y_prerelease():
    assert version.etiqueta_version("1.3.0") == "v1.3.0"
    assert version.etiqueta_version("1.3.0-beta.1") == "v1.3.0-beta.1"
    assert version.etiqueta_version("dev-12-abc1234") == "dev-12-abc1234"
    assert not version.es_prerelease("1.3.0")
    assert version.es_prerelease("1.3.0-rc.1") and version.es_prerelease("dev-1-abc")


def test_estampar_reemplaza_solo_la_linea_de_version(tmp_path):
    est = _cargar_estampador()
    f = tmp_path / "version.py"
    f.write_text('"""doc"""\n\n__version__ = "1.0.0"\n\n\ndef otra():\n    return 1\n', encoding="utf-8")
    assert est.estampar("v1.4.0-rc.1", str(f)) == "1.4.0-rc.1"        # acepta el tag con «v»
    texto = f.read_text(encoding="utf-8")
    assert '__version__ = "1.4.0-rc.1"' in texto and "def otra()" in texto and '"""doc"""' in texto
    assert est.estampar("dev-7-abc1234", str(f)) == "dev-7-abc1234"


def test_estampar_rechaza_versiones_invalidas(tmp_path):
    est = _cargar_estampador()
    f = tmp_path / "version.py"
    f.write_text('__version__ = "1.0.0"\n', encoding="utf-8")
    for mala in ("latest-dev", "1.2", "v1.2.x", '1.0.0"; import os'):
        with pytest.raises(ValueError):
            est.estampar(mala, str(f))
    assert f.read_text(encoding="utf-8") == '__version__ = "1.0.0"\n'


def test_estampar_funciona_sobre_el_version_py_real(tmp_path):
    """El patrón del script debe encontrar la línea en el archivo real (si no, el CI fallaría)."""
    est = _cargar_estampador()
    copia = tmp_path / "version.py"
    copia.write_text(open(os.path.join(RAIZ, "app", "version.py"), encoding="utf-8").read(), encoding="utf-8")
    assert est.estampar("9.9.9", str(copia)) == "9.9.9"


def test_el_workflow_publica_prerelease_para_tags_con_sufijo():
    with open(os.path.join(RAIZ, ".github", "workflows", "build.yml"), encoding="utf-8") as f:
        yml = f.read()
    assert "prerelease: ${{ contains(steps.version.outputs.VERSION, '-') }}" in yml
    # la versión debe determinarse y estamparse ANTES de compilar con PyInstaller
    assert yml.index("Determinar version") < yml.index("Estampar la version") < yml.index("pyinstaller main.spec")

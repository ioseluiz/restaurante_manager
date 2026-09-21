"""Escribe la versión en app/version.py (lo usa el CI antes de compilar).

    python scripts/estampar_version.py v1.3.0-beta.1     # -> __version__ = "1.3.0-beta.1"
    python scripts/estampar_version.py dev-12-abc1234    # -> __version__ = "dev-12-abc1234"

Acepta el tag con o sin la «v» inicial. Reemplaza solo la línea `__version__ = "..."`.
"""

import os
import re
import sys

ARCHIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app", "version.py")
_VALIDA = re.compile(r"^(\d+\.\d+\.\d+(-[0-9A-Za-z.]+)?|dev-[0-9A-Za-z.-]+)$")


def normalizar(version):
    v = str(version).strip()
    if re.match(r"^v\d", v):
        v = v[1:]
    if not _VALIDA.match(v):
        raise ValueError(f"Versión no válida: {version!r} (esperado X.Y.Z, X.Y.Z-sufijo o dev-…)")
    return v


def estampar(version, archivo=ARCHIVO):
    v = normalizar(version)
    with open(archivo, encoding="utf-8") as f:
        texto = f.read()
    nuevo, n = re.subn(r'(?m)^__version__ = ".*"$', f'__version__ = "{v}"', texto)
    if n != 1:
        raise RuntimeError("No se encontró la línea __version__ en app/version.py")
    with open(archivo, "w", encoding="utf-8", newline="") as f:
        f.write(nuevo)
    return v


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    print(f"Versión estampada: {estampar(sys.argv[1])}")

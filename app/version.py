# [FILE: app/version.py]
"""Versión de la aplicación (única fuente).

El flujo de CI (.github/workflows/build.yml) REEMPLAZA este valor antes de compilar:
  - build de un tag `vX.Y.Z[-sufijo]`  -> "X.Y.Z[-sufijo]"
  - build de la rama main               -> "dev-<n° de corrida>-<sha corto>"
De ese modo el ejecutable siempre muestra la versión de su tag. Al trabajar desde el código fuente se
ve el valor de este archivo: actualícelo cuando prepare una versión nueva (ver docs/versiones.md).
"""

__version__ = "1.3.0-beta.1"


def etiqueta_version(version=None):
    """Texto para mostrar: «v1.3.0-beta.1»; las versiones de desarrollo («dev-12-abc1234») van tal cual."""
    v = str(version if version is not None else __version__).strip()
    return f"v{v}" if v[:1].isdigit() else v


def es_prerelease(version=None):
    """True si la versión lleva sufijo (beta, rc…) o es de desarrollo."""
    v = str(version if version is not None else __version__).strip()
    return "-" in v or not v[:1].isdigit()

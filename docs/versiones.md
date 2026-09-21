# Versiones y publicación

## Dónde se ve la versión

- **Título de la ventana:** «Sistema de Gestión de Restaurante — v1.3.0-beta.1».
- **Barra de estado** (abajo a la derecha).
- **Ayuda → Acerca de Italos Manager…**, que además muestra la base de datos en uso.

Pida esta versión al usuario cuando reporte un problema.

## Cómo se define

La versión vive en un solo archivo: `app/version.py` (`__version__`).

- **Ejecutable publicado:** el CI (`.github/workflows/build.yml`) **reemplaza** `__version__` con la del tag
  antes de compilar (`scripts/estampar_version.py`), así que el instalador siempre muestra la versión de su tag.
  Un build de la rama `main` muestra `dev-<n° de corrida>-<sha>`.
- **Desde el código fuente:** se ve el valor escrito en `app/version.py`; actualícelo al preparar una versión.

Formato: `X.Y.Z` (versión oficial) o `X.Y.Z-sufijo` (por ejemplo `1.3.0-beta.1`, `1.3.0-rc.1`).

## Publicar una versión

1. Actualice `__version__` en `app/version.py` y haga commit.
2. Cree y suba el tag con una «v» delante:

```
git tag v1.3.0-beta.1
git push origin v1.3.0-beta.1
```

3. El CI compila el ejecutable y el instalador (`ItalosManager_Setup.exe`) y crea el release en GitHub:
   - tag **con sufijo** (`v1.3.0-beta.1`, `v1.3.0-rc.1`) → release marcado como **pre-release**;
   - tag **sin sufijo** (`v1.3.0`) → release **oficial**.
4. Un push a `main` además actualiza el pre-release `latest-dev` con el último build de desarrollo.

## Numeración sugerida

- Correcciones: `1.3.1`. Funciones nuevas compatibles: `1.4.0`. Cambios que exigen migrar datos o rehacer costumbres: `2.0.0`.
- Pruebas con usuarios antes de liberar: `-beta.N`; candidata final: `-rc.N`.

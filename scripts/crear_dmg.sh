#!/bin/bash
# Crea el instalador de macOS (DMG) a partir de dist/Italos Manager.app (generado con `pyinstaller main.spec`).
# Instalar = abrir el DMG y arrastrar «Italos Manager» a la carpeta Aplicaciones.
#
#   scripts/crear_dmg.sh            -> installer_output/ItalosManager_mac_arm64.dmg
set -euo pipefail

cd "$(dirname "$0")/.."
APP="dist/Italos Manager.app"
SALIDA="installer_output/ItalosManager_mac_arm64.dmg"

if [ ! -d "$APP" ]; then
    echo "No existe $APP: ejecute primero 'pyinstaller main.spec'" >&2
    exit 1
fi

STAGING="$(mktemp -d)"
trap 'rm -rf "$STAGING"' EXIT
cp -R "$APP" "$STAGING/"
ln -s /Applications "$STAGING/Aplicaciones"

mkdir -p installer_output
rm -f "$SALIDA"
hdiutil create -volname "Italos Manager" -srcfolder "$STAGING" -ov -format UDZO "$SALIDA"
echo "Instalador creado: $SALIDA"

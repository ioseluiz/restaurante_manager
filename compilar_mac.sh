#!/bin/bash
# Compila Italos Manager para macOS (Apple Silicon) y crea el instalador DMG.
#
#   python3 -m venv venv && source venv/bin/activate && pip install -r requirements-build.txt
#   ./compilar_mac.sh
#
# Resultado: dist/Italos Manager.app e installer_output/ItalosManager_mac_arm64.dmg (sin firmar: la primera
# vez se abre con clic derecho -> Abrir; ver README).
set -euo pipefail
cd "$(dirname "$0")"

echo "== Compilando Italos Manager con PyInstaller =="
rm -rf build dist
pyinstaller --noconfirm main.spec

echo "== Prueba de humo del ejecutable =="
QT_QPA_PLATFORM=offscreen "dist/Italos Manager.app/Contents/MacOS/RestauranteManager" --smoke

echo "== Creando el DMG =="
scripts/crear_dmg.sh

# -*- mode: python ; coding: utf-8 -*-
# Un solo spec para Windows (carpeta con RestauranteManager.exe -> Inno Setup) y macOS (Italos Manager.app -> DMG).
import re
import sys

from PyInstaller.utils.hooks import collect_submodules

ES_MAC = sys.platform == "darwin"

# Versión estampada por scripts/estampar_version.py (se muestra en «Acerca de» del Finder)
with open("app/version.py", encoding="utf-8") as _f:
    VERSION = re.search(r'__version__\s*=\s*"([^"]+)"', _f.read()).group(1)


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets')],
    hiddenimports=[
        'matplotlib.backends.backend_qt5agg',
        'matplotlib.backends.backend_agg',
        'PyQt5.sip',
        'openpyxl',
        # reportlab importa los tipos de código de barras con exec(): PyInstaller no los detecta solo
        *collect_submodules('reportlab.graphics.barcode'),
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='RestauranteManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=not ES_MAC,  # UPX daña los binarios arm64 de macOS
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64' if ES_MAC else None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icons/app.icns' if ES_MAC else 'assets/icons/app.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=not ES_MAC,
    upx_exclude=[],
    name='RestauranteManager',
)

if ES_MAC:
    app = BUNDLE(
        coll,
        name='Italos Manager.app',
        icon='assets/icons/app.icns',
        bundle_identifier='com.italos.restaurantemanager',
        version=VERSION,
        info_plist={
            'CFBundleName': 'Italos Manager',
            'CFBundleDisplayName': 'Italos Manager',
            'CFBundleShortVersionString': VERSION,
            'CFBundleVersion': VERSION,
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '11.0',
            # Las hojas de estilo son claras: la app no sigue el modo oscuro del sistema
            'NSRequiresAquaSystemAppearance': True,
            'CFBundleDevelopmentRegion': 'es',
        },
    )

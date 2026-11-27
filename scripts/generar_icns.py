"""Genera assets/icons/app.icns (ícono del .app de macOS) a partir de assets/icons/app.ico.

    python scripts/generar_icns.py

Usa Pillow, así que funciona en Windows y macOS. El .icns resultante se versiona en el repositorio; solo
hace falta volver a generarlo si cambia app.ico. El .ico llega a 256 px: los tamaños mayores se escalan.
"""

import os
import sys

from PIL import Image

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ORIGEN = os.path.join(RAIZ, "assets", "icons", "app.ico")
DESTINO = os.path.join(RAIZ, "assets", "icons", "app.icns")


def main():
    ico = Image.open(ORIGEN)
    mayor = max(ico.info.get("sizes", {ico.size}))
    ico.size = mayor  # el cuadro más grande del .ico
    ico.load()
    base = ico.convert("RGBA").resize((1024, 1024), Image.LANCZOS)
    base.save(DESTINO, format="ICNS",
              append_images=[base.resize((s, s), Image.LANCZOS) for s in (16, 32, 64, 128, 256, 512)])
    print(f"Ícono generado: {os.path.abspath(DESTINO)}  (desde {mayor[0]}×{mayor[1]} px)")


if __name__ == "__main__":
    sys.exit(main())

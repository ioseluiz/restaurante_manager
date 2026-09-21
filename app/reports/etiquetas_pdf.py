"""Generación de etiquetas de inventario con código QR (impresión térmica).

Cada etiqueta se emite en su propia página, dimensionada al tamaño del rollo
térmico (por defecto 50x30 mm), lista para una impresora de etiquetas. El QR
codifica el código interno/único del insumo; a su lado se imprime el nombre, la
presentación y el peso estándar, y bajo el QR el código legible (respaldo si el
QR llega a dañarse).
"""
import os
import tempfile

from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF


_DARK = colors.HexColor("#2c3e50")
_RED = colors.HexColor("#a20f22")


def _texto_ajustado(c, texto, x, y, max_width, font="Helvetica", size=7,
                    color=_DARK, max_lines=2, leading=None):
    """Dibuja `texto` con ajuste de línea simple dentro de `max_width`.

    Devuelve la coordenada Y tras la última línea escrita.
    """
    if leading is None:
        leading = size + 1.5
    c.setFont(font, size)
    c.setFillColor(color)

    palabras = (texto or "").split()
    lineas = []
    actual = ""
    for palabra in palabras:
        prueba = f"{actual} {palabra}".strip()
        if c.stringWidth(prueba, font, size) <= max_width:
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = palabra
        if len(lineas) >= max_lines:
            break
    if actual and len(lineas) < max_lines:
        lineas.append(actual)

    # Recorte con elipsis si excede max_lines
    if palabras and len(lineas) == max_lines:
        ultima = lineas[-1]
        while ultima and c.stringWidth(ultima + "…", font, size) > max_width:
            ultima = ultima[:-1]
        # Si aún quedaban palabras sin colocar, marca el recorte
        colocadas = " ".join(lineas)
        if len(colocadas.split()) < len(palabras):
            lineas[-1] = (ultima + "…") if ultima else "…"

    for linea in lineas:
        c.drawString(x, y, linea)
        y -= leading
    return y


def generar_pdf_etiquetas(items, ancho_mm=50, alto_mm=30, ruta=None):
    """Genera un PDF con una etiqueta QR por página.

    items: lista de dicts con claves:
        codigo        str   (obligatorio; se codifica en el QR)
        nombre        str   (obligatorio)
        presentacion  str   (opcional)
        peso_texto    str   (opcional; p.ej. "50 lb" / "1 kg")
        categoria     str   (opcional)
        fecha         str   (opcional)
    Devuelve la ruta del PDF generado.
    """
    if ruta is None:
        ruta = os.path.join(tempfile.gettempdir(), "etiquetas_inventario.pdf")

    ancho = ancho_mm * mm
    alto = alto_mm * mm
    margen = 2 * mm

    c = canvas.Canvas(ruta, pagesize=(ancho, alto))

    for item in items or []:
        codigo = str(item.get("codigo", "")).strip()
        nombre = item.get("nombre", "")

        # ── QR (columna izquierda, cuadrado) ──────────────────────────────────
        # Reserva espacio bajo el QR para el código legible.
        code_h = 8
        qr_lado = min(alto - 2 * margen - code_h, (ancho - 2 * margen) * 0.5)
        qr_lado = max(qr_lado, 10 * mm)

        widget = qr.QrCodeWidget(codigo or " ")
        b = widget.getBounds()
        w = b[2] - b[0]
        h = b[3] - b[1]
        d = Drawing(qr_lado, qr_lado, transform=[qr_lado / w, 0, 0, qr_lado / h, 0, 0])
        d.add(widget)

        qr_x = margen
        qr_y = alto - margen - qr_lado
        renderPDF.draw(d, c, qr_x, qr_y)

        # Código legible bajo el QR
        c.setFont("Helvetica", 5.5)
        c.setFillColor(_DARK)
        c.drawCentredString(qr_x + qr_lado / 2, qr_y - 6, codigo)

        # ── Texto (columna derecha) ───────────────────────────────────────────
        tx = qr_x + qr_lado + 2 * mm
        max_w = ancho - tx - margen
        ty = alto - margen - 6

        ty = _texto_ajustado(c, nombre, tx, ty, max_w,
                            font="Helvetica-Bold", size=7.5, color=_RED,
                            max_lines=2)
        ty -= 1

        presentacion = item.get("presentacion")
        if presentacion:
            ty = _texto_ajustado(c, presentacion, tx, ty, max_w,
                                font="Helvetica", size=6.5, max_lines=1)

        peso = item.get("peso_texto")
        if peso:
            c.setFont("Helvetica-Bold", 7)
            c.setFillColor(_DARK)
            c.drawString(tx, ty, f"Peso: {peso}")
            ty -= 9

        categoria = item.get("categoria")
        if categoria:
            c.setFont("Helvetica-Oblique", 5.5)
            c.setFillColor(colors.HexColor("#666666"))
            c.drawString(tx, ty, categoria)

        c.showPage()

    c.save()
    return ruta

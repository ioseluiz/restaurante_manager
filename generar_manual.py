"""
Genera el Manual de Usuario en PDF a partir de la ayuda en pantalla (assets/ayuda/*.md).

Una sola fuente de verdad: lo que dice el manual es exactamente lo que muestra F1 en la aplicación.
Para cambiar el manual, edite el .md del módulo y vuelva a ejecutar:

    python generar_manual.py

Salida: docs/Manual_de_Usuario_ItalosManager.pdf
(El generador anterior, con texto escrito a mano, quedó en docs/legacy como referencia obsoleta.)
"""

import datetime
import hashlib
import os
import re
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app.utils import ayuda  # noqa: E402  (sin dependencias de Qt)

# ── Colores corporativos ─────────────────────────────────────────────────────
ROJO = colors.HexColor("#a20f22")
DORADO = colors.HexColor("#db9930")
AZUL = colors.HexColor("#2980b9")
GRIS = colors.HexColor("#7f8c8d")
GRIS_C = colors.HexColor("#ecf0f1")
OSCURO = colors.HexColor("#2c3e50")
NARANJA = colors.HexColor("#d0741d")
BLANCO = colors.white

PAGE_W, PAGE_H = A4
ANCHO_UTIL = PAGE_W - 4 * cm
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


# ── Fuentes: DejaVu (incluida con matplotlib) cubre →, −, ≈, ⚠, ✓ que Helvetica no tiene ─────
def registrar_fuentes():
    try:
        import matplotlib

        base = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
        pdfmetrics.registerFont(TTFont("Manual", os.path.join(base, "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("Manual-Bold", os.path.join(base, "DejaVuSans-Bold.ttf")))
        pdfmetrics.registerFont(TTFont("Manual-Italic", os.path.join(base, "DejaVuSans-Oblique.ttf")))
        pdfmetrics.registerFont(TTFont("Manual-BoldItalic", os.path.join(base, "DejaVuSans-BoldOblique.ttf")))
        pdfmetrics.registerFontFamily("Manual", normal="Manual", bold="Manual-Bold",
                                      italic="Manual-Italic", boldItalic="Manual-BoldItalic")
        return "Manual", "Manual-Bold"
    except Exception as e:  # sin matplotlib: se cae a Helvetica y se sustituyen símbolos
        print(f"Aviso: no se pudo cargar DejaVu ({e}); se usa Helvetica.")
        return "Helvetica", "Helvetica-Bold"


FUENTE, FUENTE_B = registrar_fuentes()
_HELVETICA = FUENTE == "Helvetica"


def _limpiar(t):
    if not _HELVETICA:
        return t
    return (t.replace("→", "->").replace("−", "-").replace("≈", "~").replace("⚠", "(!)")
             .replace("✓", "OK").replace("✕", "x").replace("÷", "/"))


# ── Estilos ──────────────────────────────────────────────────────────────────
def estilos():
    def s(name, **kw):
        kw.setdefault("fontName", FUENTE)
        return ParagraphStyle(name, **kw)

    return {
        "titulo_portada": s("tp", fontSize=30, textColor=BLANCO, alignment=TA_CENTER,
                            fontName=FUENTE_B, leading=36),
        "subtitulo_portada": s("sp", fontSize=15, textColor=colors.HexColor("#fde8e8"),
                               alignment=TA_CENTER, leading=20),
        "h1": s("h1", fontSize=18, textColor=ROJO, fontName=FUENTE_B, spaceAfter=8, spaceBefore=6, leading=22),
        "banner": s("bn", fontSize=17, textColor=BLANCO, fontName=FUENTE_B, leading=21),
        "h2": s("h2", fontSize=13, textColor=OSCURO, fontName=FUENTE_B, spaceAfter=5, spaceBefore=12, leading=16),
        "h3": s("h3", fontSize=11, textColor=AZUL, fontName=FUENTE_B, spaceAfter=3, spaceBefore=8, leading=14),
        "body": s("body", fontSize=9.5, leading=14, spaceAfter=5, alignment=TA_LEFT),
        "celda": s("celda", fontSize=8.5, leading=11),
        "celda_h": s("celdah", fontSize=8.5, leading=11, textColor=BLANCO, fontName=FUENTE_B),
        "box": s("box", fontSize=9, leading=13),
        "code": s("code", fontName="Courier", fontSize=8, leading=10),
        "toc1": s("toc1", fontSize=10, leading=15, leftIndent=8, fontName=FUENTE),
        "fin": s("fin", fontSize=10.5, textColor=BLANCO, alignment=TA_CENTER, leading=17),
    }


S = estilos()


# ── Markdown (subconjunto usado por la ayuda) → texto de reportlab ─────────────────────
def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(texto):
    """**negrita**, *cursiva*, `código`, [texto](enlace)."""
    t = esc(_limpiar(texto))
    t = re.sub(r"`([^`]+)`", r'<font name="Courier" size="8.5">\1</font>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<i>\1</i>", t)

    def enlace(m):
        txt, url = m.group(1), m.group(2)
        if url.startswith("ayuda:"):
            return f'<a href="#tema_{url[6:]}" color="#2980b9">{txt}</a>'
        return f'<a href="{url}" color="#2980b9">{txt}</a>'

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", enlace, t)


class Titulo(Paragraph):
    """Encabezado de módulo, registrado para el índice y como destino de enlaces."""

    def __init__(self, texto, clave):
        super().__init__(f'<a name="tema_{clave}"/>{esc(texto)}', S["banner"])
        self.texto_toc = texto


def caja(texto_html, color, fondo):
    t = Table([[Paragraph(texto_html, S["box"])]], colWidths=[ANCHO_UTIL])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), fondo),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 1.2, color), ("LINEBEFORE", (0, 0), (0, -1), 4, color),
    ]))
    return t


def banner(texto, clave):
    t = Table([[Titulo(texto, clave)]], colWidths=[ANCHO_UTIL])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ROJO),
        ("LEFTPADDING", (0, 0), (-1, -1), 14), ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    t.titulo_toc = texto
    return t


def tabla(filas):
    """filas: lista de listas de texto markdown; la primera es el encabezado."""
    ncol = max(len(f) for f in filas)
    filas = [f + [""] * (ncol - len(f)) for f in filas]
    # anchos proporcionales a la longitud del contenido, con mínimo y máximo razonables
    pesos = []
    for c in range(ncol):
        largo = max(len(re.sub(r"[*`\[\]]", "", f[c])) for f in filas)
        pesos.append(min(max(largo, 8), 60))
    total = float(sum(pesos))
    anchos = [ANCHO_UTIL * p / total for p in pesos]
    datos = [[Paragraph(inline(c), S["celda_h"] if i == 0 else S["celda"]) for c in fila]
             for i, fila in enumerate(filas)]
    t = Table(datos, colWidths=anchos, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ROJO),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bdc3c7")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BLANCO, colors.HexColor("#fdf6f6")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def parse_fila_tabla(linea):
    celdas = linea.strip().strip("|").split("|")
    return [c.strip() for c in celdas]


def es_separador_tabla(linea):
    return bool(re.fullmatch(r"\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*", linea))


def markdown_a_flowables(md, clave):
    """Convierte un tema de ayuda en una lista de flowables. La primera línea '# ' es el banner."""
    lineas = md.replace("\r\n", "\n").split("\n")
    out, i, n = [], 0, len(lineas)
    parrafo = []

    def volcar():
        if parrafo:
            out.append(Paragraph(inline(" ".join(p.strip() for p in parrafo)), S["body"]))
            parrafo.clear()

    while i < n:
        ln = lineas[i]
        if not ln.strip():
            volcar(); i += 1; continue
        if ln.startswith("# "):
            volcar(); out.append(banner(ln[2:].strip(), clave)); out.append(Spacer(1, 0.3 * cm)); i += 1; continue
        if ln.startswith("### "):
            volcar(); out.append(Paragraph(inline(ln[4:].strip()), S["h3"])); i += 1; continue
        if ln.startswith("## "):
            volcar(); out.append(Paragraph(inline(ln[3:].strip()), S["h2"])); i += 1; continue
        if re.fullmatch(r"-{3,}", ln.strip()):
            volcar(); out.append(HRFlowable(width="100%", color=GRIS_C, spaceBefore=4, spaceAfter=4)); i += 1; continue
        if ln.startswith("```"):
            volcar(); i += 1; bloque = []
            while i < n and not lineas[i].startswith("```"):
                bloque.append(_limpiar(lineas[i])); i += 1
            i += 1
            out.append(Preformatted("\n".join(bloque), S["code"])); continue
        if ln.lstrip().startswith("|"):
            volcar(); filas = []
            while i < n and lineas[i].lstrip().startswith("|"):
                if not es_separador_tabla(lineas[i]):
                    filas.append(parse_fila_tabla(lineas[i]))
                i += 1
            if filas:
                out.append(tabla(filas)); out.append(Spacer(1, 0.25 * cm))
            continue
        if ln.startswith(">"):
            volcar(); citas = []
            while i < n and lineas[i].startswith(">"):
                citas.append(lineas[i].lstrip(">").strip()); i += 1
            texto = " ".join(c for c in citas if c)
            aviso = re.search(r"importante|no descuenta|no genera|cuidado|precauci|no \*\*", texto, re.I)
            html = inline(texto)
            out.append(caja(html, NARANJA if aviso else AZUL,
                            colors.HexColor("#fef9e7") if aviso else colors.HexColor("#eaf4fb")))
            out.append(Spacer(1, 0.25 * cm)); continue
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", ln)
        if m:
            volcar()
            sangria = len(m.group(1))
            marca = "•" if m.group(2) in "-*" else m.group(2)
            texto = m.group(3)
            i += 1
            while i < n and lineas[i].strip() and not re.match(r"^\s*([-*]|\d+\.)\s+", lineas[i]) \
                    and not lineas[i].lstrip().startswith(("|", ">", "#", "```")) and lineas[i].startswith(" "):
                texto += " " + lineas[i].strip(); i += 1   # continuación de la misma viñeta
            nivel = sangria // 3
            estilo = ParagraphStyle(f"li{nivel}", parent=S["body"], leftIndent=14 + 14 * (nivel + 1),
                                    bulletIndent=14 * (nivel + 1), spaceAfter=2)
            out.append(Paragraph(inline(texto), estilo, bulletText=_limpiar(marca)))
            continue
        parrafo.append(ln); i += 1
    volcar()
    return out


# ── Documento ────────────────────────────────────────────────────────────────
class Manual(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        titulo = getattr(flowable, "titulo_toc", None)
        if titulo:
            self.notify("TOCEntry", (0, titulo, self.page))


def encabezado_pie(canvas, doc, con_encabezado=True):
    canvas.saveState()
    if con_encabezado:
        canvas.setFillColor(ROJO)
        canvas.rect(doc.leftMargin, PAGE_H - 1.8 * cm, PAGE_W - doc.leftMargin - doc.rightMargin, 0.7 * cm, fill=1, stroke=0)
        canvas.setFillColor(BLANCO)
        canvas.setFont(FUENTE_B, 9)
        canvas.drawString(doc.leftMargin + 6, PAGE_H - 1.6 * cm, "Manual de Usuario — Italos Manager")
    y = doc.bottomMargin - 0.3 * cm
    canvas.setStrokeColor(DORADO); canvas.setLineWidth(1)
    canvas.line(doc.leftMargin, y, PAGE_W - doc.rightMargin, y)
    canvas.setFont(FUENTE, 8); canvas.setFillColor(GRIS)
    canvas.drawString(doc.leftMargin, y - 14, "Generado desde la ayuda en pantalla (F1)")
    canvas.drawRightString(PAGE_W - doc.rightMargin, y - 14, f"Página {doc.page}")
    canvas.restoreState()


def fecha_larga(hoy):
    return f"{hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}"


def portada(hoy):
    caja_titulo = Table([[Paragraph("ITALOS MANAGER", S["titulo_portada"])]], colWidths=[ANCHO_UTIL])
    caja_titulo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ROJO), ("TOPPADDING", (0, 0), (-1, -1), 40),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 20)]))
    sub = Table([[Paragraph("Sistema de Gestión de Restaurante", S["subtitulo_portada"])]], colWidths=[ANCHO_UTIL])
    sub.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#c0392b")),
        ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12)]))
    info = Table([["Documento", "Manual de Usuario"], ["Fecha de emisión", fecha_larga(hoy)],
                  ["Contenido", f"{len(ayuda.TEMAS)} temas: primeros pasos y un capítulo por módulo"],
                  ["Origen", "Se genera desde la ayuda en pantalla (menú Ayuda / F1)"]],
                 colWidths=[5 * cm, ANCHO_UTIL - 5 * cm])
    info.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FUENTE), ("FONTNAME", (0, 0), (0, -1), FUENTE_B),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5), ("TEXTCOLOR", (0, 0), (0, -1), OSCURO),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d5d8dc")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [BLANCO, GRIS_C]),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6), ("LEFTPADDING", (0, 0), (-1, -1), 10)]))
    return [Spacer(1, 3 * cm), caja_titulo, Spacer(1, 0.3 * cm), sub, Spacer(1, 1.5 * cm), info, PageBreak()]


def construir_historia(hoy):
    historia = portada(hoy)
    historia.append(Paragraph("Contenido", S["h1"]))
    historia.append(HRFlowable(width="100%", color=DORADO, thickness=2, spaceAfter=8))
    toc = TableOfContents()
    toc.levelStyles = [S["toc1"]]
    toc.dotsMinLevel = 0
    historia += [toc, PageBreak()]

    for clave, _titulo in ayuda.TEMAS:
        if not ayuda.existe(clave):
            print(f"Aviso: falta assets/ayuda/{clave}.md; se omite.")
            continue
        historia += markdown_a_flowables(ayuda.leer(clave), clave)
        historia.append(PageBreak())

    historia.append(Spacer(1, 4 * cm))
    fin = Table([[Paragraph(f"Generado el {fecha_larga(hoy)}<br/>Documento de uso interno.", S["fin"])]], colWidths=[ANCHO_UTIL])
    fin.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ROJO),
                             ("TOPPADDING", (0, 0), (-1, -1), 28), ("BOTTOMPADDING", (0, 0), (-1, -1), 28)]))
    historia.append(fin)
    return historia


ARCHIVO_HUELLA = "docs/Manual_de_Usuario_ItalosManager.huella"


def huella_ayuda():
    """SHA-256 del contenido de la ayuda (temas en orden). Cambia si se edita cualquier tema."""
    h = hashlib.sha256()
    for clave, titulo in ayuda.TEMAS:
        h.update(f"{clave}|{titulo}\n".encode("utf-8"))
        h.update(ayuda.leer(clave).replace("\r\n", "\n").encode("utf-8"))
    return h.hexdigest()


def generar(salida="docs/Manual_de_Usuario_ItalosManager.pdf", hoy=None):
    hoy = hoy or datetime.date.today()
    os.makedirs(os.path.dirname(salida) or ".", exist_ok=True)
    doc = Manual(salida, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2.4 * cm,
                 bottomMargin=2 * cm, title="Manual de Usuario — Italos Manager", author="Italos Manager",
                 subject="Sistema de Gestión de Restaurante")
    doc.multiBuild(construir_historia(hoy),
                   onFirstPage=lambda c, d: encabezado_pie(c, d, con_encabezado=False),
                   onLaterPages=encabezado_pie)
    # Huella de la ayuda con la que se generó: una prueba automática avisa si el manual quedó desactualizado.
    with open(os.path.splitext(salida)[0] + ".huella", "w", encoding="utf-8") as f:
        f.write(huella_ayuda() + "\n")
    return salida


if __name__ == "__main__":
    ruta = generar()
    print(f"Manual generado: {ruta}  ({os.path.getsize(ruta) / 1024:.1f} KB, {len(ayuda.TEMAS)} temas)")

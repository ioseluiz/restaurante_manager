from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os
import tempfile


_RED = colors.HexColor("#a20f22")
_ORANGE = colors.HexColor("#d0741d")
_GRAY = colors.HexColor("#f5f5f5")
_LIGHT_YELLOW = colors.HexColor("#fffde7")
_LIGHT_BLUE = colors.HexColor("#f0f4ff")
_DARK = colors.HexColor("#2c3e50")
_BORDER = colors.HexColor("#cccccc")
_PRES_TEXT = colors.HexColor("#555555")


def generar_pdf_conteo(conteo_id, fecha, descripcion, categoria_nombre, filas):
    """
    Generate a physical inventory count PDF and return the file path.

    filas: list of dicts with keys:
        numero      int
        nombre      str
        unidad      str   (base unit name)
        presentaciones  list[str]  (optional; names of available purchase presentations)
    """
    path = os.path.join(tempfile.gettempdir(), f"conteo_inventario_{conteo_id}.pdf")

    doc = SimpleDocTemplate(
        path,
        pagesize=letter,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "title", parent=styles["Normal"],
        fontSize=16, fontName="Helvetica-Bold",
        textColor=_RED, alignment=TA_CENTER, spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "subtitle", parent=styles["Normal"],
        fontSize=10, fontName="Helvetica",
        textColor=_DARK, alignment=TA_CENTER, spaceAfter=2,
    )
    meta_style = ParagraphStyle(
        "meta", parent=styles["Normal"],
        fontSize=9, fontName="Helvetica",
        textColor=_DARK, alignment=TA_CENTER,
    )
    instr_style = ParagraphStyle(
        "instr", parent=styles["Normal"],
        fontSize=8, fontName="Helvetica-Oblique",
        textColor=colors.HexColor("#555555"), alignment=TA_LEFT,
    )
    pres_style = ParagraphStyle(
        "pres", parent=styles["Normal"],
        fontSize=7, fontName="Helvetica",
        textColor=_PRES_TEXT, leading=9,
    )

    story = []

    story.append(Paragraph("Restaurante Italos", title_style))
    story.append(Paragraph("Formato de Toma de Inventario Físico", subtitle_style))
    story.append(Spacer(1, 0.2 * cm))

    meta_text = (
        f"<b>Conteo N°:</b> {conteo_id}&nbsp;&nbsp;&nbsp;"
        f"<b>Fecha:</b> {fecha}&nbsp;&nbsp;&nbsp;"
        f"<b>Categoría:</b> {categoria_nombre or 'Todas'}"
    )
    if descripcion:
        meta_text += f"&nbsp;&nbsp;&nbsp;<b>Descripción:</b> {descripcion}"
    story.append(Paragraph(meta_text, meta_style))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        "Instrucciones: Cuente el stock real en bodega y complete las columnas <b>Cant. Física</b> "
        "y <b>Unidad usada</b>. Si usa una presentación de compra (columna <i>Presentaciones disponibles</i>), "
        "anote la cantidad en esa unidad y escriba el nombre de la presentación en la columna Unidad usada. "
        "Registre decimales si aplica.",
        instr_style,
    ))
    story.append(Spacer(1, 0.4 * cm))

    # Columns: # | Descripción | Unidad base | Presentaciones disponibles | Cant. Física | Unidad usada
    # Total content width ≈ 17.9 cm
    col_widths = [0.8 * cm, 5.5 * cm, 2.0 * cm, 4.5 * cm, 2.8 * cm, 2.3 * cm]
    header = ["#", "Descripción del Insumo", "Unidad\nbase", "Presentaciones\ndisponibles", "Cant.\nFísica", "Unidad\nusada"]
    table_data = [header]

    for fila in filas:
        pres_list = fila.get("presentaciones") or []
        if pres_list:
            pres_cell = Paragraph("<br/>".join(pres_list), pres_style)
        else:
            pres_cell = Paragraph("—", pres_style)

        table_data.append([
            str(fila["numero"]),
            fila["nombre"],
            fila["unidad"],
            pres_cell,
            "",   # Cant. Física — blank
            "",   # Unidad usada — blank
        ])

    row_count = len(table_data)

    ts = TableStyle([
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), _RED),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
        # Data rows — base font
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("VALIGN", (0, 1), (-1, -1), "MIDDLE"),
        # Column alignments
        ("ALIGN", (0, 1), (0, -1), "CENTER"),   # #
        ("ALIGN", (2, 1), (2, -1), "CENTER"),   # Unidad base
        ("ALIGN", (4, 1), (4, -1), "CENTER"),   # Cant. Física
        ("ALIGN", (5, 1), (5, -1), "CENTER"),   # Unidad usada
        # Alternating row backgrounds
        *[("BACKGROUND", (0, r), (-1, r), _GRAY if r % 2 == 0 else colors.white)
          for r in range(1, row_count)],
        # Highlight writable columns
        ("BACKGROUND", (4, 1), (4, -1), _LIGHT_YELLOW),
        ("BACKGROUND", (5, 1), (5, -1), _LIGHT_BLUE),
        # Borders
        ("GRID", (0, 0), (-1, -1), 0.4, _BORDER),
        ("LINEBELOW", (0, 0), (-1, 0), 1.2, _RED),
        ("LINEAFTER", (4, 0), (4, -1), 0.8, _ORANGE),
        # Padding
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ])

    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(ts)
    story.append(table)

    story.append(Spacer(1, 1.0 * cm))

    sign_data = [
        ["Elaborado por:", "", "Revisado por:", ""],
        ["_________________________", "", "_________________________", ""],
        ["Nombre y Firma", "", "Nombre y Firma", ""],
    ]
    sign_table = Table(sign_data, colWidths=[4.5 * cm, 2 * cm, 4.5 * cm, 2 * cm])
    sign_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TEXTCOLOR", (0, 0), (-1, -1), _DARK),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(sign_table)

    doc.build(story)
    return path

"""OBSOLETO — conservado solo como referencia.
Este generador contiene texto escrito a mano que NO coincide con el programa
(campos inexistentes, stock descontado por ventas, etc.). El manual vigente se genera
desde la ayuda en pantalla con `python generar_manual.py` (ver docs/ayuda.md)."""

"""
Script para generar el Manual de Usuario en PDF del Sistema de Gestión de Restaurante.
Ejecutar con: python generar_manual.py
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus.flowables import Flowable
import datetime

# ── Colores corporativos ───────────────────────────────────────────────────────
ROJO   = colors.HexColor("#a20f22")
DORADO = colors.HexColor("#db9930")
AZUL   = colors.HexColor("#2980b9")
VERDE  = colors.HexColor("#27ae60")
GRIS   = colors.HexColor("#7f8c8d")
GRIS_C = colors.HexColor("#ecf0f1")
OSCURO = colors.HexColor("#2c3e50")
NARANJA= colors.HexColor("#d0741d")
MORADO = colors.HexColor("#8e44ad")
BLANCO = colors.white
NEGRO  = colors.black

PAGE_W, PAGE_H = A4

# ── Estilos ────────────────────────────────────────────────────────────────────
def build_styles():
    base = getSampleStyleSheet()

    def s(name, **kw):
        return ParagraphStyle(name, **kw)

    return {
        "titulo_portada": s("tp",
            fontSize=32, textColor=BLANCO, alignment=TA_CENTER,
            fontName="Helvetica-Bold", spaceAfter=6),
        "subtitulo_portada": s("sp",
            fontSize=16, textColor=colors.HexColor("#fde8e8"),
            alignment=TA_CENTER, fontName="Helvetica", spaceAfter=4),
        "version_portada": s("vp",
            fontSize=11, textColor=colors.HexColor("#f0c0c0"),
            alignment=TA_CENTER, fontName="Helvetica"),

        "h1": s("h1",
            fontSize=18, textColor=ROJO, fontName="Helvetica-Bold",
            spaceAfter=8, spaceBefore=18,
            borderPadding=(0, 0, 4, 0)),
        "h2": s("h2",
            fontSize=14, textColor=OSCURO, fontName="Helvetica-Bold",
            spaceAfter=6, spaceBefore=12),
        "h3": s("h3",
            fontSize=12, textColor=AZUL, fontName="Helvetica-Bold",
            spaceAfter=4, spaceBefore=8),
        "h4": s("h4",
            fontSize=11, textColor=NARANJA, fontName="Helvetica-Bold",
            spaceAfter=3, spaceBefore=6),

        "body": s("body",
            fontSize=10, textColor=OSCURO, fontName="Helvetica",
            spaceAfter=5, leading=15, alignment=TA_JUSTIFY),
        "body_left": s("body_left",
            fontSize=10, textColor=OSCURO, fontName="Helvetica",
            spaceAfter=4, leading=14),
        "bullet": s("bullet",
            fontSize=10, textColor=OSCURO, fontName="Helvetica",
            spaceAfter=3, leading=13, leftIndent=18, bulletIndent=6),
        "bullet2": s("bullet2",
            fontSize=9.5, textColor=colors.HexColor("#34495e"),
            fontName="Helvetica", spaceAfter=2, leading=12,
            leftIndent=36, bulletIndent=24),
        "nota": s("nota",
            fontSize=9.5, textColor=colors.HexColor("#5d6d7e"),
            fontName="Helvetica-Oblique", spaceAfter=4, leading=13,
            leftIndent=12),
        "advertencia": s("adv",
            fontSize=9.5, textColor=colors.HexColor("#7d3c98"),
            fontName="Helvetica-Bold", spaceAfter=4),
        "tabla_header": s("th",
            fontSize=9, textColor=BLANCO, fontName="Helvetica-Bold",
            alignment=TA_CENTER),
        "tabla_cell": s("tc",
            fontSize=9, textColor=OSCURO, fontName="Helvetica",
            alignment=TA_LEFT, leading=12),
        "pie_pagina": s("pp",
            fontSize=8, textColor=GRIS, fontName="Helvetica",
            alignment=TA_CENTER),
        "toc_item": s("toc",
            fontSize=11, textColor=OSCURO, fontName="Helvetica",
            spaceAfter=3, leftIndent=0),
        "toc_sub": s("tocs",
            fontSize=10, textColor=colors.HexColor("#555555"),
            fontName="Helvetica", spaceAfter=2, leftIndent=20),
        "seccion_num": s("sn",
            fontSize=10, textColor=ROJO, fontName="Helvetica-Bold",
            spaceAfter=0),
    }


# ── Flowables personalizados ───────────────────────────────────────────────────
class BannerCabecera(Flowable):
    """Banner rojo para encabezados de sección."""
    def __init__(self, texto, subtexto="", w=None):
        super().__init__()
        self.texto = texto
        self.subtexto = subtexto
        self.w = w or (PAGE_W - 4*cm)
        self.h = 44 if subtexto else 32

    def wrap(self, aw, ah):
        return self.w, self.h

    def draw(self):
        c = self.canv
        c.setFillColor(ROJO)
        c.roundRect(0, 0, self.w, self.h, 6, fill=1, stroke=0)
        c.setFillColor(DORADO)
        c.setLineWidth(2)
        c.setStrokeColor(DORADO)
        c.roundRect(0, 0, self.w, self.h, 6, fill=0, stroke=1)

        c.setFillColor(BLANCO)
        c.setFont("Helvetica-Bold", 14)
        y_text = self.h - 20 if self.subtexto else self.h / 2 - 5
        c.drawString(14, y_text, self.texto)

        if self.subtexto:
            c.setFont("Helvetica", 9)
            c.setFillColor(colors.HexColor("#fde8e8"))
            c.drawString(14, 8, self.subtexto)


class FilaColor(Flowable):
    """Banda de color horizontal."""
    def __init__(self, color, h=3, w=None):
        super().__init__()
        self.color = color
        self.h = h
        self.w = w or (PAGE_W - 4*cm)

    def wrap(self, aw, ah):
        return self.w, self.h

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.rect(0, 0, self.w, self.h, fill=1, stroke=0)


# ── Header / Footer ────────────────────────────────────────────────────────────
TOTAL_PAGES = [0]

def primera_pagina(canvas, doc):
    canvas.saveState()
    _draw_footer(canvas, doc)
    canvas.restoreState()

def paginas_siguientes(canvas, doc):
    canvas.saveState()
    _draw_header(canvas, doc)
    _draw_footer(canvas, doc)
    canvas.restoreState()

def _draw_header(canvas, doc):
    canvas.setFillColor(ROJO)
    canvas.rect(doc.leftMargin, PAGE_H - 1.8*cm,
                PAGE_W - doc.leftMargin - doc.rightMargin, 0.7*cm, fill=1, stroke=0)
    canvas.setFillColor(BLANCO)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(doc.leftMargin + 6, PAGE_H - 1.3*cm,
                      "Manual de Usuario — Sistema de Gestión de Restaurante")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(PAGE_W - doc.rightMargin - 6, PAGE_H - 1.3*cm,
                           "ItalosManager")

def _draw_footer(canvas, doc):
    canvas.setStrokeColor(DORADO)
    canvas.setLineWidth(1)
    y = doc.bottomMargin - 0.3*cm
    canvas.line(doc.leftMargin, y, PAGE_W - doc.rightMargin, y)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GRIS)
    canvas.drawString(doc.leftMargin, y - 14,
                      f"© {datetime.date.today().year} ItalosManager — Confidencial")
    canvas.drawRightString(PAGE_W - doc.rightMargin, y - 14,
                           f"Página {doc.page}")


# ── Helpers ────────────────────────────────────────────────────────────────────
def tabla(data, col_widths, header_color=ROJO, alt_color=colors.HexColor("#fdf6f6")):
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("TEXTCOLOR",  (0, 0), (-1, 0), BLANCO),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 9),
        ("ALIGN",      (0, 0), (-1, 0), "CENTER"),
        ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#bdc3c7")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BLANCO, alt_color]),
        ("FONTNAME",   (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",   (0, 1), (-1, -1), 9),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
    ])
    t = Table(data, colWidths=col_widths)
    t.setStyle(style)
    return t


def info_box(texto, S, color=AZUL, icon="ℹ"):
    """Cuadro de información coloreado."""
    data = [[Paragraph(f"<b>{icon} {texto}</b>", S["body_left"])]]
    t = Table(data, colWidths=[PAGE_W - 5.4*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eaf4fb")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",(0, 0), (-1, -1), 10),
        ("TOPPADDING",  (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 7),
        ("BOX",         (0, 0), (-1, -1), 1.5, color),
        ("LINEAFTER",   (0, 0), (0, -1),  4, color),
        ("BORDERRADIUS",(0, 0), (-1, -1), 4),
    ]))
    return t


def warning_box(texto, S):
    data = [[Paragraph(f"<b>⚠ {texto}</b>", S["advertencia"])]]
    t = Table(data, colWidths=[PAGE_W - 5.4*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fef9e7")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",(0, 0), (-1, -1), 10),
        ("TOPPADDING",  (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 7),
        ("BOX",         (0, 0), (-1, -1), 1.5, NARANJA),
        ("LINEAFTER",   (0, 0), (0, -1),  4, NARANJA),
    ]))
    return t


# ══════════════════════════════════════════════════════════════════════════════
# CONTENIDO
# ══════════════════════════════════════════════════════════════════════════════
def build_story(S):
    story = []

    # ─── PORTADA ──────────────────────────────────────────────────────────────
    story.append(Spacer(1, 3*cm))

    # Fondo portada (tabla grande)
    portada_data = [[
        Paragraph("ITALOS MANAGER", S["titulo_portada"]),
    ]]
    portada = Table(portada_data, colWidths=[PAGE_W - 4*cm])
    portada.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ROJO),
        ("TOPPADDING",  (0, 0), (-1, -1), 40),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 20),
        ("LEFTPADDING", (0, 0), (-1, -1), 20),
        ("RIGHTPADDING",(0, 0), (-1, -1), 20),
        ("ROUNDEDCORNERS", (0, 0), (-1, -1), [10, 10, 10, 10]),
    ]))
    story.append(portada)

    story.append(Spacer(1, 0.3*cm))
    sub_data = [[
        Paragraph("Sistema de Gestión de Restaurante", S["subtitulo_portada"]),
    ]]
    sub_tbl = Table(sub_data, colWidths=[PAGE_W - 4*cm])
    sub_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#c0392b")),
        ("TOPPADDING",  (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 12),
    ]))
    story.append(sub_tbl)

    story.append(Spacer(1, 1.5*cm))

    info_port = [
        ["Manual de Usuario",      "Versión 1.0"],
        ["Fecha de emisión",       datetime.date.today().strftime("%d de %B de %Y")],
        ["Plataforma",             "Windows 10/11"],
        ["Clasificación",          "Confidencial — Uso Interno"],
    ]
    t_port = Table(info_port, colWidths=[7*cm, 9*cm])
    t_port.setStyle(TableStyle([
        ("FONTNAME",   (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",   (0, 0), (-1, -1), 10),
        ("FONTNAME",   (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR",  (0, 0), (0, -1), OSCURO),
        ("TEXTCOLOR",  (1, 0), (1, -1), colors.HexColor("#34495e")),
        ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#d5d8dc")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [BLANCO, GRIS_C]),
        ("TOPPADDING",  (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(t_port)
    story.append(PageBreak())

    # ─── TABLA DE CONTENIDO ───────────────────────────────────────────────────
    story.append(Paragraph("TABLA DE CONTENIDO", S["h1"]))
    story.append(FilaColor(DORADO, 2))
    story.append(Spacer(1, 0.4*cm))

    toc = [
        ("1.", "Introducción al Sistema", ""),
        ("2.", "Inicio de Sesión", ""),
        ("3.", "Ventana Principal y Navegación", ""),
        ("4.", "Dashboard — Panel de Control", ""),
        ("5.", "Módulo: Insumos y Costos", ""),
        ("  5.1", "Catálogo de Insumos", ""),
        ("  5.2", "Presentaciones de Compra", ""),
        ("  5.3", "Categorías de Insumos", ""),
        ("6.", "Módulo: Menú del Restaurante", ""),
        ("7.", "Módulo: Recetas (Escandallo)", ""),
        ("8.", "Módulo: Compras e Inventario", ""),
        ("  8.1", "Registro de Compras", ""),
        ("  8.2", "Gestión de Proveedores", ""),
        ("  8.3", "Resumen Semanal y Mensual", ""),
        ("  8.4", "Abastecimiento Interno", ""),
        ("9.", "Módulo: Inventario Actual", ""),
        ("10.", "Módulo: Conteo de Inventario", ""),
        ("11.", "Módulo: Presupuestos", ""),
        ("12.", "Módulo: Reportes de Ventas (Carga CSV)", ""),
        ("13.", "Módulo: Consolidados Financieros", ""),
        ("  13.1", "Resumen General Mensual", ""),
        ("  13.2", "Chequera", ""),
        ("  13.3", "Tarjetas de Crédito", ""),
        ("  13.4", "Pagos en Efectivo", ""),
        ("  13.5", "Pagos con Yappy", ""),
        ("  13.6", "Diario de Ventas", ""),
        ("14.", "Módulo: Unidades de Medida", ""),
        ("15.", "Módulo: Administración", ""),
        ("  15.1", "Usuarios", ""),
        ("  15.2", "Sucursales", ""),
        ("16.", "Kardex — Trazabilidad del Inventario", ""),
        ("17.", "Supuestos y Reglas del Sistema", ""),
        ("18.", "Solución de Problemas Frecuentes", ""),
    ]
    for num, titulo, _ in toc:
        is_sub = num.startswith("  ")
        st = S["toc_sub"] if is_sub else S["toc_item"]
        story.append(Paragraph(f"<b>{num.strip()}</b>  {titulo}", st))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 1. INTRODUCCIÓN
    # ══════════════════════════════════════════════════════════════════════════
    story.append(BannerCabecera("1. Introducción al Sistema",
                                "ItalosManager — Gestión integral de restaurante"))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph(
        "ItalosManager es un sistema de escritorio desarrollado en Python con interfaz gráfica PyQt5 "
        "y base de datos SQLite. Su objetivo es centralizar la gestión operativa y financiera de un "
        "restaurante, eliminando el uso de hojas de cálculo dispersas y proporcionando trazabilidad "
        "completa sobre inventario, compras, ventas y finanzas.", S["body"]))

    story.append(Paragraph("<b>Características principales:</b>", S["h3"]))
    features = [
        "Control completo de inventario con kardex (historial de movimientos).",
        "Gestión de insumos, presentaciones de compra y categorías.",
        "Definición de menú, recetas y escandallos (costo por plato).",
        "Registro y seguimiento de compras a proveedores.",
        "Transferencias internas entre sucursales.",
        "Presupuestación mensual vinculada a reportes de ventas.",
        "Carga de reportes CSV desde el sistema POS.",
        "Control financiero: chequera, tarjetas de crédito, Yappy, pagos en efectivo.",
        "Diario de ventas diario con conciliación de caja.",
        "Reportes consolidados mensuales con gráficas.",
        "Generación de PDFs de conteos de inventario.",
        "Soporte para múltiples sucursales.",
        "Gestión de usuarios con roles (Administrador / Empleado).",
    ]
    for f in features:
        story.append(Paragraph(f"• {f}", S["bullet"]))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>Tecnología:</b>", S["h3"]))
    tbl_tech = tabla(
        [["Componente", "Tecnología"],
         ["Lenguaje", "Python 3"],
         ["Interfaz gráfica", "PyQt5 5.15"],
         ["Base de datos", "SQLite 3 (archivo local)"],
         ["Generación de PDFs", "ReportLab"],
         ["Gráficas", "Matplotlib"],
         ["Análisis de datos", "Pandas"],
         ["Empaquetado", "PyInstaller (instalador .exe)"]],
        [6*cm, 10*cm], OSCURO
    )
    story.append(tbl_tech)
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 2. INICIO DE SESIÓN
    # ══════════════════════════════════════════════════════════════════════════
    story.append(BannerCabecera("2. Inicio de Sesión"))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph(
        "Al ejecutar la aplicación, se muestra la pantalla de inicio de sesión con el logo "
        "del restaurante en formato circular. El sistema valida las credenciales contra la "
        "base de datos local.", S["body"]))

    story.append(Paragraph("<b>Campos requeridos:</b>", S["h3"]))
    story.append(Paragraph("• <b>Usuario:</b> Nombre de usuario registrado en el sistema.", S["bullet"]))
    story.append(Paragraph("• <b>Contraseña:</b> Contraseña asociada al usuario (encriptada con SHA-256).", S["bullet"]))

    story.append(Spacer(1, 0.3*cm))
    story.append(info_box(
        "Credenciales predeterminadas: Usuario: admin | Contraseña: admin123  "
        "Se recomienda cambiar la contraseña del administrador en el primer uso.",
        S, VERDE, "✓"))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>Comportamiento post-login:</b>", S["h3"]))
    story.append(Paragraph(
        "Una vez autenticado correctamente, el sistema abre la ventana principal con el menú de "
        "navegación lateral. Al cerrar sesión, el sistema vuelve a mostrar la pantalla de login "
        "sin cerrar la aplicación, permitiendo que otro usuario inicie sesión.", S["body"]))

    story.append(Spacer(1, 0.3*cm))
    story.append(warning_box(
        "Si se ingresan credenciales incorrectas, el sistema muestra un mensaje de error. "
        "No existe un límite de intentos implementado en esta versión.", S))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 3. VENTANA PRINCIPAL
    # ══════════════════════════════════════════════════════════════════════════
    story.append(BannerCabecera("3. Ventana Principal y Navegación"))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph(
        "La ventana principal está compuesta por una barra lateral de navegación (sidebar) a la "
        "izquierda y el área de contenido a la derecha.", S["body"]))

    story.append(Paragraph("<b>Barra lateral (Sidebar):</b>", S["h3"]))
    story.append(Paragraph(
        "Contiene botones de navegación para cada módulo del sistema. Puede colapsarse para "
        "maximizar el espacio de trabajo haciendo clic en el botón con el ícono de hamburguesa (☰). "
        "Cuando está colapsada, solo muestra íconos; al expandirla se muestran los nombres completos.", S["body"]))

    nav_items = [
        ["Botón / Módulo", "Descripción"],
        ["Dashboard", "Panel con KPIs, gráficas de ventas e inventario"],
        ["Insumos y Costos", "Gestión de ingredientes, presentaciones y categorías"],
        ["Menú", "Administración de ítems del menú del restaurante"],
        ["Recetas", "Definición de recetas/escandallos por plato"],
        ["Compras", "Registro de compras, proveedores y transferencias"],
        ["Inventario", "Vista del stock actual por insumo"],
        ["Conteo de Inventario", "Sesiones de conteo físico con ajustes"],
        ["Presupuestos", "Creación y control de presupuestos mensuales"],
        ["Reportes", "Carga de reportes CSV del POS"],
        ["Consolidados", "Resumen financiero, chequera, tarjetas, Yappy"],
        ["Unidades", "Administración de unidades de medida"],
        ["Usuarios", "Gestión de cuentas de usuario"],
        ["Sucursales", "Administración de sucursales del restaurante"],
    ]
    story.append(tabla(nav_items, [4*cm, 12*cm]))

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("<b>Barra de estado (Status Bar):</b>", S["h3"]))
    story.append(Paragraph(
        "En la parte inferior de la ventana se muestra el usuario activo y la versión del sistema. "
        "El botón 'Cerrar Sesión' cierra la sesión actual y regresa al login.", S["body"]))

    story.append(info_box(
        "El sistema se adapta al tamaño de pantalla disponible, con un máximo de 1200×800 px "
        "y un mínimo relativo al 92% de la pantalla disponible.", S))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 4. DASHBOARD
    # ══════════════════════════════════════════════════════════════════════════
    story.append(BannerCabecera("4. Dashboard — Panel de Control"))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph(
        "El Dashboard es la pantalla de inicio después del login. Muestra un resumen visual "
        "del estado actual del negocio a través de tarjetas KPI y gráficas.", S["body"]))

    story.append(Paragraph("<b>Tarjetas KPI (Indicadores Clave):</b>", S["h3"]))
    kpis = [
        ["Tarjeta", "Color", "Qué muestra"],
        ["Ventas del Mes", "Rojo", "Total de ventas del mes en curso (del Diario de Ventas)"],
        ["Compras del Mes", "Naranja", "Total de compras registradas en el mes actual"],
        ["Stock Bajo", "Azul", "Cantidad de insumos con stock en cero o negativo"],
        ["Presupuesto", "Verde", "Monto total del presupuesto activo del mes"],
    ]
    story.append(tabla(kpis, [4*cm, 3*cm, 9*cm]))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>Gráficas:</b>", S["h3"]))
    story.append(Paragraph(
        "• <b>Ventas Semanales:</b> Gráfica de barras con las ventas de los últimos 7 días "
        "(lunes a domingo), con valores en dólares sobre cada barra.", S["bullet"]))
    story.append(Paragraph(
        "• <b>Ventas Mensuales:</b> Gráfica de barras con los totales de venta de los últimos "
        "6 meses, mostrando la tendencia histórica.", S["bullet"]))

    story.append(Spacer(1, 0.3*cm))
    story.append(info_box(
        "Los datos del Dashboard se actualizan automáticamente cada vez que se navega a él. "
        "Si no hay datos registrados, las gráficas muestran el mensaje 'Sin datos de ventas aún'.",
        S, AZUL))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 5. INSUMOS Y COSTOS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(BannerCabecera("5. Módulo: Insumos y Costos",
                                "Catálogo de ingredientes, presentaciones y categorías"))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph(
        "Este módulo es la base de todo el sistema de inventario. Aquí se registran todos los "
        "ingredientes o insumos que utiliza el restaurante, junto con las formas en que se "
        "compran y las categorías a las que pertenecen.", S["body"]))

    # 5.1
    story.append(Paragraph("5.1 Catálogo de Insumos", S["h2"]))
    story.append(Paragraph(
        "Lista maestra de todos los ingredientes del restaurante. Cada insumo tiene un stock "
        "actual que se actualiza automáticamente con cada compra, venta y ajuste.", S["body"]))

    story.append(Paragraph("<b>Campos del insumo:</b>", S["h3"]))
    campos_insumo = [
        ["Campo", "Descripción", "Requerido"],
        ["Nombre", "Nombre descriptivo del insumo (ej: Pollo, Aceite de oliva)", "Sí"],
        ["Unidad de Medida", "Unidad base para el control de stock (kg, L, unidades)", "Sí"],
        ["Categoría", "Grupo al que pertenece el insumo para reportes y presupuestos", "Sí"],
        ["Grupo Presupuestal", "Clasificación para el presupuesto mensual", "No"],
        ["Stock Actual", "Cantidad disponible en inventario (actualizada automáticamente)", "Auto"],
        ["Costo Unitario", "Precio por unidad base (calculado desde presentaciones)", "Auto"],
        ["Activo", "Indica si el insumo está en uso activo", "Sí"],
    ]
    story.append(tabla(campos_insumo, [4*cm, 9*cm, 3*cm]))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>Acciones disponibles:</b>", S["h3"]))
    story.append(Paragraph("• <b>Nuevo:</b> Abre formulario para registrar un nuevo insumo.", S["bullet"]))
    story.append(Paragraph("• <b>Editar:</b> Modifica los datos del insumo seleccionado en la tabla.", S["bullet"]))
    story.append(Paragraph("• <b>Eliminar:</b> Elimina el insumo (solo si no tiene movimientos registrados).", S["bullet"]))
    story.append(Paragraph("• <b>Buscar:</b> Filtra la lista en tiempo real por nombre o categoría.", S["bullet"]))

    story.append(Spacer(1, 0.3*cm))
    story.append(warning_box(
        "No se puede eliminar un insumo que tenga compras, movimientos de inventario o que forme "
        "parte de recetas. Primero debe eliminar o inactivar esas referencias.", S))

    # 5.2
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("5.2 Presentaciones de Compra", S["h2"]))
    story.append(Paragraph(
        "Define cómo se compra cada insumo en el mercado. Un insumo puede tener múltiples "
        "presentaciones (ej: el aceite puede comprarse en botella de 1L, en galón de 4L, etc.).", S["body"]))

    campos_pres = [
        ["Campo", "Descripción"],
        ["Insumo", "Insumo al que pertenece esta presentación"],
        ["Nombre", "Nombre de la presentación (ej: Botella 1L, Costal 50kg)"],
        ["Contenido", "Cantidad de la unidad base que contiene (ej: 1.0 para 1L)"],
        ["Unidad", "Unidad del contenido (debe coincidir con la unidad del insumo)"],
        ["Precio de Compra", "Costo de compra de esta presentación"],
        ["Costo por Unidad", "Calculado automáticamente: Precio ÷ Contenido"],
    ]
    story.append(tabla(campos_pres, [4*cm, 12*cm]))

    story.append(Spacer(1, 0.2*cm))
    story.append(info_box(
        "El 'Costo por Unidad' calculado aquí se usa en las recetas para calcular el costo "
        "de producción de cada plato del menú.", S, VERDE, "✓"))

    # 5.3
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("5.3 Categorías de Insumos", S["h2"]))
    story.append(Paragraph(
        "Las categorías agrupan los insumos para facilitar reportes, presupuestos y análisis. "
        "Cada categoría tiene un código único y un nombre descriptivo.", S["body"]))
    story.append(Paragraph("• Ejemplos: Carnes, Lácteos, Vegetales, Bebidas, Condimentos, Empaques.", S["bullet"]))
    story.append(Paragraph("• El código se usa en los reportes de presupuesto para identificar grupos.", S["bullet"]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 6. MENÚ
    # ══════════════════════════════════════════════════════════════════════════
    story.append(BannerCabecera("6. Módulo: Menú del Restaurante"))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph(
        "Administra el catálogo de platos y productos que ofrece el restaurante a sus clientes. "
        "Los ítems del menú son la base para el sistema de recetas y el análisis de rentabilidad.", S["body"]))

    campos_menu = [
        ["Campo", "Descripción"],
        ["Código", "Identificador único del plato (debe coincidir con el código del POS)"],
        ["Nombre", "Nombre del plato tal como aparece en el menú"],
        ["Precio de Venta", "Precio al público del plato"],
        ["Categoría", "Clasificación del plato (Entradas, Platos fuertes, Bebidas, etc.)"],
        ["Es Preparado", "Indica si el plato se elabora en la cocina (afecta al kardex)"],
        ["Activo", "Si está disponible actualmente para la venta"],
    ]
    story.append(tabla(campos_menu, [4.5*cm, 11.5*cm]))

    story.append(Spacer(1, 0.3*cm))
    story.append(info_box(
        "El código del ítem de menú debe coincidir exactamente con el código que reporta el "
        "sistema POS en el archivo CSV. Si no coincide, la carga de reportes marcará esa fila "
        "en rojo (código no encontrado).", S, NARANJA, "⚠"))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 7. RECETAS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(BannerCabecera("7. Módulo: Recetas (Escandallo)"))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph(
        "Las recetas vinculan cada ítem del menú con los insumos necesarios para prepararlo "
        "y sus cantidades exactas. Esto permite calcular el costo de producción (escandallo) "
        "de cada plato.", S["body"]))

    story.append(Paragraph("<b>Cómo funciona:</b>", S["h3"]))
    story.append(Paragraph(
        "1. Seleccione el ítem de menú para el que desea crear la receta.", S["bullet"]))
    story.append(Paragraph(
        "2. Agregue cada insumo con la cantidad exacta que se usa por plato.", S["bullet"]))
    story.append(Paragraph(
        "3. El sistema calcula automáticamente el costo total usando el costo unitario de cada insumo.", S["bullet"]))
    story.append(Paragraph(
        "4. Se puede ver el margen de ganancia comparando el costo con el precio de venta.", S["bullet"]))

    campos_receta = [
        ["Campo", "Descripción"],
        ["Ítem de Menú", "Plato al que pertenece esta receta"],
        ["Insumo", "Ingrediente que forma parte de la receta"],
        ["Cantidad", "Cantidad del insumo por porción (en la unidad base del insumo)"],
        ["Costo Parcial", "Calculado: Cantidad × Costo Unitario del insumo"],
        ["Costo Total Receta", "Suma de todos los costos parciales de la receta"],
    ]
    story.append(tabla(campos_receta, [4*cm, 12*cm]))

    story.append(Spacer(1, 0.3*cm))
    story.append(info_box(
        "El costo de receta se usa en los presupuestos para estimar el costo de materia prima "
        "basado en las ventas proyectadas. A mayor precisión en las recetas, más exacto será el presupuesto.", S))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 8. COMPRAS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(BannerCabecera("8. Módulo: Compras e Inventario",
                                "Registro de compras, proveedores, resúmenes y transferencias"))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph(
        "Este módulo centraliza todo lo relacionado con las compras al proveedor y el movimiento "
        "de inventario por concepto de adquisiciones. Está organizado en 5 pestañas.", S["body"]))

    # 8.1
    story.append(Paragraph("8.1 Registro de Compras", S["h2"]))
    story.append(Paragraph(
        "Permite registrar cada compra realizada a un proveedor, con el detalle de los productos "
        "adquiridos. Al guardar una compra, el stock de los insumos se actualiza automáticamente "
        "y se registra en el kardex.", S["body"]))

    campos_compra = [
        ["Campo", "Descripción"],
        ["Fecha", "Fecha en que se realizó la compra"],
        ["Proveedor", "Empresa o persona a quien se realizó la compra"],
        ["Número de Factura", "Número de la factura o recibo de la compra"],
        ["Tipo de Pago", "Forma de pago: Efectivo, Cheque, Tarjeta, Yappy, Crédito"],
        ["Presupuesto Asociado", "Número de presupuesto mensual al que se carga esta compra"],
        ["Insumo / Presentación", "Producto comprado y su presentación comercial"],
        ["Cantidad", "Número de unidades de la presentación comprada"],
        ["Precio Unitario", "Precio pagado por cada presentación"],
        ["Subtotal", "Calculado automáticamente: Cantidad × Precio Unitario"],
    ]
    story.append(tabla(campos_compra, [5*cm, 11*cm]))

    story.append(Spacer(1, 0.2*cm))
    story.append(info_box(
        "Al registrar una compra vinculada a un presupuesto, el sistema actualiza automáticamente "
        "el porcentaje de ejecución del presupuesto en el módulo de Presupuestos.", S, VERDE, "✓"))

    # 8.2
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("8.2 Gestión de Proveedores", S["h2"]))
    story.append(Paragraph(
        "Catálogo de todos los proveedores del restaurante. Los datos del proveedor se "
        "usan al registrar compras para trazabilidad.", S["body"]))
    campos_prov = [
        ["Campo", "Descripción"],
        ["Nombre", "Razón social o nombre del proveedor"],
        ["RUC / ID", "Número de identificación fiscal"],
        ["Teléfono", "Número de contacto"],
        ["Email", "Correo electrónico de contacto"],
        ["Dirección", "Dirección física o de envíos"],
        ["Contacto", "Nombre de la persona de contacto"],
    ]
    story.append(tabla(campos_prov, [4*cm, 12*cm]))

    # 8.3
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("8.3 Resumen Semanal y Mensual", S["h2"]))
    story.append(Paragraph(
        "Vistas de análisis que agrupan las compras por semana o mes, mostrando totales por "
        "proveedor y categoría de insumo. Permite identificar patrones de gasto y comparar "
        "con el presupuesto establecido.", S["body"]))
    story.append(Paragraph("• El <b>Resumen Semanal</b> muestra las compras de la semana en curso y las anteriores, agrupadas por proveedor.", S["bullet"]))
    story.append(Paragraph("• El <b>Resumen Mensual</b> consolida por mes con totales y subtotales por categoría.", S["bullet"]))

    # 8.4
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("8.4 Abastecimiento Interno (Transferencias)", S["h2"]))
    story.append(Paragraph(
        "Permite registrar transferencias de insumos entre sucursales del restaurante. "
        "Al registrar un abastecimiento, se descuenta el stock de la sucursal origen y se "
        "suma en la sucursal destino, con registro en el kardex de ambas.", S["body"]))
    campos_abast = [
        ["Campo", "Descripción"],
        ["Fecha", "Fecha de la transferencia"],
        ["Sucursal Origen", "Sucursal que envía los insumos"],
        ["Sucursal Destino", "Sucursal que recibe los insumos"],
        ["Insumos a Transferir", "Lista de insumos con cantidad a transferir"],
    ]
    story.append(tabla(campos_abast, [5*cm, 11*cm]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 9. INVENTARIO ACTUAL
    # ══════════════════════════════════════════════════════════════════════════
    story.append(BannerCabecera("9. Módulo: Inventario Actual"))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph(
        "Vista de solo lectura que muestra el stock actual de todos los insumos. "
        "Los datos se actualizan en tiempo real con cada compra, venta y ajuste.", S["body"]))

    story.append(Paragraph("<b>Columnas mostradas:</b>", S["h3"]))
    story.append(Paragraph("• <b>Código / ID:</b> Identificador único del insumo.", S["bullet"]))
    story.append(Paragraph("• <b>Nombre del Insumo:</b> Nombre descriptivo.", S["bullet"]))
    story.append(Paragraph("• <b>Categoría:</b> Grupo al que pertenece.", S["bullet"]))
    story.append(Paragraph("• <b>Stock Actual:</b> Cantidad disponible en la unidad base.", S["bullet"]))
    story.append(Paragraph("• <b>Unidad:</b> Unidad de medida del stock.", S["bullet"]))
    story.append(Paragraph("• <b>Costo Unitario:</b> Precio promedio por unidad.", S["bullet"]))
    story.append(Paragraph("• <b>Valor en Inventario:</b> Stock × Costo Unitario.", S["bullet"]))

    story.append(Spacer(1, 0.3*cm))
    story.append(info_box(
        "Los insumos con stock en cero o negativo aparecen resaltados en rojo. "
        "Esto también se refleja en el Dashboard como 'Stock Bajo'.", S, NARANJA, "⚠"))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 10. CONTEO DE INVENTARIO
    # ══════════════════════════════════════════════════════════════════════════
    story.append(BannerCabecera("10. Módulo: Conteo de Inventario",
                                "Conteos físicos con ajuste automático al kardex"))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph(
        "Permite realizar conteos físicos del inventario para corregir diferencias entre "
        "el stock del sistema y el stock real. Cada sesión de conteo pasa por tres estados.", S["body"]))

    estados = [
        ["Estado", "Color", "Descripción"],
        ["BORRADOR", "Gris", "Sesión creada pero no iniciada. Se puede eliminar."],
        ["EN_PROCESO", "Naranja", "Conteo en curso. Se están ingresando cantidades."],
        ["CERRADO", "Verde", "Conteo finalizado. Los ajustes ya se aplicaron al inventario."],
    ]
    story.append(tabla(estados, [3.5*cm, 2.5*cm, 10*cm]))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>Flujo de trabajo:</b>", S["h3"]))
    story.append(Paragraph(
        "1. <b>Crear sesión:</b> Definir nombre, fecha y categoría(s) de insumos a contar.", S["bullet"]))
    story.append(Paragraph(
        "2. <b>Iniciar conteo:</b> Cambiar estado a EN_PROCESO. El sistema muestra el stock "
        "del sistema vs. el campo para ingresar la cantidad contada.", S["bullet"]))
    story.append(Paragraph(
        "3. <b>Ingresar cantidades:</b> Para cada insumo, escribir la cantidad física encontrada. "
        "El sistema calcula la diferencia automáticamente.", S["bullet"]))
    story.append(Paragraph(
        "4. <b>Añadir motivo (opcional):</b> Para cada diferencia, se puede especificar la razón "
        "(merma, robo, error de registro, etc.).", S["bullet"]))
    story.append(Paragraph(
        "5. <b>Cerrar conteo:</b> Al cerrar, el sistema aplica todos los ajustes al inventario "
        "y registra cada diferencia en el kardex como 'AJUSTE_INVENTARIO'.", S["bullet"]))
    story.append(Paragraph(
        "6. <b>Generar PDF:</b> Se puede exportar el reporte del conteo en formato PDF.", S["bullet"]))

    story.append(Spacer(1, 0.2*cm))
    story.append(warning_box(
        "Una vez cerrado el conteo, no se puede reabrir ni modificar. Los ajustes al inventario "
        "son definitivos. Verifique los datos antes de cerrar.", S))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 11. PRESUPUESTOS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(BannerCabecera("11. Módulo: Presupuestos",
                                "Planificación mensual y control presupuestal"))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph(
        "El módulo de presupuestos permite crear presupuestos mensuales de compras, "
        "estimar los costos de insumos necesarios y hacer seguimiento de la ejecución "
        "real versus lo presupuestado.", S["body"]))

    story.append(Paragraph("<b>Crear un nuevo presupuesto:</b>", S["h3"]))
    campos_pres2 = [
        ["Campo", "Descripción"],
        ["Mes", "Mes al que aplica el presupuesto (1-12)"],
        ["Año", "Año del presupuesto"],
        ["Descripción", "Nombre o descripción del presupuesto"],
        ["Reporte Vinculado", "Reporte de ventas CSV importado que se usa como base de cálculo"],
    ]
    story.append(tabla(campos_pres2, [4.5*cm, 11.5*cm]))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>Ver / Editar Insumos del Presupuesto:</b>", S["h3"]))
    story.append(Paragraph(
        "Una vez creado el presupuesto, se puede acceder al detalle de insumos. El sistema "
        "puede calcular automáticamente los insumos necesarios basándose en:", S["body"]))
    story.append(Paragraph("• Las ventas proyectadas del reporte vinculado.", S["bullet"]))
    story.append(Paragraph("• Las recetas de cada ítem de menú.", S["bullet"]))
    story.append(Paragraph("• El costo unitario actual de cada insumo.", S["bullet"]))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>Control Presupuestal:</b>", S["h3"]))
    story.append(Paragraph(
        "La opción 'Control Presupuestal' muestra una comparativa entre lo presupuestado "
        "y las compras reales registradas para ese período. Incluye:", S["body"]))
    story.append(Paragraph("• Monto presupuestado por categoría.", S["bullet"]))
    story.append(Paragraph("• Monto ejecutado (compras reales vinculadas al presupuesto).", S["bullet"]))
    story.append(Paragraph("• Diferencia (favorable o desfavorable).", S["bullet"]))
    story.append(Paragraph("• Porcentaje de ejecución del presupuesto.", S["bullet"]))

    story.append(Spacer(1, 0.2*cm))
    story.append(info_box(
        "Para que las compras se reflejen en el control presupuestal, deben estar asociadas "
        "al número de presupuesto al momento de registrarlas en el módulo de Compras.", S, VERDE, "✓"))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 12. REPORTES
    # ══════════════════════════════════════════════════════════════════════════
    story.append(BannerCabecera("12. Módulo: Reportes de Ventas (Carga CSV)",
                                "Importación de datos desde el sistema POS"))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph(
        "Este módulo permite importar los reportes de ventas generados por el sistema POS "
        "(Point of Sale) en formato CSV. El sistema parsea el archivo, extrae los datos de "
        "ventas por producto y día, y los almacena para análisis.", S["body"]))

    story.append(Paragraph("<b>Pestaña: Cargar Nuevo Reporte</b>", S["h3"]))
    story.append(Paragraph(
        "1. Haga clic en <b>'Seleccionar Archivo CSV...'</b>.", S["bullet"]))
    story.append(Paragraph(
        "2. El sistema detecta automáticamente el período del reporte (fecha inicio y fin) "
        "y el porcentaje sugerido de costo.", S["bullet"]))
    story.append(Paragraph(
        "3. La tabla muestra los productos encontrados en el CSV.", S["bullet"]))
    story.append(Paragraph(
        "4. Las filas en <b>rojo</b> indican productos cuyo código no está registrado en el "
        "módulo de Menú. Debe registrarlos antes de guardar.", S["bullet"]))
    story.append(Paragraph(
        "5. Haga clic en <b>'Guardar Reporte'</b> para importar los datos.", S["bullet"]))

    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("<b>Información detectada automáticamente del CSV:</b>", S["h3"]))
    story.append(Paragraph("• Rango de fechas del período reportado.", S["bullet"]))
    story.append(Paragraph("• Porcentaje de costo sugerido (% sugerido del POS).", S["bullet"]))
    story.append(Paragraph("• Cantidad vendida por producto y por día.", S["bullet"]))
    story.append(Paragraph("• Total de ventas por producto.", S["bullet"]))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>Pestaña: Historial y Consultas</b>", S["h3"]))
    story.append(Paragraph(
        "Muestra todos los reportes importados previamente. Al seleccionar un reporte, "
        "se despliega el detalle de ventas por producto, con filtros de búsqueda.", S["body"]))

    story.append(Spacer(1, 0.2*cm))
    story.append(warning_box(
        "El archivo CSV debe estar en el formato generado por el sistema POS configurado. "
        "El sistema intenta detectar la codificación automáticamente (UTF-8, Latin-1, CP1252). "
        "Si el archivo no se parsea correctamente, verifique la fuente del CSV.", S))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 13. CONSOLIDADOS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(BannerCabecera("13. Módulo: Consolidados Financieros",
                                "Resumen general, chequera, tarjetas, efectivo, Yappy y diario"))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph(
        "El módulo de Consolidados agrupa todas las herramientas de control financiero "
        "del restaurante en un solo lugar, organizado en 6 pestañas.", S["body"]))

    # 13.1
    story.append(Paragraph("13.1 Resumen General Mensual", S["h2"]))
    story.append(Paragraph(
        "Vista consolidada del estado financiero del mes seleccionado. Incluye:", S["body"]))
    story.append(Paragraph("• <b>Total de ventas</b> por método de pago.", S["bullet"]))
    story.append(Paragraph("• <b>Total de gastos</b> por categoría.", S["bullet"]))
    story.append(Paragraph("• <b>Gráficas de dona:</b> distribución de ingresos y gastos.", S["bullet"]))
    story.append(Paragraph("• <b>Selector de mes/año</b> para navegar entre períodos.", S["bullet"]))
    story.append(Paragraph("• <b>Exportar CSV:</b> descarga el resumen en formato de hoja de cálculo.", S["bullet"]))

    # 13.2
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("13.2 Chequera", S["h2"]))
    story.append(Paragraph(
        "Registro de cheques emitidos por el restaurante. Permite llevar un control "
        "de los pagos realizados con cheque.", S["body"]))
    campos_cheq = [
        ["Campo", "Descripción"],
        ["Número de Cheque", "Número impreso en el cheque"],
        ["Fecha", "Fecha de emisión del cheque"],
        ["Beneficiario", "A quién se emitió el cheque"],
        ["Concepto", "Descripción del pago"],
        ["Monto", "Valor del cheque"],
        ["Estado", "Estado: Emitido, Cobrado, Anulado"],
    ]
    story.append(tabla(campos_cheq, [4.5*cm, 11.5*cm]))

    # 13.3
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("13.3 Tarjetas de Crédito", S["h2"]))
    story.append(Paragraph(
        "Gestión de las tarjetas de crédito corporativas del restaurante. Organizada en "
        "dos partes: el catálogo de tarjetas y el registro de transacciones.", S["body"]))

    story.append(Paragraph("<b>Datos de la tarjeta:</b>", S["h4"]))
    story.append(Paragraph("• Número de tarjeta (parcialmente enmascarado en la vista).", S["bullet"]))
    story.append(Paragraph("• Tipo: Visa, MasterCard, American Express, Diners Club, Otra.", S["bullet"]))
    story.append(Paragraph("• Banco emisor.", S["bullet"]))
    story.append(Paragraph("• Día de corte y día de pago.", S["bullet"]))
    story.append(Paragraph("• Tasa de interés.", S["bullet"]))

    story.append(Paragraph("<b>Registro de transacciones:</b>", S["h4"]))
    story.append(Paragraph("• Fecha, descripción, monto y categoría de cada cargo.", S["bullet"]))
    story.append(Paragraph("• La tarjeta debe seleccionarse del catálogo antes de registrar transacciones.", S["bullet"]))

    # 13.4
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("13.4 Pagos en Efectivo", S["h2"]))
    story.append(Paragraph(
        "Registro de todos los pagos y gastos realizados con dinero en efectivo. "
        "Permite categorizar cada pago para análisis financiero.", S["body"]))

    categorias_ef = [
        ["Categoría", "Descripción"],
        ["Costo de Víveres", "Compras de ingredientes básicos (vegetales, granos, etc.)"],
        ["Costo de Carnes", "Compras de carnes, aves y mariscos"],
        ["Desayunos", "Gastos de desayunos del personal u operativos"],
        ["Otros", "Gastos que no encajan en las otras categorías"],
        ["Planilla", "Pago de salarios y planilla"],
        ["Gastos Propietarios", "Gastos personales del propietario cargados al negocio"],
        ["Honorarios", "Pagos a profesionales o consultores externos"],
        ["Reparaciones y Mantenimiento", "Gastos de reparación de equipos o instalaciones"],
        ["Atención Empleados", "Alimentación o beneficios para empleados"],
        ["Combustible", "Gastos de combustible para vehículos del negocio"],
        ["Medicamentos", "Botiquín o medicamentos para el personal"],
    ]
    story.append(tabla(categorias_ef, [6*cm, 10*cm], OSCURO))

    story.append(Spacer(1, 0.2*cm))
    story.append(info_box(
        "Un pago en efectivo puede desglosarse en múltiples categorías. Por ejemplo, "
        "una compra en el mercado puede dividirse en Costo de Víveres y Costo de Carnes.", S))

    # 13.5
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("13.5 Pagos con Yappy", S["h2"]))
    story.append(Paragraph(
        "Yappy es el sistema de pagos digitales de Panamá. Este módulo registra "
        "los pagos realizados a proveedores o terceros mediante Yappy.", S["body"]))
    story.append(Paragraph("• Se administran las cuentas Yappy registradas.", S["bullet"]))
    story.append(Paragraph("• Se registran las transacciones con fecha, beneficiario y monto.", S["bullet"]))
    story.append(Paragraph("• Permite vincular el pago a un proveedor del catálogo.", S["bullet"]))

    # 13.6
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("13.6 Diario de Ventas", S["h2"]))
    story.append(Paragraph(
        "Registro diario del cierre de caja del restaurante. Es el módulo más usado "
        "en el día a día, pues permite registrar las ventas y conciliar la caja.", S["body"]))

    campos_diario = [
        ["Campo", "Descripción"],
        ["Fecha", "Fecha del día que se está registrando"],
        ["TOTAL VENTAS", "Calculado automáticamente: suma de todos los métodos de pago"],
        ["Pagos Yappy", "Ventas cobradas mediante Yappy ese día"],
        ["Pagos Pedidos Ya", "Ventas de plataforma de delivery Pedidos Ya"],
        ["Pagos Clave", "Ventas cobradas con clave bancaria (ACH / pago electrónico)"],
        ["Pagos Visa/MC", "Ventas cobradas con tarjetas de débito/crédito Visa o MasterCard"],
        ["Vale", "Monto de vales emitidos ese día"],
        ["Descripción del Vale", "Descripción del vale (aparece si el monto es > 0)"],
        ["No. Facturas", "Número total de facturas emitidas ese día"],
        ["Sobrante de Caja", "Diferencia positiva en la conciliación de caja"],
        ["Faltante de Caja", "Diferencia negativa en la conciliación de caja"],
        ["Depósitos", "Monto depositado en banco ese día"],
    ]
    story.append(tabla(campos_diario, [5*cm, 11*cm]))

    story.append(Spacer(1, 0.2*cm))
    story.append(info_box(
        "El campo TOTAL VENTAS es de solo lectura y se calcula automáticamente sumando: "
        "Yappy + Pedidos Ya + Clave + Visa/MC + Vale + Sobrante - Faltante.", S, AZUL))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 14. UNIDADES
    # ══════════════════════════════════════════════════════════════════════════
    story.append(BannerCabecera("14. Módulo: Unidades de Medida"))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph(
        "Administra el catálogo de unidades de medida usadas en el sistema. "
        "Las unidades son la base para el control de inventario.", S["body"]))

    story.append(Paragraph("<b>Campos:</b>", S["h3"]))
    story.append(Paragraph("• <b>Nombre:</b> Nombre completo de la unidad (ej: Kilogramo, Litro).", S["bullet"]))
    story.append(Paragraph("• <b>Abreviatura:</b> Forma corta de la unidad (ej: kg, L, und).", S["bullet"]))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>Conversiones de Unidades:</b>", S["h3"]))
    story.append(Paragraph(
        "Permite definir factores de conversión entre unidades (ej: 1 kg = 1000 g). "
        "Esto es útil cuando un insumo se compra en gramos pero se controla en kilogramos.", S["body"]))

    story.append(Spacer(1, 0.2*cm))
    story.append(info_box(
        "Ejemplo de unidades comunes preconfiguradas: kg (kilogramo), g (gramo), "
        "L (litro), ml (mililitro), und (unidad), caja, bolsa, lb (libra).", S))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 15. ADMINISTRACIÓN
    # ══════════════════════════════════════════════════════════════════════════
    story.append(BannerCabecera("15. Módulo: Administración",
                                "Usuarios y sucursales del sistema"))
    story.append(Spacer(1, 0.4*cm))

    # 15.1
    story.append(Paragraph("15.1 Usuarios", S["h2"]))
    story.append(Paragraph(
        "Gestiona las cuentas de acceso al sistema. Solo los administradores pueden "
        "crear, editar o eliminar usuarios.", S["body"]))

    campos_user = [
        ["Campo", "Descripción"],
        ["Nombre de Usuario", "Identificador único para iniciar sesión"],
        ["Nombre Completo", "Nombre real del empleado"],
        ["Contraseña", "Contraseña (se guarda encriptada con SHA-256)"],
        ["Rol", "Administrador: acceso total | Empleado: acceso limitado"],
        ["Activo", "Si el usuario puede iniciar sesión"],
    ]
    story.append(tabla(campos_user, [5*cm, 11*cm]))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>Roles del sistema:</b>", S["h3"]))
    roles = [
        ["Rol", "Permisos"],
        ["Administrador", "Acceso completo a todos los módulos, incluyendo gestión de usuarios"],
        ["Empleado", "Acceso a módulos operativos (compras, inventario, ventas). "
                     "Sin acceso a configuración y administración de usuarios."],
    ]
    story.append(tabla(roles, [4*cm, 12*cm], MORADO))

    story.append(Spacer(1, 0.2*cm))
    story.append(warning_box(
        "No es posible eliminar el usuario administrador principal (admin) ni el propio "
        "usuario con el que se inició sesión actualmente.", S))

    # 15.2
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("15.2 Sucursales", S["h2"]))
    story.append(Paragraph(
        "Registra las diferentes ubicaciones del restaurante para el control de inventario "
        "descentralizado y las transferencias internas.", S["body"]))

    campos_suc = [
        ["Campo", "Descripción"],
        ["Nombre", "Nombre de la sucursal (ej: Sede Principal, Sucursal Norte)"],
        ["Dirección", "Dirección física de la sucursal"],
        ["Teléfono", "Número de contacto"],
        ["Es Principal", "Indica si es la sucursal principal del negocio"],
    ]
    story.append(tabla(campos_suc, [4*cm, 12*cm]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 16. KARDEX
    # ══════════════════════════════════════════════════════════════════════════
    story.append(BannerCabecera("16. Kardex — Trazabilidad del Inventario",
                                "Historial completo de todos los movimientos de stock"))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph(
        "El kardex es el registro histórico de todos los cambios que ha tenido el stock "
        "de cada insumo. Funciona de forma automática en segundo plano: el usuario no necesita "
        "registrarlo manualmente.", S["body"]))

    story.append(Paragraph("<b>Tipos de movimiento registrados:</b>", S["h3"]))
    tipos_mv = [
        ["Tipo", "Cuándo se genera"],
        ["ENTRADA", "Al registrar una compra a un proveedor"],
        ["SALIDA", "Al deducir stock por ventas (si aplica según configuración)"],
        ["AJUSTE_INVENTARIO", "Al cerrar un conteo de inventario con diferencias"],
        ["TRANSFERENCIA_ENTRADA", "Al recibir un abastecimiento interno"],
        ["TRANSFERENCIA_SALIDA", "Al enviar un abastecimiento interno"],
    ]
    story.append(tabla(tipos_mv, [5*cm, 11*cm]))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>Datos registrados en cada movimiento:</b>", S["h3"]))
    story.append(Paragraph("• Insumo afectado.", S["bullet"]))
    story.append(Paragraph("• Tipo de movimiento.", S["bullet"]))
    story.append(Paragraph("• Cantidad del movimiento.", S["bullet"]))
    story.append(Paragraph("• Stock anterior al movimiento.", S["bullet"]))
    story.append(Paragraph("• Stock nuevo después del movimiento.", S["bullet"]))
    story.append(Paragraph("• Referencia (ID de compra, conteo, etc.).", S["bullet"]))
    story.append(Paragraph("• Observación o motivo.", S["bullet"]))
    story.append(Paragraph("• Fecha y hora del registro.", S["bullet"]))

    story.append(Spacer(1, 0.2*cm))
    story.append(info_box(
        "El kardex garantiza que siempre se pueda auditar qué pasó con el inventario, "
        "quién realizó el movimiento y cuándo. Es el historial oficial del stock.", S, VERDE, "✓"))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 17. SUPUESTOS Y REGLAS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(BannerCabecera("17. Supuestos y Reglas del Sistema"))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph(
        "A continuación se documentan los supuestos de diseño y las reglas de negocio "
        "que se asumieron al desarrollar el sistema:", S["body"]))

    supuestos = [
        ("Moneda", "Todos los valores monetarios se manejan en dólares americanos (USD). "
                   "No hay conversión de divisas."),
        ("Zona horaria", "Las fechas se registran en la zona horaria del sistema operativo del equipo."),
        ("Método de costeo", "El costo unitario de los insumos se calcula a partir del precio "
                             "de la presentación de compra más reciente. No usa FIFO, LIFO ni promedio ponderado automático."),
        ("Stock negativo", "El sistema permite que el stock quede en negativo si hay más salidas "
                           "que entradas. Esto se toma como una alerta, no como un error bloqueante."),
        ("CSV del POS", "El módulo de carga de reportes asume un formato CSV jerárquico específico "
                        "del sistema POS utilizado. Si cambia el POS, puede ser necesario adaptar el parser."),
        ("Un usuario activo", "No existe control de sesiones concurrentes. El sistema no impide que "
                              "dos usuarios abran la aplicación en el mismo equipo simultáneamente."),
        ("Base de datos local", "SQLite no requiere servidor. La base de datos es un archivo local. "
                                "Para respaldo, se debe copiar el archivo restaurante.db."),
        ("Cálculo del Total Ventas (Diario)", "El total de ventas del Diario de Ventas se calcula como: "
                                             "Yappy + Pedidos Ya + Clave + Visa/MC + Vale + Sobrante - Faltante. "
                                             "Las ventas en efectivo se deducen por diferencia si se conocen los otros métodos."),
        ("Conteo de inventario", "Los ajustes de un conteo cerrado no pueden revertirse directamente. "
                                 "Si se necesita corregir un error, se debe crear un nuevo conteo o ajuste manual."),
        ("Presupuesto y compras", "Solo las compras marcadas con el número de presupuesto correspondiente "
                                  "se contabilizan en el control presupuestal."),
        ("Rol de empleado", "El sistema diferencia entre Admin y Empleado, pero los permisos específicos "
                            "por módulo no están implementados a nivel de menú en esta versión."),
        ("Exportación de datos", "Los módulos de Consolidados y Diario de Ventas permiten exportar a CSV. "
                                  "El módulo de Conteo permite exportar a PDF vía ReportLab."),
        ("Yappy", "Yappy es el sistema de pagos digitales de Panamá. Su presencia en el sistema "
                  "refleja el mercado local donde opera el restaurante."),
        ("Pedidos Ya", "Es la plataforma de delivery más usada en Panamá. Las ventas por delivery "
                       "se registran como método de pago separado en el Diario de Ventas."),
    ]

    for titulo, desc in supuestos:
        story.append(KeepTogether([
            Paragraph(f"<b>• {titulo}:</b>", S["h4"]),
            Paragraph(desc, S["body"]),
            Spacer(1, 0.15*cm),
        ]))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 18. SOLUCIÓN DE PROBLEMAS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(BannerCabecera("18. Solución de Problemas Frecuentes"))
    story.append(Spacer(1, 0.4*cm))

    problemas = [
        ("No puedo iniciar sesión",
         "Verifique que el usuario y la contraseña sean correctos. "
         "La contraseña distingue entre mayúsculas y minúsculas. "
         "Si olvidó la contraseña del admin, contacte al equipo técnico para restablecer el hash en la base de datos."),
        ("El CSV no se carga correctamente",
         "Asegúrese de que el archivo fue generado por el sistema POS configurado. "
         "El archivo no debe estar abierto en Excel u otro programa al momento de cargarlo. "
         "Pruebe guardar el CSV con codificación UTF-8 desde Excel antes de cargarlo."),
        ("Un insumo no aparece en las compras",
         "Verifique que el insumo tenga al menos una Presentación de Compra registrada en "
         "el módulo de Insumos y Costos > Pestaña 2."),
        ("El stock no se actualizó después de una compra",
         "Verifique que la compra fue guardada correctamente. Revise el kardex del insumo "
         "para ver si el movimiento de ENTRADA aparece registrado."),
        ("Los productos del CSV aparecen en rojo",
         "El código del producto en el CSV no coincide con ningún código registrado en el "
         "módulo de Menú. Registre el producto en el menú con el código exacto del POS."),
        ("El presupuesto no muestra ejecución",
         "Asegúrese de que las compras del período están vinculadas al número de presupuesto "
         "correcto. El campo 'Presupuesto Asociado' en el formulario de compra debe tener el ID correcto."),
        ("El sistema está lento",
         "Si la base de datos ha crecido mucho, considere hacer un respaldo y optimizarla. "
         "SQLite puede degradarse con tablas de más de 1 millón de registros sin índices. "
         "También verifique que no haya otros programas consumiendo recursos del equipo."),
        ("No puedo eliminar un insumo",
         "El insumo tiene registros asociados (compras, movimientos, recetas). "
         "No se puede eliminar para mantener la integridad histórica. "
         "Si ya no se usa, márquelo como inactivo en lugar de eliminarlo."),
        ("¿Cómo hago una copia de seguridad?",
         "La base de datos está en el archivo restaurante.db dentro de la carpeta 'data' del sistema. "
         "Copie ese archivo a una unidad USB o servicio en la nube regularmente. "
         "Para restaurar, simplemente reemplace el archivo."),
        ("La gráfica del dashboard no muestra datos",
         "Asegúrese de tener registros en el Diario de Ventas para el mes en curso. "
         "Las gráficas se alimentan de los datos del módulo de Diario de Ventas."),
    ]

    for titulo, desc in problemas:
        story.append(KeepTogether([
            Paragraph(f"<b>• {titulo}</b>", S["h4"]),
            Paragraph(desc, S["body"]),
            Spacer(1, 0.2*cm),
        ]))

    # ─── PIE FINAL ────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Spacer(1, 4*cm))

    fin_data = [[Paragraph(
        "<b>Manual de Usuario — ItalosManager</b><br/>"
        f"Generado el {datetime.date.today().strftime('%d de %B de %Y')}<br/>"
        "Este documento es de uso interno y confidencial.",
        ParagraphStyle("fin", fontSize=11, textColor=BLANCO,
                       alignment=TA_CENTER, fontName="Helvetica", leading=18))]]
    fin_tbl = Table(fin_data, colWidths=[PAGE_W - 4*cm])
    fin_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ROJO),
        ("TOPPADDING",  (0, 0), (-1, -1), 30),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 30),
        ("LEFTPADDING", (0, 0), (-1, -1), 20),
        ("RIGHTPADDING",(0, 0), (-1, -1), 20),
    ]))
    story.append(fin_tbl)

    return story


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    output = "docs/Manual_de_Usuario_ItalosManager.pdf"

    import os
    os.makedirs("docs", exist_ok=True)

    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=2.2*cm,
        bottomMargin=2*cm,
        title="Manual de Usuario — ItalosManager",
        author="ItalosManager",
        subject="Sistema de Gestión de Restaurante",
    )

    S = build_styles()
    story = build_story(S)

    doc.build(story,
              onFirstPage=primera_pagina,
              onLaterPages=paginas_siguientes)

    print(f"\nManual generado exitosamente: {output}")
    print(f"  Tamano: {os.path.getsize(output) / 1024:.1f} KB")

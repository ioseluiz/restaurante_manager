"""Cálculo del bloque de compras del Presupuesto — fuente única para «generar» y «recalcular».

Sin dependencias de Qt. A partir de los reportes del POS elegidos:

1. Promedio por plato y día de la semana (Prom/Med) entre los reportes (ausente = 0).
2. Platos del mes = Σ promedios de los 7 días × SEMANAS_POR_MES.
3. Requerido por insumo = platos del mes × cantidad por porción (v_recetas_explotadas) × (1 + % / 100).
   El % es el promedio del % sugerido de los reportes, o el ajustado a mano para ese insumo.
4. Empaques para llevar: los extras de tipo EMPAQUE del plato (Costo de Platos) se compran según el
   «% de platos para llevar» (costeo_config.pct_platos_llevar): canal LLEVAR × %, LOCAL × (1 − %),
   AMBOS × 1. La caja no los registra, a diferencia de acompañamientos y bebidas, que son líneas propias.
5. A comprar = ⌈ requerido / contenido de la presentación preferida ⌉ × su precio
   (sin presentación: ⌈ requerido ⌉ × costo promedio del insumo).
"""
import math

from app.controllers.costeo_controller import peso_canal_empaque, pct_platos_llevar
from app.database.costeo_sql import SQL_ORDEN_PRESENTACION

SEMANAS_POR_MES = 4.0

DIAS_VALIDOS = {
    "lunes", "martes", "miercoles", "miércoles", "jueves", "viernes", "sabado", "sábado", "domingo",
    "lun", "mar", "mie", "jue", "vie", "sab", "dom",
}

_CANAL_EMPAQUE = {"LLEVAR": "para llevar", "LOCAL": "en local", "AMBOS": "todos los platos"}


def promedio_pct_sugerido(db, reportes_ids):
    ph = ",".join(["?"] * len(reportes_ids))
    row = db.fetch_one(f"SELECT AVG(porcentaje_sugerido) FROM reportes_ventas WHERE id IN ({ph})",
                       tuple(reportes_ids))
    return float(row[0]) if row and row[0] else 0.0


def ventas_mensuales(db, reportes_ids):
    """{codigo: {"dias": {dia: promedio}, "total_mensual": platos del mes}}."""
    ph = ",".join(["?"] * len(reportes_ids))
    filas = db.fetch_all(
        f"SELECT reporte_id, codigo_producto, LOWER(dia_semana), SUM(promedio_medida) "
        f"FROM detalle_reportes_ventas WHERE reporte_id IN ({ph}) "
        f"GROUP BY reporte_id, codigo_producto, LOWER(dia_semana)",
        tuple(reportes_ids),
    )
    por_producto = {}
    for _rep, cod, dia, cant in filas:
        dia = str(dia).strip().lower()
        if dia in DIAS_VALIDOS:
            por_producto.setdefault(cod, {}).setdefault(dia, []).append(cant)

    total_reportes = len(reportes_ids)
    resultado = {}
    for cod, dias in por_producto.items():
        detalle = {dia: sum(cants) / total_reportes for dia, cants in dias.items()}
        resultado[cod] = {"dias": detalle, "total_mensual": sum(detalle.values()) * SEMANAS_POR_MES}
    return resultado


def _consumos_por_plato(db, cod, pct_llevar):
    """[(insumo_id, nombre, categoria, cantidad por plato vendido, etiqueta, unidad)] del plato con
    código `cod`: su receta explotada y los insumos de sus empaques ponderados por canal."""
    filas = [
        (ins_id, nom, cat, cant, menu_nom, abrev)
        for ins_id, nom, cat, cant, menu_nom, abrev in db.fetch_all(
            """SELECT r.insumo_id, i.nombre, c.nombre, r.cantidad_necesaria, m.nombre, u.abreviatura
               FROM v_recetas_explotadas r
               JOIN menu_items m ON r.menu_item_id = m.id
               JOIN insumos i ON r.insumo_id = i.id
               LEFT JOIN categorias_insumos c ON i.categoria_id = c.id
               LEFT JOIN unidades_medida u ON i.unidad_base_id = u.id
               WHERE m.codigo = ?""",
            (cod,),
        )
    ]
    for ins_id, nom, cat, cant, menu_nom, abrev, porciones, canal in db.fetch_all(
        """SELECT r.insumo_id, i.nombre, c.nombre, r.cantidad_necesaria, m.nombre, u.abreviatura,
                  e.cantidad_porciones, e.canal
           FROM plato_extras e
           JOIN menu_items m ON m.id = e.menu_item_id
           JOIN v_recetas_explotadas r ON r.menu_item_id = e.componente_id
           JOIN insumos i ON r.insumo_id = i.id
           LEFT JOIN categorias_insumos c ON i.categoria_id = c.id
           LEFT JOIN unidades_medida u ON i.unidad_base_id = u.id
           WHERE m.codigo = ? AND e.tipo = 'EMPAQUE'""",
        (cod,),
    ):
        peso = peso_canal_empaque(canal, pct_llevar)
        if peso <= 0:
            continue
        etiqueta = f"{menu_nom} — empaque {_CANAL_EMPAQUE.get(canal, canal)}"
        if canal == "LLEVAR":
            etiqueta += f" ({pct_llevar * 100:g} % de los platos)"
        elif canal == "LOCAL":
            etiqueta += f" ({(1 - pct_llevar) * 100:g} % de los platos)"
        filas.append((ins_id, nom, cat, (cant or 0.0) * float(porciones or 0) * peso, etiqueta, abrev))
    return filas


def calcular_compras(db, reportes_ids, pcts_por_insumo=None):
    """Bloque de compras del presupuesto. `pcts_por_insumo` = {nombre de insumo: %} ajustados a mano
    (se conservan al recalcular). Devuelve (detalles, total); cada detalle es la tupla
    (categoria, insumo, unidad de compra, cantidad a comprar, monto, items_menu, detalle_html, % usado)."""
    pcts_por_insumo = pcts_por_insumo or {}
    avg_pct = promedio_pct_sugerido(db, reportes_ids)
    pct_llevar = pct_platos_llevar(db)

    insumos_calc = {}
    for cod, info_ventas in ventas_mensuales(db, reportes_ids).items():
        ventas_totales = info_ventas["total_mensual"]
        if ventas_totales <= 0:
            continue
        for ins_id, ins_nom, cat_nom, cant_nec, menu_nom, abrev_uni in _consumos_por_plato(db, cod, pct_llevar):
            pct_usado = pcts_por_insumo.get(ins_nom, avg_pct)
            factor_val = 1.0 + (pct_usado / 100.0)
            cant_amplificada = (ventas_totales * cant_nec) * factor_val

            data = insumos_calc.setdefault(ins_id, {
                "nombre": ins_nom,
                "categoria": cat_nom or "Sin Categoría",
                "unidad_base": abrev_uni or "Und.",
                "pct_usado": pct_usado,
                "factor": factor_val,
                "qty_base_total": 0.0,
                "items_menu": {},
            })
            data["qty_base_total"] += cant_amplificada
            item = data["items_menu"].setdefault(menu_nom, {
                "ventas_dias": info_ventas["dias"],
                "ventas_mensual": ventas_totales,
                "receta_cant": cant_nec,
                "total_plato": 0.0,
            })
            item["total_plato"] += cant_amplificada

    total = 0.0
    detalles = []
    for ins_id, data in insumos_calc.items():
        pres = db.fetch_one(
            f"SELECT cantidad_contenido, precio_compra, nombre FROM presentaciones_compra "
            f"WHERE insumo_id = ? ORDER BY {SQL_ORDEN_PRESENTACION} LIMIT 1",
            (ins_id,),
        )
        if pres and pres[0] > 0:
            contenido, precio, unidad_compra = pres
            exacta = data["qty_base_total"] / contenido
            precio_info = ("presentacion", contenido, precio, unidad_compra)
        else:
            row = db.fetch_one("SELECT costo_unitario FROM insumos WHERE id = ?", (ins_id,))
            precio = row[0] if row and row[0] else 0.0
            exacta = data["qty_base_total"]
            unidad_compra = data["unidad_base"]
            precio_info = ("base", None, precio, unidad_compra)
        a_comprar = math.ceil(exacta)
        monto = a_comprar * precio
        total += monto

        items_str = "\n".join(f"• {k} ({v['total_plato']:.2f})" for k, v in data["items_menu"].items())
        detalles.append((
            data["categoria"], data["nombre"], unidad_compra, a_comprar, monto, items_str,
            _detalle_html(data, precio_info, exacta, a_comprar, monto), data["pct_usado"],
        ))
    return detalles, total


def _detalle_html(data, precio_info, exacta, a_comprar, monto):
    """Explicación del cálculo de un insumo (diálogo «Detalle» del presupuesto)."""
    abrev_base = data["unidad_base"]
    factor_val = data["factor"]
    tipo, contenido, precio, unidad_compra = precio_info

    h = "<div style='font-family: Arial, sans-serif;'>"
    h += (f"<h3 style='color:#2c3e50; border-bottom: 2px solid #bdc3c7; padding-bottom: 5px;'>"
          f"Detalle de Cálculo: {data['nombre']}</h3>")
    h += "<table width='100%' style='margin-bottom: 15px;'><tr>"
    h += f"<td width='50%'><b>Unidad Base Recetas:</b> {abrev_base}</td>"
    h += (f"<td width='50%'><b>Porcentaje Sugerido Aplicado:</b> {data['pct_usado']:.2f}% "
          f"(Factor: {factor_val:.2f})</td>")
    h += "</tr></table>"

    if tipo == "presentacion":
        h += ("<div style='background-color: #e8f8f5; padding: 10px; border-radius: 4px; "
              "border: 1px solid #1abc9c; margin-bottom: 15px;'>")
        h += f"<b>Presentación de Compra:</b> {unidad_compra}<br>"
        h += f"<b>Contenido:</b> {contenido} {abrev_base}<br>"
        h += f"<b>Precio:</b> ${precio:,.2f}"
        h += "</div>"
    else:
        h += ("<div style='background-color: #fcf3cf; padding: 10px; border-radius: 4px; "
              "border: 1px solid #f1c40f; margin-bottom: 15px;'>")
        h += "<i>No tiene presentación de compra asignada. Se calcula sobre unidad base.</i><br>"
        h += f"<b>Precio Unitario (Base):</b> ${precio:,.2f}"
        h += "</div>"

    h += "<h4 style='color:#2980b9;'>1. Requerimiento por Platos de Menú</h4>"
    factor_str = f" x {factor_val:.2f} (Factor)" if factor_val != 1.0 else ""
    for m_nom, m_info in data["items_menu"].items():
        dias_format = " | ".join(f"{d[:3].capitalize()}: {v:.1f}" for d, v in m_info["ventas_dias"].items())
        h += ("<div style='margin-bottom: 10px; padding: 10px; border-left: 4px solid #3498db; "
              "background-color: #f8f9fa; border-radius: 0 4px 4px 0;'>")
        h += f"<b style='color:#2c3e50; font-size: 14px;'>{m_nom}</b><br>"
        h += "<table width='100%' style='font-size: 12px; margin-top: 5px; color: #555;'>"
        h += f"<tr><td width='35%'><b>Ventas Diario (Promedio):</b></td><td>[{dias_format}]</td></tr>"
        h += (f"<tr><td><b>Ventas Mensual Proyectado:</b></td>"
              f"<td>{m_info['ventas_mensual']:.2f} platos vendidos</td></tr>")
        h += (f"<tr><td><b>Requerido en Receta:</b></td>"
              f"<td>{m_info['receta_cant']:.4f} {abrev_base} por plato</td></tr>")
        h += "</table>"
        h += ("<div style='margin-top: 6px; padding-top: 6px; border-top: 1px dashed #ccc; "
              "font-family: monospace; font-size: 13px;'>")
        h += (f"Fórmula: {m_info['ventas_mensual']:.2f} platos x {m_info['receta_cant']:.4f} {abrev_base}"
              f"{factor_str} = <b style='color: #c0392b;'>{m_info['total_plato']:.2f} {abrev_base}</b>")
        h += "</div></div>"

    h += "<h4 style='color:#27ae60; margin-top: 20px;'>2. Conversión a Compras y Costo Final</h4>"
    h += ("<ul style='font-size: 14px; background-color: #ecf0f1; padding: 15px 15px 15px 35px; "
          "border-radius: 5px;'>")
    h += (f"<li style='margin-bottom: 5px;'><b>Total Base Requerido (Suma Platos):</b> "
          f"{data['qty_base_total']:.2f} {abrev_base}</li>")
    h += f"<li style='margin-bottom: 5px;'><b>Cantidad Exacta de Compra:</b> {exacta:.2f} {unidad_compra}</li>"
    h += ("<li style='margin-bottom: 5px; color: #c0392b;'><b>Cantidad a Comprar (Redondeada):</b> "
          "<span style='background-color:#f1c40f; padding: 2px 5px; border-radius: 3px; font-weight: bold; "
          f"color: #2c3e50;'>{int(a_comprar)} {unidad_compra}</span></li>")
    h += f"<li><b>Costo Estimado:</b> ${monto:,.2f}</li>"
    h += "</ul></div>"
    return h

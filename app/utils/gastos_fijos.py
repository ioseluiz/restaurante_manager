"""Utilidades para la etiqueta 'tipo de gasto' de los egresos de consolidados.

La lista de conceptos proviene del mismo catálogo que usan los presupuestos
(`gastos_fijos_catalogo`), de modo que lo ejecutado en consolidados se pueda
vincular con los gastos fijos presupuestados.
"""

OPCION_NINGUNO = "— Ninguno —"


def listar_conceptos(db):
    """Devuelve la lista de conceptos del catálogo de gastos fijos."""
    try:
        return [c for (c,) in db.fetch_all(
            "SELECT concepto FROM gastos_fijos_catalogo ORDER BY concepto"
        )]
    except Exception:
        return []


def poblar_combo(db, combo, seleccionado=None):
    """Llena un QComboBox con la opción 'Ninguno' + los conceptos del catálogo.
    Si 'seleccionado' se pasa y existe, lo deja como valor actual."""
    combo.clear()
    combo.addItem(OPCION_NINGUNO)
    for concepto in listar_conceptos(db):
        combo.addItem(concepto)
    if seleccionado:
        idx = combo.findText(seleccionado)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        else:
            combo.setCurrentIndex(0)
    else:
        combo.setCurrentIndex(0)


def valor_combo(combo):
    """Devuelve el concepto elegido, o None si es 'Ninguno'."""
    texto = combo.currentText().strip()
    if not texto or texto == OPCION_NINGUNO:
        return None
    return texto

"""Código propio de los insumos (#V002, #IC005, #C018… en las fichas del cliente)."""

import re


def normalizar_codigo_insumo(texto):
    """'#v002 ' -> 'V002'. Cadena vacía si no hay código. Se guarda así en insumos.codigo."""
    return re.sub(r"[\s#]+", "", str(texto or "")).upper()


def es_codigo_subreceta(texto):
    """Los códigos solo numéricos (#200 guizos, #203 salsa espesor) son sub-recetas o platos, no insumos."""
    return bool(re.fullmatch(r"\d+", normalizar_codigo_insumo(texto)))

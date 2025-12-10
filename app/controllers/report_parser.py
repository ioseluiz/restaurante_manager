import csv


class ReportParser:
    """
    Clase encargada de interpretar archivos CSV con formatos específicos
    (encabezados irregulares, metadatos en primeras líneas, etc).
    """

    @staticmethod
    def parse_csv(file_path):
        metadata = {"desde": "N/A", "hasta": "N/A"}
        records = []
        lines = []

        # 1. Lectura robusta del archivo (Encoding)
        try:
            with open(file_path, "r", encoding="latin-1") as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            except Exception as e:
                return metadata, records, f"Error de codificación: {str(e)}"
        except Exception as e:
            return metadata, records, f"Error leyendo archivo: {str(e)}"

        # Variables de estado
        current_code = ""
        current_desc = ""
        header_found = False

        try:
            for line_idx, line in enumerate(lines):
                # El delimitador es punto y coma (;) según tu temp_code.py
                cells = [c.strip() for c in line.split(";")]

                # -- A. Extraccion de Metadatos ---
                if line_idx < 20:
                    if "Desde" in cells:
                        metadata["desde"] = ReportParser._find_next_value(
                            cells, "Desde"
                        )
                    if "Hasta" in cells:
                        metadata["hasta"] = ReportParser._find_next_value(
                            cells, "Hasta"
                        )

                # -- B. Deteccion de Inicio de Datos ---
                if "Código" in cells and "Descripción" in cells:
                    header_found = True
                    continue

                if not header_found:
                    continue

                # -- C. Mapeo de Columnas (Hardcoded según tu formato) ---
                # Validamos longitudes para evitar IndexError
                val_code_1 = cells[1] if len(cells) > 1 else ""
                val_code_2 = cells[2] if len(cells) > 2 else ""
                val_desc_5 = cells[5] if len(cells) > 5 else ""
                val_desc_6 = cells[6] if len(cells) > 6 else ""

                val_day = cells[7] if len(cells) > 7 else ""
                val_qty = cells[10] if len(cells) > 10 else ""
                val_sales = cells[24] if len(cells) > 24 else ""

                # Actualizar contexto (si la fila trae el código pero no el total, guardamos el dato)
                if val_code_1:
                    current_code = val_code_1
                if val_code_2:
                    current_code = val_code_2
                if val_desc_5:
                    current_desc = val_desc_5
                if val_desc_6:
                    current_desc = val_desc_6

                # -- D. Identificar filas de TOTAL ---
                # Criterio: NO tiene día, SI tiene cantidad y ventas
                is_total_row = (
                    not val_day
                    and val_qty
                    and val_sales
                    and not val_code_1
                    and not val_code_2
                )

                if is_total_row:
                    # Limpieza de números (quitar 'B/.', comas, espacios)
                    qty_clean = val_qty.replace(",", "")
                    sales_clean = (
                        val_sales.replace("B/.", "")
                        .replace("B/", "")
                        .replace(",", "")
                        .strip()
                    )

                    records.append(
                        {
                            "code": current_code,
                            "desc": current_desc,
                            "qty": float(qty_clean) if qty_clean else 0.0,
                            "total": float(sales_clean) if sales_clean else 0.0,
                        }
                    )

            return metadata, records, None  # None = Sin errores

        except Exception as e:
            return metadata, records, f"Error procesando líneas: {str(e)}"

    @staticmethod
    def _find_next_value(cells, key):
        try:
            idx = cells.index(key)
            for i in range(idx + 1, len(cells)):
                if cells[i].strip():
                    return cells[i].strip()
        except ValueError:
            pass
        return "N/A"

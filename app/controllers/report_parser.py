import unicodedata


class ReportParser:
    """
    Clase encargada de interpretar archivos CSV del reporte de ventas MENSUAL.
    Adaptada para leer estructura jerárquica (Categoria/Producto -> Filas de días).
    """

    @staticmethod
    def normalize_text(text):
        """Elimina acentos y convierte a minúsculas."""
        if not text:
            return ""
        return (
            "".join(
                c
                for c in unicodedata.normalize("NFD", text)
                if unicodedata.category(c) != "Mn"
            )
            .lower()
            .strip()
        )

    @staticmethod
    def clean_currency(value_str):
        """Limpia cadenas como 'B/.1,234.56' o '-B/.10.00' a float."""
        if not value_str:
            return 0.0

        # Manejo de negativos y símbolos
        clean = value_str.replace("B/.", "").replace("B/", "").replace(",", "").strip()

        # A veces el negativo viene antes del B/. (ej -B/.10) o después
        # La limpieza anterior deja "-10" o "10-". Python maneja "-10".
        try:
            return float(clean)
        except ValueError:
            return 0.0

    @staticmethod
    def parse_csv(file_path):
        metadata = {"desde": "N/A", "hasta": "N/A"}
        records = []

        lines = []
        encodings = ["utf-8", "latin-1", "cp1252"]
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    lines = f.readlines()
                break
            except UnicodeDecodeError:
                continue

        if not lines:
            return metadata, records, "Error: No se pudo leer el archivo."

        # Variables de estado
        current_product_desc = "DESCONOCIDO"
        valid_days_norm = [
            "domingo",
            "lunes",
            "martes",
            "miercoles",
            "jueves",
            "viernes",
            "sabado",
        ]

        # Índices esperados (basados en el ejemplo proporcionado)
        # Código: col 1
        # Desc Header: col 5
        # Día: col 7 (índice 7 si empieza en 0)
        # Cantidad: col 10
        # Promedio: col 12 (aprox)
        # Total Venta: col 26 (aprox)
        # Costo y Utilidad: suelen estar después de Venta

        try:
            for line_idx, line in enumerate(lines):
                cells = [c.strip() for c in line.split(";")]
                cells_norm = [ReportParser.normalize_text(c) for c in cells]

                # 1. Extracción de Metadatos (Fechas)
                if line_idx < 15:
                    for i, cell in enumerate(cells_norm):
                        if "desde" in cell and i + 1 < len(cells):
                            # Buscar valor en celdas adyacentes vacías
                            val = ReportParser._find_next_value(cells, i)
                            if val:
                                metadata["desde"] = val
                        if "hasta" in cell and i + 1 < len(cells):
                            val = ReportParser._find_next_value(cells, i)
                            if val:
                                metadata["hasta"] = val

                # 2. Detección de filas
                if len(cells) < 8:
                    continue

                col_1_code = cells[1]
                col_5_desc = cells[5] if len(cells) > 5 else ""
                col_7_day = cells[7] if len(cells) > 7 else ""

                norm_day = ReportParser.normalize_text(col_7_day)

                # CASO A: Fila de Encabezado de Producto (Tiene descripción en col 5, código vacío en col 1)
                # Ejemplo: ;;;;;PAPITAS FRITAS;;;;...
                if (
                    not col_1_code
                    and col_5_desc
                    and "promed" not in ReportParser.normalize_text(col_5_desc)
                ):
                    # Evitar capturar encabezados de tabla como "Descripción"
                    if "descripcion" not in ReportParser.normalize_text(col_5_desc):
                        current_product_desc = col_5_desc

                # CASO B: Fila de Datos (Tiene Código y tiene Día válido)
                # Ejemplo: ;ACOMP01;;;;;;Domingo...
                if col_1_code and norm_day in valid_days_norm:
                    # Extracción de valores numéricos
                    # Cantidad suele estar en índice 10
                    qty_raw = cells[10] if len(cells) > 10 else "0"

                    # Promedio suele estar alrededor del 12
                    prom_raw = "0"
                    if len(cells) > 12:
                        # Buscar alrededor del índice 12
                        for offset in range(3):
                            idx = 12 + offset
                            if idx < len(cells) and cells[idx].strip():
                                prom_raw = cells[idx]
                                break

                    # Total Venta suele estar lejos, índice 26 o buscamos "B/."
                    total_venta_raw = "0"
                    total_costo_raw = "0"
                    total_util_raw = "0"

                    # Búsqueda heurística de montos monetarios desde la columna del día hacia adelante
                    money_values = []
                    for k in range(14, len(cells)):
                        if "B/." in cells[k] or "B/" in cells[k]:
                            money_values.append(cells[k])

                    # Asignación tentativa (Venta, Costo, Utilidad)
                    if len(money_values) >= 1:
                        total_venta_raw = money_values[0]
                    if len(money_values) >= 2:
                        total_costo_raw = money_values[1]
                    if len(money_values) >= 3:
                        total_util_raw = money_values[2]

                    # Parsear floats
                    try:
                        qty = float(qty_raw.replace(",", ""))
                        prom = (
                            float(prom_raw.replace(",", ""))
                            if prom_raw.replace(".", "").isdigit()
                            else 0.0
                        )
                        total_venta = ReportParser.clean_currency(total_venta_raw)
                        total_costo = ReportParser.clean_currency(total_costo_raw)
                        total_util = ReportParser.clean_currency(total_util_raw)

                        records.append(
                            {
                                "code": col_1_code,
                                "desc": current_product_desc,  # Usamos la descripción capturada previamente
                                "day": col_7_day,
                                "qty": qty,
                                "prom": prom,
                                "total_venta": total_venta,
                                "total_costo": total_costo,
                                "total_utilidad": total_util,
                            }
                        )

                    except ValueError:
                        continue

            return metadata, records, None

        except Exception as e:
            return metadata, records, f"Error inesperado parsing: {str(e)}"

    @staticmethod
    def _find_next_value(cells, start_idx):
        for i in range(start_idx + 1, len(cells)):
            if cells[i].strip():
                return cells[i].strip()
        return None

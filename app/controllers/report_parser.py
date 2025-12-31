import unicodedata


class ReportParser:
    """
    Clase encargada de interpretar archivos CSV del reporte de ventas.
    Versión Robusta: Ignora acentos, busca columnas dinámicamente y corrige desplazamientos.
    """

    @staticmethod
    def normalize_text(text):
        """Elimina acentos y convierte a minúsculas para comparaciones seguras."""
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
    def parse_csv(file_path):
        metadata = {"desde": "N/A", "hasta": "N/A"}
        records = []

        # Intentar leer con diferentes codificaciones
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
            return (
                metadata,
                records,
                "Error: No se pudo leer el archivo con ninguna codificación estándar.",
            )

        # Variables de estado
        current_code = ""
        current_desc = ""
        header_found = False

        # Índices de columnas por defecto
        idx_desc = 6
        idx_day = 7
        idx_qty = 10
        idx_prom = 12  # Valor por defecto común
        idx_total = 26

        # Días válidos normalizados
        valid_days_norm = [
            "lunes",
            "martes",
            "miercoles",
            "jueves",
            "viernes",
            "sabado",
            "domingo",
        ]

        try:
            for line_idx, line in enumerate(lines):
                cells = [c.strip() for c in line.split(";")]
                cells_norm = [ReportParser.normalize_text(c) for c in cells]

                # -- A. Metadatos --
                if line_idx < 20:
                    for i, cell in enumerate(cells_norm):
                        if "desde" in cell and i + 1 < len(cells):
                            val = ReportParser._find_next_value(cells, i)
                            if val:
                                metadata["desde"] = val
                        if "hasta" in cell and i + 1 < len(cells):
                            val = ReportParser._find_next_value(cells, i)
                            if val:
                                metadata["hasta"] = val

                # -- B. Detección de Encabezado Principal --
                if "codigo" in cells_norm and "descripcion" in cells_norm:
                    header_found = True
                    # Localizar dinámicamente columnas clave
                    for i, cell in enumerate(cells_norm):
                        if "total ventas" in cell:
                            idx_total = i
                        # Busca "Prom/Med" o variantes
                        if "prom/med" in cell or "promed" in cell:
                            idx_prom = i
                    continue

                # Detección alternativa si no se encontró header explícito
                if (
                    len(cells) > 7
                    and ReportParser.normalize_text(cells[7]) in valid_days_norm
                ):
                    header_found = True

                if not header_found:
                    continue

                # -- C. Procesamiento de Filas --
                if len(cells) < 8:
                    continue

                val_code_1 = cells[1] if len(cells) > 1 else ""
                val_code_2 = cells[2] if len(cells) > 2 else ""

                # Descripción
                val_desc_raw = ""
                if len(cells) > idx_desc:
                    val_desc_raw = cells[idx_desc]
                if not val_desc_raw and len(cells) > 5:
                    val_desc_raw = cells[5]

                val_day = cells[idx_day] if len(cells) > idx_day else ""
                val_qty = cells[idx_qty] if len(cells) > idx_qty else ""

                # --- CORRECCION CRITICA: EXTRACCIÓN DE PROM/MED ---
                # Buscamos en el índice detectado y en sus vecinos (derecha +1, +2)
                # Esto soluciona que el Header esté en col 11 y el Dato en col 12
                val_prom = ""
                search_indices = [idx_prom, idx_prom + 1, idx_prom + 2]

                for i in search_indices:
                    if i < len(cells) and cells[i].strip():
                        candidate = cells[i].strip()
                        # Es válido si tiene dígitos o empieza con punto (.22)
                        if any(c.isdigit() for c in candidate) or candidate.startswith(
                            "."
                        ):
                            val_prom = candidate
                            break

                # Extracción Total Ventas (con lógica similar de vecindad si está vacío)
                val_sales = cells[idx_total] if len(cells) > idx_total else ""
                if not val_sales:
                    start_search = max(0, idx_total - 2)
                    end_search = min(len(cells), idx_total + 3)
                    for k in range(start_search, end_search):
                        if "B/." in cells[k] or "B/" in cells[k]:
                            val_sales = cells[k]
                            break

                # Mantener contexto del producto
                if val_code_1:
                    current_code = val_code_1
                elif val_code_2:
                    current_code = val_code_2

                val_desc_norm = ReportParser.normalize_text(val_desc_raw)
                if val_desc_raw and val_desc_norm not in valid_days_norm:
                    current_desc = val_desc_raw

                # -- D. Validación Final --
                val_day_norm = ReportParser.normalize_text(val_day)

                if val_day_norm in valid_days_norm and val_qty and val_sales:
                    try:
                        qty_float = float(val_qty.replace(",", ""))

                        sales_clean = (
                            val_sales.replace("B/.", "")
                            .replace("B/", "")
                            .replace(",", "")
                            .strip()
                        )
                        total_float = float(sales_clean)

                        # Limpieza Promedio
                        prom_clean = (
                            val_prom.replace(",", "").strip() if val_prom else "0"
                        )
                        if prom_clean.startswith("."):
                            prom_clean = "0" + prom_clean
                        prom_float = float(prom_clean)

                        records.append(
                            {
                                "code": current_code,
                                "desc": current_desc,
                                "day": val_day,
                                "qty": qty_float,
                                "prom": prom_float,
                                "total": total_float,
                            }
                        )
                    except ValueError:
                        continue

            return metadata, records, None

        except Exception as e:
            return metadata, records, f"Error inesperado: {str(e)}"

    @staticmethod
    def _find_next_value(cells, start_idx):
        for i in range(start_idx + 1, len(cells)):
            if cells[i].strip():
                return cells[i].strip()
        return None

import os
import subprocess
import sys

from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.reports.conteo_pdf import generar_pdf_conteo


# ── helpers ───────────────────────────────────────────────────────────────────

def _badge(text, bg, fg="#ffffff"):
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setFixedWidth(90)
    lbl.setStyleSheet(
        f"background-color:{bg}; color:{fg}; border-radius:4px;"
        f"padding:2px 6px; font-size:11px; font-weight:bold;"
    )
    return lbl


_ESTADO_STYLE = {
    "BORRADOR":   ("#9e9e9e", "#ffffff"),
    "EN_PROCESO": ("#d0741d", "#ffffff"),
    "CERRADO":    ("#2e7d32", "#ffffff"),
}


def _registrar_ajuste_kardex(db, insumo_id, diferencia, conteo_id, motivo):
    row = db.fetch_one("SELECT stock_actual FROM insumos WHERE id = ?", (insumo_id,))
    stock_anterior = row[0] if row and row[0] is not None else 0.0
    stock_nuevo = round(stock_anterior + diferencia, 4)
    db.execute_query("UPDATE insumos SET stock_actual = ? WHERE id = ?", (stock_nuevo, insumo_id))
    obs = f"Ajuste de inventario (Conteo #{conteo_id})"
    if motivo:
        obs += f" — {motivo}"
    db.execute_query(
        """INSERT INTO movimientos_inventario
           (insumo_id, tipo_movimiento, cantidad, stock_anterior, stock_nuevo, referencia_id, observacion)
           VALUES (?, 'AJUSTE_INVENTARIO', ?, ?, ?, ?, ?)""",
        (insumo_id, diferencia, stock_anterior, stock_nuevo, conteo_id, obs),
    )


def _open_pdf(path):
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass


# ── NuevoConteoDialog ─────────────────────────────────────────────────────────

class NuevoConteoDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Nuevo Conteo de Inventario")
        self.setMinimumWidth(460)
        self._build_ui()
        self._load_categorias()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Crear Sesión de Conteo")
        title.setStyleSheet("font-size:15px; font-weight:bold; color:#a20f22;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Fecha:", self.date_edit)

        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText("Descripción opcional del conteo")
        form.addRow("Descripción:", self.txt_desc)

        self.cmb_categoria = QComboBox()
        form.addRow("Categoría:", self.cmb_categoria)

        self.lbl_preview = QLabel("0 insumos incluidos")
        self.lbl_preview.setStyleSheet("color:#666666; font-size:11px;")
        form.addRow("", self.lbl_preview)

        layout.addLayout(form)
        self.cmb_categoria.currentIndexChanged.connect(self._actualizar_preview)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#dddddd;")
        layout.addWidget(sep)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Crear y Generar PDF")
        btns.accepted.connect(self._crear)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _load_categorias(self):
        self.cmb_categoria.blockSignals(True)
        self.cmb_categoria.clear()
        self.cmb_categoria.addItem("Todas las categorías", None)
        rows = self.db.fetch_all("SELECT id, nombre FROM categorias_insumos ORDER BY nombre")
        for r in rows:
            self.cmb_categoria.addItem(r[1], r[0])
        self.cmb_categoria.blockSignals(False)
        self._actualizar_preview()

    def _actualizar_preview(self):
        cat_id = self.cmb_categoria.currentData()
        if cat_id:
            count = self.db.fetch_one(
                "SELECT COUNT(*) FROM insumos WHERE categoria_id = ?", (cat_id,)
            )
        else:
            count = self.db.fetch_one("SELECT COUNT(*) FROM insumos")
        n = count[0] if count else 0
        self.lbl_preview.setText(f"{n} insumos incluidos")

    def _crear(self):
        fecha = self.date_edit.date().toString("yyyy-MM-dd")
        desc = self.txt_desc.text().strip() or None
        cat_id = self.cmb_categoria.currentData()
        cat_nombre = self.cmb_categoria.currentText()

        self.db.execute_query(
            "INSERT INTO conteos_inventario (fecha, descripcion, categoria_id, estado) VALUES (?,?,?,'EN_PROCESO')",
            (fecha, desc, cat_id),
        )
        conteo_id = self.db.fetch_one("SELECT last_insert_rowid()")[0]

        if cat_id:
            insumos = self.db.fetch_all(
                """SELECT i.id, i.nombre, i.stock_actual, u.nombre, c.nombre
                   FROM insumos i
                   JOIN unidades_medida u ON u.id = i.unidad_base_id
                   LEFT JOIN categorias_insumos c ON c.id = i.categoria_id
                   WHERE i.categoria_id = ?
                   ORDER BY c.nombre, i.nombre""",
                (cat_id,),
            )
        else:
            insumos = self.db.fetch_all(
                """SELECT i.id, i.nombre, i.stock_actual, u.nombre, c.nombre
                   FROM insumos i
                   JOIN unidades_medida u ON u.id = i.unidad_base_id
                   LEFT JOIN categorias_insumos c ON c.id = i.categoria_id
                   ORDER BY c.nombre, i.nombre"""
            )

        filas_pdf = []
        for idx, ins in enumerate(insumos, 1):
            insumo_id, nombre, stock, unidad, cat_n = ins
            self.db.execute_query(
                """INSERT INTO detalle_conteo_inventario
                   (conteo_id, insumo_id, categoria_nombre, unidad_nombre, stock_teorico)
                   VALUES (?,?,?,?,?)""",
                (conteo_id, insumo_id, cat_n or "", unidad or "", stock or 0.0),
            )
            presentaciones = self.db.fetch_all(
                "SELECT nombre FROM presentaciones_compra WHERE insumo_id = ? ORDER BY nombre",
                (insumo_id,),
            )
            filas_pdf.append({
                "numero": idx,
                "nombre": nombre,
                "unidad": unidad or "",
                "presentaciones": [p[0] for p in presentaciones],
            })

        try:
            pdf_path = generar_pdf_conteo(conteo_id, fecha, desc, cat_nombre, filas_pdf)
            _open_pdf(pdf_path)
            QMessageBox.information(
                self,
                "PDF Generado",
                f"El formato de conteo ha sido abierto.\n\nArchivo: {pdf_path}\n\n"
                "Imprímalo y entréguelo al personal para realizar el conteo físico.\n"
                "Cuando tenga los resultados, abra la sesión para ingresar las cantidades.",
            )
        except Exception as e:
            QMessageBox.warning(self, "PDF Error", f"No se pudo generar el PDF:\n{e}")

        self.accept()


# ── ConteoActivoDialog ────────────────────────────────────────────────────────

class ConteoActivoDialog(QDialog):
    def __init__(self, db, conteo_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.conteo_id = conteo_id
        self.setWindowTitle(f"Conteo Activo #{conteo_id}")
        self.setMinimumSize(960, 600)
        self._build_ui()
        self._cargar_datos()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        row = self.db.fetch_one(
            "SELECT fecha, descripcion FROM conteos_inventario WHERE id = ?",
            (self.conteo_id,),
        )
        if row:
            info = QLabel(f"Sesión #{self.conteo_id}  |  Fecha: {row[0]}  |  {row[1] or ''}")
            info.setStyleSheet("font-size:12px; color:#555555;")
            layout.addWidget(info)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        # ── Tab 1: Ingreso de cantidades ──────────────────────────────────────
        tab1 = QWidget()
        t1_layout = QVBoxLayout(tab1)
        t1_layout.setContentsMargins(0, 8, 0, 0)

        lbl_hint = QLabel(
            "Seleccione la unidad de conteo por fila (unidad base o una presentación de compra). "
            "Ingrese la cantidad contada — la columna <b>Equiv. (base)</b> muestra la conversión en tiempo real."
        )
        lbl_hint.setWordWrap(True)
        lbl_hint.setStyleSheet("color:#666666; font-size:11px;")
        t1_layout.addWidget(lbl_hint)

        self.tbl_ingreso = QTableWidget()
        self.tbl_ingreso.setColumnCount(7)
        self.tbl_ingreso.setHorizontalHeaderLabels(
            ["ID", "Categoría", "Insumo", "Teórico (base)", "Contar en", "Cantidad", "Equiv. (base)"]
        )
        self.tbl_ingreso.setColumnHidden(0, True)
        hdr = self.tbl_ingreso.horizontalHeader()
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.Fixed)
        self.tbl_ingreso.setColumnWidth(4, 180)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.tbl_ingreso.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_ingreso.setAlternatingRowColors(True)
        self.tbl_ingreso.verticalHeader().setDefaultSectionSize(36)
        t1_layout.addWidget(self.tbl_ingreso, 1)

        btn_row = QHBoxLayout()
        btn_guardar = QPushButton("Guardar Cantidades")
        btn_guardar.setProperty("class", "btn-success")
        btn_guardar.clicked.connect(self._guardar_cantidades)
        btn_row.addStretch()
        btn_row.addWidget(btn_guardar)
        t1_layout.addLayout(btn_row)
        self.tabs.addTab(tab1, "1. Ingreso de Cantidades")

        # ── Tab 2: Revisión y aprobación ──────────────────────────────────────
        tab2 = QWidget()
        t2_layout = QVBoxLayout(tab2)
        t2_layout.setContentsMargins(0, 8, 0, 0)

        lbl_hint2 = QLabel(
            "Revise las diferencias línea por línea. Ingrese el motivo y marque como aprobado "
            "para incluir el ajuste al kardex. Solo las líneas aprobadas serán ajustadas."
        )
        lbl_hint2.setWordWrap(True)
        lbl_hint2.setStyleSheet("color:#666666; font-size:11px;")
        t2_layout.addWidget(lbl_hint2)

        self.tbl_revision = QTableWidget()
        self.tbl_revision.setColumnCount(8)
        self.tbl_revision.setHorizontalHeaderLabels(
            ["ID", "Insumo", "Unidad", "Teórico", "Contado", "Diferencia", "Motivo", "Aprobar"]
        )
        self.tbl_revision.setColumnHidden(0, True)
        hdr2 = self.tbl_revision.horizontalHeader()
        hdr2.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr2.setSectionResizeMode(6, QHeaderView.Stretch)
        for col in [2, 3, 4, 5, 7]:
            hdr2.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        self.tbl_revision.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_revision.setAlternatingRowColors(True)
        t2_layout.addWidget(self.tbl_revision, 1)

        btn_row2 = QHBoxLayout()
        btn_aplicar = QPushButton("Aplicar Ajustes y Cerrar Sesión")
        btn_aplicar.setProperty("class", "btn-danger")
        btn_aplicar.clicked.connect(self._aplicar_y_cerrar)
        btn_row2.addStretch()
        btn_row2.addWidget(btn_aplicar)
        t2_layout.addLayout(btn_row2)
        self.tabs.addTab(tab2, "2. Revisión y Aprobación")

        # Footer
        footer = QHBoxLayout()
        btn_pdf = QPushButton("Volver a Generar PDF")
        btn_pdf.clicked.connect(self._generar_pdf)
        footer.addWidget(btn_pdf)
        footer.addStretch()
        layout.addLayout(footer)

    def _cargar_datos(self):
        filas = self.db.fetch_all(
            """SELECT id, categoria_nombre, insumo_id, unidad_nombre, stock_teorico, cantidad_contada
               FROM detalle_conteo_inventario WHERE conteo_id = ?
               ORDER BY categoria_nombre, id""",
            (self.conteo_id,),
        )

        self.tbl_ingreso.setRowCount(len(filas))
        for r, fila in enumerate(filas):
            det_id, cat, insumo_id, unidad, teorico, contada = fila
            nombre_row = self.db.fetch_one("SELECT nombre FROM insumos WHERE id = ?", (insumo_id,))
            nombre = nombre_row[0] if nombre_row else str(insumo_id)

            # Static columns
            self.tbl_ingreso.setItem(r, 0, QTableWidgetItem(str(det_id)))

            cat_item = QTableWidgetItem(cat or "")
            cat_item.setFlags(cat_item.flags() & ~Qt.ItemIsEditable)
            self.tbl_ingreso.setItem(r, 1, cat_item)

            nombre_item = QTableWidgetItem(nombre)
            nombre_item.setFlags(nombre_item.flags() & ~Qt.ItemIsEditable)
            self.tbl_ingreso.setItem(r, 2, nombre_item)

            teorico_item = QTableWidgetItem(f"{teorico:.4f} {unidad}")
            teorico_item.setFlags(teorico_item.flags() & ~Qt.ItemIsEditable)
            teorico_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_ingreso.setItem(r, 3, teorico_item)

            # Combobox: base unit + all purchase presentations for this insumo
            cmb = QComboBox()
            cmb.addItem(unidad or "unidad", 1.0)
            presentaciones = self.db.fetch_all(
                "SELECT nombre, cantidad_contenido FROM presentaciones_compra WHERE insumo_id = ? ORDER BY nombre",
                (insumo_id,),
            )
            for p in presentaciones:
                factor = float(p[1]) if p[1] else 1.0
                cmb.addItem(f"{p[0]}  (×{factor:g})", factor)
            self.tbl_ingreso.setCellWidget(r, 4, cmb)

            # SpinBox — always in the selected unit; defaults to base unit
            spin = QDoubleSpinBox()
            spin.setRange(0, 9999999)
            spin.setDecimals(4)
            spin.setValue(contada if contada is not None else 0.0)
            self.tbl_ingreso.setCellWidget(r, 5, spin)

            # Equivalente label (live conversion to base units)
            equiv_val = contada if contada is not None else 0.0
            lbl_equiv = QLabel(f"= {equiv_val:.4f} {unidad}")
            lbl_equiv.setAlignment(Qt.AlignCenter)
            lbl_equiv.setStyleSheet(
                "color:#2c3e50; font-size:11px; padding:0 4px;"
                "background-color:#f0fff4; border-radius:3px;"
            )
            self.tbl_ingreso.setCellWidget(r, 6, lbl_equiv)

            # Connect signals for live update (capture r and unidad in closure)
            cmb.currentIndexChanged.connect(
                lambda _, row=r, u=unidad: self._actualizar_equivalente(row, u)
            )
            spin.valueChanged.connect(
                lambda _, row=r, u=unidad: self._actualizar_equivalente(row, u)
            )

        self._cargar_revision()

    def _actualizar_equivalente(self, r, unidad):
        cmb = self.tbl_ingreso.cellWidget(r, 4)
        spin = self.tbl_ingreso.cellWidget(r, 5)
        lbl = self.tbl_ingreso.cellWidget(r, 6)
        if not (cmb and spin and lbl):
            return
        factor = cmb.currentData() or 1.0
        equiv = round(spin.value() * factor, 4)
        lbl.setText(f"= {equiv:.4f} {unidad}")

    def _cargar_revision(self):
        filas = self.db.fetch_all(
            """SELECT d.id, i.nombre, d.unidad_nombre, d.stock_teorico,
                      d.cantidad_contada, d.diferencia, d.motivo_ajuste, d.aprobado
               FROM detalle_conteo_inventario d
               JOIN insumos i ON i.id = d.insumo_id
               WHERE d.conteo_id = ? AND d.cantidad_contada IS NOT NULL
               ORDER BY i.nombre""",
            (self.conteo_id,),
        )
        self.tbl_revision.setRowCount(len(filas))
        for r, fila in enumerate(filas):
            det_id, nombre, unidad, teorico, contada, dif, motivo, aprobado = fila
            self.tbl_revision.setItem(r, 0, QTableWidgetItem(str(det_id)))
            self.tbl_revision.setItem(r, 1, QTableWidgetItem(nombre))
            self.tbl_revision.setItem(r, 2, QTableWidgetItem(unidad or ""))

            for col, val in [(3, teorico), (4, contada)]:
                item = QTableWidgetItem(f"{val:.4f}" if val is not None else "—")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tbl_revision.setItem(r, col, item)

            dif_val = dif if dif is not None else 0.0
            dif_item = QTableWidgetItem(f"{dif_val:+.4f}")
            dif_item.setFlags(dif_item.flags() & ~Qt.ItemIsEditable)
            dif_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if dif_val < 0:
                dif_item.setForeground(QColor("#a20f22"))
            elif dif_val > 0:
                dif_item.setForeground(QColor("#2e7d32"))
            self.tbl_revision.setItem(r, 5, dif_item)

            motivo_edit = QLineEdit(motivo or "")
            motivo_edit.setPlaceholderText("Ingrese motivo del ajuste…")
            self.tbl_revision.setCellWidget(r, 6, motivo_edit)

            chk = QCheckBox()
            chk.setChecked(bool(aprobado))
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.addWidget(chk)
            chk_layout.setAlignment(Qt.AlignCenter)
            chk_layout.setContentsMargins(0, 0, 0, 0)
            self.tbl_revision.setCellWidget(r, 7, chk_widget)

    def _guardar_cantidades(self):
        for r in range(self.tbl_ingreso.rowCount()):
            det_id = int(self.tbl_ingreso.item(r, 0).text())
            cmb = self.tbl_ingreso.cellWidget(r, 4)
            spin = self.tbl_ingreso.cellWidget(r, 5)
            factor = cmb.currentData() if cmb else 1.0
            contada_base = round(spin.value() * factor, 4)

            row = self.db.fetch_one(
                "SELECT stock_teorico FROM detalle_conteo_inventario WHERE id = ?", (det_id,)
            )
            teorico = row[0] if row else 0.0
            diferencia = round(contada_base - teorico, 4)

            self.db.execute_query(
                "UPDATE detalle_conteo_inventario SET cantidad_contada=?, diferencia=? WHERE id=?",
                (contada_base, diferencia, det_id),
            )

        QMessageBox.information(self, "Guardado", "Cantidades guardadas correctamente.")
        self._cargar_revision()
        self.tabs.setCurrentIndex(1)

    def _aplicar_y_cerrar(self):
        reply = QMessageBox.question(
            self,
            "Confirmar cierre",
            "¿Está seguro de aplicar los ajustes aprobados y cerrar esta sesión?\n\n"
            "Esta acción modificará el inventario y no puede deshacerse.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        ajustados = 0
        for r in range(self.tbl_revision.rowCount()):
            det_id = int(self.tbl_revision.item(r, 0).text())
            chk_widget = self.tbl_revision.cellWidget(r, 7)
            chk = chk_widget.findChild(QCheckBox)
            if not chk or not chk.isChecked():
                continue

            motivo_edit = self.tbl_revision.cellWidget(r, 6)
            motivo = motivo_edit.text().strip() if motivo_edit else ""

            row = self.db.fetch_one(
                "SELECT insumo_id, diferencia, ajuste_aplicado FROM detalle_conteo_inventario WHERE id = ?",
                (det_id,),
            )
            if not row or row[2]:
                continue
            insumo_id, diferencia, _ = row
            if diferencia is None or diferencia == 0:
                continue

            _registrar_ajuste_kardex(self.db, insumo_id, diferencia, self.conteo_id, motivo)
            self.db.execute_query(
                "UPDATE detalle_conteo_inventario SET aprobado=1, ajuste_aplicado=1, motivo_ajuste=? WHERE id=?",
                (motivo, det_id),
            )
            ajustados += 1

        from datetime import datetime
        self.db.execute_query(
            "UPDATE conteos_inventario SET estado='CERRADO', fecha_cierre=? WHERE id=?",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.conteo_id),
        )

        QMessageBox.information(
            self,
            "Sesión cerrada",
            f"Se aplicaron {ajustados} ajuste(s) al inventario.\nLa sesión ha sido cerrada.",
        )
        self.accept()

    def _generar_pdf(self):
        row = self.db.fetch_one(
            "SELECT fecha, descripcion, categoria_id FROM conteos_inventario WHERE id = ?",
            (self.conteo_id,),
        )
        if not row:
            return
        fecha, desc, cat_id = row
        cat_nombre = "Todas"
        if cat_id:
            r2 = self.db.fetch_one("SELECT nombre FROM categorias_insumos WHERE id = ?", (cat_id,))
            if r2:
                cat_nombre = r2[0]

        filas = self.db.fetch_all(
            """SELECT ROW_NUMBER() OVER (ORDER BY i.nombre) num, i.nombre, u.nombre, i.id
               FROM detalle_conteo_inventario d
               JOIN insumos i ON i.id = d.insumo_id
               JOIN unidades_medida u ON u.id = i.unidad_base_id
               WHERE d.conteo_id = ? ORDER BY i.nombre""",
            (self.conteo_id,),
        )
        filas_pdf = []
        for f in filas:
            num, nombre, unidad, insumo_id = f
            presentaciones = self.db.fetch_all(
                "SELECT nombre FROM presentaciones_compra WHERE insumo_id = ? ORDER BY nombre",
                (insumo_id,),
            )
            filas_pdf.append({
                "numero": num,
                "nombre": nombre,
                "unidad": unidad,
                "presentaciones": [p[0] for p in presentaciones],
            })
        try:
            path = generar_pdf_conteo(self.conteo_id, fecha, desc, cat_nombre, filas_pdf)
            _open_pdf(path)
        except Exception as e:
            QMessageBox.warning(self, "Error PDF", str(e))


# ── VerDetalleDialog ──────────────────────────────────────────────────────────

class VerDetalleDialog(QDialog):
    def __init__(self, db, conteo_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.conteo_id = conteo_id
        self.setWindowTitle(f"Detalle Conteo #{conteo_id}")
        self.setMinimumSize(800, 520)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        row = self.db.fetch_one(
            "SELECT fecha, descripcion, estado, fecha_cierre FROM conteos_inventario WHERE id = ?",
            (self.conteo_id,),
        )
        if row:
            fecha, desc, estado, fecha_cierre = row
            bg, fg = _ESTADO_STYLE.get(estado, ("#9e9e9e", "#ffffff"))
            info_row = QHBoxLayout()
            info_row.addWidget(
                QLabel(f"<b>Sesión #{self.conteo_id}</b>  |  Fecha: {fecha}  |  {desc or ''}")
            )
            info_row.addStretch()
            info_row.addWidget(_badge(estado, bg, fg))
            layout.addLayout(info_row)

        tbl = QTableWidget()
        tbl.setColumnCount(7)
        tbl.setHorizontalHeaderLabels(
            ["Insumo", "Categoría", "Unidad", "Teórico", "Contado", "Diferencia", "Motivo"]
        )
        hdr = tbl.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(6, QHeaderView.Stretch)
        for col in [1, 2, 3, 4, 5]:
            hdr.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        tbl.setAlternatingRowColors(True)
        tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        tbl.setSelectionBehavior(QTableWidget.SelectRows)

        filas = self.db.fetch_all(
            """SELECT i.nombre, d.categoria_nombre, d.unidad_nombre,
                      d.stock_teorico, d.cantidad_contada, d.diferencia,
                      d.motivo_ajuste, d.aprobado
               FROM detalle_conteo_inventario d
               JOIN insumos i ON i.id = d.insumo_id
               WHERE d.conteo_id = ?
               ORDER BY d.categoria_nombre, i.nombre""",
            (self.conteo_id,),
        )
        tbl.setRowCount(len(filas))
        for r, fila in enumerate(filas):
            nombre, cat, unidad, teorico, contada, dif, motivo, aprobado = fila
            tbl.setItem(r, 0, QTableWidgetItem(nombre))
            tbl.setItem(r, 1, QTableWidgetItem(cat or ""))
            tbl.setItem(r, 2, QTableWidgetItem(unidad or ""))

            for col, val in [(3, teorico), (4, contada)]:
                item = QTableWidgetItem(f"{val:.4f}" if val is not None else "—")
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                tbl.setItem(r, col, item)

            dif_val = dif if dif is not None else 0.0
            dif_item = QTableWidgetItem(f"{dif_val:+.4f}")
            dif_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if dif_val < 0:
                dif_item.setForeground(QColor("#a20f22"))
            elif dif_val > 0:
                dif_item.setForeground(QColor("#2e7d32"))
            tbl.setItem(r, 5, dif_item)

            tbl.setItem(r, 6, QTableWidgetItem(motivo or ""))

            if aprobado:
                for col in range(7):
                    item = tbl.item(r, col)
                    if item:
                        item.setBackground(QColor("#e8f5e9"))

        layout.addWidget(tbl, 1)

        btns = QDialogButtonBox(QDialogButtonBox.Close)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)


# ── ConteoInventarioView (main module widget) ─────────────────────────────────

class ConteoInventarioView(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._build_ui()
        self._cargar_sesiones()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("<h2>Toma de Inventario Físico</h2>")
        header.addWidget(title)
        header.addStretch()

        btn_nuevo = QPushButton("Nueva Sesión de Conteo")
        btn_nuevo.clicked.connect(self._nuevo_conteo)
        header.addWidget(btn_nuevo)

        btn_refresh = QPushButton("Actualizar")
        btn_refresh.clicked.connect(self._cargar_sesiones)
        header.addWidget(btn_refresh)
        layout.addLayout(header)

        desc = QLabel(
            "Gestione los conteos físicos de inventario. Cree una sesión para generar el formato PDF "
            "que se entrega al personal, ingrese las cantidades contadas y aplique los ajustes al kardex. "
            "Las sesiones en BORRADOR o EN_PROCESO pueden eliminarse si fueron creadas por error."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color:#666666; font-size:11px;")
        layout.addWidget(desc)

        self.tbl = QTableWidget()
        self.tbl.setColumnCount(6)
        self.tbl.setHorizontalHeaderLabels(
            ["ID", "Fecha", "Descripción", "Categoría", "Estado", "Acciones"]
        )
        self.tbl.setColumnHidden(0, True)
        hdr = self.tbl.horizontalHeader()
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.tbl.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.verticalHeader().setDefaultSectionSize(42)
        layout.addWidget(self.tbl, 1)

    def _cargar_sesiones(self):
        rows = self.db.fetch_all(
            """SELECT c.id, c.fecha, c.descripcion, cat.nombre, c.estado
               FROM conteos_inventario c
               LEFT JOIN categorias_insumos cat ON cat.id = c.categoria_id
               ORDER BY c.id DESC"""
        )
        self.tbl.setRowCount(len(rows))
        for r, row in enumerate(rows):
            conteo_id, fecha, desc, cat_nombre, estado = row
            self.tbl.setItem(r, 0, QTableWidgetItem(str(conteo_id)))
            self.tbl.setItem(r, 1, QTableWidgetItem(fecha or ""))
            self.tbl.setItem(r, 2, QTableWidgetItem(desc or ""))
            self.tbl.setItem(r, 3, QTableWidgetItem(cat_nombre or "Todas"))

            bg, fg = _ESTADO_STYLE.get(estado, ("#9e9e9e", "#ffffff"))
            badge_widget = QWidget()
            bl = QHBoxLayout(badge_widget)
            bl.addWidget(_badge(estado, bg, fg))
            bl.setAlignment(Qt.AlignCenter)
            bl.setContentsMargins(4, 2, 4, 2)
            self.tbl.setCellWidget(r, 4, badge_widget)

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(4)

            if estado == "EN_PROCESO":
                btn_abrir = QPushButton("Ingresar Conteo")
                btn_abrir.setProperty("class", "btn-warning")
                btn_abrir.setFixedHeight(28)
                btn_abrir.setProperty("skip-auto-icon", True)
                btn_abrir.clicked.connect(lambda _, cid=conteo_id: self._abrir_conteo(cid))
                btn_layout.addWidget(btn_abrir)

                btn_del = QPushButton("Eliminar")
                btn_del.setProperty("class", "btn-danger")
                btn_del.setFixedHeight(28)
                btn_del.setProperty("skip-auto-icon", True)
                btn_del.clicked.connect(lambda _, cid=conteo_id, est=estado: self._eliminar_conteo(cid, est))
                btn_layout.addWidget(btn_del)

            elif estado == "BORRADOR":
                btn_del = QPushButton("Eliminar")
                btn_del.setProperty("class", "btn-danger")
                btn_del.setFixedHeight(28)
                btn_del.setProperty("skip-auto-icon", True)
                btn_del.clicked.connect(lambda _, cid=conteo_id, est=estado: self._eliminar_conteo(cid, est))
                btn_layout.addWidget(btn_del)

            else:  # CERRADO
                btn_ver = QPushButton("Ver Detalle")
                btn_ver.setProperty("class", "btn-view")
                btn_ver.setFixedHeight(28)
                btn_ver.setProperty("skip-auto-icon", True)
                btn_ver.clicked.connect(lambda _, cid=conteo_id: self._ver_detalle(cid))
                btn_layout.addWidget(btn_ver)

            self.tbl.setCellWidget(r, 5, btn_widget)

    def _nuevo_conteo(self):
        dlg = NuevoConteoDialog(self.db, self)
        if dlg.exec_() == QDialog.Accepted:
            self._cargar_sesiones()

    def _abrir_conteo(self, conteo_id):
        dlg = ConteoActivoDialog(self.db, conteo_id, self)
        dlg.exec_()
        self._cargar_sesiones()

    def _ver_detalle(self, conteo_id):
        dlg = VerDetalleDialog(self.db, conteo_id, self)
        dlg.exec_()

    def _eliminar_conteo(self, conteo_id, estado):
        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Está seguro de eliminar la sesión #{conteo_id}?\n\n"
            "Se eliminarán todos los datos del conteo. Esta acción no puede deshacerse.\n"
            "El inventario no será modificado.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self.db.execute_query(
            "DELETE FROM conteos_inventario WHERE id = ?", (conteo_id,)
        )
        self._cargar_sesiones()

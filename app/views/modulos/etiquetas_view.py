# [FILE: app/views/modulos/etiquetas_view.py]
import os
import subprocess
import sys
from datetime import date

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.controllers.codigos_controller import CodigosController
from app.reports.etiquetas_pdf import generar_pdf_etiquetas


def _open_file(path):
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass


class EtiquetasView(QWidget):
    """Gestión de códigos de barras/QR e impresión de etiquetas de inventario."""

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.ctrl = CodigosController(db_manager)
        self.filtros = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # --- HEADER ---
        header = QHBoxLayout()
        header.addWidget(QLabel("<h2>Etiquetas y Códigos de Inventario</h2>"))
        header.addStretch()

        btn_registrar = QPushButton("Registrar por Escaneo")
        btn_registrar.setCursor(Qt.PointingHandCursor)
        btn_registrar.clicked.connect(self.registrar_por_escaneo)

        btn_generar = QPushButton("Generar Código Interno")
        btn_generar.setCursor(Qt.PointingHandCursor)
        btn_generar.setProperty("class", "btn-success")
        btn_generar.clicked.connect(self.generar_codigo_interno)

        btn_imprimir = QPushButton("Imprimir Etiqueta(s)")
        btn_imprimir.setCursor(Qt.PointingHandCursor)
        btn_imprimir.clicked.connect(self.imprimir_etiquetas)

        btn_codigos = QPushButton("Ver / Eliminar Códigos")
        btn_codigos.setCursor(Qt.PointingHandCursor)
        btn_codigos.clicked.connect(self.ver_codigos)

        for b in (btn_registrar, btn_generar, btn_imprimir, btn_codigos):
            header.addWidget(b)
        layout.addLayout(header)

        hint = QLabel(
            "Los productos que ya traen código de fábrica: use <b>Registrar por Escaneo</b>. "
            "Los que no lo traen: use <b>Generar Código Interno</b> y luego <b>Imprimir</b> la "
            "etiqueta térmica."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#666666; font-size:11px;")
        layout.addWidget(hint)

        # --- FILTROS ---
        filter_layout = QHBoxLayout()
        for col_idx, placeholder in [(1, "Filtrar Insumo"), (2, "Filtrar Categoría")]:
            inp = QLineEdit()
            inp.setPlaceholderText(placeholder)
            inp.setClearButtonEnabled(True)
            inp.textChanged.connect(self.aplicar_filtros)
            self.filtros[col_idx] = inp
            filter_layout.addWidget(inp)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # --- TABLA ---
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Insumo", "Categoría", "Códigos asignados"]
        )
        self.table.setColumnHidden(0, True)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.cargar_datos()

    def cargar_datos(self):
        rows = self.db.fetch_all(
            """
            SELECT i.id, i.nombre, COALESCE(c.nombre, '—') AS categoria,
                   (SELECT COUNT(*) FROM codigos_barras cb WHERE cb.insumo_id = i.id) AS n_codigos
            FROM insumos i
            LEFT JOIN categorias_insumos c ON c.id = i.categoria_id
            ORDER BY i.nombre
            """
        )
        self.table.setRowCount(0)
        for r_idx, (iid, nombre, categoria, n_codigos) in enumerate(rows):
            self.table.insertRow(r_idx)
            self.table.setItem(r_idx, 0, QTableWidgetItem(str(iid)))
            self.table.setItem(r_idx, 1, QTableWidgetItem(nombre))
            self.table.setItem(r_idx, 2, QTableWidgetItem(categoria))
            cod_item = QTableWidgetItem(str(n_codigos))
            cod_item.setTextAlignment(Qt.AlignCenter)
            if n_codigos == 0:
                cod_item.setForeground(Qt.red)
            self.table.setItem(r_idx, 3, cod_item)
        self.aplicar_filtros()

    def aplicar_filtros(self):
        for row in range(self.table.rowCount()):
            mostrar = True
            for col, inp in self.filtros.items():
                texto = inp.text().lower().strip()
                if not texto:
                    continue
                item = self.table.item(row, col)
                if item and texto not in item.text().lower():
                    mostrar = False
                    break
            self.table.setRowHidden(row, not mostrar)

    def _insumo_seleccionado(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Seleccione un insumo de la lista.")
            return None, None
        return int(self.table.item(row, 0).text()), self.table.item(row, 1).text()

    # --- ACCIONES ---

    def registrar_por_escaneo(self):
        insumo_id, nombre = self._insumo_seleccionado()
        if insumo_id is None:
            return
        dlg = AsignarCodigoDialog(self.db, self.ctrl, insumo_id, nombre, parent=self)
        dlg.exec_()
        if dlg.registrado:
            self.cargar_datos()

    def generar_codigo_interno(self):
        insumo_id, nombre = self._insumo_seleccionado()
        if insumo_id is None:
            return
        dlg = GenerarInternoDialog(self.db, self.ctrl, insumo_id, nombre, parent=self)
        if dlg.exec_():
            self.cargar_datos()

    def ver_codigos(self):
        insumo_id, nombre = self._insumo_seleccionado()
        if insumo_id is None:
            return
        dlg = CodigosInsumoDialog(self.db, self.ctrl, insumo_id, nombre, parent=self)
        dlg.exec_()
        self.cargar_datos()

    def imprimir_etiquetas(self):
        insumo_id, nombre = self._insumo_seleccionado()
        if insumo_id is None:
            return
        codigos = self.ctrl.listar_codigos(insumo_id)
        if not codigos:
            resp = QMessageBox.question(
                self, "Sin código",
                f"'{nombre}' no tiene códigos. ¿Generar uno interno ahora?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if resp == QMessageBox.Yes:
                codigo, msg = self.ctrl.generar_codigo_interno(insumo_id)
                if not codigo:
                    return QMessageBox.critical(self, "Error", msg)
                self.cargar_datos()
                codigos = self.ctrl.listar_codigos(insumo_id)
            else:
                return

        dlg = ImprimirEtiquetasDialog(self.db, insumo_id, nombre, codigos, parent=self)
        dlg.exec_()


# ── Diálogos ──────────────────────────────────────────────────────────────────

# Sentinela para "aún no se ha elegido nada" en los combos de presentación.
_SIN_SELECCION = "__sin_seleccion__"


def _cargar_presentaciones(db, combo, insumo_id, incluir_base=True):
    """Llena `combo` con placeholder [+ unidad base] + presentaciones del insumo.

    Regla híbrida:
      - incluir_base=True  (códigos INTERNOS): se ofrece "unidad base" para
        productos de peso variable/a granel.
      - incluir_base=False (códigos de FABRICANTE): solo presentaciones reales,
        porque un código de fábrica siempre identifica un empaque específico.

    Ítems resultantes:
        índice 0            → placeholder no válido (_SIN_SELECCION)
        índice 1 (si base)  → "unidad base" (data = None)
        siguientes          → presentaciones reales (data = presentacion_id)

    Devuelve el número de presentaciones reales cargadas.
    """
    combo.clear()
    combo.addItem("— Seleccione una presentación —", _SIN_SELECCION)
    if incluir_base:
        combo.addItem("Sin presentación (unidad base)", None)
    presentaciones = db.fetch_all(
        "SELECT id, nombre, cantidad_contenido FROM presentaciones_compra WHERE insumo_id = ? ORDER BY nombre",
        (insumo_id,),
    )
    for pid, pnombre, cont in presentaciones:
        combo.addItem(f"{pnombre}  (×{cont:g})", pid)
    combo.setCurrentIndex(0)
    return len(presentaciones)


class AsignarCodigoDialog(QDialog):
    """Registrar un código de fábrica escaneado y asignarlo al insumo."""

    def __init__(self, db, ctrl, insumo_id, nombre, parent=None):
        super().__init__(parent)
        self.db = db
        self.ctrl = ctrl
        self.insumo_id = insumo_id
        self.registrado = False
        self.setWindowTitle("Registrar Código por Escaneo")
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<b>Insumo:</b> {nombre}"))

        info = QLabel(
            "Coloque el cursor en el campo de abajo y escanee el código del producto "
            "con el lector. Puede escanear varios seguidos; cierre cuando termine."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#666666; font-size:11px;")
        layout.addWidget(info)

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.txt_codigo = QLineEdit()
        self.txt_codigo.setPlaceholderText("Escanee o escriba el código…")
        self.txt_codigo.returnPressed.connect(self.guardar)
        form.addRow("Código:", self.txt_codigo)

        self.cmb_pres = QComboBox()
        self.cmb_pres.setMinimumWidth(340)
        self.cmb_pres.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        # Código de FABRICANTE → siempre un empaque real (sin unidad base)
        self._n_pres = _cargar_presentaciones(db, self.cmb_pres, insumo_id, incluir_base=False)
        if self._n_pres == 1:
            self.cmb_pres.setCurrentIndex(1)  # única presentación → preseleccionada
        form.addRow("Presentación:", self.cmb_pres)
        layout.addLayout(form)

        # Mensaje de estado (confirmación / error) siempre visible
        self.lbl_status = QLabel("")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setMinimumHeight(20)
        layout.addWidget(self.lbl_status)

        btn_row = QHBoxLayout()
        btn = QPushButton("Guardar")
        btn.setProperty("class", "btn-success")
        btn.clicked.connect(self.guardar)
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)
        btn_row.addStretch()
        btn_row.addWidget(btn)
        btn_row.addWidget(btn_cerrar)
        layout.addLayout(btn_row)

        self.txt_codigo.setFocus()

    def guardar(self):
        codigo = self.txt_codigo.text().strip()
        if not codigo:
            self._status("Escanee o escriba un código.", error=True)
            return

        if self._n_pres == 0:
            self._status(
                "Este insumo no tiene presentaciones. Cree una presentación de "
                "compra antes de asignar un código de fábrica.", error=True)
            return

        pres = self.cmb_pres.currentData()
        if pres == _SIN_SELECCION:
            self._status("Seleccione una presentación antes de continuar.", error=True)
            self.cmb_pres.setFocus()
            return

        ok, msg = self.ctrl.registrar_codigo(
            codigo, self.insumo_id, pres, tipo="FABRICANTE"
        )
        if ok:
            self.registrado = True
            self._status(f"✓ {msg}  Escanee otro o presione Cerrar.", error=False)
            self.txt_codigo.clear()
        elif "asignado a" in msg:
            # Código en uso por otro insumo: ofrecer reasignarlo aquí
            resp = QMessageBox.question(
                self, "Código en uso",
                f"{msg}\n\n¿Desea reasignarlo a ESTE insumo?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if resp == QMessageBox.Yes:
                ok2, msg2 = self.ctrl.reasignar_codigo(
                    codigo, self.insumo_id, pres, tipo="FABRICANTE"
                )
                if ok2:
                    self.registrado = True
                    self._status(f"✓ {msg2}  Escanee otro o presione Cerrar.", error=False)
                    self.txt_codigo.clear()
                else:
                    self._status(f"✗ {msg2}", error=True)
            else:
                self._status("Operación cancelada.", error=True)
                self.txt_codigo.selectAll()
        else:
            self._status(f"✗ {msg}", error=True)
            self.txt_codigo.selectAll()
        self.txt_codigo.setFocus()

    def _status(self, texto, error=False):
        color = "#a20f22" if error else "#2e7d32"
        self.lbl_status.setStyleSheet(f"color:{color}; font-weight:bold;")
        self.lbl_status.setText(texto)


class GenerarInternoDialog(QDialog):
    """Genera un código interno (para insumos sin código de fábrica)."""

    def __init__(self, db, ctrl, insumo_id, nombre, parent=None):
        super().__init__(parent)
        self.db = db
        self.ctrl = ctrl
        self.insumo_id = insumo_id
        self.nombre = nombre
        self.setWindowTitle("Generar Código Interno")
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<b>Insumo:</b> {nombre}"))

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.cmb_pres = QComboBox()
        self.cmb_pres.setMinimumWidth(340)
        self.cmb_pres.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        # Código INTERNO → se permite unidad base (peso variable/a granel)
        n_pres = _cargar_presentaciones(db, self.cmb_pres, insumo_id, incluir_base=True)
        # Default inteligente: 1 presentación → preselecciónala; ninguna → unidad base;
        # varias → placeholder (elección obligatoria).
        if n_pres == 1:
            self.cmb_pres.setCurrentIndex(2)   # 0=placeholder,1=base,2=única pres.
        elif n_pres == 0:
            self.cmb_pres.setCurrentIndex(1)   # unidad base
        form.addRow("Presentación:", self.cmb_pres)

        hint = QLabel(
            "Elija una presentación para productos de peso fijo, o «unidad base» "
            "para productos de peso variable (carnes, congelados a granel)."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#666666; font-size:10px;")
        layout.addLayout(form)
        layout.addWidget(hint)

        btn_row = QHBoxLayout()
        btn_gen = QPushButton("Generar")
        btn_gen.setProperty("class", "btn-success")
        btn_gen.clicked.connect(self._generar)
        btn_gen_print = QPushButton("Generar e Imprimir")
        btn_gen_print.clicked.connect(lambda: self._generar(imprimir=True))
        btn_row.addWidget(btn_gen)
        btn_row.addWidget(btn_gen_print)
        layout.addLayout(btn_row)

    def _generar(self, imprimir=False):
        pres_id = self.cmb_pres.currentData()
        if pres_id == _SIN_SELECCION:
            return QMessageBox.warning(
                self, "Aviso", "Seleccione una presentación antes de continuar."
            )
        codigo, msg = self.ctrl.generar_codigo_interno(self.insumo_id, pres_id)
        if not codigo:
            return QMessageBox.critical(self, "Error", msg)
        if imprimir:
            codigos = self.ctrl.listar_codigos(self.insumo_id)
            dlg = ImprimirEtiquetasDialog(
                self.db, self.insumo_id, self.nombre, codigos, parent=self
            )
            dlg.exec_()
        else:
            QMessageBox.information(self, "Éxito", msg)
        self.accept()


class CodigosInsumoDialog(QDialog):
    """Lista los códigos de un insumo y permite eliminarlos."""

    def __init__(self, db, ctrl, insumo_id, nombre, parent=None):
        super().__init__(parent)
        self.db = db
        self.ctrl = ctrl
        self.insumo_id = insumo_id
        self.setWindowTitle(f"Códigos de: {nombre}")
        self.setMinimumSize(560, 360)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<b>Insumo:</b> {nombre}"))

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Código", "Tipo", "Presentación"])
        self.table.setColumnHidden(0, True)
        _hdr = self.table.horizontalHeader()
        _hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        _hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        _hdr.setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        btn_del = QPushButton("Eliminar Código Seleccionado")
        btn_del.setProperty("class", "btn-danger")
        btn_del.clicked.connect(self._eliminar)
        layout.addWidget(btn_del)

        self._cargar()

    def _cargar(self):
        codigos = self.ctrl.listar_codigos(self.insumo_id)
        self.table.setRowCount(0)
        for r, (cid, codigo, tipo, _pid, pnombre, _desc) in enumerate(codigos):
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(cid)))
            self.table.setItem(r, 1, QTableWidgetItem(codigo))
            self.table.setItem(r, 2, QTableWidgetItem(tipo or ""))
            self.table.setItem(r, 3, QTableWidgetItem(pnombre or "—"))

    def _eliminar(self):
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(self, "Aviso", "Seleccione un código.")
        cid = int(self.table.item(row, 0).text())
        if QMessageBox.question(
            self, "Confirmar", "¿Eliminar este código?",
            QMessageBox.Yes | QMessageBox.No,
        ) == QMessageBox.Yes:
            ok, msg = self.ctrl.eliminar_codigo(cid)
            if ok:
                self._cargar()
            else:
                QMessageBox.critical(self, "Error", msg)


class ImprimirEtiquetasDialog(QDialog):
    """Selecciona un código, cantidad de copias y tamaño; genera el PDF."""

    def __init__(self, db, insumo_id, nombre, codigos, parent=None):
        super().__init__(parent)
        self.db = db
        self.insumo_id = insumo_id
        self.nombre = nombre
        self.setWindowTitle("Imprimir Etiquetas")
        self.setMinimumWidth(560)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<b>Insumo:</b> {nombre}"))

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.cmb_codigo = QComboBox()
        self.cmb_codigo.setMinimumWidth(360)
        self.cmb_codigo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        for cid, codigo, tipo, pid, pnombre, _desc in codigos:
            etiqueta = f"{codigo}  [{tipo}]"
            if pnombre:
                etiqueta += f" — {pnombre}"
            self.cmb_codigo.addItem(etiqueta, (codigo, pid, pnombre))
        form.addRow("Código:", self.cmb_codigo)

        self.spin_copias = QSpinBox()
        self.spin_copias.setRange(1, 200)
        self.spin_copias.setValue(1)
        form.addRow("Cantidad de etiquetas:", self.spin_copias)

        self.spin_ancho = QSpinBox()
        self.spin_ancho.setRange(20, 150)
        self.spin_ancho.setValue(50)
        self.spin_ancho.setSuffix(" mm")
        form.addRow("Ancho etiqueta:", self.spin_ancho)

        self.spin_alto = QSpinBox()
        self.spin_alto.setRange(15, 150)
        self.spin_alto.setValue(30)
        self.spin_alto.setSuffix(" mm")
        form.addRow("Alto etiqueta:", self.spin_alto)
        layout.addLayout(form)

        btn = QPushButton("Generar PDF e Imprimir")
        btn.setProperty("class", "btn-success")
        btn.clicked.connect(self._generar)
        layout.addWidget(btn)

    def _peso_texto(self, pres_id):
        """Peso/contenido estándar de la presentación para mostrar en la etiqueta."""
        if not pres_id:
            row = self.db.fetch_one(
                """SELECT um.abreviatura FROM insumos i
                   LEFT JOIN unidades_medida um ON um.id = i.unidad_base_id
                   WHERE i.id = ?""",
                (self.insumo_id,),
            )
            return row[0] if row and row[0] else ""
        row = self.db.fetch_one(
            """SELECT pc.cantidad_contenido, um.abreviatura
               FROM presentaciones_compra pc
               JOIN insumos i ON i.id = pc.insumo_id
               LEFT JOIN unidades_medida um ON um.id = i.unidad_base_id
               WHERE pc.id = ?""",
            (pres_id,),
        )
        if row and row[0]:
            return f"{row[0]:g} {row[1] or ''}".strip()
        return ""

    def _generar(self):
        codigo, pres_id, pres_nombre = self.cmb_codigo.currentData()
        cat_row = self.db.fetch_one(
            """SELECT c.nombre FROM insumos i
               LEFT JOIN categorias_insumos c ON c.id = i.categoria_id
               WHERE i.id = ?""",
            (self.insumo_id,),
        )
        categoria = cat_row[0] if cat_row and cat_row[0] else ""

        item = {
            "codigo": codigo,
            "nombre": self.nombre,
            "presentacion": pres_nombre or "",
            "peso_texto": self._peso_texto(pres_id),
            "categoria": categoria,
            "fecha": date.today().isoformat(),
        }
        items = [item] * self.spin_copias.value()
        try:
            path = generar_pdf_etiquetas(
                items,
                ancho_mm=self.spin_ancho.value(),
                alto_mm=self.spin_alto.value(),
            )
            _open_file(path)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar el PDF:\n{e}")

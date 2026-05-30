import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QFormLayout, QLineEdit,
    QComboBox, QDoubleSpinBox, QDateEdit, QCheckBox,
    QMessageBox, QDialogButtonBox, QFrame, QSizePolicy,
    QFileDialog,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont

_RED   = "#a20f22"
_DARK  = "#2c3e50"
_GREEN = "#2e7d32"
_BG_GREEN  = "#e8f5e9"
_BG_YELLOW = "#fffde7"
_BG_GRAY   = "#f5f5f5"


def _ro(item):
    """Make a QTableWidgetItem read-only."""
    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
    return item


def _bold_item(text, color=None, bg=None):
    item = QTableWidgetItem(str(text))
    f = item.font(); f.setBold(True); item.setFont(f)
    if color:
        item.setForeground(QColor(color))
    if bg:
        item.setBackground(QColor(bg))
    return item


def _money(val):
    return f"$ {float(val or 0):,.2f}"


# =============================================================================
# EMPLEADOS — dialog
# =============================================================================
class EmpleadoDialog(QDialog):
    def __init__(self, db, empleado_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.empleado_id = empleado_id
        self.setWindowTitle("Editar Empleado" if empleado_id else "Nuevo Empleado")
        self.setMinimumWidth(420)
        self._build_ui()
        if empleado_id:
            self._cargar()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        self.nombre_input   = QLineEdit()
        self.apellido_input = QLineEdit()
        self.puesto_input   = QLineEdit()

        self.sucursal_combo = QComboBox()
        self.sucursal_combo.addItem("— Sin sucursal —", None)
        for sid, sname in self.db.fetch_all(
            "SELECT id, nombre FROM sucursales ORDER BY nombre", ()
        ):
            self.sucursal_combo.addItem(sname, sid)

        self.salario_spin = QDoubleSpinBox()
        self.salario_spin.setRange(0, 999_999)
        self.salario_spin.setDecimals(2)
        self.salario_spin.setPrefix("$ ")

        self.fecha_input = QDateEdit()
        self.fecha_input.setCalendarPopup(True)
        self.fecha_input.setDate(QDate.currentDate())
        self.fecha_input.setDisplayFormat("dd/MM/yyyy")

        self.activo_check = QCheckBox("Empleado activo")
        self.activo_check.setChecked(True)

        form.addRow("Nombre *:",        self.nombre_input)
        form.addRow("Apellido *:",       self.apellido_input)
        form.addRow("Puesto:",           self.puesto_input)
        form.addRow("Sucursal:",         self.sucursal_combo)
        form.addRow("Salario por Hora:", self.salario_spin)
        form.addRow("Fecha de Ingreso:", self.fecha_input)
        form.addRow("",                  self.activo_check)
        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._guardar)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _cargar(self):
        row = self.db.fetch_one(
            "SELECT nombre, apellido, puesto, sucursal_id, salario_hora, activo, fecha_ingreso FROM empleados WHERE id=?",
            (self.empleado_id,),
        )
        if not row:
            return
        nombre, apellido, puesto, sucursal_id, salario, activo, fecha = row
        self.nombre_input.setText(nombre or "")
        self.apellido_input.setText(apellido or "")
        self.puesto_input.setText(puesto or "")
        self.salario_spin.setValue(float(salario or 0))
        self.activo_check.setChecked(bool(activo))
        for i in range(self.sucursal_combo.count()):
            if self.sucursal_combo.itemData(i) == sucursal_id:
                self.sucursal_combo.setCurrentIndex(i)
                break
        if fecha:
            try:
                y, m, d = str(fecha).split("-")
                self.fecha_input.setDate(QDate(int(y), int(m), int(d)))
            except Exception:
                pass

    def _guardar(self):
        nombre   = self.nombre_input.text().strip()
        apellido = self.apellido_input.text().strip()
        if not nombre or not apellido:
            QMessageBox.warning(self, "Aviso", "Nombre y apellido son obligatorios.")
            return
        puesto      = self.puesto_input.text().strip()
        sucursal_id = self.sucursal_combo.currentData()
        salario     = self.salario_spin.value()
        activo      = 1 if self.activo_check.isChecked() else 0
        fecha       = self.fecha_input.date().toString("yyyy-MM-dd")
        if self.empleado_id:
            self.db.execute_query(
                "UPDATE empleados SET nombre=?, apellido=?, puesto=?, sucursal_id=?, salario_hora=?, activo=?, fecha_ingreso=? WHERE id=?",
                (nombre, apellido, puesto, sucursal_id, salario, activo, fecha, self.empleado_id),
            )
        else:
            self.db.execute_query(
                "INSERT INTO empleados (nombre, apellido, puesto, sucursal_id, salario_hora, activo, fecha_ingreso) VALUES (?,?,?,?,?,?,?)",
                (nombre, apellido, puesto, sucursal_id, salario, activo, fecha),
            )
        self.accept()


# =============================================================================
# EMPLEADOS — tab
# =============================================================================
class TabEmpleados(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Sucursal:"))
        self.cmb_sucursal = QComboBox()
        self.cmb_sucursal.setMinimumWidth(190)
        self.cmb_sucursal.currentIndexChanged.connect(self._cargar_tabla)
        toolbar.addWidget(self.cmb_sucursal)
        toolbar.addStretch()

        for label, slot, cls in [
            ("+ Nuevo Empleado", self._nuevo,         "btn-success"),
            ("Editar",           self._editar,         None),
            ("Activar / Desactivar", self._toggle_activo, None),
        ]:
            btn = QPushButton(label)
            if cls:
                btn.setProperty("class", cls)
            btn.clicked.connect(slot)
            toolbar.addWidget(btn)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nombre", "Apellido", "Puesto",
            "Sucursal", "Salario/Hora", "Fecha Ingreso", "Estado",
        ])
        hdr = self.table.horizontalHeader()
        for c, m in [(0, QHeaderView.ResizeToContents), (1, QHeaderView.ResizeToContents),
                     (2, QHeaderView.ResizeToContents), (3, QHeaderView.Stretch),
                     (4, QHeaderView.ResizeToContents), (5, QHeaderView.ResizeToContents),
                     (6, QHeaderView.ResizeToContents), (7, QHeaderView.ResizeToContents)]:
            hdr.setSectionResizeMode(c, m)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.hideColumn(0)
        layout.addWidget(self.table)

    def _cargar_sucursales(self):
        current = self.cmb_sucursal.currentData()
        self.cmb_sucursal.blockSignals(True)
        self.cmb_sucursal.clear()
        self.cmb_sucursal.addItem("— Todas las sucursales —", None)
        for sid, sname in self.db.fetch_all("SELECT id, nombre FROM sucursales ORDER BY nombre", ()):
            self.cmb_sucursal.addItem(sname, sid)
        if current is not None:
            for i in range(self.cmb_sucursal.count()):
                if self.cmb_sucursal.itemData(i) == current:
                    self.cmb_sucursal.setCurrentIndex(i); break
        self.cmb_sucursal.blockSignals(False)

    def _cargar_tabla(self):
        suc = self.cmb_sucursal.currentData()
        sql = """SELECT e.id, e.nombre, e.apellido, e.puesto,
                        COALESCE(s.nombre,'—'), e.salario_hora,
                        COALESCE(e.fecha_ingreso,''), e.activo
                 FROM empleados e LEFT JOIN sucursales s ON s.id=e.sucursal_id
                 {where} ORDER BY e.apellido, e.nombre"""
        rows = self.db.fetch_all(
            sql.format(where="WHERE e.sucursal_id=?" if suc else ""),
            (suc,) if suc else (),
        )
        self.table.setRowCount(len(rows))
        for r, (eid, n, ap, p, s, sal, fe, act) in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(str(eid)))
            self.table.setItem(r, 1, QTableWidgetItem(n or ""))
            self.table.setItem(r, 2, QTableWidgetItem(ap or ""))
            self.table.setItem(r, 3, QTableWidgetItem(p or ""))
            self.table.setItem(r, 4, QTableWidgetItem(str(s)))
            self.table.setItem(r, 5, QTableWidgetItem(_money(sal)))
            self.table.setItem(r, 6, QTableWidgetItem(str(fe)))
            ei = QTableWidgetItem("Activo" if act else "Inactivo")
            if act:
                ei.setForeground(QColor(_GREEN)); ei.setBackground(QColor(_BG_GREEN))
                f = ei.font(); f.setBold(True); ei.setFont(f)
            else:
                ei.setForeground(QColor("#9e9e9e"))
            ei.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 7, ei)

    def cargar_datos(self):
        self._cargar_sucursales(); self._cargar_tabla()

    def _selected_id(self):
        row = self.table.currentRow()
        item = self.table.item(row, 0) if row >= 0 else None
        return int(item.text()) if item else None

    def _nuevo(self):
        if EmpleadoDialog(self.db, parent=self).exec_():
            self._cargar_tabla()

    def _editar(self):
        eid = self._selected_id()
        if not eid:
            return QMessageBox.warning(self, "Aviso", "Seleccione un empleado.")
        if EmpleadoDialog(self.db, eid, parent=self).exec_():
            self._cargar_tabla()

    def _toggle_activo(self):
        eid = self._selected_id()
        if not eid:
            return QMessageBox.warning(self, "Aviso", "Seleccione un empleado.")
        row = self.db.fetch_one("SELECT activo, nombre, apellido FROM empleados WHERE id=?", (eid,))
        if not row:
            return
        nuevo = 0 if row[0] else 1
        if QMessageBox.question(self, "Confirmar",
                                f"¿{'Activar' if nuevo else 'Desactivar'} a {row[1]} {row[2]}?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.execute_query("UPDATE empleados SET activo=? WHERE id=?", (nuevo, eid))
            self._cargar_tabla()


# =============================================================================
# PERÍODOS — dialog
# =============================================================================
class PeriodoPagoDialog(QDialog):
    def __init__(self, db, periodo_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.periodo_id = periodo_id
        self.setWindowTitle("Editar Período" if periodo_id else "Nuevo Período de Pago")
        self.setMinimumWidth(440)
        self._build_ui()
        if periodo_id:
            self._cargar()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        self.nombre_input = QLineEdit()
        self.nombre_input.setPlaceholderText("Ej: Quincenal 1-15 Enero 2025")
        self.fecha_inicio = QDateEdit()
        self.fecha_inicio.setCalendarPopup(True)
        self.fecha_inicio.setDate(QDate.currentDate().addDays(-14))
        self.fecha_inicio.setDisplayFormat("dd/MM/yyyy")
        self.fecha_fin = QDateEdit()
        self.fecha_fin.setCalendarPopup(True)
        self.fecha_fin.setDate(QDate.currentDate())
        self.fecha_fin.setDisplayFormat("dd/MM/yyyy")
        self.sucursal_combo = QComboBox()
        self.sucursal_combo.addItem("— Todas las sucursales —", None)
        for sid, sname in self.db.fetch_all("SELECT id, nombre FROM sucursales ORDER BY nombre", ()):
            self.sucursal_combo.addItem(sname, sid)

        form.addRow("Nombre *:",     self.nombre_input)
        form.addRow("Fecha Inicio:", self.fecha_inicio)
        form.addRow("Fecha Fin:",    self.fecha_fin)
        form.addRow("Sucursal:",     self.sucursal_combo)
        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._guardar); btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _cargar(self):
        row = self.db.fetch_one(
            "SELECT nombre, fecha_inicio, fecha_fin, sucursal_id FROM periodos_pago WHERE id=?",
            (self.periodo_id,))
        if not row:
            return
        self.nombre_input.setText(row[0] or "")
        for de, ds in [(self.fecha_inicio, row[1]), (self.fecha_fin, row[2])]:
            if ds:
                try:
                    y, m, d = str(ds).split("-"); de.setDate(QDate(int(y), int(m), int(d)))
                except Exception:
                    pass
        for i in range(self.sucursal_combo.count()):
            if self.sucursal_combo.itemData(i) == row[3]:
                self.sucursal_combo.setCurrentIndex(i); break

    def _guardar(self):
        nombre = self.nombre_input.text().strip()
        if not nombre:
            return QMessageBox.warning(self, "Aviso", "El nombre del período es obligatorio.")
        fi = self.fecha_inicio.date().toString("yyyy-MM-dd")
        ff = self.fecha_fin.date().toString("yyyy-MM-dd")
        suc = self.sucursal_combo.currentData()
        if self.periodo_id:
            self.db.execute_query(
                "UPDATE periodos_pago SET nombre=?, fecha_inicio=?, fecha_fin=?, sucursal_id=? WHERE id=?",
                (nombre, fi, ff, suc, self.periodo_id))
        else:
            self.db.execute_query(
                "INSERT INTO periodos_pago (nombre, fecha_inicio, fecha_fin, sucursal_id, estado) VALUES (?,?,?,?,'ABIERTO')",
                (nombre, fi, ff, suc))
        self.accept()


# =============================================================================
# DEDUCCIONES OTRAS — form dialog
# =============================================================================
class DeduccionFormDialog(QDialog):
    def __init__(self, db, periodo_id, sucursal_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.periodo_id = periodo_id
        self.setWindowTitle("Agregar Deducción")
        self.setMinimumWidth(400)
        self._build_ui(sucursal_id)

    def _build_ui(self, sucursal_id):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        self.cmb_empleado = QComboBox()
        sql = ("SELECT id, nombre||' '||apellido FROM empleados WHERE activo=1 AND sucursal_id=? ORDER BY apellido, nombre"
               if sucursal_id else
               "SELECT id, nombre||' '||apellido FROM empleados WHERE activo=1 ORDER BY apellido, nombre")
        params = (sucursal_id,) if sucursal_id else ()
        for eid, nombre in self.db.fetch_all(sql, params):
            self.cmb_empleado.addItem(nombre, eid)

        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItem("Descuento Bancario", "bancario")
        self.cmb_tipo.addItem("Pensión",            "pension")
        self.cmb_tipo.addItem("Otro",               "otro")

        self.desc_input  = QLineEdit()
        self.monto_spin  = QDoubleSpinBox()
        self.monto_spin.setRange(0.01, 999_999); self.monto_spin.setDecimals(2)
        self.monto_spin.setPrefix("$ ")

        form.addRow("Empleado *:", self.cmb_empleado)
        form.addRow("Tipo:",       self.cmb_tipo)
        form.addRow("Descripción:", self.desc_input)
        form.addRow("Monto *:",    self.monto_spin)
        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._guardar); btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _guardar(self):
        eid = self.cmb_empleado.currentData()
        if not eid:
            return QMessageBox.warning(self, "Aviso", "Seleccione un empleado.")
        monto = self.monto_spin.value()
        if monto <= 0:
            return QMessageBox.warning(self, "Aviso", "El monto debe ser mayor a 0.")
        self.db.execute_query(
            "INSERT INTO planilla_deducciones_otras (empleado_id, periodo_id, tipo, descripcion, monto) VALUES (?,?,?,?,?)",
            (eid, self.periodo_id, self.cmb_tipo.currentData(), self.desc_input.text().strip(), monto))
        self.accept()


# =============================================================================
# DEDUCCIONES OTRAS — dialog principal (2 tabs)
# =============================================================================
class OtrasDeduccionesDialog(QDialog):
    def __init__(self, db, periodo_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.periodo_id = periodo_id
        row = self.db.fetch_one("SELECT nombre, sucursal_id FROM periodos_pago WHERE id=?", (periodo_id,))
        self.periodo_nombre = row[0] if row else f"Período #{periodo_id}"
        self.sucursal_id    = row[1] if row else None
        self.setWindowTitle(f"Deducciones — {self.periodo_nombre}")
        self.setMinimumSize(900, 580)
        self._build_ui()
        self._cargar()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        lbl = QLabel(f"<b>{self.periodo_nombre}</b>")
        lbl.setStyleSheet(f"font-size:13px; color:{_RED};")
        layout.addWidget(lbl)

        tabs = QTabWidget()

        # ── Tab A: Otras deducciones ──────────────────────────────────────────
        tab_a = QWidget()
        lay_a = QVBoxLayout(tab_a)
        tb_a = QHBoxLayout()
        btn_add = QPushButton("+ Agregar Deducción")
        btn_add.setProperty("class", "btn-success")
        btn_add.clicked.connect(self._agregar)
        btn_del = QPushButton("Eliminar")
        btn_del.setProperty("class", "btn-danger")
        btn_del.clicked.connect(self._eliminar)
        tb_a.addWidget(btn_add); tb_a.addWidget(btn_del); tb_a.addStretch()
        lay_a.addLayout(tb_a)

        self.tbl_otras = QTableWidget()
        self.tbl_otras.setColumnCount(5)
        self.tbl_otras.setHorizontalHeaderLabels(["ID", "Empleado", "Tipo", "Descripción", "Monto"])
        hdr = self.tbl_otras.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.Stretch)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tbl_otras.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_otras.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_otras.setAlternatingRowColors(True)
        self.tbl_otras.hideColumn(0)
        lay_a.addWidget(self.tbl_otras)
        tabs.addTab(tab_a, "Otras Deducciones")

        # ── Tab B: Descuentos de vales ────────────────────────────────────────
        tab_b = QWidget()
        lay_b = QVBoxLayout(tab_b)
        lbl_b = QLabel("Registre el monto a descontar de cada vale pendiente en este período.")
        lbl_b.setStyleSheet("color:#555; font-size:11px;")
        lay_b.addWidget(lbl_b)

        self.tbl_vales = QTableWidget()
        self.tbl_vales.setColumnCount(7)
        self.tbl_vales.setHorizontalHeaderLabels([
            "ID Vale", "Empleado", "Fecha Vale",
            "Monto Original", "Saldo Actual",
            "Abono Este Período", "Descripción",
        ])
        hdrv = self.tbl_vales.horizontalHeader()
        for c, m in [(0, QHeaderView.ResizeToContents), (1, QHeaderView.ResizeToContents),
                     (2, QHeaderView.ResizeToContents), (3, QHeaderView.ResizeToContents),
                     (4, QHeaderView.ResizeToContents), (5, QHeaderView.ResizeToContents),
                     (6, QHeaderView.Stretch)]:
            hdrv.setSectionResizeMode(c, m)
        self.tbl_vales.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_vales.setAlternatingRowColors(True)
        self.tbl_vales.hideColumn(0)
        lay_b.addWidget(self.tbl_vales)

        btn_save_vales = QPushButton("Guardar Abonos de Vales")
        btn_save_vales.setProperty("class", "btn-success")
        btn_save_vales.clicked.connect(self._guardar_vales)
        lay_b.addWidget(btn_save_vales)
        tabs.addTab(tab_b, "Descuentos de Vales")

        layout.addWidget(tabs)
        btns = QDialogButtonBox(QDialogButtonBox.Close)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _cargar(self):
        self._cargar_otras()
        self._cargar_vales()

    def _cargar_otras(self):
        rows = self.db.fetch_all(
            """SELECT d.id, e.nombre||' '||e.apellido, d.tipo, d.descripcion, d.monto
               FROM planilla_deducciones_otras d
               JOIN empleados e ON e.id=d.empleado_id
               WHERE d.periodo_id=? ORDER BY e.apellido, e.nombre""",
            (self.periodo_id,))
        self.tbl_otras.setRowCount(len(rows))
        for r, (did, emp, tipo, desc, monto) in enumerate(rows):
            self.tbl_otras.setItem(r, 0, QTableWidgetItem(str(did)))
            self.tbl_otras.setItem(r, 1, QTableWidgetItem(emp or ""))
            self.tbl_otras.setItem(r, 2, QTableWidgetItem(tipo or ""))
            self.tbl_otras.setItem(r, 3, QTableWidgetItem(desc or ""))
            amt = QTableWidgetItem(_money(monto))
            amt.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_otras.setItem(r, 4, amt)

    def _cargar_vales(self):
        where_suc = "AND e.sucursal_id=?" if self.sucursal_id else ""
        params = []
        if self.sucursal_id:
            params.append(self.sucursal_id)
        rows = self.db.fetch_all(
            f"""SELECT v.id, e.nombre||' '||e.apellido, v.fecha_emision,
                       v.monto_original, COALESCE(SUM(vp.monto),0)
                FROM vales_empleados v
                JOIN empleados e ON e.id=v.empleado_id
                LEFT JOIN vale_pagos vp ON vp.vale_id=v.id
                WHERE v.estado='PENDIENTE' {where_suc}
                GROUP BY v.id ORDER BY e.apellido, e.nombre""",
            tuple(params))
        existentes = {vid: (monto, desc) for vid, monto, desc in self.db.fetch_all(
            "SELECT vale_id, monto, descripcion FROM vale_pagos WHERE periodo_id=?",
            (self.periodo_id,))}
        self.tbl_vales.setRowCount(len(rows))
        for r, (vid, emp, fecha, monto_orig, total_pag) in enumerate(rows):
            saldo = float(monto_orig) - float(total_pag)
            abono, desc = existentes.get(vid, (0.0, ""))
            self.tbl_vales.setItem(r, 0, QTableWidgetItem(str(vid)))
            for c, v in [(1, emp), (2, str(fecha or ""))]:
                self.tbl_vales.setItem(r, c, _ro(QTableWidgetItem(v or "")))
            orig_i = _ro(QTableWidgetItem(_money(monto_orig)))
            orig_i.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_vales.setItem(r, 3, orig_i)
            saldo_i = _ro(QTableWidgetItem(_money(saldo)))
            saldo_i.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            saldo_i.setForeground(QColor(_RED))
            self.tbl_vales.setItem(r, 4, saldo_i)
            self.tbl_vales.setItem(r, 5, QTableWidgetItem(str(abono or "0")))
            self.tbl_vales.setItem(r, 6, QTableWidgetItem(desc or ""))

    def _guardar_vales(self):
        hoy = QDate.currentDate().toString("yyyy-MM-dd")
        for r in range(self.tbl_vales.rowCount()):
            vid  = int(self.tbl_vales.item(r, 0).text())
            raw  = (self.tbl_vales.item(r, 5) or QTableWidgetItem("0")).text() or "0"
            try:
                abono = float(raw)
            except ValueError:
                return QMessageBox.warning(self, "Error", f"Fila {r+1}: monto de abono inválido.")
            if abono <= 0:
                continue
            desc = self.tbl_vales.item(r, 6).text() if self.tbl_vales.item(r, 6) else ""
            exist = self.db.fetch_one(
                "SELECT id FROM vale_pagos WHERE vale_id=? AND periodo_id=?", (vid, self.periodo_id))
            if exist:
                self.db.execute_query(
                    "UPDATE vale_pagos SET monto=?, descripcion=? WHERE vale_id=? AND periodo_id=?",
                    (abono, desc, vid, self.periodo_id))
            else:
                self.db.execute_query(
                    "INSERT INTO vale_pagos (vale_id, fecha, monto, periodo_id, descripcion) VALUES (?,?,?,?,?)",
                    (vid, hoy, abono, self.periodo_id, desc))
            # Auto-cancelar si saldo = 0
            total = self.db.fetch_one(
                "SELECT COALESCE(SUM(monto),0) FROM vale_pagos WHERE vale_id=?", (vid,))[0]
            orig  = self.db.fetch_one(
                "SELECT monto_original FROM vales_empleados WHERE id=?", (vid,))[0]
            if float(total) >= float(orig):
                self.db.execute_query(
                    "UPDATE vales_empleados SET estado='CANCELADO', fecha_cancelacion=? WHERE id=?",
                    (hoy, vid))
        QMessageBox.information(self, "Éxito", "Abonos de vales guardados.")
        self._cargar_vales()

    def _agregar(self):
        if DeduccionFormDialog(self.db, self.periodo_id, self.sucursal_id, parent=self).exec_():
            self._cargar_otras()

    def _eliminar(self):
        row = self.tbl_otras.currentRow()
        if row < 0:
            return QMessageBox.warning(self, "Aviso", "Seleccione una deducción.")
        did = int(self.tbl_otras.item(row, 0).text())
        if QMessageBox.question(self, "Confirmar", "¿Eliminar esta deducción?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.execute_query("DELETE FROM planilla_deducciones_otras WHERE id=?", (did,))
            self._cargar_otras()


# =============================================================================
# REGISTRO DE HORAS — dialog
# =============================================================================
class RegistroHorasDialog(QDialog):
    _HORAS_COLS = [
        ("H. Regulares",      4, "horas_regulares"),
        ("H. Festivos",       5, "horas_festivos"),
        ("H. Domingos",       6, "horas_domingos"),
        ("H. Extra Diurnas",  7, "horas_extra_diurnas"),
        ("H. Extra Nocturnas",8, "horas_extra_nocturnas"),
    ]

    def __init__(self, db, periodo_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.periodo_id = periodo_id
        row = self.db.fetch_one("SELECT nombre, sucursal_id FROM periodos_pago WHERE id=?", (periodo_id,))
        self.periodo_nombre   = row[0] if row else f"Período #{periodo_id}"
        self.periodo_sucursal = row[1] if row else None
        self.setWindowTitle(f"Registro de Horas — {self.periodo_nombre}")
        self.setMinimumSize(1060, 560)
        self._build_ui()
        self._cargar()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        lbl = QLabel(f"<b>{self.periodo_nombre}</b>")
        lbl.setStyleSheet(f"font-size:13px; color:{_RED};")
        layout.addWidget(lbl)
        lbl2 = QLabel("Haga doble clic en las celdas de horas u observación para editarlas.")
        lbl2.setStyleSheet("color:#555; font-size:11px;")
        layout.addWidget(lbl2)

        fb = QHBoxLayout(); fb.setSpacing(8)
        fb.addWidget(QLabel("Sucursal:"))
        self.cmb_filtro_suc = QComboBox()
        self.cmb_filtro_suc.setMinimumWidth(180)
        self._poblar_combo_sucursales()
        fb.addWidget(self.cmb_filtro_suc)
        fb.addSpacing(16)
        fb.addWidget(QLabel("Ordenar por:"))
        self.cmb_orden = QComboBox()
        self.cmb_orden.addItem("Nombre",   "nombre")
        self.cmb_orden.addItem("Sucursal", "sucursal")
        fb.addWidget(self.cmb_orden)
        btn_ap = QPushButton("Aplicar"); btn_ap.clicked.connect(self._cargar)
        fb.addWidget(btn_ap); fb.addStretch()
        layout.addLayout(fb)

        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nombre", "Apellido", "Sucursal",
            "H. Regulares", "H. Festivos", "H. Domingos",
            "H. Extra Diurnas", "H. Extra Nocturnas", "Observación",
        ])
        hdr = self.table.horizontalHeader()
        for c in range(10):
            hdr.setSectionResizeMode(c, QHeaderView.Stretch if c == 9 else QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.hideColumn(0)
        layout.addWidget(self.table)

        br = QHBoxLayout()
        btn_g = QPushButton("Guardar Horas"); btn_g.setProperty("class", "btn-success")
        btn_g.clicked.connect(self._guardar)
        btn_c = QPushButton("Cerrar"); btn_c.clicked.connect(self.reject)
        br.addWidget(btn_g); br.addStretch(); br.addWidget(btn_c)
        layout.addLayout(br)

    def _poblar_combo_sucursales(self):
        self.cmb_filtro_suc.clear()
        self.cmb_filtro_suc.addItem("— Todas las sucursales —", None)
        for sid, sname in self.db.fetch_all("SELECT id, nombre FROM sucursales ORDER BY nombre", ()):
            self.cmb_filtro_suc.addItem(sname, sid)
        if self.periodo_sucursal is not None:
            for i in range(self.cmb_filtro_suc.count()):
                if self.cmb_filtro_suc.itemData(i) == self.periodo_sucursal:
                    self.cmb_filtro_suc.setCurrentIndex(i); break
            self.cmb_filtro_suc.setEnabled(False)

    def _cargar(self):
        filtro = self.cmb_filtro_suc.currentData()
        orden  = self.cmb_orden.currentData()
        order_sql = ("ORDER BY s.nombre, e.apellido, e.nombre"
                     if orden == "sucursal" else "ORDER BY e.apellido, e.nombre")
        where = "WHERE e.activo=1"
        params = []
        if filtro is not None:
            where += " AND e.sucursal_id=?"; params.append(filtro)
        empleados = self.db.fetch_all(
            f"SELECT e.id, e.nombre, e.apellido, COALESCE(s.nombre,'—') FROM empleados e LEFT JOIN sucursales s ON s.id=e.sucursal_id {where} {order_sql}",
            tuple(params))
        existentes = {row[0]: row[1:] for row in self.db.fetch_all(
            "SELECT empleado_id, horas_regulares, horas_festivos, horas_domingos, horas_extra_diurnas, horas_extra_nocturnas, observacion FROM horas_empleado WHERE periodo_id=?",
            (self.periodo_id,))}
        self.table.setRowCount(len(empleados))
        for r, (eid, nombre, apellido, sucursal) in enumerate(empleados):
            self.table.setItem(r, 0, QTableWidgetItem(str(eid)))
            for c, v in [(1, nombre), (2, apellido), (3, sucursal)]:
                self.table.setItem(r, c, _ro(QTableWidgetItem(v or "")))
            hr, hf, hd, hed, hen, obs = existentes.get(eid, (0.0,)*5 + ("",))
            for c, v in [(4, hr), (5, hf), (6, hd), (7, hed), (8, hen)]:
                self.table.setItem(r, c, QTableWidgetItem(str(v or "0")))
            self.table.setItem(r, 9, QTableWidgetItem(obs or ""))

    def _guardar(self):
        for r in range(self.table.rowCount()):
            eid = int(self.table.item(r, 0).text())
            vals = {}
            for header, col, db_col in self._HORAS_COLS:
                raw = (self.table.item(r, col) or QTableWidgetItem("0")).text() or "0"
                try:
                    vals[db_col] = float(raw)
                except ValueError:
                    return QMessageBox.warning(self, "Error",
                        f"Fila {r+1} ({header}): valor numérico requerido.")
            obs = self.table.item(r, 9).text() if self.table.item(r, 9) else ""
            exist = self.db.fetch_one(
                "SELECT id FROM horas_empleado WHERE empleado_id=? AND periodo_id=?", (eid, self.periodo_id))
            if exist:
                self.db.execute_query(
                    "UPDATE horas_empleado SET horas_regulares=?, horas_festivos=?, horas_domingos=?, horas_extra_diurnas=?, horas_extra_nocturnas=?, observacion=? WHERE empleado_id=? AND periodo_id=?",
                    (vals["horas_regulares"], vals["horas_festivos"], vals["horas_domingos"],
                     vals["horas_extra_diurnas"], vals["horas_extra_nocturnas"], obs, eid, self.periodo_id))
            else:
                self.db.execute_query(
                    "INSERT INTO horas_empleado (empleado_id, periodo_id, horas_regulares, horas_festivos, horas_domingos, horas_extra_diurnas, horas_extra_nocturnas, observacion) VALUES (?,?,?,?,?,?,?,?)",
                    (eid, self.periodo_id, vals["horas_regulares"], vals["horas_festivos"],
                     vals["horas_domingos"], vals["horas_extra_diurnas"], vals["horas_extra_nocturnas"], obs))
        QMessageBox.information(self, "Éxito", "Horas guardadas correctamente.")
        self.accept()


# =============================================================================
# PERÍODOS — tab
# =============================================================================
class TabPeriodos(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Sucursal:"))
        self.cmb_sucursal = QComboBox()
        self.cmb_sucursal.setMinimumWidth(190)
        self.cmb_sucursal.currentIndexChanged.connect(self._cargar_tabla)
        toolbar.addWidget(self.cmb_sucursal)
        toolbar.addStretch()

        for label, slot, cls in [
            ("+ Nuevo Período",  self._nuevo,             "btn-success"),
            ("Registrar Horas",  self._registrar_horas,   None),
            ("Deducciones",      self._abrir_deducciones,  None),
            ("Cerrar Período",   self._cerrar_periodo,    "btn-danger"),
        ]:
            btn = QPushButton(label)
            if cls:
                btn.setProperty("class", cls)
            btn.clicked.connect(slot)
            toolbar.addWidget(btn)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nombre del Período", "Fecha Inicio", "Fecha Fin",
            "Sucursal", "# Registros", "Estado",
        ])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        for c in range(2, 7):
            hdr.setSectionResizeMode(c, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.hideColumn(0)
        layout.addWidget(self.table)

    def _cargar_sucursales(self):
        current = self.cmb_sucursal.currentData()
        self.cmb_sucursal.blockSignals(True)
        self.cmb_sucursal.clear()
        self.cmb_sucursal.addItem("— Todas las sucursales —", None)
        for sid, sname in self.db.fetch_all("SELECT id, nombre FROM sucursales ORDER BY nombre", ()):
            self.cmb_sucursal.addItem(sname, sid)
        if current is not None:
            for i in range(self.cmb_sucursal.count()):
                if self.cmb_sucursal.itemData(i) == current:
                    self.cmb_sucursal.setCurrentIndex(i); break
        self.cmb_sucursal.blockSignals(False)

    def _cargar_tabla(self):
        suc = self.cmb_sucursal.currentData()
        sql = """SELECT p.id, p.nombre, p.fecha_inicio, p.fecha_fin,
                        COALESCE(s.nombre,'—'), COUNT(h.id), p.estado
                 FROM periodos_pago p
                 LEFT JOIN sucursales s ON s.id=p.sucursal_id
                 LEFT JOIN horas_empleado h ON h.periodo_id=p.id
                 {where} GROUP BY p.id ORDER BY p.fecha_inicio DESC"""
        rows = self.db.fetch_all(
            sql.format(where="WHERE p.sucursal_id=?" if suc else ""),
            (suc,) if suc else ())
        self.table.setRowCount(len(rows))
        for r, (pid, nombre, fi, ff, s, n, estado) in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(str(pid)))
            self.table.setItem(r, 1, QTableWidgetItem(nombre or ""))
            self.table.setItem(r, 2, QTableWidgetItem(str(fi or "")))
            self.table.setItem(r, 3, QTableWidgetItem(str(ff or "")))
            self.table.setItem(r, 4, QTableWidgetItem(str(s)))
            self.table.setItem(r, 5, QTableWidgetItem(str(n)))
            estado = estado or "ABIERTO"
            ei = QTableWidgetItem(estado)
            if estado == "CERRADO":
                ei.setForeground(QColor("#9e9e9e")); ei.setBackground(QColor(_BG_GRAY))
            else:
                ei.setForeground(QColor(_GREEN)); ei.setBackground(QColor(_BG_GREEN))
                f = ei.font(); f.setBold(True); ei.setFont(f)
            ei.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 6, ei)

    def cargar_datos(self):
        self._cargar_sucursales(); self._cargar_tabla()

    def _selected_id(self):
        row = self.table.currentRow()
        item = self.table.item(row, 0) if row >= 0 else None
        return int(item.text()) if item else None

    def _nuevo(self):
        if PeriodoPagoDialog(self.db, parent=self).exec_():
            self._cargar_tabla()

    def _registrar_horas(self):
        pid = self._selected_id()
        if not pid:
            return QMessageBox.warning(self, "Aviso", "Seleccione un período.")
        estado = self.db.fetch_one("SELECT estado FROM periodos_pago WHERE id=?", (pid,))
        if estado and estado[0] == "CERRADO":
            return QMessageBox.warning(self, "Período cerrado",
                "Este período ya fue cerrado. No se pueden modificar las horas.")
        RegistroHorasDialog(self.db, pid, parent=self).exec_()
        self._cargar_tabla()

    def _abrir_deducciones(self):
        pid = self._selected_id()
        if not pid:
            return QMessageBox.warning(self, "Aviso", "Seleccione un período.")
        OtrasDeduccionesDialog(self.db, pid, parent=self).exec_()

    def _cerrar_periodo(self):
        pid = self._selected_id()
        if not pid:
            return QMessageBox.warning(self, "Aviso", "Seleccione un período.")
        row = self.db.fetch_one("SELECT nombre, estado FROM periodos_pago WHERE id=?", (pid,))
        if not row:
            return
        if row[1] == "CERRADO":
            return QMessageBox.information(self, "Aviso", "Este período ya está cerrado.")
        if QMessageBox.question(self, "Confirmar cierre",
                                f"¿Cerrar el período «{row[0]}»?\nNo podrá modificar horas ni deducciones.",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.execute_query("UPDATE periodos_pago SET estado='CERRADO' WHERE id=?", (pid,))
            self._cargar_tabla()


# =============================================================================
# VALES — dialogs
# =============================================================================
class AbonoValeDialog(QDialog):
    def __init__(self, db, vale_id, saldo, parent=None):
        super().__init__(parent)
        self.db = db
        self.vale_id = vale_id
        self.setWindowTitle("Registrar Abono")
        self.setMinimumWidth(360)
        self._build_ui(saldo)

    def _build_ui(self, saldo):
        layout = QVBoxLayout(self)
        lbl = QLabel(f"Saldo actual: <b>{_money(saldo)}</b>")
        lbl.setStyleSheet(f"color:{_RED}; font-size:12px;")
        layout.addWidget(lbl)
        form = QFormLayout()
        self.fecha_input = QDateEdit()
        self.fecha_input.setCalendarPopup(True)
        self.fecha_input.setDate(QDate.currentDate())
        self.fecha_input.setDisplayFormat("dd/MM/yyyy")
        self.monto_spin = QDoubleSpinBox()
        self.monto_spin.setRange(0.01, saldo)
        self.monto_spin.setValue(saldo)
        self.monto_spin.setDecimals(2)
        self.monto_spin.setPrefix("$ ")
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Descripción del abono...")
        form.addRow("Fecha:",    self.fecha_input)
        form.addRow("Monto:",    self.monto_spin)
        form.addRow("Detalle:",  self.desc_input)
        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._guardar); btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _guardar(self):
        fecha = self.fecha_input.date().toString("yyyy-MM-dd")
        monto = self.monto_spin.value()
        desc  = self.desc_input.text().strip()
        self.db.execute_query(
            "INSERT INTO vale_pagos (vale_id, fecha, monto, descripcion) VALUES (?,?,?,?)",
            (self.vale_id, fecha, monto, desc))
        total = self.db.fetch_one(
            "SELECT COALESCE(SUM(monto),0) FROM vale_pagos WHERE vale_id=?", (self.vale_id,))[0]
        orig  = self.db.fetch_one(
            "SELECT monto_original FROM vales_empleados WHERE id=?", (self.vale_id,))[0]
        if float(total) >= float(orig):
            self.db.execute_query(
                "UPDATE vales_empleados SET estado='CANCELADO', fecha_cancelacion=? WHERE id=?",
                (fecha, self.vale_id))
        self.accept()


class HistorialPagosValeDialog(QDialog):
    def __init__(self, db, vale_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.vale_id = vale_id
        row = self.db.fetch_one(
            "SELECT v.monto_original, v.descripcion, e.nombre||' '||e.apellido FROM vales_empleados v JOIN empleados e ON e.id=v.empleado_id WHERE v.id=?",
            (vale_id,))
        self.monto_original = float(row[0]) if row else 0
        self.setWindowTitle(f"Historial de Pagos — {row[2] if row else ''}")
        self.setMinimumSize(700, 440)
        self._build_ui(row)
        self._cargar()

    def _build_ui(self, row):
        layout = QVBoxLayout(self)
        if row:
            lbl = QLabel(f"<b>{row[2]}</b>  |  {row[1] or ''}  |  Monto: <b>{_money(row[0])}</b>")
            lbl.setStyleSheet(f"font-size:13px; color:{_RED};")
            layout.addWidget(lbl)
        self.lbl_saldo = QLabel()
        self.lbl_saldo.setStyleSheet("font-size:11px;")
        layout.addWidget(self.lbl_saldo)

        tb = QHBoxLayout()
        btn_a = QPushButton("+ Registrar Abono"); btn_a.setProperty("class", "btn-success")
        btn_a.clicked.connect(self._abono)
        tb.addWidget(btn_a); tb.addStretch()
        layout.addLayout(tb)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Fecha", "Monto", "Período Planilla", "Descripción"])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        btns = QDialogButtonBox(QDialogButtonBox.Close)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _cargar(self):
        rows = self.db.fetch_all(
            "SELECT vp.fecha, vp.monto, COALESCE(pp.nombre,'—'), vp.descripcion FROM vale_pagos vp LEFT JOIN periodos_pago pp ON pp.id=vp.periodo_id WHERE vp.vale_id=? ORDER BY vp.fecha DESC",
            (self.vale_id,))
        self.table.setRowCount(len(rows))
        total_pag = 0
        for r, (fecha, monto, periodo, desc) in enumerate(rows):
            total_pag += float(monto)
            self.table.setItem(r, 0, QTableWidgetItem(str(fecha or "")))
            amt = QTableWidgetItem(_money(monto))
            amt.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(r, 1, amt)
            self.table.setItem(r, 2, QTableWidgetItem(str(periodo)))
            self.table.setItem(r, 3, QTableWidgetItem(desc or ""))
        saldo = self.monto_original - total_pag
        color = _GREEN if saldo <= 0 else _RED
        self.lbl_saldo.setText(
            f"Total abonado: <b>{_money(total_pag)}</b>  |  "
            f"Saldo: <b><span style='color:{color}'>{_money(saldo)}</span></b>")

    def _abono(self):
        total = self.db.fetch_one(
            "SELECT COALESCE(SUM(monto),0) FROM vale_pagos WHERE vale_id=?", (self.vale_id,))[0]
        saldo = self.monto_original - float(total)
        if saldo <= 0:
            return QMessageBox.information(self, "Aviso", "Este vale ya está cancelado.")
        if AbonoValeDialog(self.db, self.vale_id, saldo, parent=self).exec_():
            self._cargar()


class NuevoValeDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Nuevo Vale")
        self.setMinimumWidth(500)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        self.cmb_empleado = QComboBox()
        for eid, nombre in self.db.fetch_all(
            "SELECT id, apellido||', '||nombre FROM empleados WHERE activo=1 ORDER BY apellido, nombre", ()):
            self.cmb_empleado.addItem(nombre, eid)

        self.fecha_input = QDateEdit()
        self.fecha_input.setCalendarPopup(True)
        self.fecha_input.setDate(QDate.currentDate())
        self.fecha_input.setDisplayFormat("dd/MM/yyyy")

        self.monto_spin = QDoubleSpinBox()
        self.monto_spin.setRange(0.01, 999_999)
        self.monto_spin.setDecimals(2)
        self.monto_spin.setPrefix("$ ")

        self.desc_input = QLineEdit()

        form.addRow("Empleado *:", self.cmb_empleado)
        form.addRow("Fecha *:",    self.fecha_input)
        form.addRow("Monto *:",    self.monto_spin)
        form.addRow("Descripción:", self.desc_input)
        layout.addLayout(form)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#e0e0e0;"); layout.addWidget(sep)

        lbl_link = QLabel("Vincular con Consolidados (opcional):")
        lbl_link.setStyleSheet("font-weight:bold; color:#555;")
        layout.addWidget(lbl_link)
        lbl_link2 = QLabel("Seleccione una entrada de Diario de Ventas donde se registró este vale.")
        lbl_link2.setStyleSheet("color:#888; font-size:10px;")
        layout.addWidget(lbl_link2)

        self.cmb_diario = QComboBox()
        self.cmb_diario.addItem("— No vincular —", None)
        for did, fecha, vale, desc in self.db.fetch_all(
            "SELECT id, fecha, vale, COALESCE(vale_descripcion,'') FROM diario_ventas WHERE vale>0 ORDER BY fecha DESC LIMIT 60", ()):
            self.cmb_diario.addItem(f"{fecha}  |  {_money(vale)}  |  {desc}", did)
        layout.addWidget(self.cmb_diario)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._guardar); btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _guardar(self):
        eid   = self.cmb_empleado.currentData()
        monto = self.monto_spin.value()
        if not eid:
            return QMessageBox.warning(self, "Aviso", "Seleccione un empleado.")
        if monto <= 0:
            return QMessageBox.warning(self, "Aviso", "El monto debe ser mayor a 0.")
        self.db.execute_query(
            "INSERT INTO vales_empleados (empleado_id, fecha_emision, monto_original, descripcion, diario_ventas_id, estado) VALUES (?,?,?,?,?,'PENDIENTE')",
            (eid, self.fecha_input.date().toString("yyyy-MM-dd"), monto,
             self.desc_input.text().strip(), self.cmb_diario.currentData()))
        self.accept()


# =============================================================================
# VALES — tab
# =============================================================================
class TabVales(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Empleado:"))
        self.cmb_empleado = QComboBox(); self.cmb_empleado.setMinimumWidth(210)
        self.cmb_empleado.currentIndexChanged.connect(self._cargar_tabla)
        toolbar.addWidget(self.cmb_empleado)
        toolbar.addWidget(QLabel("Estado:"))
        self.cmb_estado = QComboBox()
        self.cmb_estado.addItem("Todos",     None)
        self.cmb_estado.addItem("Pendiente", "PENDIENTE")
        self.cmb_estado.addItem("Cancelado", "CANCELADO")
        self.cmb_estado.currentIndexChanged.connect(self._cargar_tabla)
        toolbar.addWidget(self.cmb_estado)
        toolbar.addStretch()

        for label, slot, cls in [
            ("+ Nuevo Vale",        self._nuevo,      "btn-success"),
            ("Historial de Pagos",  self._historial,  None),
            ("Registrar Abono",     self._abono,      None),
            ("Cancelar Vale",       self._cancelar,   "btn-danger"),
        ]:
            btn = QPushButton(label)
            if cls: btn.setProperty("class", cls)
            btn.clicked.connect(slot)
            toolbar.addWidget(btn)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Empleado", "Sucursal", "Fecha Emisión",
            "Monto Original", "Total Abonado", "Saldo",
            "Consolidados", "Estado",
        ])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        for c in range(2, 9):
            hdr.setSectionResizeMode(c, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.hideColumn(0)
        layout.addWidget(self.table)

    def _cargar_empleados(self):
        current = self.cmb_empleado.currentData()
        self.cmb_empleado.blockSignals(True)
        self.cmb_empleado.clear()
        self.cmb_empleado.addItem("— Todos los empleados —", None)
        for eid, ap, n in self.db.fetch_all(
            "SELECT id, apellido, nombre FROM empleados ORDER BY apellido, nombre", ()):
            self.cmb_empleado.addItem(f"{ap}, {n}", eid)
        if current is not None:
            for i in range(self.cmb_empleado.count()):
                if self.cmb_empleado.itemData(i) == current:
                    self.cmb_empleado.setCurrentIndex(i); break
        self.cmb_empleado.blockSignals(False)

    def _cargar_tabla(self):
        eid    = self.cmb_empleado.currentData()
        estado = self.cmb_estado.currentData()
        where, params = [], []
        if eid:    where.append("v.empleado_id=?");  params.append(eid)
        if estado: where.append("v.estado=?");        params.append(estado)
        w = ("WHERE " + " AND ".join(where)) if where else ""
        rows = self.db.fetch_all(
            f"""SELECT v.id, e.nombre||' '||e.apellido, COALESCE(s.nombre,'—'),
                       v.fecha_emision, v.monto_original,
                       COALESCE(SUM(vp.monto),0), v.diario_ventas_id, v.estado
                FROM vales_empleados v
                JOIN empleados e ON e.id=v.empleado_id
                LEFT JOIN sucursales s ON s.id=e.sucursal_id
                LEFT JOIN vale_pagos vp ON vp.vale_id=v.id
                {w} GROUP BY v.id ORDER BY v.fecha_emision DESC""",
            tuple(params))
        self.table.setRowCount(len(rows))
        for r, (vid, emp, suc, fecha, orig, pag, diario_id, est) in enumerate(rows):
            saldo = float(orig) - float(pag)
            self.table.setItem(r, 0, QTableWidgetItem(str(vid)))
            self.table.setItem(r, 1, QTableWidgetItem(emp or ""))
            self.table.setItem(r, 2, QTableWidgetItem(suc or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(str(fecha or "")))
            for c, v in [(4, orig), (5, pag)]:
                i = QTableWidgetItem(_money(v))
                i.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(r, c, i)
            si = QTableWidgetItem(_money(saldo))
            si.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            si.setForeground(QColor(_GREEN if saldo <= 0 else _RED))
            self.table.setItem(r, 6, si)
            li = QTableWidgetItem("✓" if diario_id else "—")
            li.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 7, li)
            est = est or "PENDIENTE"
            ei = QTableWidgetItem(est)
            ei.setTextAlignment(Qt.AlignCenter)
            if est == "CANCELADO":
                ei.setForeground(QColor("#9e9e9e")); ei.setBackground(QColor(_BG_GRAY))
            else:
                ei.setForeground(QColor("#e65100"))
                f = ei.font(); f.setBold(True); ei.setFont(f)
            self.table.setItem(r, 8, ei)

    def cargar_datos(self):
        self._cargar_empleados(); self._cargar_tabla()

    def _selected_id(self):
        row = self.table.currentRow()
        item = self.table.item(row, 0) if row >= 0 else None
        return int(item.text()) if item else None

    def _nuevo(self):
        if NuevoValeDialog(self.db, parent=self).exec_():
            self._cargar_tabla()

    def _historial(self):
        vid = self._selected_id()
        if not vid:
            return QMessageBox.warning(self, "Aviso", "Seleccione un vale.")
        HistorialPagosValeDialog(self.db, vid, parent=self).exec_()
        self._cargar_tabla()

    def _abono(self):
        vid = self._selected_id()
        if not vid:
            return QMessageBox.warning(self, "Aviso", "Seleccione un vale.")
        total = float(self.db.fetch_one(
            "SELECT COALESCE(SUM(monto),0) FROM vale_pagos WHERE vale_id=?", (vid,))[0])
        orig  = float(self.db.fetch_one(
            "SELECT monto_original FROM vales_empleados WHERE id=?", (vid,))[0])
        saldo = orig - total
        if saldo <= 0:
            return QMessageBox.information(self, "Aviso", "Este vale ya está cancelado.")
        if AbonoValeDialog(self.db, vid, saldo, parent=self).exec_():
            self._cargar_tabla()

    def _cancelar(self):
        vid = self._selected_id()
        if not vid:
            return QMessageBox.warning(self, "Aviso", "Seleccione un vale.")
        row = self.db.fetch_one("SELECT estado FROM vales_empleados WHERE id=?", (vid,))
        if row and row[0] == "CANCELADO":
            return QMessageBox.information(self, "Aviso", "Este vale ya está cancelado.")
        if QMessageBox.question(self, "Confirmar", "¿Cancelar este vale?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.execute_query(
                "UPDATE vales_empleados SET estado='CANCELADO', fecha_cancelacion=? WHERE id=?",
                (QDate.currentDate().toString("yyyy-MM-dd"), vid))
            self._cargar_tabla()


# =============================================================================
# RESUMEN DE PLANILLA — tab
# =============================================================================
class TabResumen(QWidget):
    _TIPOS = [
        ("regulares",       "horas_regulares"),
        ("festivos",        "horas_festivos"),
        ("domingos",        "horas_domingos"),
        ("extra_diurnas",   "horas_extra_diurnas"),
        ("extra_nocturnas", "horas_extra_nocturnas"),
    ]

    def __init__(self, db):
        super().__init__()
        self.db = db
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)

        fb = QHBoxLayout(); fb.setSpacing(8)
        fb.addWidget(QLabel("Período:"))
        self.cmb_periodo = QComboBox(); self.cmb_periodo.setMinimumWidth(300)
        fb.addWidget(self.cmb_periodo)
        fb.addWidget(QLabel("Sucursal:"))
        self.cmb_sucursal = QComboBox(); self.cmb_sucursal.setMinimumWidth(180)
        fb.addWidget(self.cmb_sucursal)
        btn_calc = QPushButton("Calcular Planilla")
        btn_calc.setStyleSheet(
            f"background:{_RED}; color:white; padding:6px 16px; border:none; border-radius:4px; font-weight:bold;")
        btn_calc.clicked.connect(self._calcular)
        fb.addWidget(btn_calc)

        btn_xlsx = QPushButton("Exportar Excel")
        btn_xlsx.setStyleSheet(
            "background:#1d6f42; color:white; padding:6px 14px; border:none; border-radius:4px; font-weight:bold;")
        btn_xlsx.clicked.connect(self._exportar_excel)
        fb.addWidget(btn_xlsx)

        btn_pdf = QPushButton("Exportar PDF")
        btn_pdf.setStyleSheet(
            "background:#c62828; color:white; padding:6px 14px; border:none; border-radius:4px; font-weight:bold;")
        btn_pdf.clicked.connect(self._exportar_pdf)
        fb.addWidget(btn_pdf)

        fb.addStretch()
        layout.addLayout(fb)

        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "Empleado", "Sucursal",
            "Salario Bruto",
            "SS Colaborador", "SE Colaborador",
            "Ded. Bancarias", "Ded. Vales",
            "Total Deducciones", "Salario Neto",
            "SS Empleador", "SE Empleador", "Gasto Total Empl.",
        ])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        for c in range(2, 12):
            hdr.setSectionResizeMode(c, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def _cargar_combos(self):
        for cmb, sql, label in [
            (self.cmb_periodo,  "SELECT id, nombre FROM periodos_pago ORDER BY fecha_inicio DESC",
             "— Seleccione un período —"),
            (self.cmb_sucursal, "SELECT id, nombre FROM sucursales ORDER BY nombre",
             "— Todas las sucursales —"),
        ]:
            current = cmb.currentData()
            cmb.blockSignals(True); cmb.clear()
            cmb.addItem(label, None)
            for rid, rname in self.db.fetch_all(sql, ()):
                cmb.addItem(rname, rid)
            if current is not None:
                for i in range(cmb.count()):
                    if cmb.itemData(i) == current:
                        cmb.setCurrentIndex(i); break
            cmb.blockSignals(False)

    def cargar_datos(self):
        self._cargar_combos()

    def _calcular(self):
        pid = self.cmb_periodo.currentData()
        if not pid:
            return QMessageBox.warning(self, "Aviso", "Seleccione un período de pago.")
        suc = self.cmb_sucursal.currentData()

        recargos_rows = self.db.fetch_all(
            "SELECT tipo_hora, nombre_display, recargo FROM planilla_config_recargos", ())
        recargos = {t: r for t, _, r in recargos_rows}

        ded_rows = self.db.fetch_all(
            "SELECT concepto, nombre_display, porcentaje, aplica_a FROM planilla_config_deducciones", ())
        pcts = {c: p for c, _, p, _ in ded_rows}
        pct_ss_c = pcts.get("seguro_social_colaborador",    9.75)  / 100
        pct_ss_e = pcts.get("seguro_social_empleador",     12.25) / 100
        pct_se_c = pcts.get("seguro_educativo_colaborador",  1.25) / 100
        pct_se_e = pcts.get("seguro_educativo_empleador",    1.50) / 100

        periodo_row = self.db.fetch_one(
            "SELECT nombre, fecha_inicio, fecha_fin FROM periodos_pago WHERE id=?", (pid,))
        suc_nombre = self.cmb_sucursal.currentText() if suc else "Todas"

        where = "AND e.sucursal_id=?" if suc else ""
        params = [pid] + ([suc] if suc else [])
        horas_rows = self.db.fetch_all(
            f"""SELECT e.id, e.nombre||' '||e.apellido, COALESCE(s.nombre,'—'), e.salario_hora,
                       h.horas_regulares, h.horas_festivos, h.horas_domingos,
                       h.horas_extra_diurnas, h.horas_extra_nocturnas
                FROM horas_empleado h
                JOIN empleados e ON e.id=h.empleado_id
                LEFT JOIN sucursales s ON s.id=e.sucursal_id
                WHERE h.periodo_id=? {where}
                ORDER BY e.apellido, e.nombre""",
            tuple(params))

        resultados = []
        export_rows = []
        for (eid, nombre, sucursal, sal_hora,
             h_reg, h_fest, h_dom, h_exd, h_exn) in horas_rows:
            sal = float(sal_hora or 0)
            bruto = (
                float(h_reg  or 0) * sal * recargos.get("regulares",       1.00) +
                float(h_fest or 0) * sal * recargos.get("festivos",         2.50) +
                float(h_dom  or 0) * sal * recargos.get("domingos",         1.50) +
                float(h_exd  or 0) * sal * recargos.get("extra_diurnas",    1.25) +
                float(h_exn  or 0) * sal * recargos.get("extra_nocturnas",  1.50)
            )
            ss_c = bruto * pct_ss_c
            se_c = bruto * pct_se_c
            ded_otras = float(self.db.fetch_one(
                "SELECT COALESCE(SUM(monto),0) FROM planilla_deducciones_otras WHERE empleado_id=? AND periodo_id=?",
                (eid, pid))[0])
            ded_vales = float(self.db.fetch_one(
                "SELECT COALESCE(SUM(monto),0) FROM vale_pagos WHERE periodo_id=? AND vale_id IN (SELECT id FROM vales_empleados WHERE empleado_id=?)",
                (pid, eid))[0])
            total_ded = ss_c + se_c + ded_otras + ded_vales
            neto      = bruto - total_ded
            ss_e      = bruto * pct_ss_e
            se_e      = bruto * pct_se_e
            resultados.append((nombre, sucursal, bruto, ss_c, se_c,
                                ded_otras, ded_vales, total_ded, neto, ss_e, se_e, ss_e + se_e))
            export_rows.append({
                "nombre": nombre, "sucursal": sucursal, "sal_hora": sal,
                "h_reg": h_reg, "h_fest": h_fest, "h_dom": h_dom,
                "h_exd": h_exd, "h_exn": h_exn,
                "bruto": bruto, "ss_c": ss_c, "se_c": se_c,
                "ded_otras": ded_otras, "ded_vales": ded_vales,
                "total_ded": total_ded, "neto": neto,
                "ss_e": ss_e, "se_e": se_e, "gasto": ss_e + se_e,
            })

        from datetime import date as _date
        self._last_result = export_rows
        self._last_meta = {
            "periodo_nombre": periodo_row[0] if periodo_row else "",
            "fecha_inicio":   str(periodo_row[1]) if periodo_row else "",
            "fecha_fin":      str(periodo_row[2]) if periodo_row else "",
            "sucursal":       suc_nombre,
            "generado":       str(_date.today()),
        }
        self._last_recargos_cfg = list(recargos_rows)
        self._last_ded_cfg      = list(ded_rows)

        self._poblar(resultados)

    def _poblar(self, resultados):
        self.table.setRowCount(len(resultados) + (1 if resultados else 0))
        totales = [0.0] * 10

        for r, (nombre, suc, bruto, ss_c, se_c, do, dv, td, neto, ss_e, se_e, gasto) in enumerate(resultados):
            vals = [bruto, ss_c, se_c, do, dv, td, neto, ss_e, se_e, gasto]
            for i, v in enumerate(vals): totales[i] += v
            self.table.setItem(r, 0, QTableWidgetItem(nombre))
            self.table.setItem(r, 1, QTableWidgetItem(suc))
            for c, v in enumerate(vals, 2):
                it = QTableWidgetItem(_money(v))
                it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if c == 8:   # Neto
                    it.setBackground(QColor(_BG_GREEN)); it.setForeground(QColor(_GREEN))
                    f = it.font(); f.setBold(True); it.setFont(f)
                elif c in (9, 10, 11):  # Gasto empleador
                    it.setBackground(QColor(_BG_YELLOW)); it.setForeground(QColor("#e65100"))
                self.table.setItem(r, c, it)

        if resultados:
            tr = len(resultados)
            self.table.setItem(tr, 0, _bold_item("TOTALES", bg=_BG_GRAY))
            self.table.setItem(tr, 1, _bold_item("", bg=_BG_GRAY))
            for c, v in enumerate(totales, 2):
                it = _bold_item(_money(v), bg=_BG_GRAY)
                it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if c == 8:   it.setForeground(QColor(_GREEN))
                elif c in (9, 10, 11): it.setForeground(QColor("#e65100"))
                self.table.setItem(tr, c, it)

    def _get_export_data(self):
        """Run _calcular if no cached result, return False if still empty."""
        if not hasattr(self, "_last_result") or self._last_result is None:
            self._calcular()
        if not getattr(self, "_last_result", None):
            QMessageBox.warning(self, "Aviso",
                "No hay datos calculados. Seleccione un período y haga clic en «Calcular Planilla».")
            return False
        return True

    def _exportar_excel(self):
        if not self._get_export_data():
            return
        nombre_per = self._last_meta.get("periodo_nombre", "planilla").replace(" ", "_").replace("/", "-")
        default_name = f"Planilla_{nombre_per}_{self._last_meta.get('generado','')}.xlsx"
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Guardar Excel", default_name,
            "Excel (*.xlsx);;Todos los archivos (*)")
        if not filepath:
            return
        try:
            from app.utils.export_planilla import export_excel
            export_excel(self._last_meta, self._last_recargos_cfg,
                         self._last_ded_cfg, self._last_result, filepath)
            if QMessageBox.question(
                    self, "Exportado",
                    f"Archivo guardado:\n{filepath}\n\n¿Abrir ahora?",
                    QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                os.startfile(filepath)
        except Exception as e:
            QMessageBox.critical(self, "Error al exportar Excel", str(e))

    def _exportar_pdf(self):
        if not self._get_export_data():
            return
        nombre_per = self._last_meta.get("periodo_nombre", "planilla").replace(" ", "_").replace("/", "-")
        default_name = f"Planilla_{nombre_per}_{self._last_meta.get('generado','')}.pdf"
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF", default_name,
            "PDF (*.pdf);;Todos los archivos (*)")
        if not filepath:
            return
        try:
            from app.utils.export_planilla import export_pdf
            export_pdf(self._last_meta, self._last_recargos_cfg,
                       self._last_ded_cfg, self._last_result, filepath)
            if QMessageBox.question(
                    self, "Exportado",
                    f"Archivo guardado:\n{filepath}\n\n¿Abrir ahora?",
                    QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                os.startfile(filepath)
        except Exception as e:
            QMessageBox.critical(self, "Error al exportar PDF", str(e))


# =============================================================================
# CONFIGURACIÓN — tab
# =============================================================================
class TabConfiguracion(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(16)

        # ── Sección A: Recargos ───────────────────────────────────────────────
        lbl_a = QLabel("Recargos por Tipo de Hora")
        lbl_a.setStyleSheet(f"font-size:13px; font-weight:bold; color:{_DARK};")
        layout.addWidget(lbl_a)
        lbl_a2 = QLabel("Edite el multiplicador en la columna «Recargo». Se aplica sobre (horas × salario/hora).")
        lbl_a2.setStyleSheet("color:#666; font-size:11px;")
        layout.addWidget(lbl_a2)

        self.tbl_recargos = QTableWidget()
        self.tbl_recargos.setColumnCount(2)
        self.tbl_recargos.setHorizontalHeaderLabels(["Tipo de Hora", "Recargo (×)"])
        self.tbl_recargos.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tbl_recargos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tbl_recargos.setMaximumHeight(180)
        layout.addWidget(self.tbl_recargos)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setStyleSheet("color:#e0e0e0;")
        layout.addWidget(sep)

        # ── Sección B: Deducciones ────────────────────────────────────────────
        lbl_b = QLabel("Porcentajes de Deducciones (Panamá)")
        lbl_b.setStyleSheet(f"font-size:13px; font-weight:bold; color:{_DARK};")
        layout.addWidget(lbl_b)

        form_b = QFormLayout()
        form_b.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self._ded_spins = {}
        configs = [
            ("seguro_social_colaborador",    "Seguro Social — Colaborador (%):"),
            ("seguro_social_empleador",      "Seguro Social — Empleador (gasto, %):"),
            ("seguro_educativo_colaborador", "Seguro Educativo — Colaborador (%):"),
            ("seguro_educativo_empleador",   "Seguro Educativo — Empleador (gasto, %):"),
        ]
        for concepto, label in configs:
            spin = QDoubleSpinBox()
            spin.setRange(0, 100); spin.setDecimals(4); spin.setSuffix(" %")
            spin.setMaximumWidth(140)
            self._ded_spins[concepto] = spin
            form_b.addRow(label, spin)
        layout.addLayout(form_b)

        btn_save = QPushButton("Guardar Configuración")
        btn_save.setProperty("class", "btn-success")
        btn_save.clicked.connect(self._guardar)
        layout.addWidget(btn_save)
        layout.addStretch()

    def cargar_datos(self):
        rows = self.db.fetch_all(
            "SELECT tipo_hora, nombre_display, recargo FROM planilla_config_recargos ORDER BY id", ())
        self.tbl_recargos.setRowCount(len(rows))
        for r, (tipo, nombre, recargo) in enumerate(rows):
            nombre_item = QTableWidgetItem(nombre)
            nombre_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.tbl_recargos.setItem(r, 0, nombre_item)
            self.tbl_recargos.setItem(r, 1, QTableWidgetItem(str(recargo)))

        for concepto, spin in self._ded_spins.items():
            row = self.db.fetch_one(
                "SELECT porcentaje FROM planilla_config_deducciones WHERE concepto=?", (concepto,))
            if row:
                spin.setValue(float(row[0]))

    def _guardar(self):
        tipos = self.db.fetch_all(
            "SELECT tipo_hora FROM planilla_config_recargos ORDER BY id", ())
        for r, (tipo,) in enumerate(tipos):
            item = self.tbl_recargos.item(r, 1)
            if not item:
                continue
            try:
                recargo = float(item.text())
            except ValueError:
                return QMessageBox.warning(self, "Error",
                    f"Fila {r+1}: el recargo debe ser un número válido.")
            self.db.execute_query(
                "UPDATE planilla_config_recargos SET recargo=? WHERE tipo_hora=?", (recargo, tipo))
        for concepto, spin in self._ded_spins.items():
            self.db.execute_query(
                "UPDATE planilla_config_deducciones SET porcentaje=? WHERE concepto=?",
                (spin.value(), concepto))
        QMessageBox.information(self, "Éxito", "Configuración guardada correctamente.")


# =============================================================================
# VISTA PRINCIPAL
# =============================================================================
class PlanillaView(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        lbl = QLabel("Módulo de Planilla")
        lbl.setStyleSheet(f"font-size:17px; font-weight:bold; color:{_RED};")
        root.addWidget(lbl)

        self.tabs = QTabWidget()
        self.tab_empleados  = TabEmpleados(self.db)
        self.tab_periodos   = TabPeriodos(self.db)
        self.tab_vales      = TabVales(self.db)
        self.tab_resumen    = TabResumen(self.db)
        self.tab_config     = TabConfiguracion(self.db)

        self.tabs.addTab(self.tab_empleados, "Empleados")
        self.tabs.addTab(self.tab_periodos,  "Períodos de Pago")
        self.tabs.addTab(self.tab_vales,     "Vales")
        self.tabs.addTab(self.tab_resumen,   "Resumen de Planilla")
        self.tabs.addTab(self.tab_config,    "Configuración")
        root.addWidget(self.tabs)

    def cargar_datos(self):
        self.tab_empleados.cargar_datos()
        self.tab_periodos.cargar_datos()
        self.tab_vales.cargar_datos()
        self.tab_resumen.cargar_datos()
        self.tab_config.cargar_datos()

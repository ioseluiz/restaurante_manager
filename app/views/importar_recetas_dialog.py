"""Diálogo «Importar recetas»: plantilla estándar, convertidor de fichas del cliente, simulación e importación."""

import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QButtonGroup, QDialog, QFileDialog, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QRadioButton, QTextEdit, QVBoxLayout,
)

from app.utils.plataforma import abrir_archivo


class ImportarRecetasDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._resultado = None
        self.setWindowTitle("Importar recetas")
        self.resize(940, 680)
        lay = QVBoxLayout(self)

        intro = QLabel(
            "Cargue recetas desde la <b>plantilla estándar</b>. Si el cliente las tiene en fichas (una receta por "
            "hoja), conviértalas primero: se genera la plantilla prellenada con lo que hay que revisar. "
            "<b>Nunca se borra</b> nada que no esté en el archivo.")
        intro.setWordWrap(True)
        lay.addWidget(intro)

        paso1 = QGroupBox("1. Preparar el archivo")
        f1 = QHBoxLayout(paso1)
        b_plantilla = QPushButton("Descargar plantilla vacía…")
        b_plantilla.clicked.connect(self._descargar_plantilla)
        b_convertir = QPushButton("Convertir fichas del cliente…")
        b_convertir.setToolTip("Lee un Excel con una ficha de receta por hoja (formato «Baño María») y genera "
                               "la plantilla prellenada, con la hoja «Revisión».")
        b_convertir.clicked.connect(self._convertir_fichas)
        f1.addWidget(b_plantilla)
        f1.addWidget(b_convertir)
        f1.addStretch()
        lay.addWidget(paso1)

        paso2 = QGroupBox("2. Importar la plantilla")
        f2 = QVBoxLayout(paso2)
        fila = QHBoxLayout()
        self.txt_ruta = QLineEdit()
        self.txt_ruta.setPlaceholderText("Plantilla de recetas (.xlsx)…")
        b_examinar = QPushButton("Examinar…")
        b_examinar.clicked.connect(self._examinar)
        fila.addWidget(self.txt_ruta, 1)
        fila.addWidget(b_examinar)
        f2.addLayout(fila)
        modos = QHBoxLayout()
        self.rb_nuevas = QRadioButton("Solo recetas nuevas (no toca las que ya existen)")
        self.rb_actualizar = QRadioButton("Actualizar existentes (reemplaza las recetas del archivo)")
        self.rb_nuevas.setChecked(True)
        grupo = QButtonGroup(self)
        grupo.addButton(self.rb_nuevas)
        grupo.addButton(self.rb_actualizar)
        modos.addWidget(self.rb_nuevas)
        modos.addWidget(self.rb_actualizar)
        modos.addStretch()
        f2.addLayout(modos)
        botones = QHBoxLayout()
        self.btn_sim = QPushButton("Simular (no guarda)")
        self.btn_sim.clicked.connect(lambda: self._ejecutar(True))
        self.btn_imp = QPushButton("Importar")
        self.btn_imp.setProperty("class", "btn-success")
        self.btn_imp.clicked.connect(lambda: self._ejecutar(False))
        self.btn_reporte = QPushButton("Guardar reporte…")
        self.btn_reporte.setToolTip("Excel con los problemas y la hoja «Insumos faltantes» lista para completar")
        self.btn_reporte.setEnabled(False)
        self.btn_reporte.clicked.connect(self._guardar_reporte)
        b_faltantes = QPushButton("Importar insumos faltantes…")
        b_faltantes.setToolTip("Crea los insumos de la hoja «Insumos faltantes» de un reporte ya completado")
        b_faltantes.clicked.connect(self._importar_faltantes)
        for b in (self.btn_sim, self.btn_imp, self.btn_reporte, b_faltantes):
            botones.addWidget(b)
        botones.addStretch()
        f2.addLayout(botones)
        lay.addWidget(paso2)

        self.txt_reporte = QTextEdit()
        self.txt_reporte.setReadOnly(True)
        self.txt_reporte.setStyleSheet("font-family: Consolas, Menlo, monospace;")
        lay.addWidget(self.txt_reporte, 1)

        pie = QHBoxLayout()
        b_anterior = QPushButton("Formato anterior (COSTEO DE PLATOS)…")
        b_anterior.setToolTip("Importador del Excel «COSTEO DE PLATOS Y SUS INSUMOS» (hoja «PLATOS CODIGOS Y RECETAS»)")
        b_anterior.clicked.connect(self._formato_anterior)
        pie.addWidget(b_anterior)
        pie.addStretch()
        b_cerrar = QPushButton("Cerrar")
        b_cerrar.clicked.connect(self.accept)
        pie.addWidget(b_cerrar, alignment=Qt.AlignRight)
        lay.addLayout(pie)

    # ------------------------------------------------------------------ paso 1
    def _descargar_plantilla(self):
        from app.utils.plantilla_recetas import generar_plantilla

        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar plantilla", "Plantilla recetas.xlsx", "Excel (*.xlsx)")
        if not ruta:
            return
        try:
            generar_plantilla(self.db, ruta)
        except Exception as e:
            QMessageBox.critical(self, "Plantilla", f"No se pudo crear la plantilla: {e}")
            return
        self.txt_ruta.setText(ruta)
        if QMessageBox.question(self, "Plantilla", f"Plantilla guardada:\n{ruta}\n\n¿Abrirla ahora?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            abrir_archivo(ruta)

    def _convertir_fichas(self):
        from app.utils.fichas_bano_maria import convertir_a_plantilla

        origen, _ = QFileDialog.getOpenFileName(self, "Fichas de recetas del cliente", "", "Excel (*.xlsx *.xlsm)")
        if not origen:
            return
        base = os.path.splitext(os.path.basename(origen))[0]
        destino, _ = QFileDialog.getSaveFileName(
            self, "Guardar plantilla prellenada",
            os.path.join(os.path.dirname(origen), f"Plantilla - {base} (para revisar).xlsx"), "Excel (*.xlsx)")
        if not destino:
            return
        if os.path.abspath(destino) == os.path.abspath(origen):
            QMessageBox.warning(self, "Convertir", "Elija otro nombre: no se sobrescribe el archivo del cliente.")
            return
        try:
            _fichas, resumen = convertir_a_plantilla(origen, destino, self.db)
        except Exception as e:
            QMessageBox.critical(self, "Convertir", f"No se pudo leer el archivo de fichas: {e}")
            return
        self.txt_ruta.setText(destino)
        self.txt_reporte.setPlainText(
            "PLANTILLA PRELLENADA\n====================\n" + "\n".join(resumen)
            + f"\n\nArchivo: {destino}\n\nRevise la hoja «Revisión», complete los rendimientos y luego pulse "
              "«Simular».")
        if QMessageBox.question(self, "Convertir", "Plantilla generada. ¿Abrirla para revisarla?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            abrir_archivo(destino)

    # ------------------------------------------------------------------ paso 2
    def _examinar(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Plantilla de recetas", "", "Excel (*.xlsx)")
        if ruta:
            self.txt_ruta.setText(ruta)

    def _ejecutar(self, simular):
        from app.utils.importar_recetas import importar

        ruta = self.txt_ruta.text().strip()
        if not ruta or not os.path.exists(ruta):
            QMessageBox.warning(self, "Importar", "Seleccione la plantilla de recetas.")
            return
        modo = "ACTUALIZAR" if self.rb_actualizar.isChecked() else "NUEVAS"
        prefijo = ""
        if not simular:
            aviso = ("Se reemplazarán las recetas del archivo que ya existen. " if modo == "ACTUALIZAR" else "")
            if QMessageBox.question(self, "Importar", aviso + "Se guardará antes una copia de respaldo de la base "
                                    "de datos. ¿Continuar?", QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
                return
            ok, destino = self.db.create_backup(os.path.dirname(self.db.db_path))
            if not ok:
                QMessageBox.critical(self, "Importar", f"No se pudo crear el respaldo; no se importó nada: {destino}")
                return
            prefijo = f"Respaldo creado: {destino}\n\n"
        try:
            self._resultado = importar(self.db, ruta, dry_run=simular, modo=modo)
        except Exception as e:
            QMessageBox.critical(self, "Importar", f"No se pudo leer/importar el archivo: {e}")
            return
        self.txt_reporte.setPlainText(prefijo + self._resultado.texto())
        self.btn_reporte.setEnabled(True)

    def _guardar_reporte(self):
        from app.utils.importar_recetas import exportar_reporte

        if not self._resultado:
            return
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar reporte", "Reporte importación recetas.xlsx",
                                              "Excel (*.xlsx)")
        if ruta:
            exportar_reporte(self._resultado, ruta)
            abrir_archivo(ruta)

    def _importar_faltantes(self):
        from app.utils.importar_recetas import importar_insumos_faltantes

        ruta, _ = QFileDialog.getOpenFileName(self, "Reporte con «Insumos faltantes» completado", "", "Excel (*.xlsx)")
        if not ruta:
            return
        try:
            _creados, mensajes = importar_insumos_faltantes(self.db, ruta)
        except Exception as e:
            QMessageBox.critical(self, "Insumos faltantes", str(e))
            return
        self.txt_reporte.setPlainText("INSUMOS FALTANTES\n=================\n" + "\n".join(mensajes)
                                      + "\n\nVuelva a simular la importación de recetas.")

    def _formato_anterior(self):
        from app.views.modulos.costo_platos import ImportarExcelDialog

        ImportarExcelDialog(self.db, self).exec_()

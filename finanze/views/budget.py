"""Budget mensili per categoria con stato di avanzamento."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QDoubleSpinBox,
                               QHeaderView, QLabel, QMessageBox, QProgressBar,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QVBoxLayout)

from ..componenti import Scheda, SchedaStat, etichetta, riga
from ..grafici import GraficoBarre
from ..icone import etichetta_categoria
from ..utils import euro, mese_corrente
from . import VistaBase


class VistaBudget(VistaBase):
    titolo = "Budget"
    sottotitolo = "Limiti di spesa mensili per categoria"

    def costruisci(self) -> None:
        _, lay = self.area_scorrevole()

        fila = riga()
        self.s_pianificato = SchedaStat("Budget pianificato", self.c, self.c["accento"])
        self.s_speso = SchedaStat("Speso questo mese", self.c, self.c["uscita"])
        self.s_residuo = SchedaStat("Residuo disponibile", self.c, self.c["entrata"])
        for s in (self.s_pianificato, self.s_speso, self.s_residuo):
            fila.addWidget(s)
        lay.addLayout(fila)

        sc_nuovo = Scheda("Imposta un budget")
        self.cmb_categoria = QComboBox()
        self.sp_importo = QDoubleSpinBox()
        self.sp_importo.setRange(0, 9_999_999)
        self.sp_importo.setDecimals(2)
        self.sp_importo.setSingleStep(25)
        self.sp_importo.setSuffix(f" {self.valuta}")
        b_salva = QPushButton("Salva budget"); b_salva.setObjectName("Primario")
        b_elimina = QPushButton("Rimuovi selezionato"); b_elimina.setObjectName("Pericolo")
        sc_nuovo.aggiungi_layout(riga(etichetta("Categoria"), self.cmb_categoria,
                                      etichetta("Limite mensile"), self.sp_importo,
                                      b_salva, b_elimina, None))
        lay.addWidget(sc_nuovo)

        sc_tab = Scheda("Stato dei budget")
        self.tab = QTableWidget(0, 5)
        self.tab.setHorizontalHeaderLabels(
            ["Categoria", "Limite", "Speso", "Residuo", "Avanzamento"])
        self.tab.verticalHeader().setVisible(False)
        self.tab.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tab.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tab.setMinimumHeight(300)
        h = self.tab.horizontalHeader()
        h.setSectionResizeMode(4, QHeaderView.Stretch)
        for c, l in ((0, 200), (1, 140), (2, 140), (3, 140)):
            h.resizeSection(c, l)
        sc_tab.aggiungi(self.tab)
        lay.addWidget(sc_tab)

        sc_graf = Scheda("Confronto limite / spesa effettiva")
        self.g_barre = GraficoBarre(self.c)
        self.g_barre.setMinimumHeight(260)
        sc_graf.aggiungi(self.g_barre, 1)
        lay.addWidget(sc_graf)
        lay.addStretch(1)

        b_salva.clicked.connect(self.salva)
        b_elimina.clicked.connect(self.elimina)
        self.grafici = [self.g_barre]

    def aggiorna(self) -> None:
        v = self.valuta
        dal, al = mese_corrente()
        scelta = self.cmb_categoria.currentData()
        self.cmb_categoria.clear()
        for r in self.db.query(
                "SELECT nome, icona FROM categorie WHERE tipo='uscita' ORDER BY nome"):
            self.cmb_categoria.addItem(etichetta_categoria(r["nome"], r["icona"]), r["nome"])
        idx = self.cmb_categoria.findData(scelta) if scelta else -1
        if idx >= 0:
            self.cmb_categoria.setCurrentIndex(idx)

        icone = self.db.icone_categorie()
        righe = self.db.query("SELECT * FROM budget ORDER BY mensile DESC")
        self.tab.setRowCount(len(righe))
        tot_limite = tot_speso = 0.0
        dati_grafico = []
        for r, b in enumerate(righe):
            limite = float(b["mensile"])
            speso = float(self.db.query(
                "SELECT COALESCE(SUM(importo),0) s FROM movimenti "
                "WHERE tipo='uscita' AND categoria=? AND data BETWEEN ? AND ?",
                (b["categoria"], dal, al))[0]["s"])
            tot_limite += limite
            tot_speso += speso
            residuo = limite - speso
            quota = int(speso / limite * 100) if limite else 0
            colore = (self.c["entrata"] if quota < 75 else
                      self.c["attenzione"] if quota < 100 else self.c["uscita"])

            it_cat = QTableWidgetItem(
                etichetta_categoria(b["categoria"], icone.get(b["categoria"])))
            it_cat.setData(Qt.UserRole, b["id"])
            self.tab.setItem(r, 0, it_cat)
            for col, val, col_testo in ((1, limite, None), (2, speso, colore),
                                        (3, residuo, colore)):
                it = QTableWidgetItem(euro(val, v))
                it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if col_testo:
                    it.setForeground(QColor(col_testo))
                self.tab.setItem(r, col, it)
            barra = QProgressBar()
            barra.setRange(0, 100)
            barra.setValue(min(100, quota))
            barra.setFormat(f"{quota}%")
            barra.setStyleSheet(
                f"QProgressBar {{ color: {self.c['testo']}; }}"
                f"QProgressBar::chunk {{ background: {colore}; border-radius: 7px; }}")
            self.tab.setCellWidget(r, 4, barra)
            dati_grafico.append((b["categoria"][:12], [limite, speso]))

        self.s_pianificato.imposta(tot_limite, f"{len(righe)} categorie con budget", v)
        self.s_speso.imposta(tot_speso,
                             f"{(tot_speso/tot_limite*100 if tot_limite else 0):.0f}% del budget", v)
        self.s_residuo.imposta(tot_limite - tot_speso, "fino alla fine del mese", v)
        self.g_barre.imposta_dati(dati_grafico,
                                  [("Limite", self.c["accento"]), ("Speso", self.c["uscita"])])

    def salva(self) -> None:
        cat = (self.cmb_categoria.currentData() or "").strip()
        if not cat:
            return
        self.db.esegui(
            "INSERT INTO budget(categoria, mensile) VALUES(?,?) "
            "ON CONFLICT(categoria) DO UPDATE SET mensile=excluded.mensile",
            (cat, self.sp_importo.value()))
        self.dati_cambiati.emit()

    def elimina(self) -> None:
        sel = self.tab.selectionModel().selectedRows()
        if not sel:
            QMessageBox.information(self, "Nessuna selezione",
                                    "Seleziona una riga della tabella da rimuovere.")
            return
        for idx in sel:
            self.db.elimina("budget", int(self.tab.item(idx.row(), 0).data(Qt.UserRole)))
        self.dati_cambiati.emit()

"""Movimenti ricorrenti: canoni, stipendi, abbonamenti."""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QDateEdit,
                               QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
                               QHeaderView, QLabel, QLineEdit, QMessageBox,
                               QPushButton, QSpinBox, QTableWidget, QTableWidgetItem,
                               QVBoxLayout)

from ..componenti import (Scheda, SchedaStat, abilita_deselezione, etichetta,
                          riga)
from ..ricorrenze import prossima
from ..utils import data_it, euro
from . import VistaBase
from ..lingue import t

FREQUENZE = ["settimanale", "quindicinale", "mensile", "trimestrale", "annuale"]


class DialogoRicorrente(QDialog):
    def __init__(self, db, ricorrente=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.ric = dict(ricorrente) if ricorrente else None
        self.setWindowTitle("Modifica ricorrenza" if ricorrente else "Nuova ricorrenza")
        self.setMinimumWidth(430)
        v = db.leggi("valuta", "€")

        self.descrizione = QLineEdit(); self.descrizione.setPlaceholderText(t("es. Affitto"))
        self.tipo = QComboBox(); self.tipo.addItems(["uscita", "entrata"])
        self.importo = QDoubleSpinBox(); self.importo.setRange(0.01, 9_999_999)
        self.importo.setDecimals(2); self.importo.setSuffix(f" {v}")
        self.categoria = QComboBox(); self.categoria.setEditable(True)
        self.conto = QComboBox()
        self.conto.addItems([r["nome"] for r in db.query("SELECT nome FROM conti ORDER BY nome")])
        self.frequenza = QComboBox(); self.frequenza.addItems(FREQUENZE)
        self.frequenza.setCurrentText("mensile")
        self.giorno = QSpinBox(); self.giorno.setRange(1, 31); self.giorno.setValue(1)
        self.inizio = QDateEdit(QDate.currentDate())
        self.inizio.setCalendarPopup(True); self.inizio.setDisplayFormat("dd/MM/yyyy")
        self.attiva = QCheckBox("Attiva"); self.attiva.setChecked(True)

        modulo = QFormLayout(); modulo.setSpacing(10)
        modulo.addRow(t("Descrizione"), self.descrizione)
        modulo.addRow(t("Tipo"), self.tipo)
        modulo.addRow(t("Importo"), self.importo)
        modulo.addRow(t("Categoria"), self.categoria)
        modulo.addRow(t("Conto"), self.conto)
        modulo.addRow(t("Frequenza"), self.frequenza)
        modulo.addRow(t("Giorno del mese"), self.giorno)
        modulo.addRow(t("Prima scadenza"), self.inizio)
        modulo.addRow("", self.attiva)

        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Save).setText(t("Salva"))
        bb.button(QDialogButtonBox.Save).setObjectName("Primario")
        bb.button(QDialogButtonBox.Cancel).setText(t("Annulla"))
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        lay = QVBoxLayout(self); lay.setContentsMargins(18, 18, 18, 14)
        lay.addLayout(modulo); lay.addWidget(bb)

        self.tipo.currentTextChanged.connect(self._categorie)
        self._categorie(self.tipo.currentText())

        if self.ric:
            r = self.ric
            self.descrizione.setText(r["descrizione"])
            self.tipo.setCurrentText(r["tipo"])
            self._categorie(r["tipo"])
            self.importo.setValue(float(r["importo"]))
            self.categoria.setCurrentText(r["categoria"])
            self.conto.setCurrentText(r["conto"])
            self.frequenza.setCurrentText(r["frequenza"])
            self.giorno.setValue(int(r["giorno"]) or 1)
            try:
                a, m, g = (int(x) for x in r["inizio"].split("-"))
                self.inizio.setDate(QDate(a, m, g))
            except ValueError:
                pass
            self.attiva.setChecked(bool(r["attiva"]))

    def _categorie(self, tipo: str) -> None:
        corrente = self.categoria.currentText()
        self.categoria.clear()
        self.categoria.addItems([r["nome"] for r in self.db.query(
            "SELECT nome FROM categorie WHERE tipo=? ORDER BY nome", (tipo,))])
        if corrente:
            idx = self.categoria.findText(corrente)
            if idx >= 0:
                self.categoria.setCurrentIndex(idx)

    def dati(self) -> dict:
        return {
            "id": self.ric["id"] if self.ric else None,
            "descrizione": self.descrizione.text().strip() or "Ricorrenza",
            "tipo": self.tipo.currentText(),
            "importo": self.importo.value(),
            "categoria": self.categoria.currentText().strip() or "Altro",
            "conto": self.conto.currentText().strip() or "Principale",
            "frequenza": self.frequenza.currentText(),
            "giorno": self.giorno.value(),
            "inizio": self.inizio.date().toString("yyyy-MM-dd"),
            "attiva": 1 if self.attiva.isChecked() else 0,
        }


class VistaRicorrenti(VistaBase):
    titolo = "Ricorrenti"
    sottotitolo = "Movimenti automatici periodici"

    def costruisci(self) -> None:
        _, lay = self.area_scorrevole()

        fila = riga()
        self.s_entrate = SchedaStat(t("Entrate fisse / mese"), self.c, self.c["entrata"])
        self.s_uscite = SchedaStat(t("Uscite fisse / mese"), self.c, self.c["uscita"])
        self.s_netto = SchedaStat(t("Flusso fisso netto"), self.c, self.c["accento"])
        for s in (self.s_entrate, self.s_uscite, self.s_netto):
            fila.addWidget(s)
        lay.addLayout(fila)

        b_nuovo = QPushButton(t("+  Nuova ricorrenza")); b_nuovo.setObjectName("Primario")
        b_mod = QPushButton(t("Modifica"))
        b_attiva = QPushButton(t("Attiva / sospendi"))
        b_del = QPushButton(t("Elimina")); b_del.setObjectName("Pericolo")
        b_genera = QPushButton(t("Genera movimenti dovuti"))
        lay.addLayout(riga(b_nuovo, b_mod, b_attiva, b_del, None, b_genera))

        sc = Scheda(t("Regole configurate"))
        self.tab = QTableWidget(0, 8)
        self.tab.setHorizontalHeaderLabels(
            [t("Descrizione"), t("Tipo"), t("Importo"), t("Categoria"), t("Conto"),
             t("Frequenza"), t("Prossima"), t("Stato")])
        self.tab.verticalHeader().setVisible(False)
        self.tab.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tab.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tab.setMinimumHeight(340)
        h = self.tab.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Stretch)
        for c, l in ((1, 80), (2, 120), (3, 150), (4, 130), (5, 120), (6, 110), (7, 100)):
            h.resizeSection(c, l)
        sc.aggiungi(self.tab)
        lay.addWidget(sc)
        lay.addStretch(1)

        b_nuovo.clicked.connect(self.nuovo)
        b_mod.clicked.connect(self.modifica)
        b_attiva.clicked.connect(self.commuta)
        b_del.clicked.connect(self.elimina)
        b_genera.clicked.connect(self.genera)
        self.tab.doubleClicked.connect(self.modifica)
        abilita_deselezione(self.tab)

    # ------------------------------------------------------------------ dati
    def aggiorna(self) -> None:
        v = self.valuta
        righe = self.db.query("SELECT * FROM ricorrenti ORDER BY tipo, descrizione")
        self.tab.setRowCount(len(righe))
        ent = usc = 0.0
        for r, x in enumerate(righe):
            mensile = self._importo_mensile(float(x["importo"]), x["frequenza"])
            if x["attiva"]:
                if x["tipo"] == "entrata":
                    ent += mensile
                else:
                    usc += mensile
            ultima = x["ultima_generazione"] or x["inizio"]
            try:
                a, m, g = (int(i) for i in ultima.split("-"))
                pros = prossima(x["frequenza"], date(a, m, g), int(x["giorno"]))
                testo_pros = data_it(pros.isoformat())
            except ValueError:
                testo_pros = "—"
            testi = [x["descrizione"], x["tipo"], euro(float(x["importo"]), v),
                     x["categoria"], x["conto"], x["frequenza"], testo_pros,
                     "attiva" if x["attiva"] else "sospesa"]
            for col, t in enumerate(testi):
                it = QTableWidgetItem(t)
                if col == 0:
                    it.setData(Qt.UserRole, x["id"])
                if col == 2:
                    it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tab.setItem(r, col, it)

        self.s_entrate.imposta(ent, "normalizzate su base mensile", v)
        self.s_uscite.imposta(usc, "normalizzate su base mensile", v)
        self.s_netto.imposta(ent - usc, "disponibile prima delle spese variabili", v)

    @staticmethod
    def _importo_mensile(importo: float, frequenza: str) -> float:
        fattori = {"settimanale": 52 / 12, "quindicinale": 26 / 12, "mensile": 1,
                   "trimestrale": 1 / 3, "annuale": 1 / 12}
        return importo * fattori.get(frequenza, 1)

    def _selezionato(self):
        sel = self.tab.selectionModel().selectedRows()
        if not sel:
            return None
        id_ = int(self.tab.item(sel[0].row(), 0).data(Qt.UserRole))
        return self.db.query("SELECT * FROM ricorrenti WHERE id=?", (id_,))[0]

    # ---------------------------------------------------------------- azioni
    def nuovo(self) -> None:
        dlg = DialogoRicorrente(self.db, None, self)
        if dlg.exec():
            d = dlg.dati()
            self.db.esegui(
                "INSERT INTO ricorrenti(descrizione,tipo,importo,categoria,conto,"
                "frequenza,giorno,inizio,attiva) VALUES(?,?,?,?,?,?,?,?,?)",
                (d["descrizione"], d["tipo"], d["importo"], d["categoria"], d["conto"],
                 d["frequenza"], d["giorno"], d["inizio"], d["attiva"]))
            self.dati_cambiati.emit()

    def modifica(self) -> None:
        r = self._selezionato()
        if r is None:
            return
        dlg = DialogoRicorrente(self.db, r, self)
        if dlg.exec():
            d = dlg.dati()
            self.db.esegui(
                "UPDATE ricorrenti SET descrizione=?, tipo=?, importo=?, categoria=?, "
                "conto=?, frequenza=?, giorno=?, inizio=?, attiva=? WHERE id=?",
                (d["descrizione"], d["tipo"], d["importo"], d["categoria"], d["conto"],
                 d["frequenza"], d["giorno"], d["inizio"], d["attiva"], r["id"]))
            self.dati_cambiati.emit()

    def commuta(self) -> None:
        r = self._selezionato()
        if r is None:
            return
        self.db.esegui("UPDATE ricorrenti SET attiva=? WHERE id=?",
                       (0 if r["attiva"] else 1, r["id"]))
        self.dati_cambiati.emit()

    def elimina(self) -> None:
        r = self._selezionato()
        if r is None:
            return
        if QMessageBox.question(
                self, "Conferma", f"Eliminare la ricorrenza «{r['descrizione']}»?\n"
                "I movimenti già generati restano in archivio.",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            self.db.elimina("ricorrenti", r["id"])
            self.dati_cambiati.emit()

    def genera(self) -> None:
        n = self.db.genera_ricorrenti()
        QMessageBox.information(
            self, "Generazione completata",
            f"Creati {n} movimenti dalle regole attive." if n
            else "Nessun movimento da generare: sei in pari.")
        if n:
            self.dati_cambiati.emit()
        else:
            self.aggiorna()

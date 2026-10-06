"""Registro movimenti: inserimento, modifica, filtri, import/export CSV."""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QDateEdit, QFileDialog,
                               QHBoxLayout, QHeaderView, QLabel, QLineEdit,
                               QMessageBox, QPushButton, QTableWidget,
                               QTableWidgetItem, QVBoxLayout)

from ..componenti import DialogoMovimento, Scheda, etichetta, riga
from ..utils import anno_corrente, data_it, esporta_csv, euro, importa_csv, mese_corrente
from . import VistaBase

COLONNE = ["Data", "Tipo", "Descrizione", "Categoria", "Conto", "Etichette", "Importo"]


class VistaMovimenti(VistaBase):
    titolo = "Movimenti"
    sottotitolo = "Entrate e uscite registrate"

    def costruisci(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(2, 2, 6, 6)
        lay.setSpacing(12)

        # ----------------------------------------------------------- filtri
        sc_filtri = Scheda()
        self.f_periodo = QComboBox()
        self.f_periodo.addItems(["Mese corrente", "Anno corrente", "Tutto", "Personalizzato"])
        self.f_dal = QDateEdit(QDate.currentDate().addMonths(-1))
        self.f_al = QDateEdit(QDate.currentDate())
        for d in (self.f_dal, self.f_al):
            d.setCalendarPopup(True)
            d.setDisplayFormat("dd/MM/yyyy")
            d.setEnabled(False)
        self.f_tipo = QComboBox(); self.f_tipo.addItems(["Tutti", "entrata", "uscita"])
        self.f_categoria = QComboBox()
        self.f_conto = QComboBox()
        self.f_testo = QLineEdit()
        self.f_testo.setPlaceholderText("Cerca descrizione o etichetta…")
        self.f_testo.setClearButtonEnabled(True)

        fila1 = riga(etichetta("Periodo"), self.f_periodo,
                     etichetta("dal"), self.f_dal, etichetta("al"), self.f_al, None)
        fila2 = riga(etichetta("Tipo"), self.f_tipo,
                     etichetta("Categoria"), self.f_categoria,
                     etichetta("Conto"), self.f_conto, self.f_testo)
        sc_filtri.aggiungi_layout(fila1)
        sc_filtri.aggiungi_layout(fila2)
        lay.addWidget(sc_filtri)

        # ----------------------------------------------------------- azioni
        self.b_nuovo = QPushButton("+  Nuovo movimento"); self.b_nuovo.setObjectName("Primario")
        self.b_modifica = QPushButton("Modifica")
        self.b_duplica = QPushButton("Duplica")
        self.b_elimina = QPushButton("Elimina"); self.b_elimina.setObjectName("Pericolo")
        self.b_esporta = QPushButton("Esporta CSV")
        self.b_importa = QPushButton("Importa CSV")
        self.et_riepilogo = QLabel("")
        self.et_riepilogo.setObjectName("NotaScheda")
        lay.addLayout(riga(self.b_nuovo, self.b_modifica, self.b_duplica, self.b_elimina,
                           None, self.et_riepilogo, self.b_esporta, self.b_importa))

        # ---------------------------------------------------------- tabella
        self.tab = QTableWidget(0, len(COLONNE))
        self.tab.setHorizontalHeaderLabels(COLONNE)
        self.tab.verticalHeader().setVisible(False)
        self.tab.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tab.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tab.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tab.setSortingEnabled(True)
        h = self.tab.horizontalHeader()
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        for col, larg in ((0, 100), (1, 90), (3, 170), (4, 150), (5, 150), (6, 130)):
            h.resizeSection(col, larg)
        lay.addWidget(self.tab, 1)

        # -------------------------------------------------------- connessioni
        self.f_periodo.currentIndexChanged.connect(self._cambia_periodo)
        for w in (self.f_dal, self.f_al):
            w.dateChanged.connect(self.aggiorna)
        self.f_tipo.currentIndexChanged.connect(self._cambia_tipo)
        self.f_categoria.currentIndexChanged.connect(self.aggiorna)
        self.f_conto.currentIndexChanged.connect(self.aggiorna)
        self.f_testo.textChanged.connect(self.aggiorna)
        self.b_nuovo.clicked.connect(self.nuovo)
        self.b_modifica.clicked.connect(self.modifica)
        self.b_duplica.clicked.connect(self.duplica)
        self.b_elimina.clicked.connect(self.elimina)
        self.b_esporta.clicked.connect(self.esporta)
        self.b_importa.clicked.connect(self.importa)
        self.tab.doubleClicked.connect(self.modifica)
        QShortcut(QKeySequence("Ctrl+N"), self, self.nuovo)
        QShortcut(QKeySequence("Delete"), self.tab, self.elimina)

        self._carica_elenchi()

    # --------------------------------------------------------------- supporto
    def _carica_elenchi(self) -> None:
        for combo, sql, vuoto in (
            (self.f_categoria, "SELECT DISTINCT nome FROM categorie ORDER BY nome", "Tutte"),
            (self.f_conto, "SELECT nome FROM conti ORDER BY nome", "Tutti"),
        ):
            testo = combo.currentText()
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(vuoto)
            combo.addItems([r["nome"] for r in self.db.query(sql)])
            idx = combo.findText(testo)
            combo.setCurrentIndex(max(0, idx))
            combo.blockSignals(False)

    def _cambia_periodo(self) -> None:
        pers = self.f_periodo.currentText() == "Personalizzato"
        self.f_dal.setEnabled(pers)
        self.f_al.setEnabled(pers)
        self.aggiorna()

    def _cambia_tipo(self) -> None:
        tipo = self.f_tipo.currentText()
        self.f_categoria.blockSignals(True)
        testo = self.f_categoria.currentText()
        self.f_categoria.clear()
        self.f_categoria.addItem("Tutte")
        if tipo in ("entrata", "uscita"):
            self.f_categoria.addItems(
                [r["nome"] for r in self.db.query(
                    "SELECT nome FROM categorie WHERE tipo=? ORDER BY nome", (tipo,))])
        else:
            self.f_categoria.addItems(
                [r["nome"] for r in self.db.query(
                    "SELECT DISTINCT nome FROM categorie ORDER BY nome")])
        idx = self.f_categoria.findText(testo)
        self.f_categoria.setCurrentIndex(max(0, idx))
        self.f_categoria.blockSignals(False)
        self.aggiorna()

    def _intervallo(self) -> tuple[str, str]:
        scelta = self.f_periodo.currentText()
        if scelta == "Mese corrente":
            return mese_corrente()
        if scelta == "Anno corrente":
            return anno_corrente()
        if scelta == "Tutto":
            return "", ""
        return (self.f_dal.date().toString("yyyy-MM-dd"),
                self.f_al.date().toString("yyyy-MM-dd"))

    def _filtri(self) -> dict:
        dal, al = self._intervallo()
        return {
            "dal": dal, "al": al,
            "tipo": "" if self.f_tipo.currentText() == "Tutti" else self.f_tipo.currentText(),
            "categoria": "" if self.f_categoria.currentText() in ("Tutte", "") else self.f_categoria.currentText(),
            "conto": "" if self.f_conto.currentText() in ("Tutti", "") else self.f_conto.currentText(),
            "testo": self.f_testo.text().strip(),
        }

    def _selezionati(self) -> list[int]:
        ids = []
        for idx in self.tab.selectionModel().selectedRows():
            it = self.tab.item(idx.row(), 0)
            if it is not None:
                ids.append(int(it.data(Qt.UserRole)))
        return ids

    # ------------------------------------------------------------------ dati
    def aggiorna(self) -> None:
        self._carica_elenchi()
        righe = self.db.movimenti(**self._filtri())
        v = self.valuta
        self.tab.setSortingEnabled(False)
        self.tab.setRowCount(len(righe))
        entrate = uscite = 0.0
        for r, m in enumerate(righe):
            importo = float(m["importo"])
            if m["tipo"] == "entrata":
                entrate += importo
            else:
                uscite += importo
            segno = "+" if m["tipo"] == "entrata" else "−"
            testi = [data_it(m["data"]), m["tipo"], m["descrizione"] or "—",
                     m["categoria"], m["conto"], m["etichette"],
                     f"{segno} {euro(importo, v)}"]
            for col, testo in enumerate(testi):
                it = QTableWidgetItem(testo)
                if col == 0:
                    it.setData(Qt.UserRole, m["id"])
                if col == 6:
                    it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    it.setForeground(QColor(self.c["entrata"] if m["tipo"] == "entrata"
                                            else self.c["uscita"]))
                self.tab.setItem(r, col, it)
        self.tab.setSortingEnabled(True)
        self.et_riepilogo.setText(
            f"{len(righe)} movimenti   ·   entrate {euro(entrate, v)}   ·   "
            f"uscite {euro(uscite, v)}   ·   saldo {euro(entrate - uscite, v)}")

    # ----------------------------------------------------------------- azioni
    def _elenchi_dialogo(self) -> tuple[list[str], list[str], list[str]]:
        ent = [r["nome"] for r in self.db.query(
            "SELECT nome FROM categorie WHERE tipo='entrata' ORDER BY nome")]
        usc = [r["nome"] for r in self.db.query(
            "SELECT nome FROM categorie WHERE tipo='uscita' ORDER BY nome")]
        conti = [r["nome"] for r in self.db.query("SELECT nome FROM conti ORDER BY nome")]
        return ent, usc, conti or ["Principale"]

    def nuovo(self, preimpostato: dict | None = None) -> None:
        ent, usc, conti = self._elenchi_dialogo()
        dlg = DialogoMovimento(self.db, ent, usc, conti, preimpostato, self)
        if dlg.exec():
            dati = dlg.dati()
            if dati["importo"] <= 0:
                QMessageBox.warning(self, "Importo non valido",
                                    "Inserisci un importo maggiore di zero.")
                return
            dati["id"] = None
            self.db.salva_movimento(dati)
            self.dati_cambiati.emit()

    def modifica(self) -> None:
        ids = self._selezionati()
        if not ids:
            return
        m = self.db.query("SELECT * FROM movimenti WHERE id=?", (ids[0],))[0]
        ent, usc, conti = self._elenchi_dialogo()
        dlg = DialogoMovimento(self.db, ent, usc, conti, dict(m), self)
        if dlg.exec():
            self.db.salva_movimento(dlg.dati())
            self.dati_cambiati.emit()

    def duplica(self) -> None:
        ids = self._selezionati()
        if not ids:
            return
        m = dict(self.db.query("SELECT * FROM movimenti WHERE id=?", (ids[0],))[0])
        m["data"] = date.today().isoformat()
        self.nuovo(m)

    def elimina(self) -> None:
        ids = self._selezionati()
        if not ids:
            return
        risposta = QMessageBox.question(
            self, "Conferma eliminazione",
            f"Eliminare {len(ids)} movimento/i? L'operazione non è reversibile.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if risposta != QMessageBox.Yes:
            return
        for i in ids:
            self.db.elimina("movimenti", i)
        self.dati_cambiati.emit()

    def esporta(self) -> None:
        percorso, _ = QFileDialog.getSaveFileName(
            self, "Esporta movimenti", f"movimenti-{date.today().isoformat()}.csv",
            "File CSV (*.csv)")
        if not percorso:
            return
        righe = self.db.movimenti(**self._filtri())
        n = esporta_csv(percorso, righe,
                        ["data", "tipo", "importo", "categoria", "conto",
                         "descrizione", "etichette"])
        QMessageBox.information(self, "Esportazione completata",
                                f"Esportati {n} movimenti in:\n{percorso}")

    def importa(self) -> None:
        percorso, _ = QFileDialog.getOpenFileName(
            self, "Importa movimenti da CSV", "", "File CSV (*.csv *.txt)")
        if not percorso:
            return
        try:
            righe = importa_csv(percorso)
        except Exception as e:  # file malformato
            QMessageBox.critical(self, "Errore di lettura", str(e))
            return
        if not righe:
            QMessageBox.warning(self, "Nessun dato",
                                "Il file non contiene righe riconoscibili.\n"
                                "Colonne attese: data;tipo;importo;categoria;conto;descrizione")
            return
        for r in righe:
            self.db.salva_movimento(r)
        QMessageBox.information(self, "Importazione completata",
                                f"Importati {len(righe)} movimenti.")
        self.dati_cambiati.emit()

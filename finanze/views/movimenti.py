"""Registro movimenti: inserimento rapido, filtri immediati, modifica e scambio dati.

L'obiettivo della pagina è registrare una spesa in pochi secondi: la barra in alto
salva un movimento con un importo e un Invio, i filtri sono pulsanti a un clic e
ogni operazione è annullabile o confermata senza finestre da chiudere.
"""
from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import QDate, QTimer, Qt
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (QAbstractItemView, QButtonGroup, QComboBox,
                               QDateEdit, QDoubleSpinBox, QFileDialog, QHeaderView,
                               QLabel, QLineEdit, QMenu, QMessageBox, QPushButton,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from ..categorie import DialogoNuovaCategoria
from ..componenti import (DialogoMovimento, Scheda, abilita_deselezione,
                          etichetta, riga)
from ..icone import etichetta_categoria, solo_nome
from ..utils import (anno_corrente, data_it, esporta_csv, euro, importa_csv,
                     mese_corrente)
from . import VistaBase

COLONNE = ["Data", "Tipo", "Descrizione", "Categoria", "Conto", "Etichette", "Importo"]
PERIODI = ["Oggi", "7 giorni", "Mese", "Anno", "Tutto", "Date…"]


class Cella(QTableWidgetItem):
    """Cella con chiave di ordinamento esplicita (date e importi reali)."""

    def __init__(self, testo: str, chiave=None):
        super().__init__(testo)
        self.chiave = testo if chiave is None else chiave

    def __lt__(self, altra):
        if isinstance(altra, Cella):
            try:
                return self.chiave < altra.chiave
            except TypeError:
                pass
        return super().__lt__(altra)


def data_relativa(iso: str) -> str:
    """«oggi», «ieri» o la data in formato italiano."""
    try:
        a, m, g = (int(x) for x in iso.split("-"))
        differenza = (date.today() - date(a, m, g)).days
    except ValueError:
        return iso
    if differenza == 0:
        return "oggi"
    if differenza == 1:
        return "ieri"
    return data_it(iso)


class VistaMovimenti(VistaBase):
    titolo = "Movimenti"
    sottotitolo = "Entrate e uscite registrate"

    def costruisci(self) -> None:
        self._eliminati: list[dict] = []     # per annullare l'ultima eliminazione
        self._firma_elenchi = ""             # evita di ricostruire le combo a vuoto

        lay = QVBoxLayout(self)
        lay.setContentsMargins(2, 2, 6, 6)
        lay.setSpacing(10)

        lay.addWidget(self._barra_inserimento())
        lay.addWidget(self._barra_filtri())
        lay.addLayout(self._barra_azioni())
        lay.addWidget(self._tabella(), 1)

        self.et_stato = QLabel("")
        self.et_stato.setObjectName("NotaScheda")
        lay.addWidget(self.et_stato)

        self._timer_stato = QTimer(self); self._timer_stato.setSingleShot(True)
        self._timer_stato.timeout.connect(lambda: self.et_stato.setText(""))
        self._timer_ricerca = QTimer(self); self._timer_ricerca.setSingleShot(True)
        self._timer_ricerca.timeout.connect(self.aggiorna)

        self._scorciatoie()

    # ------------------------------------------------------ inserimento veloce
    def _barra_inserimento(self) -> QWidget:
        sc = Scheda()
        self.q_tipo = QPushButton("Uscita")
        self.q_tipo.setCheckable(True)
        self.q_tipo.setObjectName("Segmento")
        self.q_tipo.setFixedWidth(96)
        self.q_tipo.clicked.connect(self._commuta_tipo_rapido)

        self.q_importo = QDoubleSpinBox()
        self.q_importo.setRange(0, 99_999_999)
        self.q_importo.setDecimals(2)
        self.q_importo.setGroupSeparatorShown(True)
        self.q_importo.setMaximumWidth(150)
        self.q_importo.setMinimumWidth(130)
        self.q_importo.setSuffix(f" {self.valuta}")

        self.q_descrizione = QLineEdit()
        self.q_descrizione.setPlaceholderText("Descrizione")
        self.q_categoria = QComboBox(); self.q_categoria.setMinimumWidth(170)
        self.b_nuova_cat = QPushButton("+")
        self.b_nuova_cat.setObjectName("AggiungiAccanto")
        self.b_nuova_cat.setFixedWidth(34)
        self.b_nuova_cat.setToolTip("Crea una nuova categoria")
        self.b_nuova_cat.clicked.connect(self.nuova_categoria)
        self.q_conto = QComboBox(); self.q_conto.setMinimumWidth(140)
        self.q_data = QDateEdit(QDate.currentDate())
        self.q_data.setCalendarPopup(True)
        self.q_data.setDisplayFormat("dd/MM/yyyy")
        self.q_data.setMaximumWidth(130)

        b_salva = QPushButton("Aggiungi"); b_salva.setObjectName("Primario")
        b_salva.clicked.connect(self.inserimento_rapido)
        b_dettagli = QPushButton("Altri campi…")
        b_dettagli.setToolTip("Apre la finestra completa con etichette e note (Ctrl+N)")
        b_dettagli.clicked.connect(self.nuovo)

        sc.aggiungi_layout(riga(self.q_tipo, self.q_importo, self.q_descrizione,
                                self.q_categoria, self.b_nuova_cat, self.q_conto,
                                self.q_data, b_salva, b_dettagli))
        for campo in (self.q_descrizione, self.q_importo):
            campo.setToolTip("Invio salva il movimento")
        self.q_descrizione.returnPressed.connect(self.inserimento_rapido)
        self._tipo_rapido = "uscita"
        self.q_tipo.setStyleSheet(
            f"background: {self.c['uscita']}; color: #ffffff; "
            f"border-color: {self.c['uscita']}; font-weight: 600;")
        return sc

    def _commuta_tipo_rapido(self) -> None:
        self._tipo_rapido = "entrata" if self.q_tipo.isChecked() else "uscita"
        self.q_tipo.setText("Entrata" if self.q_tipo.isChecked() else "Uscita")
        colore = self.c["entrata"] if self.q_tipo.isChecked() else self.c["uscita"]
        self.q_tipo.setStyleSheet(
            f"background: {colore}; color: #ffffff; border-color: {colore};"
            "font-weight: 600;")
        self._aggiorna_categorie_rapide()

    def _aggiorna_categorie_rapide(self) -> None:
        corrente = self.q_categoria.currentData() or solo_nome(self.q_categoria.currentText())
        self.q_categoria.clear()
        for r in self.db.query(
                "SELECT nome, icona FROM categorie WHERE tipo=? ORDER BY nome",
                (self._tipo_rapido,)):
            self.q_categoria.addItem(etichetta_categoria(r["nome"], r["icona"]), r["nome"])
        idx = self.q_categoria.findData(corrente)
        if idx >= 0:
            self.q_categoria.setCurrentIndex(idx)

    # ----------------------------------------------------------------- filtri
    def _barra_filtri(self) -> QWidget:
        sc = Scheda()

        self.g_periodo = QButtonGroup(self)
        fila = riga()
        for i, nome in enumerate(PERIODI):
            b = QPushButton(nome); b.setObjectName("Segmento"); b.setCheckable(True)
            b.setChecked(nome == "Mese")
            self.g_periodo.addButton(b, i)
            fila.addWidget(b)
        self.f_dal = QDateEdit(QDate.currentDate().addMonths(-1))
        self.f_al = QDateEdit(QDate.currentDate())
        for d in (self.f_dal, self.f_al):
            d.setCalendarPopup(True); d.setDisplayFormat("dd/MM/yyyy")
            d.setMaximumWidth(130); d.setVisible(False)
        fila.addWidget(self.f_dal); fila.addWidget(self.f_al)
        fila.addStretch(1)

        self.f_testo = QLineEdit()
        self.f_testo.setPlaceholderText("Cerca…")
        self.f_testo.setToolTip("Cerca nelle descrizioni e nelle etichette  ·  Ctrl+F")
        self.f_testo.setClearButtonEnabled(True)
        self.f_testo.setMinimumWidth(240)
        fila.addWidget(self.f_testo)
        sc.aggiungi_layout(fila)

        self.g_tipo = QButtonGroup(self)
        fila2 = riga()
        for i, nome in enumerate(("Tutti", "Entrate", "Uscite")):
            b = QPushButton(nome); b.setObjectName("Segmento"); b.setCheckable(True)
            b.setChecked(i == 0)
            self.g_tipo.addButton(b, i)
            fila2.addWidget(b)
        self.f_categoria = QComboBox(); self.f_categoria.setMinimumWidth(170)
        self.f_conto = QComboBox(); self.f_conto.setMinimumWidth(150)
        self.b_azzera = QPushButton("Azzera filtri")
        self.b_azzera.setVisible(False)
        fila2.addWidget(etichetta("Categoria")); fila2.addWidget(self.f_categoria)
        fila2.addWidget(etichetta("Conto")); fila2.addWidget(self.f_conto)
        fila2.addWidget(self.b_azzera)
        fila2.addStretch(1)
        sc.aggiungi_layout(fila2)

        self.g_periodo.idClicked.connect(self._cambia_periodo)
        self.g_tipo.idClicked.connect(self._cambia_tipo)
        self.f_dal.dateChanged.connect(self.aggiorna)
        self.f_al.dateChanged.connect(self.aggiorna)
        self.f_categoria.currentIndexChanged.connect(self.aggiorna)
        self.f_conto.currentIndexChanged.connect(self.aggiorna)
        self.f_testo.textChanged.connect(lambda _: self._timer_ricerca.start(220))
        self.b_azzera.clicked.connect(self.azzera_filtri)
        return sc

    # ----------------------------------------------------------------- azioni
    def _barra_azioni(self):
        self.p_entrate = QLabel(""); self.p_entrate.setObjectName("Pillola")
        self.p_uscite = QLabel(""); self.p_uscite.setObjectName("Pillola")
        self.p_saldo = QLabel(""); self.p_saldo.setObjectName("Pillola")
        self.p_conteggio = QLabel(""); self.p_conteggio.setObjectName("NotaScheda")

        self.b_modifica = QPushButton("Modifica")
        self.b_duplica = QPushButton("Duplica")
        self.b_elimina = QPushButton("Elimina"); self.b_elimina.setObjectName("Pericolo")
        self.b_esporta = QPushButton("Esporta CSV")
        self.b_importa = QPushButton("Importa CSV")
        for b in (self.b_modifica, self.b_duplica, self.b_elimina):
            b.setEnabled(False)

        self.b_modifica.clicked.connect(self.modifica)
        self.b_duplica.clicked.connect(self.duplica)
        self.b_elimina.clicked.connect(self.elimina)
        self.b_esporta.clicked.connect(self.esporta)
        self.b_importa.clicked.connect(self.importa)

        return riga(self.p_entrate, self.p_uscite, self.p_saldo, self.p_conteggio,
                    None, self.b_modifica, self.b_duplica, self.b_elimina,
                    self.b_esporta, self.b_importa)

    # ---------------------------------------------------------------- tabella
    def _tabella(self) -> QTableWidget:
        self.tab = QTableWidget(0, len(COLONNE))
        self.tab.setHorizontalHeaderLabels(COLONNE)
        self.tab.verticalHeader().setVisible(False)
        self.tab.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tab.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tab.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tab.setSortingEnabled(True)
        self.tab.setAlternatingRowColors(True)
        self.tab.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tab.customContextMenuRequested.connect(self._menu_contestuale)
        self.tab.doubleClicked.connect(self.modifica)
        self.tab.itemSelectionChanged.connect(self._selezione_cambiata)
        h = self.tab.horizontalHeader()
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        for col, larg in ((0, 110), (1, 90), (3, 170), (4, 150), (5, 150), (6, 140)):
            h.resizeSection(col, larg)
        self.tab.sortByColumn(0, Qt.DescendingOrder)
        abilita_deselezione(self.tab)
        return self.tab

    def _scorciatoie(self) -> None:
        QShortcut(QKeySequence("Ctrl+N"), self, self.nuovo)
        QShortcut(QKeySequence("Ctrl+F"), self, lambda: self.f_testo.setFocus())
        QShortcut(QKeySequence("Ctrl+D"), self, self.duplica)
        QShortcut(QKeySequence("Ctrl+Z"), self, self.annulla_eliminazione)
        QShortcut(QKeySequence("Delete"), self.tab, self.elimina)
        QShortcut(QKeySequence("Return"), self.tab, self.modifica)

    # -------------------------------------------------------------- messaggi
    def _messaggio(self, testo: str, positivo: bool = True) -> None:
        colore = self.c["entrata"] if positivo else self.c["attenzione"]
        self.et_stato.setStyleSheet(f"color: {colore};")
        self.et_stato.setText(("✓  " if positivo else "•  ") + testo)
        self._timer_stato.start(6000)

    # --------------------------------------------------------------- supporto
    def _firma(self) -> str:
        """Impronta di categorie e conti: cambia solo se cambiano davvero."""
        r = self.db.query(
            "SELECT (SELECT COUNT(*) || '/' || COALESCE(SUM(LENGTH(nome)), 0) "
            "        FROM categorie) c, "
            "       (SELECT COUNT(*) || '/' || COALESCE(SUM(LENGTH(nome)), 0) "
            "        FROM conti) k")[0]
        return f"{r['c']}|{r['k']}|{self.g_tipo.checkedId()}"

    def _carica_elenchi(self) -> None:
        """Ricarica le combo solo quando categorie o conti sono cambiati."""
        firma = self._firma()
        if firma == self._firma_elenchi:
            return
        tipo = {1: "entrata", 2: "uscita"}.get(self.g_tipo.checkedId(), "")
        categorie = self.db.query(
            "SELECT nome, MAX(icona) icona FROM categorie" +
            (" WHERE tipo=?" if tipo else "") + " GROUP BY nome ORDER BY nome",
            (tipo,) if tipo else ())
        conti = self.db.query("SELECT nome, '' icona FROM conti ORDER BY nome")
        for combo, vuoto, righe in ((self.f_categoria, "Tutte", categorie),
                                    (self.f_conto, "Tutti", conti)):
            scelta = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(vuoto, "")
            for r in righe:
                combo.addItem(etichetta_categoria(r["nome"], r["icona"]), r["nome"])
            idx = combo.findData(scelta) if scelta else 0
            combo.setCurrentIndex(max(0, idx))
            combo.blockSignals(False)

        testo_conto = self.q_conto.currentText()
        self.q_conto.clear()
        self.q_conto.addItems([r["nome"] for r in self.db.query(
            "SELECT nome FROM conti ORDER BY nome")])
        idx = self.q_conto.findText(testo_conto)
        if idx >= 0:
            self.q_conto.setCurrentIndex(idx)
        self._aggiorna_categorie_rapide()
        self._firma_elenchi = firma

    def _cambia_periodo(self, _=None) -> None:
        personalizzato = self.g_periodo.checkedId() == PERIODI.index("Date…")
        self.f_dal.setVisible(personalizzato)
        self.f_al.setVisible(personalizzato)
        self.aggiorna()

    def _cambia_tipo(self, _=None) -> None:
        self._carica_elenchi()
        self.aggiorna()

    def _intervallo(self) -> tuple[str, str]:
        oggi = date.today()
        scelta = PERIODI[self.g_periodo.checkedId()]
        if scelta == "Oggi":
            return oggi.isoformat(), oggi.isoformat()
        if scelta == "7 giorni":
            return (oggi - timedelta(days=6)).isoformat(), oggi.isoformat()
        if scelta == "Mese":
            return mese_corrente()
        if scelta == "Anno":
            return anno_corrente()
        if scelta == "Tutto":
            return "", ""
        return (self.f_dal.date().toString("yyyy-MM-dd"),
                self.f_al.date().toString("yyyy-MM-dd"))

    def _filtri(self) -> dict:
        dal, al = self._intervallo()
        tipo = {1: "entrata", 2: "uscita"}.get(self.g_tipo.checkedId(), "")
        return {
            "dal": dal, "al": al, "tipo": tipo,
            "categoria": self.f_categoria.currentData() or "",
            "conto": self.f_conto.currentData() or "",
            "testo": self.f_testo.text().strip(),
        }

    def _selezionati(self) -> list[int]:
        return [int(self.tab.item(i.row(), 0).data(Qt.UserRole))
                for i in self.tab.selectionModel().selectedRows()
                if self.tab.item(i.row(), 0) is not None]

    def _selezione_cambiata(self) -> None:
        n = len(self.tab.selectionModel().selectedRows())
        self.b_modifica.setEnabled(n == 1)
        self.b_duplica.setEnabled(n == 1)
        self.b_elimina.setEnabled(n >= 1)
        self.b_elimina.setText("Elimina" if n <= 1 else f"Elimina ({n})")

    def _menu_contestuale(self, posizione) -> None:
        if not self.tab.selectionModel().selectedRows():
            return
        menu = QMenu(self)
        menu.addAction("Modifica…", self.modifica)
        menu.addAction("Duplica a oggi", self.duplica)
        menu.addSeparator()
        riga_sel = self.tab.currentRow()
        if riga_sel >= 0:
            categoria = solo_nome(self.tab.item(riga_sel, 3).text()).lstrip("● ").strip()
            conto = self.tab.item(riga_sel, 4).text()
            menu.addAction(f"Filtra per «{categoria}»",
                           lambda: self._filtra_per(self.f_categoria, categoria))
            menu.addAction(f"Filtra per conto «{conto}»",
                           lambda: self._filtra_per(self.f_conto, conto))
        menu.addSeparator()
        menu.addAction("Elimina", self.elimina)
        menu.exec(self.tab.viewport().mapToGlobal(posizione))

    def _filtra_per(self, combo: QComboBox, valore: str) -> None:
        idx = combo.findData(valore)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def azzera_filtri(self) -> None:
        self.g_periodo.button(PERIODI.index("Mese")).setChecked(True)
        self.g_tipo.button(0).setChecked(True)
        self.f_dal.setVisible(False); self.f_al.setVisible(False)
        self.f_testo.clear()
        self.f_categoria.setCurrentIndex(0)
        self.f_conto.setCurrentIndex(0)
        self.aggiorna()

    # ------------------------------------------------------------------ dati
    def aggiorna(self) -> None:
        self._carica_elenchi()
        v = self.valuta
        self.q_importo.setSuffix(f" {v}")
        filtri = self._filtri()
        righe = self.db.movimenti(**filtri)
        colori = self.db.colori_categorie()
        icone = self.db.icone_categorie()

        self.tab.setUpdatesEnabled(False)
        self.tab.setSortingEnabled(False)
        self.tab.setRowCount(len(righe))
        entrate = uscite = 0.0
        for r, m in enumerate(righe):
            importo = float(m["importo"])
            entrata = m["tipo"] == "entrata"
            if entrata:
                entrate += importo
            else:
                uscite += importo
            colore = self.c["entrata"] if entrata else self.c["uscita"]

            celle = [
                Cella(data_relativa(m["data"]), m["data"]),
                Cella("↑ entrata" if entrata else "↓ uscita"),
                Cella(m["descrizione"] or "—"),
                Cella(etichetta_categoria(m["categoria"],
                                          icone.get(m["categoria"]) or "●")),
                Cella(m["conto"]),
                Cella(m["etichette"]),
                Cella(("+ " if entrata else "− ") + euro(importo, v),
                      importo if entrata else -importo),
            ]
            celle[0].setData(Qt.UserRole, m["id"])
            celle[1].setForeground(QColor(colore))
            celle[3].setForeground(QColor(colori.get(m["categoria"], self.c["testo"])))
            celle[6].setForeground(QColor(colore))
            celle[6].setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            for col, cella in enumerate(celle):
                self.tab.setItem(r, col, cella)
        self.tab.setSortingEnabled(True)
        self.tab.setUpdatesEnabled(True)

        saldo = entrate - uscite
        self.p_entrate.setText(f"entrate  {euro(entrate, v)}")
        self.p_entrate.setStyleSheet(f"color: {self.c['entrata']};")
        self.p_uscite.setText(f"uscite  {euro(uscite, v)}")
        self.p_uscite.setStyleSheet(f"color: {self.c['uscita']};")
        self.p_saldo.setText(f"saldo  {euro(saldo, v)}")
        self.p_saldo.setStyleSheet(
            f"color: {self.c['entrata'] if saldo >= 0 else self.c['uscita']};"
            "font-weight: 600;")

        attivi = bool(filtri["testo"] or filtri["categoria"] or filtri["conto"]
                      or filtri["tipo"]
                      or self.g_periodo.checkedId() != PERIODI.index("Mese"))
        self.b_azzera.setVisible(attivi)
        if righe:
            self.p_conteggio.setText(f"{len(righe)} movimenti")
        else:
            self.p_conteggio.setText("nessun movimento con questi filtri"
                                     if attivi else "nessun movimento registrato")
        self._selezione_cambiata()

    # ---------------------------------------------------------- inserimento
    def inserimento_rapido(self) -> None:
        importo = self.q_importo.value()
        if importo <= 0:
            self._messaggio("Inserisci un importo maggiore di zero.", positivo=False)
            self.q_importo.setFocus()
            return
        descrizione = self.q_descrizione.text().strip()
        categoria = (self.q_categoria.currentData()
                     or solo_nome(self.q_categoria.currentText()) or "Altro")
        dati = {
            "id": None,
            "data": self.q_data.date().toString("yyyy-MM-dd"),
            "tipo": self._tipo_rapido,
            "importo": importo,
            "categoria": categoria,
            "conto": self.q_conto.currentText().strip() or "Principale",
            "descrizione": descrizione or categoria,
            "etichette": "",
        }
        self.db.salva_movimento(dati)
        self.q_importo.setValue(0)
        self.q_descrizione.clear()
        self.q_descrizione.setFocus()
        self._messaggio(
            f"{'Entrata' if self._tipo_rapido == 'entrata' else 'Uscita'} di "
            f"{euro(importo, self.valuta)} registrata in «{categoria}».")
        self.dati_cambiati.emit()

    def nuova_categoria(self) -> None:
        """Crea una categoria senza lasciare la pagina e la seleziona subito."""
        dlg = DialogoNuovaCategoria(self.db, self._tipo_rapido,
                                    parent=self)
        if not dlg.exec() or not dlg.nome_creato:
            return
        self._firma_elenchi = ""            # forza il ricarico delle tendine
        self._carica_elenchi()
        indice = self.q_categoria.findData(dlg.nome_creato)
        if indice >= 0:
            self.q_categoria.setCurrentIndex(indice)
        self._messaggio(f"Categoria «{dlg.nome_creato}» creata e selezionata.")
        self.dati_cambiati.emit()

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
        if not dlg.exec():
            return
        dati = dlg.dati()
        if dati["importo"] <= 0:
            self._messaggio("Importo non valido: movimento non salvato.", positivo=False)
            return
        dati["id"] = None
        self.db.salva_movimento(dati)
        self._messaggio(f"Movimento di {euro(dati['importo'], self.valuta)} registrato.")
        self.dati_cambiati.emit()

    def modifica(self) -> None:
        ids = self._selezionati()
        if len(ids) != 1:
            return
        m = self.db.query("SELECT * FROM movimenti WHERE id=?", (ids[0],))[0]
        ent, usc, conti = self._elenchi_dialogo()
        dlg = DialogoMovimento(self.db, ent, usc, conti, dict(m), self)
        if dlg.exec():
            self.db.salva_movimento(dlg.dati())
            self._messaggio("Movimento aggiornato.")
            self.dati_cambiati.emit()

    def duplica(self) -> None:
        ids = self._selezionati()
        if len(ids) != 1:
            return
        m = dict(self.db.query("SELECT * FROM movimenti WHERE id=?", (ids[0],))[0])
        m["id"] = None
        m["data"] = date.today().isoformat()
        self.db.salva_movimento(m)
        self._messaggio(f"Movimento duplicato a oggi ({euro(float(m['importo']), self.valuta)}).")
        self.dati_cambiati.emit()

    # ------------------------------------------------------------ eliminazione
    def elimina(self) -> None:
        ids = self._selezionati()
        if not ids:
            return
        self._eliminati = [dict(self.db.query(
            "SELECT * FROM movimenti WHERE id=?", (i,))[0]) for i in ids]
        for i in ids:
            self.db.elimina("movimenti", i)
        self._messaggio(f"{len(ids)} movimento/i eliminati — Ctrl+Z per annullare.")
        self.dati_cambiati.emit()

    def annulla_eliminazione(self) -> None:
        if not self._eliminati:
            self._messaggio("Niente da annullare.", positivo=False)
            return
        for m in self._eliminati:
            m["id"] = None
            self.db.salva_movimento(m)
        n = len(self._eliminati)
        self._eliminati = []
        self._messaggio(f"Ripristinati {n} movimenti.")
        self.dati_cambiati.emit()

    # ------------------------------------------------------------ scambio dati
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
        self._messaggio(f"{n} movimenti esportati in {percorso}")

    def importa(self) -> None:
        percorso, _ = QFileDialog.getOpenFileName(
            self, "Importa movimenti da CSV", "", "File CSV (*.csv *.txt)")
        if not percorso:
            return
        try:
            righe = importa_csv(percorso)
        except Exception as e:
            QMessageBox.critical(self, "Errore di lettura", str(e))
            return
        if not righe:
            QMessageBox.warning(
                self, "Nessun dato",
                "Il file non contiene righe riconoscibili.\n"
                "Colonne attese: data;tipo;importo;categoria;conto;descrizione")
            return
        for r in righe:
            self.db.salva_movimento(r)
        self._messaggio(f"{len(righe)} movimenti importati.")
        self.dati_cambiati.emit()

    # ------------------------------------------------------------------ tema
    def aggiorna_tema(self, colori: dict) -> None:
        super().aggiorna_tema(colori)
        colore = colori["entrata"] if self.q_tipo.isChecked() else colori["uscita"]
        self.q_tipo.setStyleSheet(
            f"background: {colore}; color: #ffffff; border-color: {colore};"
            "font-weight: 600;")

"""Cruscotto: panoramica configurabile con indicatori, grafici e movimenti.

Ogni sezione è separata da un divisore trascinabile: puoi allargare un grafico,
restringere una scheda o nascondere del tutto una parte. La disposizione viene
salvata nell'archivio e ritrovata al riavvio.
"""
from __future__ import annotations

from PySide6.QtCore import QByteArray, QTimer, Qt
from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QMenu, QProgressBar,
                               QPushButton, QSizePolicy, QSplitter, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

from ..componenti import Scheda, SchedaStat, etichetta, riga
from ..grafici import GraficoBarre, GraficoCiambella, GraficoLinea
from ..icone import etichetta_categoria
from ..utils import data_it, etichetta_mese, euro, mese_corrente, mese_precedente
from . import VistaBase

# chiave di salvataggio -> etichetta mostrata nel menu
SEZIONI = {
    "indicatori": "Indicatori in alto",
    "andamento": "Andamento del saldo",
    "ripartizione": "Uscite per categoria",
    "mensili": "Entrate e uscite per mese",
    "budget": "Budget del mese",
    "ultimi": "Ultimi movimenti",
}


class VistaCruscotto(VistaBase):
    titolo = "Cruscotto"
    sottotitolo = "Panoramica della tua situazione finanziaria"

    def costruisci(self) -> None:
        self._pronto = False
        lay = QVBoxLayout(self)
        lay.setContentsMargins(2, 2, 6, 6)
        lay.setSpacing(8)

        lay.addLayout(self._barra_strumenti())
        lay.addWidget(self._contenuto(), 1)

        self._ripristina_disposizione()
        self._pronto = True

    # ------------------------------------------------------------ strumenti
    def _barra_strumenti(self):
        self.b_sezioni = QPushButton("Sezioni  ▾")
        self.b_sezioni.setToolTip("Mostra o nascondi le sezioni del cruscotto")
        self.menu_sezioni = QMenu(self)
        self.azioni_sezioni: dict[str, QAction] = {}
        for chiave, nome in SEZIONI.items():
            a = QAction(nome, self, checkable=True, checked=True)
            a.toggled.connect(lambda visibile, k=chiave: self._mostra_sezione(k, visibile))
            self.menu_sezioni.addAction(a)
            self.azioni_sezioni[chiave] = a
        self.menu_sezioni.addSeparator()
        self.menu_sezioni.addAction("Ripristina disposizione predefinita",
                                    self.ripristina_predefinita)
        self.b_sezioni.setMenu(self.menu_sezioni)

        suggerimento = etichetta(
            "Trascina i divisori tra le sezioni per ridimensionarle: la disposizione "
            "viene salvata automaticamente.", "NotaScheda")
        return riga(self.b_sezioni, suggerimento, None)

    # ------------------------------------------------------------- struttura
    def _contenuto(self) -> QWidget:
        self.divisore = QSplitter(Qt.Vertical)
        self.divisore.setChildrenCollapsible(True)
        self.divisore.setHandleWidth(8)

        # --- fascia indicatori (larghezze regolabili una per una) ----------
        self.fascia_indicatori = QSplitter(Qt.Horizontal)
        self.fascia_indicatori.setHandleWidth(8)
        self.s_saldo = SchedaStat("Saldo totale", self.c, self.c["accento"])
        self.s_entrate = SchedaStat("Entrate del mese", self.c, self.c["entrata"])
        self.s_uscite = SchedaStat("Uscite del mese", self.c, self.c["uscita"])
        self.s_risparmio = SchedaStat("Risparmio del mese", self.c, self.c["attenzione"])
        for s in (self.s_saldo, self.s_entrate, self.s_uscite, self.s_risparmio):
            s.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            s.setMinimumWidth(150)
            self.fascia_indicatori.addWidget(s)

        # --- grafici principali -------------------------------------------
        self.fascia_grafici = QSplitter(Qt.Horizontal)
        self.fascia_grafici.setHandleWidth(8)
        self.sc_andamento = Scheda("Andamento del saldo (ultimi 12 mesi)")
        self.g_saldo = GraficoLinea(self.c)
        self.g_saldo.setMinimumHeight(120)
        self.sc_andamento.aggiungi(self.g_saldo, 1)
        self.sc_torta = Scheda("Uscite del mese per categoria")
        self.g_torta = GraficoCiambella(self.c)
        self.g_torta.setMinimumHeight(120)
        self.sc_torta.aggiungi(self.g_torta, 1)
        self.fascia_grafici.addWidget(self.sc_andamento)
        self.fascia_grafici.addWidget(self.sc_torta)

        # --- barre mensili e budget ---------------------------------------
        self.fascia_budget = QSplitter(Qt.Horizontal)
        self.fascia_budget.setHandleWidth(8)
        self.sc_barre = Scheda("Entrate e uscite per mese")
        self.g_barre = GraficoBarre(self.c)
        self.g_barre.setMinimumHeight(120)
        self.sc_barre.aggiungi(self.g_barre, 1)
        self.sc_budget = Scheda("Budget del mese")
        self.cont_budget = QWidget()
        self.lay_budget = QVBoxLayout(self.cont_budget)
        self.lay_budget.setContentsMargins(0, 0, 0, 0)
        self.lay_budget.setSpacing(9)
        self.sc_budget.aggiungi(self.cont_budget, 1)
        self.fascia_budget.addWidget(self.sc_barre)
        self.fascia_budget.addWidget(self.sc_budget)

        # --- ultimi movimenti ---------------------------------------------
        self.sc_ultimi = Scheda("Ultimi movimenti")
        self.tab = QTableWidget(0, 5)
        self.tab.setHorizontalHeaderLabels(
            ["Data", "Descrizione", "Categoria", "Conto", "Importo"])
        self.tab.verticalHeader().setVisible(False)
        self.tab.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tab.setSelectionBehavior(QTableWidget.SelectRows)
        self.tab.setAlternatingRowColors(True)
        self.tab.setMinimumHeight(90)
        h = self.tab.horizontalHeader()
        h.setStretchLastSection(True)
        h.resizeSection(0, 110); h.resizeSection(1, 280)
        h.resizeSection(2, 180); h.resizeSection(3, 140)
        self.sc_ultimi.aggiungi(self.tab, 1)

        self.sezioni_widget = {
            "indicatori": self.fascia_indicatori,
            "andamento": self.sc_andamento,
            "ripartizione": self.sc_torta,
            "mensili": self.sc_barre,
            "budget": self.sc_budget,
            "ultimi": self.sc_ultimi,
        }

        for w, minimo in ((self.fascia_indicatori, 110), (self.fascia_grafici, 140),
                          (self.fascia_budget, 140), (self.sc_ultimi, 110)):
            w.setMinimumHeight(minimo)
            self.divisore.addWidget(w)
        self.divisore.setStretchFactor(0, 0)
        self.divisore.setStretchFactor(1, 3)
        self.divisore.setStretchFactor(2, 3)
        self.divisore.setStretchFactor(3, 2)

        self.divisori = {
            "verticale": self.divisore,
            "indicatori": self.fascia_indicatori,
            "grafici": self.fascia_grafici,
            "budget": self.fascia_budget,
        }
        for chiave, d in self.divisori.items():
            d.splitterMoved.connect(lambda _p, _i, k=chiave: self._salva_divisore(k))

        self.grafici = [self.g_saldo, self.g_torta, self.g_barre]
        return self.divisore

    # ---------------------------------------------------------- disposizione
    def _salva_divisore(self, chiave: str) -> None:
        if not self._pronto:
            return
        stato = bytes(self.divisori[chiave].saveState().toBase64()).decode()
        self.db.imposta(f"cruscotto_{chiave}", stato)

    def _ripristina_disposizione(self) -> None:
        for chiave, divisore in self.divisori.items():
            stato = self.db.leggi(f"cruscotto_{chiave}", "")
            if stato:
                divisore.restoreState(QByteArray.fromBase64(stato.encode()))
        nascoste = {s for s in self.db.leggi("cruscotto_nascoste", "").split(",") if s}
        for chiave, azione in self.azioni_sezioni.items():
            visibile = chiave not in nascoste
            azione.blockSignals(True)
            azione.setChecked(visibile)
            azione.blockSignals(False)
            self.sezioni_widget[chiave].setVisible(visibile)
        self._sistema_fasce()

    def _mostra_sezione(self, chiave: str, visibile: bool) -> None:
        self.sezioni_widget[chiave].setVisible(visibile)
        nascoste = [k for k, a in self.azioni_sezioni.items() if not a.isChecked()]
        self.db.imposta("cruscotto_nascoste", ",".join(nascoste))
        self._sistema_fasce()
        if visibile:
            # una sezione riattivata può restare a dimensione zero: le ridò spazio
            QTimer.singleShot(0, lambda: self._assicura_spazio(
                self.sezioni_widget[chiave]))
            self.aggiorna()

    def _assicura_spazio(self, widget: QWidget, minimo: int = 140) -> None:
        """Garantisce una dimensione minima a una sezione dentro il suo divisore."""
        divisore = widget.parent()
        while divisore is not None and not isinstance(divisore, QSplitter):
            divisore = divisore.parent()
        if divisore is None:
            return
        indice = divisore.indexOf(widget)
        dimensioni = divisore.sizes()
        if indice < 0 or indice >= len(dimensioni) or dimensioni[indice] >= minimo:
            return
        donatore = max(range(len(dimensioni)), key=lambda i: dimensioni[i])
        if dimensioni[donatore] <= minimo:
            return
        presi = min(minimo, dimensioni[donatore] // 2)
        dimensioni[donatore] -= presi
        dimensioni[indice] += presi
        divisore.setSizes(dimensioni)
        for chiave, d in self.divisori.items():
            if d is divisore:
                self._salva_divisore(chiave)

    def _sistema_fasce(self) -> None:
        """Nasconde la fascia quando entrambe le schede che contiene sono nascoste.

        Si usa isHidden() e non isVisible(): finché la finestra non è mostrata
        nessun widget risulta visibile, e il confronto sbagliato nasconderebbe
        tutto alla partenza.
        """
        self.fascia_grafici.setVisible(
            not (self.sc_andamento.isHidden() and self.sc_torta.isHidden()))
        self.fascia_budget.setVisible(
            not (self.sc_barre.isHidden() and self.sc_budget.isHidden()))

    def ripristina_predefinita(self) -> None:
        for chiave in self.divisori:
            self.db.imposta(f"cruscotto_{chiave}", "")
        self.db.imposta("cruscotto_nascoste", "")
        for azione in self.azioni_sezioni.values():
            azione.blockSignals(True); azione.setChecked(True); azione.blockSignals(False)
        for w in self.sezioni_widget.values():
            w.setVisible(True)
        self._sistema_fasce()
        # le dimensioni si applicano dopo che i widget sono tornati visibili
        QTimer.singleShot(0, self._dimensioni_predefinite)
        self.aggiorna()

    def _dimensioni_predefinite(self) -> None:
        altezza = max(420, self.divisore.height())
        self.divisore.setSizes([int(altezza * q) for q in (0.17, 0.31, 0.29, 0.23)])
        larghezza = max(700, self.fascia_indicatori.width())
        self.fascia_indicatori.setSizes([larghezza // 4] * 4)
        self.fascia_grafici.setSizes([int(larghezza * 0.6), int(larghezza * 0.4)])
        self.fascia_budget.setSizes([int(larghezza * 0.6), int(larghezza * 0.4)])
        for chiave in self.divisori:
            self._salva_divisore(chiave)

    # ------------------------------------------------------------------ dati
    def aggiorna(self) -> None:
        v = self.valuta
        dal_m, al_m = mese_corrente()
        dal_p, al_p = mese_precedente()
        ent, usc = self.db.totali_periodo(dal_m, al_m)
        ent_p, usc_p = self.db.totali_periodo(dal_p, al_p)
        serie = self.db.serie_mensile(12)

        saldo_iniziale = float(self.db.query(
            "SELECT COALESCE(SUM(saldo_iniziale),0) s FROM conti")[0]["s"])
        cumulato, punti = saldo_iniziale, []
        for mese, e, u in serie:
            cumulato += e - u
            punti.append((etichetta_mese(mese), cumulato))

        saldo = self.db.saldo_totale()
        self.s_saldo.imposta(saldo, f"{len(self.db.query('SELECT id FROM conti'))} conti registrati",
                             v, [p[1] for p in punti])
        self.s_entrate.imposta(ent, self._confronto(ent, ent_p), v, [s[1] for s in serie])
        self.s_uscite.imposta(usc, self._confronto(usc, usc_p), v, [s[2] for s in serie])
        risparmio = ent - usc
        tasso = (risparmio / ent * 100) if ent > 0 else 0.0
        self.s_risparmio.imposta(risparmio, f"tasso di risparmio {tasso:.0f}%", v,
                                 [s[1] - s[2] for s in serie])

        self.g_saldo.imposta_dati(punti, self.c["accento"])

        colori = self.db.colori_categorie()
        icone = self.db.icone_categorie()
        cats = self.db.per_categoria("uscita", dal_m, al_m)
        self.g_torta.imposta_dati(
            [(etichetta_categoria(n, icone.get(n)), t, colori.get(n, "")) for n, t in cats],
            euro(usc, v).replace(f" {v}", ""), "uscite del mese")

        self.g_barre.imposta_dati(
            [(etichetta_mese(m), [e, u]) for m, e, u in serie],
            [("Entrate", self.c["entrata"]), ("Uscite", self.c["uscita"])])

        self._aggiorna_budget(dal_m, al_m, icone)
        self._aggiorna_tabella(icone)

    def _confronto(self, ora: float, prima: float) -> str:
        if prima <= 0:
            return "nessun confronto disponibile"
        delta = (ora - prima) / prima * 100
        freccia = "▲" if delta > 0 else ("▼" if delta < 0 else "=")
        return f"{freccia} {abs(delta):.0f}% rispetto al mese scorso"

    def _aggiorna_budget(self, dal: str, al: str, icone: dict) -> None:
        while self.lay_budget.count():
            item = self.lay_budget.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

        budget = self.db.query("SELECT * FROM budget WHERE mensile > 0 ORDER BY mensile DESC")
        if not budget:
            self.lay_budget.addWidget(etichetta(
                "Nessun budget impostato.\nVai in «Budget» per definire i limiti mensili "
                "per categoria.", "NotaScheda"))
            self.lay_budget.addStretch(1)
            return

        for b in budget[:7]:
            speso = float(self.db.query(
                "SELECT COALESCE(SUM(importo),0) s FROM movimenti "
                "WHERE tipo='uscita' AND categoria=? AND data BETWEEN ? AND ?",
                (b["categoria"], dal, al))[0]["s"])
            limite = float(b["mensile"])
            quota = min(100, int(speso / limite * 100)) if limite else 0
            colore = (self.c["entrata"] if quota < 75 else
                      self.c["attenzione"] if quota < 100 else self.c["uscita"])
            blocco = QWidget()
            lv = QVBoxLayout(blocco)
            lv.setContentsMargins(0, 0, 0, 0)
            lv.setSpacing(3)
            testa = QHBoxLayout()
            nome = QLabel(etichetta_categoria(b["categoria"], icone.get(b["categoria"])))
            valore = QLabel(f"{euro(speso, self.valuta)} / {euro(limite, self.valuta)}")
            valore.setObjectName("NotaScheda")
            testa.addWidget(nome); testa.addStretch(1); testa.addWidget(valore)
            barra = QProgressBar()
            barra.setRange(0, 100); barra.setValue(quota)
            barra.setStyleSheet(
                f"QProgressBar::chunk {{ background: {colore}; border-radius: 7px; }}")
            lv.addLayout(testa); lv.addWidget(barra)
            self.lay_budget.addWidget(blocco)
        self.lay_budget.addStretch(1)

    def _aggiorna_tabella(self, icone: dict) -> None:
        righe = self.db.query("SELECT * FROM movimenti ORDER BY data DESC, id DESC LIMIT 25")
        self.tab.setRowCount(len(righe))
        for r, m in enumerate(righe):
            segno = "+" if m["tipo"] == "entrata" else "−"
            colore = self.c["entrata"] if m["tipo"] == "entrata" else self.c["uscita"]
            valori = [data_it(m["data"]), m["descrizione"] or "—",
                      etichetta_categoria(m["categoria"], icone.get(m["categoria"])),
                      m["conto"],
                      f"{segno} {euro(float(m['importo']), self.valuta)}"]
            for col, testo in enumerate(valori):
                it = QTableWidgetItem(testo)
                if col == 4:
                    it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    it.setForeground(QColor(colore))
                self.tab.setItem(r, col, it)

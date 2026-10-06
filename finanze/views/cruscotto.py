"""Cruscotto: pannello componibile con sezioni trascinabili e ridimensionabili.

Ogni riquadro si prende dalla maniglia in alto a sinistra e si porta dove serve,
anche in una riga nuova; i divisori regolano le dimensioni e i testi si adattano
allo spazio disponibile. La disposizione viene salvata nell'archivio.
"""
from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QMenu, QProgressBar,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget)

from ..componenti import ContenutoStat, etichetta, riga
from ..grafici import GraficoBarre, GraficoCiambella, GraficoLinea
from ..icone import etichetta_categoria
from ..sezioni import ContenitoreSezioni, Sezione
from ..utils import data_it, etichetta_mese, euro, mese_corrente, mese_precedente
from . import VistaBase

DISPOSIZIONE_PREDEFINITA = [
    ["saldo", "entrate", "uscite", "risparmio"],
    ["andamento", "ripartizione"],
    ["mensili", "budget"],
    ["ultimi"],
]

TITOLI = {
    "saldo": "SALDO TOTALE",
    "entrate": "ENTRATE DEL MESE",
    "uscite": "USCITE DEL MESE",
    "risparmio": "RISPARMIO DEL MESE",
    "andamento": "Andamento del saldo (ultimi 12 mesi)",
    "ripartizione": "Uscite del mese per categoria",
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

        self.contenitore = ContenitoreSezioni()
        lay.addLayout(self._barra_strumenti())
        lay.addWidget(self.contenitore, 1)

        self._crea_sezioni()
        self._ripristina()
        self.contenitore.disposizione_cambiata.connect(self._salva)
        self._pronto = True

    # ------------------------------------------------------------ strumenti
    def _barra_strumenti(self):
        self.b_sezioni = QPushButton("Sezioni")
        self.b_sezioni.setToolTip("Mostra o nascondi le sezioni del cruscotto")
        self.menu_sezioni = QMenu(self)
        self.azioni: dict[str, QAction] = {}
        for chiave, nome in TITOLI.items():
            a = QAction(nome.capitalize() if nome.isupper() else nome,
                        self, checkable=True, checked=True)
            a.toggled.connect(lambda visibile, k=chiave: self._mostra(k, visibile))
            self.menu_sezioni.addAction(a)
            self.azioni[chiave] = a
        self.menu_sezioni.addSeparator()
        self.menu_sezioni.addAction("Ripristina disposizione predefinita",
                                    self.ripristina_predefinita)
        self.b_sezioni.setMenu(self.menu_sezioni)

        aiuto = etichetta(
            "Trascina una sezione dalla maniglia ⠿ per spostarla, anche su una riga "
            "nuova; i divisori ne regolano le dimensioni. Tutto viene salvato.",
            "NotaScheda")
        return riga(self.b_sezioni, aiuto, None)

    # -------------------------------------------------------------- sezioni
    def _crea_sezioni(self) -> None:
        self.stat: dict[str, ContenutoStat] = {}
        for chiave, colore in (("saldo", self.c["accento"]),
                               ("entrate", self.c["entrata"]),
                               ("uscite", self.c["uscita"]),
                               ("risparmio", self.c["attenzione"])):
            contenuto = ContenutoStat(self.c, colore)
            self.stat[chiave] = contenuto
            self._aggiungi(chiave, contenuto, "EtichettaScheda")

        self.g_saldo = GraficoLinea(self.c)
        self.g_saldo.setMinimumHeight(70)
        self._aggiungi("andamento", self.g_saldo)

        self.g_torta = GraficoCiambella(self.c)
        self.g_torta.setMinimumHeight(70)
        self._aggiungi("ripartizione", self.g_torta)

        self.g_barre = GraficoBarre(self.c)
        self.g_barre.setMinimumHeight(70)
        self._aggiungi("mensili", self.g_barre)

        self.cont_budget = QWidget()
        self.lay_budget = QVBoxLayout(self.cont_budget)
        self.lay_budget.setContentsMargins(0, 0, 0, 0)
        self.lay_budget.setSpacing(9)
        self._aggiungi("budget", self.cont_budget)

        self.tab = QTableWidget(0, 5)
        self.tab.setHorizontalHeaderLabels(
            ["Data", "Descrizione", "Categoria", "Conto", "Importo"])
        self.tab.verticalHeader().setVisible(False)
        self.tab.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tab.setSelectionBehavior(QTableWidget.SelectRows)
        self.tab.setAlternatingRowColors(True)
        self.tab.setMinimumHeight(60)
        h = self.tab.horizontalHeader()
        h.setStretchLastSection(True)
        h.resizeSection(0, 110); h.resizeSection(1, 280)
        h.resizeSection(2, 180); h.resizeSection(3, 140)
        self._aggiungi("ultimi", self.tab)

        self.grafici = [self.g_saldo, self.g_torta, self.g_barre]

    def _aggiungi(self, chiave: str, contenuto: QWidget,
                  stile: str = "Sezione") -> None:
        sezione = Sezione(chiave, TITOLI[chiave], contenuto, stile)
        sezione.chiusura_richiesta.connect(
            lambda k: self.azioni[k].setChecked(False))
        self.contenitore.registra(sezione)

    # ---------------------------------------------------------- disposizione
    def _ripristina(self) -> None:
        stato = self.db.leggi("cruscotto_layout", "")
        if not stato or not self.contenitore.ripristina_stato(stato):
            self.contenitore.applica_disposizione(DISPOSIZIONE_PREDEFINITA)
        for chiave, azione in self.azioni.items():
            visibile = not self.contenitore.sezioni[chiave].isHidden()
            azione.blockSignals(True)
            azione.setChecked(visibile)
            azione.blockSignals(False)

    def _salva(self) -> None:
        if self._pronto:
            self.db.imposta("cruscotto_layout", self.contenitore.stato())

    def _mostra(self, chiave: str, visibile: bool) -> None:
        self.contenitore.mostra_sezione(chiave, visibile)
        if visibile:
            self.aggiorna()

    def ripristina_predefinita(self) -> None:
        for azione in self.azioni.values():
            azione.blockSignals(True); azione.setChecked(True); azione.blockSignals(False)
        for sezione in self.contenitore.sezioni.values():
            sezione.show()
        self.contenitore.applica_disposizione(DISPOSIZIONE_PREDEFINITA)
        QTimer.singleShot(0, self._dimensioni_predefinite)
        self.aggiorna()

    def _dimensioni_predefinite(self) -> None:
        altezza = max(430, self.contenitore.height())
        self.contenitore.verticale.setSizes(
            [int(altezza * q) for q in (0.19, 0.30, 0.28, 0.23)])
        for i in range(self.contenitore.verticale.count()):
            r = self.contenitore.verticale.widget(i)
            if r.count() == 2:
                r.setSizes([int(r.width() * 0.6), int(r.width() * 0.4)])
            elif r.count() > 0:
                r.setSizes([r.width() // r.count()] * r.count())
        self._salva()

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
        conti = len(self.db.query("SELECT id FROM conti"))
        self.stat["saldo"].imposta(saldo, f"{conti} conti registrati", v,
                                   [p[1] for p in punti])
        self.stat["entrate"].imposta(ent, self._confronto(ent, ent_p), v,
                                     [s[1] for s in serie])
        self.stat["uscite"].imposta(usc, self._confronto(usc, usc_p), v,
                                    [s[2] for s in serie])
        risparmio = ent - usc
        tasso = (risparmio / ent * 100) if ent > 0 else 0.0
        self.stat["risparmio"].imposta(risparmio, f"tasso di risparmio {tasso:.0f}%", v,
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
                "Nessun budget impostato.\nVai in «Budget» per definire i limiti "
                "mensili per categoria.", "NotaScheda"))
            self.lay_budget.addStretch(1)
            return

        for b in budget[:8]:
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
            lv.setContentsMargins(0, 0, 0, 0); lv.setSpacing(3)
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

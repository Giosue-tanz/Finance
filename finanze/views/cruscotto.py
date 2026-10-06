"""Cruscotto: panoramica con indicatori, grafici e ultimi movimenti."""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QGridLayout, QHBoxLayout, QLabel, QProgressBar,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from ..componenti import Scheda, SchedaStat, etichetta
from ..grafici import GraficoBarre, GraficoCiambella, GraficoLinea
from ..utils import (anno_corrente, data_it, etichetta_mese, euro, mese_corrente,
                     mese_precedente)
from . import VistaBase


class VistaCruscotto(VistaBase):
    titolo = "Cruscotto"
    sottotitolo = "Panoramica della tua situazione finanziaria"

    def costruisci(self) -> None:
        _, lay = self.area_scorrevole()

        # --- indicatori ---
        griglia = QGridLayout()
        griglia.setSpacing(12)
        self.s_saldo = SchedaStat("Saldo totale", self.c, self.c["accento"])
        self.s_entrate = SchedaStat("Entrate del mese", self.c, self.c["entrata"])
        self.s_uscite = SchedaStat("Uscite del mese", self.c, self.c["uscita"])
        self.s_risparmio = SchedaStat("Risparmio del mese", self.c, self.c["attenzione"])
        for i, s in enumerate((self.s_saldo, self.s_entrate, self.s_uscite, self.s_risparmio)):
            griglia.addWidget(s, 0, i)
        lay.addLayout(griglia)

        # --- andamento saldo + ripartizione ---
        fila = QHBoxLayout()
        fila.setSpacing(12)

        sc_andamento = Scheda("Andamento del saldo (ultimi 12 mesi)")
        self.g_saldo = GraficoLinea(self.c)
        self.g_saldo.setMinimumHeight(250)
        sc_andamento.aggiungi(self.g_saldo, 1)
        fila.addWidget(sc_andamento, 3)

        sc_torta = Scheda("Uscite del mese per categoria")
        self.g_torta = GraficoCiambella(self.c)
        self.g_torta.setMinimumHeight(250)
        sc_torta.aggiungi(self.g_torta, 1)
        fila.addWidget(sc_torta, 2)
        lay.addLayout(fila)

        # --- barre mensili + budget ---
        fila2 = QHBoxLayout()
        fila2.setSpacing(12)
        sc_barre = Scheda("Entrate e uscite per mese")
        self.g_barre = GraficoBarre(self.c)
        self.g_barre.setMinimumHeight(240)
        sc_barre.aggiungi(self.g_barre, 1)
        fila2.addWidget(sc_barre, 3)

        self.sc_budget = Scheda("Budget del mese")
        self.cont_budget = QWidget()
        self.lay_budget = QVBoxLayout(self.cont_budget)
        self.lay_budget.setContentsMargins(0, 0, 0, 0)
        self.lay_budget.setSpacing(9)
        self.sc_budget.aggiungi(self.cont_budget, 1)
        fila2.addWidget(self.sc_budget, 2)
        lay.addLayout(fila2)

        # --- ultimi movimenti ---
        sc_ultimi = Scheda("Ultimi movimenti")
        self.tab = QTableWidget(0, 5)
        self.tab.setHorizontalHeaderLabels(["Data", "Descrizione", "Categoria", "Conto", "Importo"])
        self.tab.verticalHeader().setVisible(False)
        self.tab.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tab.setSelectionBehavior(QTableWidget.SelectRows)
        self.tab.setMinimumHeight(260)
        h = self.tab.horizontalHeader()
        h.setStretchLastSection(True)
        h.resizeSection(0, 100); h.resizeSection(1, 280)
        h.resizeSection(2, 160); h.resizeSection(3, 140)
        sc_ultimi.aggiungi(self.tab)
        lay.addWidget(sc_ultimi)
        lay.addStretch(1)

        self.grafici = [self.g_saldo, self.g_torta, self.g_barre]

    # ------------------------------------------------------------------ dati
    def aggiorna(self) -> None:
        v = self.valuta
        dal_m, al_m = mese_corrente()
        dal_p, al_p = mese_precedente()
        ent, usc = self.db.totali_periodo(dal_m, al_m)
        ent_p, usc_p = self.db.totali_periodo(dal_p, al_p)
        serie = self.db.serie_mensile(12)

        # saldo cumulato mese per mese
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
        self.s_uscite.imposta(usc, self._confronto(usc, usc_p, inverti=True), v,
                              [s[2] for s in serie])
        risparmio = ent - usc
        tasso = (risparmio / ent * 100) if ent > 0 else 0.0
        self.s_risparmio.imposta(risparmio, f"tasso di risparmio {tasso:.0f}%", v,
                                 [s[1] - s[2] for s in serie])

        self.g_saldo.imposta_dati(punti, self.c["accento"])

        colori = self.db.colori_categorie()
        cats = self.db.per_categoria("uscita", dal_m, al_m)
        self.g_torta.imposta_dati(
            [(n, t, colori.get(n, "")) for n, t in cats],
            euro(usc, v).replace(f" {v}", ""), "uscite del mese")

        self.g_barre.imposta_dati(
            [(etichetta_mese(m), [e, u]) for m, e, u in serie],
            [("Entrate", self.c["entrata"]), ("Uscite", self.c["uscita"])])

        self._aggiorna_budget(dal_m, al_m)
        self._aggiorna_tabella()

    def _confronto(self, ora: float, prima: float, inverti: bool = False) -> str:
        if prima <= 0:
            return "nessun confronto disponibile"
        delta = (ora - prima) / prima * 100
        freccia = "▲" if delta > 0 else ("▼" if delta < 0 else "=")
        return f"{freccia} {abs(delta):.0f}% rispetto al mese scorso"

    def _aggiorna_budget(self, dal: str, al: str) -> None:
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
            riga = QWidget()
            lv = QVBoxLayout(riga)
            lv.setContentsMargins(0, 0, 0, 0)
            lv.setSpacing(3)
            testa = QHBoxLayout()
            nome = QLabel(b["categoria"])
            valore = QLabel(f"{euro(speso, self.valuta)} / {euro(limite, self.valuta)}")
            valore.setObjectName("NotaScheda")
            testa.addWidget(nome)
            testa.addStretch(1)
            testa.addWidget(valore)
            barra = QProgressBar()
            barra.setRange(0, 100)
            barra.setValue(quota)
            barra.setStyleSheet(f"QProgressBar::chunk {{ background: {colore}; border-radius: 7px; }}")
            lv.addLayout(testa)
            lv.addWidget(barra)
            self.lay_budget.addWidget(riga)
        self.lay_budget.addStretch(1)

    def _aggiorna_tabella(self) -> None:
        righe = self.db.query("SELECT * FROM movimenti ORDER BY data DESC, id DESC LIMIT 12")
        self.tab.setRowCount(len(righe))
        for r, m in enumerate(righe):
            segno = "+" if m["tipo"] == "entrata" else "−"
            colore = self.c["entrata"] if m["tipo"] == "entrata" else self.c["uscita"]
            valori = [data_it(m["data"]), m["descrizione"] or "—",
                      m["categoria"], m["conto"],
                      f"{segno} {euro(float(m['importo']), self.valuta)}"]
            for col, testo in enumerate(valori):
                it = QTableWidgetItem(testo)
                if col == 4:
                    it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    it.setForeground(QColor(colore))
                self.tab.setItem(r, col, it)

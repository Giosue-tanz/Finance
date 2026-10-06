"""Rapporti e analisi: confronti, ripartizioni, statistiche, previsioni."""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QDateEdit, QHeaderView,
                               QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout)

from ..componenti import Scheda, SchedaStat, etichetta, riga
from ..grafici import GraficoBarre, GraficoCiambella, GraficoLinea
from ..utils import (anno_corrente, data_it, etichetta_mese, euro, mese_corrente,
                     mese_precedente)
from . import VistaBase


class VistaRapporti(VistaBase):
    titolo = "Rapporti"
    sottotitolo = "Analisi approfondita di entrate e uscite"

    def costruisci(self) -> None:
        _, lay = self.area_scorrevole()

        sc_filtri = Scheda()
        self.cmb_periodo = QComboBox()
        self.cmb_periodo.addItems(["Mese corrente", "Mese precedente", "Anno corrente",
                                   "Ultimi 12 mesi", "Tutto", "Personalizzato"])
        self.cmb_periodo.setCurrentText("Anno corrente")
        self.dal = QDateEdit(QDate.currentDate().addYears(-1))
        self.al = QDateEdit(QDate.currentDate())
        for d in (self.dal, self.al):
            d.setCalendarPopup(True); d.setDisplayFormat("dd/MM/yyyy"); d.setEnabled(False)
        sc_filtri.aggiungi_layout(riga(etichetta("Periodo"), self.cmb_periodo,
                                       etichetta("dal"), self.dal,
                                       etichetta("al"), self.al, None))
        lay.addWidget(sc_filtri)

        fila = riga()
        self.s_entrate = SchedaStat("Entrate nel periodo", self.c, self.c["entrata"])
        self.s_uscite = SchedaStat("Uscite nel periodo", self.c, self.c["uscita"])
        self.s_saldo = SchedaStat("Saldo del periodo", self.c, self.c["accento"])
        self.s_media = SchedaStat("Spesa media mensile", self.c, self.c["attenzione"])
        for s in (self.s_entrate, self.s_uscite, self.s_saldo, self.s_media):
            fila.addWidget(s)
        lay.addLayout(fila)

        f2 = riga()
        sc_u = Scheda("Ripartizione uscite")
        self.g_uscite = GraficoCiambella(self.c); self.g_uscite.setMinimumHeight(250)
        sc_u.aggiungi(self.g_uscite, 1); f2.addWidget(sc_u)
        sc_e = Scheda("Ripartizione entrate")
        self.g_entrate = GraficoCiambella(self.c); self.g_entrate.setMinimumHeight(250)
        sc_e.aggiungi(self.g_entrate, 1); f2.addWidget(sc_e)
        lay.addLayout(f2)

        sc_cat = Scheda("Classifica categorie di spesa")
        self.g_classifica = GraficoBarre(self.c)
        self.g_classifica.orizzontale = True
        self.g_classifica.setMinimumHeight(300)
        sc_cat.aggiungi(self.g_classifica, 1)
        lay.addWidget(sc_cat)

        sc_risp = Scheda("Risparmio netto mensile")
        self.g_risparmio = GraficoLinea(self.c); self.g_risparmio.setMinimumHeight(240)
        sc_risp.aggiungi(self.g_risparmio, 1)
        lay.addWidget(sc_risp)

        sc_tab = Scheda("Dettaglio per categoria")
        self.tab = QTableWidget(0, 6)
        self.tab.setHorizontalHeaderLabels(
            ["Categoria", "Tipo", "Movimenti", "Totale", "Media", "Quota"])
        self.tab.verticalHeader().setVisible(False)
        self.tab.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tab.setSortingEnabled(True)
        self.tab.setMinimumHeight(320)
        h = self.tab.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Stretch)
        for c, l in ((1, 90), (2, 110), (3, 140), (4, 130), (5, 90)):
            h.resizeSection(c, l)
        sc_tab.aggiungi(self.tab)
        lay.addWidget(sc_tab)

        sc_mesi = Scheda("Riepilogo mensile")
        self.tab_mesi = QTableWidget(0, 5)
        self.tab_mesi.setHorizontalHeaderLabels(
            ["Mese", "Entrate", "Uscite", "Risparmio", "Tasso di risparmio"])
        self.tab_mesi.verticalHeader().setVisible(False)
        self.tab_mesi.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tab_mesi.setMinimumHeight(280)
        hm = self.tab_mesi.horizontalHeader()
        hm.setSectionResizeMode(4, QHeaderView.Stretch)
        for c, l in ((0, 140), (1, 150), (2, 150), (3, 150)):
            hm.resizeSection(c, l)
        sc_mesi.aggiungi(self.tab_mesi)
        lay.addWidget(sc_mesi)
        lay.addStretch(1)

        self.cmb_periodo.currentIndexChanged.connect(self._cambia)
        self.dal.dateChanged.connect(self.aggiorna)
        self.al.dateChanged.connect(self.aggiorna)
        self.grafici = [self.g_uscite, self.g_entrate, self.g_classifica, self.g_risparmio]

    def _cambia(self) -> None:
        pers = self.cmb_periodo.currentText() == "Personalizzato"
        self.dal.setEnabled(pers); self.al.setEnabled(pers)
        self.aggiorna()

    def _intervallo(self) -> tuple[str, str]:
        s = self.cmb_periodo.currentText()
        if s == "Mese corrente":
            return mese_corrente()
        if s == "Mese precedente":
            return mese_precedente()
        if s == "Anno corrente":
            return anno_corrente()
        if s == "Ultimi 12 mesi":
            o = date.today()
            inizio = date(o.year - 1, o.month, 1)
            return inizio.isoformat(), o.isoformat()
        if s == "Tutto":
            r = self.db.query("SELECT MIN(data) a, MAX(data) b FROM movimenti")[0]
            return (r["a"] or "1970-01-01"), (r["b"] or date.today().isoformat())
        return (self.dal.date().toString("yyyy-MM-dd"), self.al.date().toString("yyyy-MM-dd"))

    # ------------------------------------------------------------------ dati
    def aggiorna(self) -> None:
        v = self.valuta
        dal, al = self._intervallo()
        ent, usc = self.db.totali_periodo(dal, al)
        colori = self.db.colori_categorie()

        mesi = max(1, self._mesi_tra(dal, al))
        self.s_entrate.imposta(ent, f"su {mesi} mesi · media {euro(ent/mesi, v)}", v)
        self.s_uscite.imposta(usc, f"su {mesi} mesi · media {euro(usc/mesi, v)}", v)
        self.s_saldo.imposta(ent - usc,
                             f"tasso di risparmio {((ent-usc)/ent*100 if ent else 0):.0f}%", v)
        self.s_media.imposta(usc / mesi, "spesa media per mese nel periodo", v)

        cat_u = self.db.per_categoria("uscita", dal, al)
        cat_e = self.db.per_categoria("entrata", dal, al)
        self.g_uscite.imposta_dati([(n, t, colori.get(n, "")) for n, t in cat_u],
                                   euro(usc, v).replace(f" {v}", ""), "uscite")
        self.g_entrate.imposta_dati([(n, t, colori.get(n, "")) for n, t in cat_e],
                                    euro(ent, v).replace(f" {v}", ""), "entrate")
        self.g_classifica.imposta_dati(
            [(n, [t]) for n, t in cat_u[:12]],
            [(n, colori.get(n, "")) for n, _ in cat_u[:12]])

        serie = self.db.query(
            "SELECT substr(data,1,7) m, "
            "SUM(CASE WHEN tipo='entrata' THEN importo ELSE 0 END) e, "
            "SUM(CASE WHEN tipo='uscita' THEN importo ELSE 0 END) u "
            "FROM movimenti WHERE data BETWEEN ? AND ? GROUP BY m ORDER BY m",
            (dal, al))
        self.g_risparmio.imposta_dati(
            [(etichetta_mese(r["m"]), float(r["e"]) - float(r["u"])) for r in serie],
            self.c["attenzione"])

        self._tabella_categorie(dal, al, ent, usc)
        self._tabella_mesi(serie)

    @staticmethod
    def _mesi_tra(dal: str, al: str) -> int:
        try:
            a1, m1, _ = (int(x) for x in dal.split("-"))
            a2, m2, _ = (int(x) for x in al.split("-"))
            return (a2 - a1) * 12 + (m2 - m1) + 1
        except ValueError:
            return 1

    def _tabella_categorie(self, dal, al, ent, usc) -> None:
        v = self.valuta
        righe = self.db.query(
            "SELECT categoria, tipo, COUNT(*) n, SUM(importo) tot, AVG(importo) med "
            "FROM movimenti WHERE data BETWEEN ? AND ? "
            "GROUP BY categoria, tipo ORDER BY tot DESC", (dal, al))
        self.tab.setSortingEnabled(False)
        self.tab.setRowCount(len(righe))
        for r, x in enumerate(righe):
            base = ent if x["tipo"] == "entrata" else usc
            quota = float(x["tot"]) / base * 100 if base else 0
            valori = [x["categoria"], x["tipo"], str(x["n"]),
                      euro(float(x["tot"]), v), euro(float(x["med"]), v), f"{quota:.1f}%"]
            for col, t in enumerate(valori):
                it = QTableWidgetItem(t)
                if col >= 2:
                    it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tab.setItem(r, col, it)
        self.tab.setSortingEnabled(True)

    def _tabella_mesi(self, serie) -> None:
        v = self.valuta
        self.tab_mesi.setRowCount(len(serie))
        for r, x in enumerate(reversed(list(serie))):
            e, u = float(x["e"]), float(x["u"])
            tasso = (e - u) / e * 100 if e else 0
            valori = [etichetta_mese(x["m"]), euro(e, v), euro(u, v), euro(e - u, v),
                      f"{tasso:.0f}%"]
            for col, t in enumerate(valori):
                it = QTableWidgetItem(t)
                if col >= 1:
                    it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tab_mesi.setItem(r, col, it)

"""Cruscotto: pannello componibile con sezioni trascinabili e ridimensionabili.

Ogni riquadro si prende dalla maniglia in alto a sinistra e si porta dove serve,
anche in una riga nuova; i divisori regolano le dimensioni e i testi si adattano
allo spazio disponibile. La disposizione viene salvata nell'archivio.
"""
from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QMenu, QProgressBar,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget)

from ..componenti import ContenutoStat, abilita_deselezione, etichetta, riga
from ..grafici import GraficoBarre, GraficoCiambella, GraficoLinea
from ..icone import etichetta_categoria
from ..sezioni import ContenitoreSezioni, Sezione
from ..utils import (FINESTRE, PERIODI, data_it, etichetta_mese, euro, intervallo,
                     intervallo_precedente, mese_corrente, mese_precedente)
from . import VistaBase
from ..lingue import t

DISPOSIZIONE_PREDEFINITA = [
    ["saldo", "entrate", "uscite", "risparmio"],
    ["andamento", "ripartizione"],
    ["mensili", "budget"],
    ["ultimi"],
]

TITOLI = {
    "saldo": "SALDO TOTALE",
    "entrate": "ENTRATE",
    "uscite": "USCITE",
    "risparmio": "RISPARMIO",
    "andamento": "Andamento del saldo",
    "ripartizione": "Uscite per categoria",
    "mensili": "Entrate e uscite per mese",
    "budget": "Budget",
    "ultimi": "Ultimi movimenti",
}

# Che cosa può scegliere ogni riquadro e con quale valore si parte
PERIODI_SEZIONE = {
    "entrate": (PERIODI, "mese"),
    "uscite": (PERIODI, "mese"),
    "risparmio": (PERIODI, "mese"),
    "ripartizione": (PERIODI, "mese"),
    "ultimi": (PERIODI, "tutto"),
    "budget": ({"mese": "Mese corrente", "mese_scorso": "Mese scorso"}, "mese"),
    "andamento": (PERIODI, "dodici_mesi"),
    "mensili": (FINESTRE, "12"),
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
        self._prepara_menu_sezioni()
        lay.addWidget(self.contenitore, 1)

        self._crea_sezioni()
        self._ripristina()
        self.contenitore.disposizione_cambiata.connect(self._salva)
        self._pronto = True

    # ------------------------------------------------------------ strumenti
    def _prepara_menu_sezioni(self) -> None:
        """Pulsante «Sezioni», mostrato dalla finestra accanto a «Nuovo movimento»."""
        self.b_sezioni = QPushButton(t("Sezioni"))
        self.b_sezioni.setToolTip(
            "Mostra o nascondi i riquadri e ripristina la disposizione.\n\n"
            "Trascina un riquadro dal titolo per spostarlo, anche su una riga nuova.\n"
            "I divisori fra i riquadri ne regolano le dimensioni.\n"
            "Il testo accanto al titolo apre i periodi; «⋯» gli altri comandi.")
        self.menu_sezioni = QMenu(self)
        self.azioni: dict[str, QAction] = {}
        for chiave, nome in TITOLI.items():
            a = QAction(t(nome).capitalize() if nome.isupper() else t(nome),
                        self, checkable=True, checked=True)
            a.toggled.connect(lambda visibile, k=chiave: self._mostra(k, visibile))
            self.menu_sezioni.addAction(a)
            self.azioni[chiave] = a
        self.menu_sezioni.addSeparator()
        self.menu_sezioni.addAction(t("Ripristina disposizione predefinita"),
                                    self.ripristina_predefinita)
        self.b_sezioni.setMenu(self.menu_sezioni)
        self.azioni_intestazione = [self.b_sezioni]

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
            [t("Data"), t("Descrizione"), t("Categoria"), t("Conto"), t("Importo")])
        self.tab.verticalHeader().setVisible(False)
        self.tab.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tab.setSelectionBehavior(QTableWidget.SelectRows)
        self.tab.setAlternatingRowColors(True)
        self.tab.setMinimumHeight(60)
        h = self.tab.horizontalHeader()
        h.setStretchLastSection(True)
        h.resizeSection(0, 110); h.resizeSection(1, 280)
        h.resizeSection(2, 180); h.resizeSection(3, 140)
        abilita_deselezione(self.tab)
        self._aggiungi("ultimi", self.tab)

        self.grafici = [self.g_saldo, self.g_torta, self.g_barre]

    def _aggiungi(self, chiave: str, contenuto: QWidget,
                  stile: str = "Sezione") -> None:
        sezione = Sezione(chiave, t(TITOLI[chiave]), contenuto, stile)
        sezione.chiusura_richiesta.connect(
            lambda k: self.azioni[k].setChecked(False))
        sezione.periodo_richiesto.connect(self._menu_periodo)
        sezione.menu_richiesto.connect(self._menu_sezione)
        sezione.imposta_periodo(self._nome_periodo(chiave))
        self.contenitore.registra(sezione)

    # ------------------------------------------------------------- periodi
    def _periodo(self, chiave: str) -> str:
        """Periodo scelto per il riquadro, o quello predefinito."""
        if chiave not in PERIODI_SEZIONE:
            return ""
        voci, predefinito = PERIODI_SEZIONE[chiave]
        scelto = self.db.leggi(f"periodo_{chiave}", predefinito)
        return scelto if scelto in voci else predefinito

    def _nome_periodo(self, chiave: str) -> str:
        if chiave not in PERIODI_SEZIONE:
            return ""
        voci, _ = PERIODI_SEZIONE[chiave]
        return t(voci[self._periodo(chiave)]).lower()

    def _menu_periodo(self, chiave: str, punto) -> None:
        """Elenco dei periodi, aperto dal testo nell'intestazione."""
        if chiave not in PERIODI_SEZIONE:
            return
        voci, _ = PERIODI_SEZIONE[chiave]
        corrente = self._periodo(chiave)
        menu = QMenu(self)
        for valore, testo in voci.items():
            azione = menu.addAction(t(testo))
            azione.setCheckable(True)
            azione.setChecked(valore == corrente)
            azione.triggered.connect(
                lambda _=False, k=chiave, v=valore: self._imposta_periodo(k, v))
        menu.exec(punto)

    def _imposta_periodo(self, chiave: str, valore: str) -> None:
        self.db.imposta(f"periodo_{chiave}", valore)
        self.contenitore.sezioni[chiave].imposta_periodo(self._nome_periodo(chiave))
        self.aggiorna()

    def _menu_sezione(self, chiave: str, punto) -> None:
        """Menù «⋯» del riquadro: periodo e comandi della sezione."""
        menu = QMenu(self)
        if chiave in PERIODI_SEZIONE:
            voci, _ = PERIODI_SEZIONE[chiave]
            corrente = self._periodo(chiave)
            sottomenu = menu.addMenu(t("Periodo"))
            for valore, testo in voci.items():
                azione = sottomenu.addAction(t(testo))
                azione.setCheckable(True)
                azione.setChecked(valore == corrente)
                azione.triggered.connect(
                    lambda _=False, k=chiave, v=valore: self._imposta_periodo(k, v))
            menu.addSeparator()
        menu.addAction(t("Nascondi questa sezione"),
                       lambda: self.azioni[chiave].setChecked(False))
        menu.addAction(t("Ripristina disposizione"), self.ripristina_predefinita)
        menu.exec(punto)

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
        for chiave in PERIODI_SEZIONE:
            self.db.imposta(f"periodo_{chiave}", PERIODI_SEZIONE[chiave][1])
            self.contenitore.sezioni[chiave].imposta_periodo(self._nome_periodo(chiave))
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
        icone = self.db.icone_categorie()
        colori = self.db.colori_categorie()

        self._aggiorna_saldo(v)
        self._aggiorna_importi(v)
        self._aggiorna_andamento()
        self._aggiorna_ripartizione(v, colori, icone)
        self._aggiorna_mensili()
        self._aggiorna_budget_sezione(icone)
        self._aggiorna_tabella(icone)

    def _mesi_finestra(self, chiave: str) -> int:
        try:
            return int(self._periodo(chiave))
        except ValueError:
            return 12

    def _serie_saldo(self, mesi: int) -> list[tuple[str, float]]:
        """Saldo cumulato mese per mese."""
        iniziale = float(self.db.query(
            "SELECT COALESCE(SUM(saldo_iniziale),0) s FROM conti")[0]["s"])
        cumulato, punti = iniziale, []
        for mese, e, u in self.db.serie_mensile(mesi):
            cumulato += e - u
            punti.append((etichetta_mese(mese), cumulato))
        return punti

    def _serie_saldo_intervallo(self, dal: str, al: str) -> list[tuple[str, float]]:
        """Saldo cumulato sui mesi compresi nell'intervallo richiesto."""
        inizio = date.fromisoformat(dal)
        cumulato = self.db.saldo_alla_data(
            (inizio - timedelta(days=1)).isoformat())
        punti = []
        for mese, e, u in self.db.serie_mensile_intervallo(dal, al):
            cumulato += e - u
            punti.append((etichetta_mese(mese), cumulato))
        return punti

    def _serie_andamento(self) -> list[tuple[str, float]]:
        """Andamento del saldo nel periodo scelto.

        Sotto i due mesi la curva è giorno per giorno, oltre passa ai mesi:
        così anche «oggi» o «7 giorni» mostrano qualcosa di leggibile.
        """
        periodo = self._periodo("andamento")
        if periodo == "tutto":
            return self._serie_saldo(600)
        dal, al = intervallo(periodo)
        oggi = date.today().isoformat()
        al = min(al, oggi)                      # niente curva nel futuro
        giorni = (date.fromisoformat(al) - date.fromisoformat(dal)).days + 1
        if giorni > 62:
            return self._serie_saldo_intervallo(dal, al)

        # granularità giornaliera: si parte dal saldo del giorno prima
        inizio = date.fromisoformat(dal)
        saldo = self.db.saldo_alla_data((inizio - timedelta(days=1)).isoformat())
        movimenti = {d: (e, u) for d, e, u in self.db.serie_giornaliera(dal, al)}
        punti = []
        for passo in range(giorni):
            giorno = inizio + timedelta(days=passo)
            entrate, uscite = movimenti.get(giorno.isoformat(), (0.0, 0.0))
            saldo += entrate - uscite
            punti.append((giorno.strftime("%d/%m"), saldo))
        return punti

    def _aggiorna_saldo(self, v: str) -> None:
        """Il saldo è un valore puntuale: niente periodo, solo la variazione del mese."""
        ent, usc = self.db.totali_periodo(*mese_corrente())
        variazione = ent - usc
        segno = "+" if variazione >= 0 else ""
        conti = len(self.db.query("SELECT id FROM conti"))
        self.stat["saldo"].imposta(
            self.db.saldo_totale(),
            f"{conti} conti  ·  {segno}{euro(variazione, v)} questo mese", v,
            [p[1] for p in self._serie_saldo(12)])

    def _aggiorna_importi(self, v: str) -> None:
        for chiave in ("entrate", "uscite", "risparmio"):
            periodo = self._periodo(chiave)
            dal, al = intervallo(periodo)
            ent, usc = self.db.totali_periodo(dal, al)
            dal_p, al_p = intervallo_precedente(periodo)
            ent_p, usc_p = self.db.totali_periodo(dal_p, al_p)
            serie = self.db.serie_mensile(12)
            if chiave == "entrate":
                self.stat[chiave].imposta(
                    ent, self._confronto(ent, ent_p, periodo), v, [s[1] for s in serie])
            elif chiave == "uscite":
                self.stat[chiave].imposta(
                    usc, self._confronto(usc, usc_p, periodo), v, [s[2] for s in serie])
            else:
                risparmio = ent - usc
                tasso = (risparmio / ent * 100) if ent > 0 else 0.0
                self.stat[chiave].imposta(
                    risparmio, f"tasso di risparmio {tasso:.0f}%", v,
                    [s[1] - s[2] for s in serie])

    def _aggiorna_andamento(self) -> None:
        self.g_saldo.imposta_dati(self._serie_andamento(), self.c["accento"])

    def _aggiorna_ripartizione(self, v: str, colori: dict, icone: dict) -> None:
        dal, al = intervallo(self._periodo("ripartizione"))
        _, usc = self.db.totali_periodo(dal, al)
        cats = self.db.per_categoria("uscita", dal, al)
        self.g_torta.imposta_dati(
            [(etichetta_categoria(n, icone.get(n)), t, colori.get(n, "")) for n, t in cats],
            euro(usc, v).replace(f" {v}", ""),
            PERIODI[self._periodo("ripartizione")].lower())

    def _aggiorna_mensili(self) -> None:
        serie = self.db.serie_mensile(self._mesi_finestra("mensili"))
        self.g_barre.imposta_dati(
            [(etichetta_mese(m), [e, u]) for m, e, u in serie],
            [("Entrate", self.c["entrata"]), ("Uscite", self.c["uscita"])])

    def _aggiorna_budget_sezione(self, icone: dict) -> None:
        dal, al = (mese_corrente() if self._periodo("budget") == "mese"
                   else mese_precedente())
        self._aggiorna_budget(dal, al, icone)

    def _confronto(self, ora: float, prima: float, periodo: str = "mese") -> str:
        riferimento = {"oggi": "a ieri", "settimana": "ai 7 giorni prima",
                       "mese": "al mese scorso", "mese_scorso": "al mese prima",
                       "anno": "all'anno scorso"}.get(periodo, "al periodo precedente")
        if prima <= 0:
            return "nessun confronto disponibile"
        delta = (ora - prima) / prima * 100
        freccia = "▲" if delta > 0 else ("▼" if delta < 0 else "=")
        return f"{freccia} {abs(delta):.0f}% rispetto {riferimento}"

    def _aggiorna_budget(self, dal: str, al: str, icone: dict) -> None:
        while self.lay_budget.count():
            item = self.lay_budget.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

        budget = self.db.query("SELECT * FROM budget WHERE mensile > 0 ORDER BY mensile DESC")
        if not budget:
            self.lay_budget.addWidget(etichetta(t("Nessun budget impostato."),
                                                "NotaScheda"))
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
        dal, al = intervallo(self._periodo("ultimi"))
        righe = self.db.query(
            "SELECT * FROM movimenti WHERE data BETWEEN ? AND ? "
            "ORDER BY data DESC, id DESC LIMIT 40", (dal, al))
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

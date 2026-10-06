"""Strumenti di calcolo finanziario, tutti offline."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QDoubleSpinBox,
                               QFormLayout, QHeaderView, QLabel, QPushButton,
                               QSpinBox, QTabWidget, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget)

from ..componenti import Scheda, etichetta, riga
from ..grafici import GraficoLinea
from ..utils import euro
from . import VistaBase


def _modulo() -> QFormLayout:
    """QFormLayout con campi di larghezza naturale, non stirati."""
    m = QFormLayout()
    m.setSpacing(10)
    m.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
    m.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
    m.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
    return m


def _spin(valore: float, massimo: float = 99_999_999, suffisso: str = "",
          decimali: int = 2, passo: float = 1.0) -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(0, massimo)
    s.setGroupSeparatorShown(True)
    s.setMaximumWidth(260)
    s.setMinimumWidth(190)
    s.setDecimals(decimali)
    s.setSingleStep(passo)
    s.setValue(valore)
    if suffisso:
        s.setSuffix(suffisso)
    return s


class VistaStrumenti(VistaBase):
    titolo = "Strumenti"
    sottotitolo = "Calcolatrici finanziarie e utilità"

    def costruisci(self) -> None:
        _, lay = self.area_scorrevole()
        schede = QTabWidget()
        schede.addTab(self._prestito(), "Prestito / Mutuo")
        schede.addTab(self._interesse(), "Interesse composto")
        schede.addTab(self._obiettivo(), "Piano di risparmio")
        schede.addTab(self._regola(), "Regola 50/30/20")
        schede.addTab(self._iva(), "IVA e sconti")
        schede.addTab(self._divisione(), "Dividi spese")
        lay.addWidget(schede, 1)
        self.aggiorna()

    # ------------------------------------------------------- prestito / mutuo
    def _prestito(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w); lay.setSpacing(12)
        sc = Scheda("Dati del finanziamento")
        self.p_capitale = _spin(100_000, suffisso=f" {self.valuta}", passo=1000)
        self.p_tasso = _spin(3.5, 100, " %", 2, 0.1)
        self.p_anni = QSpinBox(); self.p_anni.setRange(1, 50); self.p_anni.setValue(20)
        self.p_anni.setMaximumWidth(260); self.p_anni.setMinimumWidth(190)
        self.p_anni.setSuffix(" anni")
        b = QPushButton("Calcola"); b.setObjectName("Primario")
        modulo = _modulo()
        modulo.addRow("Capitale", self.p_capitale)
        modulo.addRow("Tasso annuo (TAN)", self.p_tasso)
        modulo.addRow("Durata", self.p_anni)
        sc.aggiungi_layout(modulo)
        sc.aggiungi_layout(riga(b, None))
        lay.addWidget(sc)

        self.p_risultato = QLabel("—"); self.p_risultato.setObjectName("Sezione")
        self.p_dettaglio = QLabel(""); self.p_dettaglio.setObjectName("NotaScheda")
        sc_res = Scheda("Risultato")
        sc_res.aggiungi(self.p_risultato); sc_res.aggiungi(self.p_dettaglio)
        lay.addWidget(sc_res)

        sc_tab = Scheda("Piano di ammortamento (primi 24 mesi)")
        self.p_tab = QTableWidget(0, 5)
        self.p_tab.setHorizontalHeaderLabels(
            ["Rata", "Quota capitale", "Quota interessi", "Rata totale", "Debito residuo"])
        self.p_tab.verticalHeader().setVisible(False)
        self.p_tab.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.p_tab.setMinimumHeight(300)
        self.p_tab.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        sc_tab.aggiungi(self.p_tab)
        lay.addWidget(sc_tab)
        lay.addStretch(1)
        b.clicked.connect(self._calcola_prestito)
        self._calcola_prestito()
        return w

    def _calcola_prestito(self) -> None:
        v = self.valuta
        capitale = self.p_capitale.value()
        tasso_m = self.p_tasso.value() / 100 / 12
        n = self.p_anni.value() * 12
        if capitale <= 0 or n <= 0:
            return
        rata = (capitale / n if tasso_m == 0 else
                capitale * tasso_m / (1 - (1 + tasso_m) ** -n))
        totale = rata * n
        self.p_risultato.setText(f"Rata mensile: {euro(rata, v)}")
        self.p_dettaglio.setText(
            f"Totale restituito {euro(totale, v)}  ·  interessi complessivi "
            f"{euro(totale - capitale, v)}  ·  {n} rate  ·  "
            f"incidenza interessi {((totale-capitale)/capitale*100):.1f}%")

        residuo = capitale
        righe = []
        for i in range(1, n + 1):
            interessi = residuo * tasso_m
            quota_cap = rata - interessi
            residuo = max(0.0, residuo - quota_cap)
            if i <= 24:
                righe.append((i, quota_cap, interessi, rata, residuo))
        self.p_tab.setRowCount(len(righe))
        for r, (i, qc, qi, rt, res) in enumerate(righe):
            for col, t in enumerate([str(i), euro(qc, v), euro(qi, v),
                                     euro(rt, v), euro(res, v)]):
                it = QTableWidgetItem(t)
                if col:
                    it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.p_tab.setItem(r, col, it)

    # ------------------------------------------------------ interesse composto
    def _interesse(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w); lay.setSpacing(12)
        sc = Scheda("Capitale e versamenti")
        self.i_iniziale = _spin(5_000, suffisso=f" {self.valuta}", passo=500)
        self.i_mensile = _spin(200, suffisso=f" {self.valuta}", passo=50)
        self.i_tasso = _spin(5.0, 100, " % annuo", 2, 0.25)
        self.i_anni = QSpinBox(); self.i_anni.setRange(1, 70); self.i_anni.setValue(15)
        self.i_anni.setMaximumWidth(260); self.i_anni.setMinimumWidth(190)
        self.i_anni.setSuffix(" anni")
        b = QPushButton("Calcola"); b.setObjectName("Primario")
        modulo = _modulo()
        modulo.addRow("Capitale iniziale", self.i_iniziale)
        modulo.addRow("Versamento mensile", self.i_mensile)
        modulo.addRow("Rendimento atteso", self.i_tasso)
        modulo.addRow("Orizzonte", self.i_anni)
        sc.aggiungi_layout(modulo); sc.aggiungi_layout(riga(b, None))
        lay.addWidget(sc)

        self.i_risultato = QLabel("—"); self.i_risultato.setObjectName("Sezione")
        self.i_dettaglio = QLabel(""); self.i_dettaglio.setObjectName("NotaScheda")
        sc_res = Scheda("Proiezione")
        sc_res.aggiungi(self.i_risultato); sc_res.aggiungi(self.i_dettaglio)
        self.i_grafico = GraficoLinea(self.c); self.i_grafico.setMinimumHeight(260)
        sc_res.aggiungi(self.i_grafico, 1)
        lay.addWidget(sc_res)
        lay.addStretch(1)
        b.clicked.connect(self._calcola_interesse)
        self.grafici.append(self.i_grafico)
        self._calcola_interesse()
        return w

    def _calcola_interesse(self) -> None:
        v = self.valuta
        capitale = self.i_iniziale.value()
        mensile = self.i_mensile.value()
        tasso_m = self.i_tasso.value() / 100 / 12
        anni = self.i_anni.value()
        saldo = capitale
        punti = [("ora", saldo)]
        for anno in range(1, anni + 1):
            for _ in range(12):
                saldo = saldo * (1 + tasso_m) + mensile
            punti.append((f"{anno}a", saldo))
        versato = capitale + mensile * 12 * anni
        self.i_risultato.setText(f"Valore finale stimato: {euro(saldo, v)}")
        self.i_dettaglio.setText(
            f"Versato {euro(versato, v)}  ·  rendimento maturato "
            f"{euro(saldo - versato, v)}  ·  moltiplicatore "
            f"{(saldo/versato if versato else 0):.2f}×")
        self.i_grafico.imposta_dati(punti, self.c["entrata"])

    # ---------------------------------------------------- piano di risparmio
    def _obiettivo(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w); lay.setSpacing(12)
        sc = Scheda("Quanto devo mettere da parte?")
        self.o_target = _spin(10_000, suffisso=f" {self.valuta}", passo=500)
        self.o_attuale = _spin(1_000, suffisso=f" {self.valuta}", passo=100)
        self.o_mesi = QSpinBox(); self.o_mesi.setRange(1, 600); self.o_mesi.setValue(24)
        self.o_mesi.setMaximumWidth(260); self.o_mesi.setMinimumWidth(190)
        self.o_mesi.setSuffix(" mesi")
        self.o_tasso = _spin(0.0, 100, " % annuo", 2, 0.25)
        b = QPushButton("Calcola"); b.setObjectName("Primario")
        modulo = _modulo()
        modulo.addRow("Obiettivo", self.o_target)
        modulo.addRow("Già disponibile", self.o_attuale)
        modulo.addRow("Tempo", self.o_mesi)
        modulo.addRow("Rendimento (opzionale)", self.o_tasso)
        sc.aggiungi_layout(modulo); sc.aggiungi_layout(riga(b, None))
        lay.addWidget(sc)
        self.o_risultato = QLabel("—"); self.o_risultato.setObjectName("Sezione")
        self.o_dettaglio = QLabel(""); self.o_dettaglio.setObjectName("NotaScheda")
        self.o_dettaglio.setWordWrap(True)
        sc_res = Scheda("Risultato")
        sc_res.aggiungi(self.o_risultato); sc_res.aggiungi(self.o_dettaglio)
        lay.addWidget(sc_res); lay.addStretch(1)
        b.clicked.connect(self._calcola_obiettivo)
        self._calcola_obiettivo()
        return w

    def _calcola_obiettivo(self) -> None:
        v = self.valuta
        mancante = max(0.0, self.o_target.value() - self.o_attuale.value())
        n = self.o_mesi.value()
        i = self.o_tasso.value() / 100 / 12
        if i > 0:
            futuro_attuale = self.o_attuale.value() * (1 + i) ** n
            residuo = max(0.0, self.o_target.value() - futuro_attuale)
            rata = residuo * i / ((1 + i) ** n - 1) if residuo else 0.0
        else:
            rata = mancante / n
        self.o_risultato.setText(f"Da accantonare: {euro(rata, v)} al mese")
        self.o_dettaglio.setText(
            f"Per raggiungere {euro(self.o_target.value(), v)} in {n} mesi partendo da "
            f"{euro(self.o_attuale.value(), v)}. Totale versamenti "
            f"{euro(rata * n, v)}. Equivale a circa {euro(rata / 30.4, v)} al giorno.")

    # ------------------------------------------------------- regola 50/30/20
    def _regola(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w); lay.setSpacing(12)
        sc = Scheda("Ripartizione consigliata del reddito netto")
        self.r_reddito = _spin(1_800, suffisso=f" {self.valuta}", passo=100)
        b = QPushButton("Calcola"); b.setObjectName("Primario")
        b_reale = QPushButton("Usa le entrate reali del mese")
        modulo = _modulo(); modulo.addRow("Entrate nette mensili", self.r_reddito)
        sc.aggiungi_layout(modulo); sc.aggiungi_layout(riga(b, b_reale, None))
        lay.addWidget(sc)
        self.r_tab = QTableWidget(0, 4)
        self.r_tab.setHorizontalHeaderLabels(
            ["Voce", "Quota", "Importo consigliato", "Speso realmente nel mese"])
        self.r_tab.verticalHeader().setVisible(False)
        self.r_tab.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.r_tab.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.r_tab.setMinimumHeight(190)
        sc_t = Scheda("Risultato"); sc_t.aggiungi(self.r_tab)
        self.r_nota = QLabel(""); self.r_nota.setObjectName("NotaScheda")
        self.r_nota.setWordWrap(True)
        sc_t.aggiungi(self.r_nota)
        lay.addWidget(sc_t); lay.addStretch(1)
        b.clicked.connect(self._calcola_regola)
        b_reale.clicked.connect(self._reddito_reale)
        self._calcola_regola()
        return w

    def _reddito_reale(self) -> None:
        from ..utils import mese_corrente
        ent, _ = self.db.totali_periodo(*mese_corrente())
        self.r_reddito.setValue(ent)
        self._calcola_regola()

    def _calcola_regola(self) -> None:
        from ..utils import mese_corrente
        v = self.valuta
        reddito = self.r_reddito.value()
        dal, al = mese_corrente()
        _, uscite = self.db.totali_periodo(dal, al)
        voci = [("Necessità (casa, bollette, spesa, trasporti)", 0.50),
                ("Desideri (tempo libero, extra)", 0.30),
                ("Risparmio e investimenti", 0.20)]
        self.r_tab.setRowCount(len(voci))
        for r, (nome, quota) in enumerate(voci):
            valori = [nome, f"{int(quota*100)}%", euro(reddito * quota, v),
                      euro(uscite, v) if r == 0 else "—"]
            for col, t in enumerate(valori):
                it = QTableWidgetItem(t)
                if col >= 1:
                    it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.r_tab.setItem(r, col, it)
        self.r_nota.setText(
            f"Uscite totali registrate nel mese corrente: {euro(uscite, v)} "
            f"({(uscite/reddito*100 if reddito else 0):.0f}% delle entrate inserite). "
            "La regola è un riferimento indicativo, da adattare alla tua situazione.")

    # --------------------------------------------------------------- IVA
    def _iva(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w); lay.setSpacing(12)
        sc = Scheda("Calcolo IVA")
        self.v_importo = _spin(100, suffisso=f" {self.valuta}", passo=10)
        self.v_aliquota = QComboBox(); self.v_aliquota.addItems(["22", "10", "5", "4", "0"])
        self.v_aliquota.setMaximumWidth(260)
        self.v_aliquota.setEditable(True)
        self.v_modo = QComboBox(); self.v_modo.setMaximumWidth(320)
        self.v_modo.addItems(["L'importo è senza IVA (netto)", "L'importo è con IVA (lordo)"])
        modulo = _modulo()
        modulo.addRow("Importo", self.v_importo)
        modulo.addRow("Aliquota %", self.v_aliquota)
        modulo.addRow("Modalità", self.v_modo)
        sc.aggiungi_layout(modulo)
        self.v_risultato = QLabel("—"); self.v_risultato.setObjectName("Sezione")
        sc.aggiungi(self.v_risultato)
        lay.addWidget(sc)

        sc2 = Scheda("Sconto")
        self.s_prezzo = _spin(80, suffisso=f" {self.valuta}", passo=5)
        self.s_sconto = _spin(20, 100, " %", 2, 1)
        m2 = _modulo()
        m2.addRow("Prezzo di listino", self.s_prezzo)
        m2.addRow("Sconto", self.s_sconto)
        sc2.aggiungi_layout(m2)
        self.s_risultato = QLabel("—"); self.s_risultato.setObjectName("Sezione")
        sc2.aggiungi(self.s_risultato)
        lay.addWidget(sc2); lay.addStretch(1)

        for widget in (self.v_importo, self.s_prezzo, self.s_sconto):
            widget.valueChanged.connect(self._calcola_iva)
        self.v_aliquota.currentTextChanged.connect(self._calcola_iva)
        self.v_modo.currentIndexChanged.connect(self._calcola_iva)
        self._calcola_iva()
        return w

    def _calcola_iva(self) -> None:
        v = self.valuta
        try:
            aliquota = float(self.v_aliquota.currentText().replace(",", ".")) / 100
        except ValueError:
            aliquota = 0.22
        importo = self.v_importo.value()
        if self.v_modo.currentIndex() == 0:
            netto, iva = importo, importo * aliquota
        else:
            netto = importo / (1 + aliquota) if aliquota > -1 else importo
            iva = importo - netto
        self.v_risultato.setText(
            f"Netto {euro(netto, v)}   ·   IVA {euro(iva, v)}   ·   "
            f"Lordo {euro(netto + iva, v)}")
        prezzo, sconto = self.s_prezzo.value(), self.s_sconto.value() / 100
        self.s_risultato.setText(
            f"Risparmio {euro(prezzo * sconto, v)}   ·   "
            f"Prezzo finale {euro(prezzo * (1 - sconto), v)}")

    # ----------------------------------------------------------- dividi spese
    def _divisione(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w); lay.setSpacing(12)
        sc = Scheda("Dividi una spesa tra più persone")
        self.d_totale = _spin(120, suffisso=f" {self.valuta}", passo=10)
        self.d_persone = QSpinBox(); self.d_persone.setRange(1, 200); self.d_persone.setValue(4)
        self.d_persone.setMaximumWidth(260); self.d_persone.setMinimumWidth(190)
        self.d_persone.setSuffix(" persone")
        self.d_mancia = _spin(0, 100, " % di mancia/servizio", 1, 1)
        modulo = _modulo()
        modulo.addRow("Totale", self.d_totale)
        modulo.addRow("Partecipanti", self.d_persone)
        modulo.addRow("Extra", self.d_mancia)
        sc.aggiungi_layout(modulo)
        self.d_risultato = QLabel("—"); self.d_risultato.setObjectName("Sezione")
        self.d_nota = QLabel(""); self.d_nota.setObjectName("NotaScheda")
        sc.aggiungi(self.d_risultato); sc.aggiungi(self.d_nota)
        lay.addWidget(sc); lay.addStretch(1)
        for widget in (self.d_totale, self.d_persone, self.d_mancia):
            widget.valueChanged.connect(self._calcola_divisione)
        self._calcola_divisione()
        return w

    def _calcola_divisione(self) -> None:
        v = self.valuta
        totale = self.d_totale.value() * (1 + self.d_mancia.value() / 100)
        n = max(1, self.d_persone.value())
        quota = totale / n
        self.d_risultato.setText(f"{euro(quota, v)} a testa")
        self.d_nota.setText(
            f"Totale con extra {euro(totale, v)} diviso tra {n} persone. "
            f"Arrotondato per eccesso: {euro(round(quota + 0.49), v)} a testa.")

    def aggiorna(self) -> None:
        """Aggiorna i suffissi di valuta quando cambia l'impostazione."""
        v = self.valuta
        for widget in (getattr(self, n, None) for n in
                       ("p_capitale", "i_iniziale", "i_mensile", "o_target",
                        "o_attuale", "r_reddito", "v_importo", "s_prezzo", "d_totale")):
            if widget is not None:
                widget.setSuffix(f" {v}")

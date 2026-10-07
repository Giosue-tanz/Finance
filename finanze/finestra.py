"""Finestra principale: barra di navigazione modulare e viste impilate."""
from __future__ import annotations

import os

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import (QAction, QColor, QIcon, QKeySequence, QPalette,
                           QShortcut)
from PySide6.QtWidgets import (QApplication, QButtonGroup, QHBoxLayout, QLabel,
                               QMainWindow,
                               QMessageBox, QPushButton, QStackedWidget,
                               QStatusBar, QVBoxLayout, QWidget)

from .componenti import separatore
from .db import APP_DIR, Database
from .tema import ACCENTO_PREDEFINITO, SCALE, colori, foglio_stile
from .utils import euro, mese_corrente
from .views.budget import VistaBudget
from .views.cruscotto import VistaCruscotto
from .views.impostazioni import VistaImpostazioni
from .views.movimenti import VistaMovimenti
from .views.obiettivi import VistaObiettivi
from .views.rapporti import VistaRapporti
from .views.ricorrenti import VistaRicorrenti
from .views.strumenti import VistaStrumenti

VISTE = [
    ("◆", VistaCruscotto),
    ("≡", VistaMovimenti),
    ("▤", VistaBudget),
    ("◎", VistaObiettivi),
    ("↻", VistaRicorrenti),
    ("▦", VistaRapporti),
    ("⚙", VistaStrumenti),
    ("⚒", VistaImpostazioni),
]


class FinestraPrincipale(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.c = colori(db.leggi("tema", "scuro"),
                        db.leggi("accento", ACCENTO_PREDEFINITO))
        self.setWindowTitle("Finance — Gestione finanziaria personale")
        self.resize(1320, 860)
        self.setMinimumSize(1050, 680)
        icona = os.path.join(APP_DIR, "risorse", "icona.png")
        if os.path.exists(icona):
            self.setWindowIcon(QIcon(icona))

        centrale = QWidget()
        self.setCentralWidget(centrale)
        lay = QHBoxLayout(centrale)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(self._barra())
        lay.addWidget(self._contenuto(), 1)

        self.setStatusBar(QStatusBar())
        self.statusBar().setSizeGripEnabled(False)

        self._scorciatoie()
        self.applica_tema(db.leggi("tema", "scuro"))
        self.vai(0)

    # ------------------------------------------------------------------ barra
    def _barra(self) -> QWidget:
        barra = QWidget()
        barra.setObjectName("Barra")
        barra.setFixedWidth(224)
        lay = QVBoxLayout(barra)
        lay.setContentsMargins(14, 18, 14, 14)
        lay.setSpacing(6)

        logo = QLabel("◉  Finance")
        logo.setObjectName("Logo")
        lay.addWidget(logo)
        sotto = QLabel("archivio locale")
        sotto.setObjectName("Sottotitolo")
        lay.addWidget(sotto)
        lay.addSpacing(14)

        self.gruppo = QButtonGroup(self)
        self.gruppo.setExclusive(True)
        self.pulsanti: list[QPushButton] = []
        for i, (simbolo, classe) in enumerate(VISTE):
            b = QPushButton(f"  {simbolo}   {classe.titolo}")
            b.setObjectName("Navigazione")
            b.setCheckable(True)
            b.clicked.connect(lambda _=False, idx=i: self.vai(idx))
            self.gruppo.addButton(b, i)
            self.pulsanti.append(b)
            lay.addWidget(b)

        lay.addStretch(1)
        lay.addWidget(separatore())
        self.et_saldo = QLabel("—")
        self.et_saldo.setObjectName("ValoreScheda")
        self.et_saldo_nota = QLabel("saldo complessivo")
        self.et_saldo_nota.setObjectName("NotaScheda")
        lay.addWidget(self.et_saldo_nota)
        lay.addWidget(self.et_saldo)
        return barra

    def _contenuto(self) -> QWidget:
        contenitore = QWidget()
        lay = QVBoxLayout(contenitore)
        lay.setContentsMargins(20, 16, 20, 14)
        lay.setSpacing(12)

        testa = QHBoxLayout()
        colonna = QVBoxLayout()
        colonna.setSpacing(1)
        self.et_titolo = QLabel("")
        self.et_titolo.setObjectName("Titolo")
        self.et_sottotitolo = QLabel("")
        self.et_sottotitolo.setObjectName("Sottotitolo")
        colonna.addWidget(self.et_titolo)
        colonna.addWidget(self.et_sottotitolo)
        testa.addLayout(colonna)
        testa.addStretch(1)
        self.b_rapido = QPushButton("+  Nuovo movimento")
        self.b_rapido.setObjectName("Primario")
        self.b_rapido.clicked.connect(self.nuovo_movimento)
        testa.addWidget(self.b_rapido)
        lay.addLayout(testa)

        self.pila = QStackedWidget()
        self.viste = []
        for _, classe in VISTE:
            vista = classe(self.db, self.c)
            vista.dati_cambiati.connect(self.ricarica)
            if hasattr(vista, "tema_cambiato"):
                vista.tema_cambiato.connect(self.applica_tema)
            if hasattr(vista, "aspetto_cambiato"):
                vista.aspetto_cambiato.connect(
                    lambda: self.applica_tema(self.db.leggi("tema", "scuro")))
            self.viste.append(vista)
            self.pila.addWidget(vista)
        lay.addWidget(self.pila, 1)
        return contenitore

    def _scorciatoie(self) -> None:
        QShortcut(QKeySequence("Ctrl+N"), self, self.nuovo_movimento)
        QShortcut(QKeySequence("Ctrl+R"), self, self.ricarica)
        QShortcut(QKeySequence("Ctrl+T"), self, self.commuta_tema)
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)
        for i in range(len(VISTE)):
            QShortcut(QKeySequence(f"Ctrl+{i+1}"), self, lambda idx=i: self.vai(idx))

    # ---------------------------------------------------------------- azioni
    def vai(self, indice: int) -> None:
        self.pila.setCurrentIndex(indice)
        self.pulsanti[indice].setChecked(True)
        vista = self.viste[indice]
        self.et_titolo.setText(vista.titolo)
        self.et_sottotitolo.setText(vista.sottotitolo)
        self.b_rapido.setVisible(not isinstance(vista, VistaImpostazioni))
        vista.aggiorna()

    def nuovo_movimento(self) -> None:
        vista_mov = self.viste[1]
        vista_mov.nuovo()

    def ricarica(self) -> None:
        self.viste[self.pila.currentIndex()].aggiorna()
        self._aggiorna_stato()

    def _aggiorna_stato(self) -> None:
        v = self.db.leggi("valuta", "€")
        saldo = self.db.saldo_totale()
        self.et_saldo.setText(euro(saldo, v))
        self.et_saldo.setStyleSheet(
            f"color: {self.c['entrata'] if saldo >= 0 else self.c['uscita']};")
        dal, al = mese_corrente()
        ent, usc = self.db.totali_periodo(dal, al)
        n = self.db.query("SELECT COUNT(*) n FROM movimenti")[0]["n"]
        self.statusBar().showMessage(
            f"{n} movimenti in archivio   ·   mese corrente: entrate {euro(ent, v)}, "
            f"uscite {euro(usc, v)}   ·   archivio locale: {self.db.percorso}   ·   "
            "nessuna connessione di rete")

    def commuta_tema(self) -> None:
        nuovo = "chiaro" if self.db.leggi("tema", "scuro") == "scuro" else "scuro"
        self.db.imposta("tema", nuovo)
        self.applica_tema(nuovo)

    @staticmethod
    def _palette(c: dict) -> QPalette:
        """Palette Qt coerente col tema: serve ai widget che non passano dal QSS
        (righe alternate, selezioni, testo segnaposto)."""
        p = QPalette()
        p.setColor(QPalette.Window, QColor(c["fondo"]))
        p.setColor(QPalette.WindowText, QColor(c["testo"]))
        p.setColor(QPalette.Base, QColor(c["pannello"]))
        p.setColor(QPalette.AlternateBase, QColor(c["pannello2"]))
        p.setColor(QPalette.Text, QColor(c["testo"]))
        p.setColor(QPalette.PlaceholderText, QColor(c["testo2"]))
        p.setColor(QPalette.Button, QColor(c["pannello2"]))
        p.setColor(QPalette.ButtonText, QColor(c["testo"]))
        p.setColor(QPalette.ToolTipBase, QColor(c["pannello2"]))
        p.setColor(QPalette.ToolTipText, QColor(c["testo"]))
        p.setColor(QPalette.Highlight, QColor(c["accento"]))
        p.setColor(QPalette.HighlightedText, QColor("#ffffff"))
        p.setColor(QPalette.Link, QColor(c["accento"]))
        return p

    def applica_tema(self, nome: str) -> None:
        self.c = colori(nome, self.db.leggi("accento", ACCENTO_PREDEFINITO))
        scala = SCALE.get(self.db.leggi("scala", "normale"), 1.0)
        app = QApplication.instance()
        if app is not None:
            app.setPalette(self._palette(self.c))
        self.setStyleSheet(foglio_stile(self.c, scala))
        for vista in self.viste:
            vista.aggiorna_tema(self.c)
        self._aggiorna_stato()

    def closeEvent(self, ev) -> None:
        self.db.chiudi()
        super().closeEvent(ev)

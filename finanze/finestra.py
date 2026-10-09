"""Finestra principale: barra di navigazione modulare e viste impilate."""
from __future__ import annotations

import os

from PySide6.QtCore import (QEasingCurve, QPropertyAnimation, QSize, Qt)
from PySide6.QtGui import (QAction, QColor, QIcon, QKeySequence, QPalette,
                           QShortcut)
from PySide6.QtWidgets import (QApplication, QButtonGroup, QHBoxLayout, QLabel,
                               QMainWindow, QSizePolicy, QSpacerItem,
                               QMessageBox, QPushButton, QStackedWidget,
                               QStatusBar, QVBoxLayout, QWidget)

from .icone_nav import STILE_PREDEFINITO, icona, icona_menu
from .componenti import separatore
from .db import APP_DIR, DATA_DIR, Database
from .tema import (ACCENTO_PREDEFINITO, SCALE, colori, foglio_stile,
                   frecce_spin)
from .utils import compatto, euro, mese_corrente
from .views.budget import VistaBudget
from .views.cruscotto import VistaCruscotto
from .views.impostazioni import VistaImpostazioni
from .views.movimenti import VistaMovimenti
from .views.obiettivi import VistaObiettivi
from .views.rapporti import VistaRapporti
from .views.ricorrenti import VistaRicorrenti
from .views.strumenti import VistaStrumenti

LARGHEZZA_APERTA = 222
LARGHEZZA_CHIUSA = 62

VISTE = [
    ("cruscotto", VistaCruscotto),
    ("movimenti", VistaMovimenti),
    ("budget", VistaBudget),
    ("obiettivi", VistaObiettivi),
    ("ricorrenti", VistaRicorrenti),
    ("rapporti", VistaRapporti),
    ("strumenti", VistaStrumenti),
    ("impostazioni", VistaImpostazioni),
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
        self.barra = QWidget()
        self.barra.setObjectName("Barra")
        self.barra.setFixedWidth(LARGHEZZA_APERTA)
        lay = QVBoxLayout(self.barra)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(5)
        self.lay_barra = lay

        # testata: nome e pulsante del menu sulla stessa linea di base
        self.testata = QWidget()
        self.testata.setObjectName("TestataBarra")
        self.testata.setFixedHeight(40)
        testa = QHBoxLayout(self.testata)
        testa.setContentsMargins(6, 0, 0, 0)
        testa.setSpacing(6)

        # a barra chiusa resta solo il simbolo dell'app, centrato e cliccabile
        self.b_logo = QPushButton()
        self.b_logo.setObjectName("LogoApp")
        self.b_logo.setFixedSize(46, 44)
        self.b_logo.setIconSize(QSize(44, 44))   # il simbolo riempie il pulsante
        self.b_logo.setCursor(Qt.PointingHandCursor)
        self.b_logo.setToolTip("Apri il menu  (Ctrl+B)")
        self.b_logo.clicked.connect(self.commuta_barra)
        simbolo = os.path.join(APP_DIR, "risorse", "icona.png")
        if os.path.exists(simbolo):
            self.b_logo.setIcon(QIcon(simbolo))

        self.et_logo = QLabel("Finance")
        self.et_logo.setObjectName("Logo")
        self.b_menu = QPushButton()
        self.b_menu.setObjectName("BottoneMenu")
        self.b_menu.setFixedSize(32, 32)
        self.b_menu.setIconSize(QSize(19, 19))
        self.b_menu.setToolTip("Chiudi il menu  (Ctrl+B)")
        self.b_menu.clicked.connect(self.commuta_barra)

        self.spazio_testa = QSpacerItem(0, 0, QSizePolicy.Fixed, QSizePolicy.Minimum)
        testa.addItem(self.spazio_testa)
        testa.addWidget(self.b_logo)
        testa.addWidget(self.et_logo)
        testa.addStretch(1)
        testa.addWidget(self.b_menu)
        self.lay_testa = testa
        lay.addWidget(self.testata)
        lay.addSpacing(10)

        self.gruppo = QButtonGroup(self)
        self.gruppo.setExclusive(True)
        self.pulsanti: list[QPushButton] = []
        for i, (nome_icona, classe) in enumerate(VISTE):
            b = QPushButton()
            b.setObjectName("Navigazione")
            b.setIconSize(QSize(19, 19))
            b.setCheckable(True)
            b.clicked.connect(lambda _=False, idx=i: self.vai(idx))
            self.gruppo.addButton(b, i)
            self.pulsanti.append(b)
            lay.addWidget(b)

        lay.addStretch(1)

        # piede: saldo totale allineato al testo delle voci di navigazione
        self.separatore_barra = separatore()
        lay.addWidget(self.separatore_barra)
        self.riquadro_saldo = QWidget()
        self.riquadro_saldo.setObjectName("PiedeBarra")
        piede = QVBoxLayout(self.riquadro_saldo)
        piede.setContentsMargins(14, 10, 14, 2)
        piede.setSpacing(1)
        self.et_saldo_nota = QLabel("SALDO TOTALE")
        self.et_saldo_nota.setObjectName("EtichettaScheda")
        self.et_saldo = QLabel("—")
        self.et_saldo.setObjectName("SaldoBarra")
        piede.addWidget(self.et_saldo_nota)
        piede.addWidget(self.et_saldo)
        lay.addWidget(self.riquadro_saldo)

        self.barra_chiusa = self.db.leggi("barra_chiusa", "0") == "1"
        self._disegna_barra()
        return self.barra

    # --------------------------------------------------- apertura e chiusura
    def _disegna_barra(self, applica_larghezza: bool = True) -> None:
        """Adatta i contenuti della barra allo stato aperto o chiuso.

        Con `applica_larghezza` la dimensione è impostata subito; durante la
        commutazione se ne occupa invece l'animazione.
        """
        chiusa = self.barra_chiusa
        if applica_larghezza:
            self.barra.setFixedWidth(LARGHEZZA_CHIUSA if chiusa else LARGHEZZA_APERTA)
        self.b_menu.setVisible(not chiusa)
        self.b_logo.setVisible(chiusa)
        # da chiusa la testata non ha margini: il simbolo resta sull'asse
        self.lay_testa.setContentsMargins(*((0, 0, 0, 0) if chiusa else (6, 0, 0, 0)))
        self.testata.setFixedHeight(44 if chiusa else 40)
        # da chiusa lo spazio a sinistra si espande: il simbolo resta al centro
        self.spazio_testa.changeSize(
            0, 0, QSizePolicy.Expanding if chiusa else QSizePolicy.Fixed,
            QSizePolicy.Minimum)
        self.lay_testa.invalidate()
        self.et_logo.setVisible(not chiusa)
        self.et_saldo_nota.setVisible(not chiusa)
        self.separatore_barra.setVisible(True)
        self.riquadro_saldo.layout().setContentsMargins(
            *((0, 10, 0, 2) if chiusa else (14, 10, 14, 2)))
        self.lay_barra.setContentsMargins(*((8, 14, 8, 16) if chiusa
                                            else (12, 14, 12, 14)))
        self.lay_barra.setSpacing(5 if chiusa else 6)
        self.b_menu.setFixedSize(34, 32)
        for b in self.pulsanti:
            if chiusa:
                b.setFixedSize(46, 44)
            else:
                b.setMinimumSize(0, 0)
                b.setMaximumSize(16777215, 16777215)

        for (nome_icona, classe), b in zip(VISTE, self.pulsanti):
            b.setText("" if chiusa else f"   {classe.titolo}")
            b.setToolTip(classe.titolo if chiusa else "")
            b.setProperty("compatta", "si" if chiusa else "no")
            b.style().unpolish(b)
            b.style().polish(b)
        self._aggiorna_stato()

    def commuta_barra(self) -> None:
        self.barra_chiusa = not self.barra_chiusa
        self.db.imposta("barra_chiusa", "1" if self.barra_chiusa else "0")
        destinazione = LARGHEZZA_CHIUSA if self.barra_chiusa else LARGHEZZA_APERTA
        self._disegna_barra(applica_larghezza=False)
        self.animazione = QPropertyAnimation(self.barra, b"minimumWidth", self)
        self.animazione.setDuration(170)
        self.animazione.setStartValue(self.barra.width())
        self.animazione.setEndValue(destinazione)
        self.animazione.setEasingCurve(QEasingCurve.InOutCubic)
        self.animazione.valueChanged.connect(
            lambda valore: self.barra.setFixedWidth(int(valore)))
        self.animazione.start()

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
        self.azioni_vista = QHBoxLayout()
        self.azioni_vista.setSpacing(8)
        testa.addLayout(self.azioni_vista)
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
        QShortcut(QKeySequence("Ctrl+B"), self, self.commuta_barra)
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)
        for i in range(len(VISTE)):
            QShortcut(QKeySequence(f"Ctrl+{i+1}"), self, lambda idx=i: self.vai(idx))

    # ---------------------------------------------------------------- azioni
    def vai(self, indice: int) -> None:
        self.pila.setCurrentIndex(indice)
        self.pulsanti[indice].setChecked(True)
        vista = self.viste[indice]
        self._comandi_vista(vista)
        self.et_titolo.setText(vista.titolo)
        self.et_sottotitolo.setText(vista.sottotitolo)
        self.b_rapido.setVisible(not isinstance(vista, VistaImpostazioni))
        vista.aggiorna()

    def _comandi_vista(self, vista) -> None:
        """Mostra in alto a destra i comandi propri della vista attiva."""
        while self.azioni_vista.count():
            elemento = self.azioni_vista.takeAt(0)
            widget = elemento.widget()
            if widget is not None:
                widget.setParent(None)
        for widget in getattr(vista, "azioni_intestazione", []):
            self.azioni_vista.addWidget(widget)
            widget.show()

    def nuovo_movimento(self) -> None:
        vista_mov = self.viste[1]
        vista_mov.nuovo()

    def ricarica(self) -> None:
        self.viste[self.pila.currentIndex()].aggiorna()
        self._aggiorna_stato()

    def _aggiorna_stato(self) -> None:
        v = self.db.leggi("valuta", "€")
        saldo = self.db.saldo_totale()
        if getattr(self, "barra_chiusa", False):
            self.et_saldo.setText(compatto(saldo))
            self.et_saldo.setAlignment(Qt.AlignCenter)
            self.et_saldo.setToolTip(f"Saldo totale: {euro(saldo, v)}")
            colore = self.c["entrata"] if saldo >= 0 else self.c["uscita"]
            self.et_saldo.setStyleSheet(
                f"color: {colore}; font-size: 12px; font-weight: 700;")
            self.et_saldo.setVisible(True)
        else:
            self.et_saldo.setText(euro(saldo, v))
            self.et_saldo.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.et_saldo.setToolTip("")
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

    def _aggiorna_icone(self) -> None:
        """Ridisegna le icone con i colori del tema e lo stile scelti."""
        stile = self.db.leggi("stile_icone", STILE_PREDEFINITO)
        self.b_menu.setIcon(icona_menu(self.c["testo2"], True, stile=stile))
        for (nome_icona, _), b in zip(VISTE, self.pulsanti):
            b.setIcon(icona(nome_icona, self.c["testo2"], "#ffffff", stile=stile))
        self.b_menu.setIcon(icona_menu(self.c["testo2"], True, stile=stile))

    def applica_tema(self, nome: str) -> None:
        self.c = colori(nome, self.db.leggi("accento", ACCENTO_PREDEFINITO))
        scala = SCALE.get(self.db.leggi("scala", "normale"), 1.0)
        app = QApplication.instance()
        if app is not None:
            app.setPalette(self._palette(self.c))
        self.setStyleSheet(foglio_stile(self.c, scala, frecce_spin(
            os.path.join(DATA_DIR, "cache"), self.c["testo2"])))
        if hasattr(self, "pulsanti"):
            self._aggiorna_icone()
        for vista in self.viste:
            vista.aggiorna_tema(self.c)
        self._aggiorna_stato()

    def closeEvent(self, ev) -> None:
        self.db.chiudi()
        super().closeEvent(ev)

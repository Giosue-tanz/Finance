"""Creazione delle categorie: logica condivisa e comandi riutilizzabili.

La stessa barra di composizione serve sia alla pagina Impostazioni sia al
dialogo che si apre mentre si registra un movimento, così una categoria si può
creare ovunque serva senza cambiare pagina.
"""
from __future__ import annotations

from PySide6.QtCore import QEasingCurve, Qt, QVariantAnimation, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QButtonGroup, QColorDialog, QDialog, QFrame,
                               QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QVBoxLayout, QWidget)

from .icone import ICONA_PREDEFINITA, SelettoreIcona, icona_suggerita
from .tema import PALETTE_GRAFICI, colori as colori_tema

ALTEZZA = 38


def colore_libero(db) -> str:
    """Primo colore della tavolozza non ancora usato; esaurita, ne genera uno."""
    usati = {r["colore"].lower() for r in db.query("SELECT colore FROM categorie")}
    for colore in PALETTE_GRAFICI:
        if colore.lower() not in usati:
            return colore
    for passo in range(len(usati) + 1):
        tinta = QColor.fromHsv((passo * 47) % 360, 150, 215).name()
        if tinta.lower() not in usati:
            return tinta
    return PALETTE_GRAFICI[len(usati) % len(PALETTE_GRAFICI)]


def esiste(db, nome: str, tipo: str) -> bool:
    return bool(db.query("SELECT id FROM categorie WHERE nome=? AND tipo=?",
                         (nome, tipo)))


def crea(db, nome: str, tipo: str, icona: str = "", colore: str = "") -> str:
    """Inserisce la categoria e restituisce l'icona assegnata."""
    icona = icona or icona_suggerita(nome, tipo)
    db.esegui("INSERT INTO categorie(nome, tipo, colore, icona) VALUES(?,?,?,?)",
              (nome, tipo, colore or colore_libero(db), icona))
    return icona


class SceltaTipo(QWidget):
    """Scelta fra uscita ed entrata: due tasti normali che cambiano colore.

    L'aspetto resta quello dei pulsanti dell'applicazione: a cambiare sono solo
    il colore del testo e del bordo, che virano al rosso delle uscite o al verde
    delle entrate quando l'opzione è scelta.
    """

    cambiato = Signal(str)
    DURATA = 200
    OPZIONI = (("uscita", "Uscita"), ("entrata", "Entrata"))

    def __init__(self, tipo: str = "uscita", colori: dict | None = None, parent=None):
        super().__init__(parent)
        self.c = colori or colori_tema()
        self.setFixedHeight(ALTEZZA)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(7)
        self.gruppo = QButtonGroup(self)
        self.bottoni: list[QPushButton] = []
        for i, (chiave, etichetta) in enumerate(self.OPZIONI):
            b = QPushButton(etichetta)
            b.setObjectName("TastoTipo")
            b.setCheckable(True)
            b.setChecked(chiave == tipo)
            b.setMinimumWidth(96)
            b.setFixedHeight(ALTEZZA)
            b.setCursor(Qt.PointingHandCursor)
            self.gruppo.addButton(b, i)
            self.bottoni.append(b)
            lay.addWidget(b, 1)

        self._avanzamento = 0.0 if tipo == "uscita" else 1.0
        self._animazione = QVariantAnimation(self)
        self._animazione.setDuration(self.DURATA)
        self._animazione.setEasingCurve(QEasingCurve.OutCubic)
        self._animazione.valueChanged.connect(self._fotogramma)
        self.gruppo.idClicked.connect(self._scelto)
        self._ridisegna()

    # ------------------------------------------------------------- aspetto
    def _ridisegna(self) -> None:
        """Solo testo e bordo virano verso la tinta dell'opzione scelta.

        Lo sfondo non viene toccato: i tasti restano quelli standard
        dell'applicazione e la selezione si legge dal colore.
        """
        for i, (chiave, _etichetta) in enumerate(self.OPZIONI):
            peso = self._avanzamento if i else 1.0 - self._avanzamento
            tinta = QColor(self.c[chiave])
            spento = QColor(self.c["testo2"])
            neutro = QColor(self.c["bordo"])
            misto = lambda a, b: int(round(a + (b - a) * peso))
            testo = QColor(misto(spento.red(), tinta.red()),
                           misto(spento.green(), tinta.green()),
                           misto(spento.blue(), tinta.blue()))
            bordo = QColor(misto(neutro.red(), tinta.red()),
                           misto(neutro.green(), tinta.green()),
                           misto(neutro.blue(), tinta.blue()))
            self.bottoni[i].setStyleSheet(
                f"border: 1px solid {bordo.name()};"
                f"color: {testo.name()};"
                f"font-weight: {600 if peso > 0.5 else 500};")


    def _fotogramma(self, avanzamento: float) -> None:
        self._avanzamento = float(avanzamento)
        self._ridisegna()

    def aggiorna_tema(self, colori: dict) -> None:
        self.c = colori
        self._ridisegna()

    # --------------------------------------------------------------- stato
    def _scelto(self, indice: int) -> None:
        self._anima_verso(float(indice))
        self.cambiato.emit(self.tipo())

    def _anima_verso(self, destinazione: float) -> None:
        if abs(destinazione - self._avanzamento) < 0.001:
            return
        self._animazione.stop()
        self._animazione.setStartValue(self._avanzamento)
        self._animazione.setEndValue(destinazione)
        self._animazione.start()

    def tipo(self) -> str:
        return "uscita" if self.gruppo.checkedId() == 0 else "entrata"

    def imposta_tipo(self, tipo: str) -> None:
        indice = 0 if tipo == "uscita" else 1
        self.gruppo.button(indice).setChecked(True)
        self._anima_verso(float(indice))


class BarraNuovaCategoria(QFrame):
    """Riga unica: icona, nome, tipo, colore e conferma dentro una sola cornice."""

    creata = Signal(str, str)          # nome, tipo
    rifiutata = Signal(str)            # motivo da mostrare all'utente

    def __init__(self, db, tipo: str = "uscita", testo_conferma: str = "Aggiungi",
                 colori: dict | None = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.c = colori or colori_tema()
        self.setObjectName("Compositore")
        self._icona = ICONA_PREDEFINITA
        self._icona_scelta = False
        self._colore = colore_libero(db)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(8)

        self.b_icona = QPushButton(self._icona)
        self.b_icona.setObjectName("IconaCompositore")
        self.b_icona.setFixedSize(ALTEZZA + 8, ALTEZZA)
        self.b_icona.setCursor(Qt.PointingHandCursor)
        self.b_icona.setToolTip("L'icona segue il nome: clic per sceglierla fra 174")
        self.b_icona.clicked.connect(self._scegli_icona)

        self.nome = QLineEdit()
        self.nome.setObjectName("CampoCompositore")
        self.nome.setPlaceholderText("Nome della categoria")
        self.nome.setMinimumHeight(ALTEZZA)
        self.nome.textEdited.connect(self._nome_cambiato)
        self.nome.returnPressed.connect(self.conferma)

        separatore = QFrame()
        separatore.setObjectName("DivisoreCompositore")
        separatore.setFixedWidth(1)
        separatore.setFixedHeight(ALTEZZA - 8)

        self.scelta = SceltaTipo(tipo, self.c)
        self.scelta.cambiato.connect(lambda _: self._aggiorna())

        self.b_colore = QPushButton()
        self.b_colore.setObjectName("ColoreCompositore")
        self.b_colore.setFixedSize(ALTEZZA, ALTEZZA)
        self.b_colore.setCursor(Qt.PointingHandCursor)
        self.b_colore.setToolTip("Colore nei grafici: clic per cambiarlo")
        self.b_colore.clicked.connect(self._scegli_colore)

        self.b_conferma = QPushButton(testo_conferma)
        self.b_conferma.setObjectName("Primario")
        self.b_conferma.setFixedHeight(ALTEZZA)
        self.b_conferma.setMinimumWidth(124)
        self.b_conferma.setCursor(Qt.PointingHandCursor)
        self.b_conferma.clicked.connect(self.conferma)

        lay.addWidget(self.b_icona)
        lay.addWidget(self.nome, 1)
        lay.addWidget(separatore)
        lay.addWidget(self.scelta)
        lay.addWidget(self.b_colore)
        lay.addWidget(self.b_conferma)
        self._aggiorna()

    # ------------------------------------------------------------- contenuto
    def tipo(self) -> str:
        return self.scelta.tipo()

    def imposta_tipo(self, tipo: str) -> None:
        self.scelta.imposta_tipo(tipo)
        self._aggiorna()

    def _nome_cambiato(self, testo: str) -> None:
        if not self._icona_scelta:
            self._icona = icona_suggerita(testo, self.tipo())
        self._aggiorna()

    def _scegli_icona(self) -> None:
        dlg = SelettoreIcona(self._icona, self)
        if dlg.exec():
            self._icona = dlg.scelta
            self._icona_scelta = True
            self._aggiorna()

    def _scegli_colore(self) -> None:
        colore = QColorDialog.getColor(QColor(self._colore), self,
                                       "Colore della categoria")
        if colore.isValid():
            self._colore = colore.name()
            self._aggiorna()

    def _aggiorna(self) -> None:
        if not self._icona_scelta:
            self._icona = icona_suggerita(self.nome.text(), self.tipo())
        self.b_icona.setText(self._icona)
        self.b_colore.setStyleSheet(
            f"background: {self._colore}; border: none; border-radius: 9px;")

    # -------------------------------------------------------------- conferma
    def conferma(self) -> None:
        nome = self.nome.text().strip()
        if not nome:
            self.rifiutata.emit("Scrivi il nome della categoria da aggiungere.")
            self.nome.setFocus()
            return
        tipo = self.tipo()
        if esiste(self.db, nome, tipo):
            self.rifiutata.emit(f"La categoria «{nome}» esiste già fra le {tipo}.")
            return
        crea(self.db, nome, tipo, self._icona, self._colore)
        self.creata.emit(nome, tipo)
        self.azzera()

    def aggiorna_tema(self, colori: dict) -> None:
        """Il selettore usa colori inline: vanno rinfrescati col tema."""
        self.c = colori
        self.scelta.aggiorna_tema(colori)

    def azzera(self) -> None:
        """Pronta per la categoria successiva."""
        self.nome.clear()
        self._icona_scelta = False
        self._colore = colore_libero(self.db)
        self._aggiorna()
        self.nome.setFocus()


class DialogoNuovaCategoria(QDialog):
    """Creazione al volo mentre si registra un movimento."""

    def __init__(self, db, tipo: str = "uscita", nome_iniziale: str = "",
                 colori: dict | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuova categoria")
        self.setMinimumWidth(560)
        self.nome_creato = ""

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(10)

        self.barra = BarraNuovaCategoria(db, tipo, "Crea", colori, self)
        self.barra.nome.setText(nome_iniziale)
        self.barra._nome_cambiato(nome_iniziale)
        self.barra.creata.connect(self._creata)
        self.barra.rifiutata.connect(self._errore)
        lay.addWidget(self.barra)

        self.et_errore = QLabel("")
        self.et_errore.setObjectName("NotaScheda")
        lay.addWidget(self.et_errore)

        annulla = QPushButton("Annulla")
        annulla.clicked.connect(self.reject)
        lay.addWidget(annulla, 0, Qt.AlignRight)
        self.barra.nome.setFocus()

    def _creata(self, nome: str, _tipo: str) -> None:
        self.nome_creato = nome
        self.accept()

    def _errore(self, messaggio: str) -> None:
        self.et_errore.setText(messaggio)

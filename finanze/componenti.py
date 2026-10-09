"""Componenti riutilizzabili dell'interfaccia."""
from __future__ import annotations

from PySide6.QtCore import QDate, QEvent, QModelIndex, QObject, Qt
from PySide6.QtGui import QFont, QFontMetrics, QKeySequence, QShortcut
from PySide6.QtWidgets import (QComboBox, QDateEdit, QDialog, QDialogButtonBox,
                               QDoubleSpinBox, QFormLayout, QFrame, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QSizePolicy,
                               QSpinBox, QVBoxLayout, QWidget)

from .grafici import Sparkline
from .icone import etichetta_categoria, solo_nome
from .utils import euro


class Scheda(QFrame):
    """Pannello arrotondato con titolo opzionale."""

    def __init__(self, titolo: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("Scheda")
        self.layout_v = QVBoxLayout(self)
        self.layout_v.setContentsMargins(16, 14, 16, 14)
        self.layout_v.setSpacing(10)
        if titolo:
            et = QLabel(titolo)
            et.setObjectName("Sezione")
            self.layout_v.addWidget(et)
            self.etichetta_titolo = et

    def aggiungi(self, widget: QWidget, stiramento: int = 0) -> QWidget:
        self.layout_v.addWidget(widget, stiramento)
        return widget

    def aggiungi_layout(self, layout) -> None:
        self.layout_v.addLayout(layout)


class ContenutoStat(QWidget):
    """Valore grande, nota e sparkline: testi che si adattano allo spazio."""

    def __init__(self, colori: dict, colore_valore: str | None = None, parent=None):
        super().__init__(parent)
        self.c = colori
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(3)
        self.colore_valore = colore_valore or colori["testo"]
        self.valore = QLabel("—")
        self.valore.setObjectName("ValoreScheda")
        self.nota = QLabel("")
        self.nota.setObjectName("NotaScheda")
        self.nota.setWordWrap(True)
        self.spark = Sparkline(colori)
        self.spark.colore = colore_valore or colori["accento"]
        for w in (self.valore, self.nota, self.spark):
            lay.addWidget(w)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def imposta(self, valore: float | str, nota: str = "", valuta: str = "€",
                serie: list[float] | None = None) -> None:
        self.valore.setText(euro(valore, valuta) if isinstance(valore, (int, float))
                            else str(valore))
        self.nota.setText(nota)
        if serie is not None:
            self.spark.imposta_dati(serie)
        self.adatta_dimensioni(self.size())

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self.adatta_dimensioni(ev.size())

    def adatta_dimensioni(self, dimensione) -> None:
        """Il valore cresce con la scheda e si restringe se il testo non entra.

        La misura si applica con uno stile sul widget: il foglio di stile globale
        fissa i px e avrebbe la meglio su un semplice setFont().
        """
        larghezza = max(80, dimensione.width())
        altezza = max(50, dimensione.height())
        px = int(max(15, min(42, min(larghezza / 7.2, altezza / 2.6))))
        prova = QFont(self.valore.font())
        prova.setBold(True)
        prova.setPixelSize(px)
        while px > 13 and QFontMetrics(prova).horizontalAdvance(
                self.valore.text()) > larghezza - 6:
            px -= 1
            prova.setPixelSize(px)
        self.valore.setStyleSheet(
            f"color: {self.colore_valore}; font-size: {px}px; font-weight: 700;")
        self.px_valore = px

        self.nota.setStyleSheet(f"color: {self.c['testo2']}; "
                                f"font-size: {max(10, min(14, int(px * 0.4)))}px;")
        self.nota.setVisible(altezza > 50)
        self.spark.setVisible(altezza > 95)
        self.spark.setFixedHeight(max(18, min(46, int(altezza * 0.22))))


class SchedaStat(Scheda):
    """Scheda con etichetta, valore grande, nota e sparkline."""

    def __init__(self, etichetta: str, colori: dict, colore_valore: str | None = None,
                 parent=None):
        super().__init__(parent=parent)
        self.c = colori
        self.layout_v.setSpacing(4)
        self.et = QLabel(etichetta.upper())
        self.et.setObjectName("EtichettaScheda")
        self.contenuto = ContenutoStat(colori, colore_valore)
        self.valore = self.contenuto.valore
        self.nota = self.contenuto.nota
        self.spark = self.contenuto.spark
        self.layout_v.addWidget(self.et)
        self.layout_v.addWidget(self.contenuto, 1)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(118)

    def imposta(self, valore: float | str, nota: str = "", valuta: str = "€",
                serie: list[float] | None = None) -> None:
        self.contenuto.imposta(valore, nota, valuta, serie)


def riga(*widgets, spaziatura: int = 10) -> QHBoxLayout:
    lay = QHBoxLayout()
    lay.setSpacing(spaziatura)
    for w in widgets:
        if w is None:
            lay.addStretch(1)
        elif isinstance(w, QWidget):
            lay.addWidget(w)
        else:
            lay.addLayout(w)
    return lay


def separatore() -> QFrame:
    f = QFrame()
    f.setObjectName("Separatore")
    f.setFrameShape(QFrame.HLine)
    return f


def etichetta(testo: str, oggetto: str = "") -> QLabel:
    e = QLabel(testo)
    if oggetto:
        e.setObjectName(oggetto)
    return e


class _Deselezionatore(QObject):
    """Annulla la selezione quando si clicca in un punto vuoto della tabella."""

    def eventFilter(self, oggetto, evento):
        if evento.type() == QEvent.MouseButtonPress:
            tabella = oggetto.parent()
            if tabella is not None and not tabella.indexAt(
                    evento.position().toPoint()).isValid():
                tabella.clearSelection()
                tabella.setCurrentIndex(QModelIndex())
        return False


def abilita_deselezione(*tabelle) -> None:
    """Clic nello spazio vuoto (o Esc) per togliere la selezione."""
    for tabella in tabelle:
        filtro = _Deselezionatore(tabella)
        tabella._filtro_deselezione = filtro        # evita la raccolta rifiuti
        tabella.viewport().installEventFilter(filtro)
        scorciatoia = QShortcut(QKeySequence(Qt.Key_Escape), tabella)
        scorciatoia.setContext(Qt.WidgetWithChildrenShortcut)
        scorciatoia.activated.connect(tabella.clearSelection)


class DialogoMovimento(QDialog):
    """Finestra di inserimento/modifica di un movimento."""

    def __init__(self, db, categorie_entrata, categorie_uscita, conti,
                 movimento=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.icone = db.icone_categorie()
        self.movimento = dict(movimento) if movimento else None
        self.cat_entrata = categorie_entrata
        self.cat_uscita = categorie_uscita
        self.setWindowTitle("Modifica movimento" if movimento else "Nuovo movimento")
        self.setMinimumWidth(430)

        self.tipo = QComboBox(); self.tipo.addItems(["uscita", "entrata"])
        self.data = QDateEdit(QDate.currentDate())
        self.data.setCalendarPopup(True)
        self.data.setDisplayFormat("dd/MM/yyyy")
        self.importo = QDoubleSpinBox()
        self.importo.setRange(0.0, 99_999_999.0)
        self.importo.setDecimals(2)
        self.importo.setSingleStep(10.0)
        self.importo.setSuffix(f" {db.leggi('valuta', '€')}")
        self.categoria = QComboBox(); self.categoria.setEditable(True)
        self.b_nuova_categoria = QPushButton("+")
        self.b_nuova_categoria.setObjectName("AggiungiAccanto")
        self.b_nuova_categoria.setFixedWidth(34)
        self.b_nuova_categoria.setToolTip("Crea una nuova categoria")
        self.b_nuova_categoria.clicked.connect(self._nuova_categoria)
        blocco_categoria = QWidget()
        fila_categoria = QHBoxLayout(blocco_categoria)
        fila_categoria.setContentsMargins(0, 0, 0, 0)
        fila_categoria.setSpacing(6)
        fila_categoria.addWidget(self.categoria, 1)
        fila_categoria.addWidget(self.b_nuova_categoria)
        self.conto = QComboBox(); self.conto.addItems(conti)
        self.descrizione = QLineEdit()
        self.descrizione.setPlaceholderText("es. Spesa settimanale")
        self.etichette = QLineEdit()
        self.etichette.setPlaceholderText("etichette separate da virgola (opzionale)")

        modulo = QFormLayout()
        modulo.setSpacing(10)
        modulo.addRow("Tipo", self.tipo)
        modulo.addRow("Data", self.data)
        modulo.addRow("Importo", self.importo)
        modulo.addRow("Categoria", blocco_categoria)
        modulo.addRow("Conto", self.conto)
        modulo.addRow("Descrizione", self.descrizione)
        modulo.addRow("Etichette", self.etichette)

        bottoni = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        bottoni.button(QDialogButtonBox.Save).setText("Salva")
        bottoni.button(QDialogButtonBox.Save).setObjectName("Primario")
        bottoni.button(QDialogButtonBox.Cancel).setText("Annulla")
        bottoni.accepted.connect(self.accept)
        bottoni.rejected.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 18, 18, 14)
        lay.addLayout(modulo)
        lay.addWidget(bottoni)

        self.tipo.currentTextChanged.connect(self._aggiorna_categorie)
        self._aggiorna_categorie(self.tipo.currentText())

        if self.movimento:
            m = self.movimento
            self.tipo.setCurrentText(m["tipo"])
            self._aggiorna_categorie(m["tipo"])
            a, me, g = (int(x) for x in m["data"].split("-"))
            self.data.setDate(QDate(a, me, g))
            self.importo.setValue(float(m["importo"]))
            idx = self.categoria.findData(m["categoria"])
            if idx >= 0:
                self.categoria.setCurrentIndex(idx)
            else:
                self.categoria.setCurrentText(m["categoria"])
            self.conto.setCurrentText(m["conto"])
            self.descrizione.setText(m["descrizione"])
            self.etichette.setText(m["etichette"])

    def _nuova_categoria(self) -> None:
        """Crea la categoria al volo e la seleziona, senza chiudere il dialogo."""
        from .categorie import DialogoNuovaCategoria

        tipo = self.tipo.currentText()
        scritto = solo_nome(self.categoria.currentText()).strip()
        gia_presente = any(scritto == self.categoria.itemData(i)
                           for i in range(self.categoria.count()))
        dlg = DialogoNuovaCategoria(self.db, tipo,
                                    "" if gia_presente else scritto, parent=self)
        if not dlg.exec() or not dlg.nome_creato:
            return
        elenco = self.cat_entrata if tipo == "entrata" else self.cat_uscita
        if dlg.nome_creato not in elenco:
            elenco.append(dlg.nome_creato)
            elenco.sort()
        self.icone = self.db.icone_categorie()
        self._aggiorna_categorie(tipo)
        indice = self.categoria.findData(dlg.nome_creato)
        if indice >= 0:
            self.categoria.setCurrentIndex(indice)

    def _aggiorna_categorie(self, tipo: str) -> None:
        corrente = self.categoria.currentData() or solo_nome(self.categoria.currentText())
        self.categoria.clear()
        for nome in (self.cat_entrata if tipo == "entrata" else self.cat_uscita):
            self.categoria.addItem(etichetta_categoria(nome, self.icone.get(nome)), nome)
        if corrente:
            idx = self.categoria.findData(corrente)
            if idx >= 0:
                self.categoria.setCurrentIndex(idx)

    def dati(self) -> dict:
        return {
            "id": self.movimento["id"] if self.movimento else None,
            "data": self.data.date().toString("yyyy-MM-dd"),
            "tipo": self.tipo.currentText(),
            "importo": self.importo.value(),
            "categoria": (self.categoria.currentData()
                          if self.categoria.currentData()
                          and self.categoria.currentText() ==
                          etichetta_categoria(self.categoria.currentData(),
                                              self.icone.get(self.categoria.currentData()))
                          else solo_nome(self.categoria.currentText())) or "Altro",
            "conto": self.conto.currentText().strip() or "Principale",
            "descrizione": self.descrizione.text().strip(),
            "etichette": self.etichette.text().strip(),
        }

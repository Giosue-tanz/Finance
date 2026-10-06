"""Componenti riutilizzabili dell'interfaccia."""
from __future__ import annotations

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (QComboBox, QDateEdit, QDialog, QDialogButtonBox,
                               QDoubleSpinBox, QFormLayout, QFrame, QHBoxLayout,
                               QLabel, QLineEdit, QSizePolicy, QSpinBox,
                               QVBoxLayout, QWidget)

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


class SchedaStat(Scheda):
    """Scheda con etichetta, valore grande, nota e sparkline."""

    def __init__(self, etichetta: str, colori: dict, colore_valore: str | None = None,
                 parent=None):
        super().__init__(parent=parent)
        self.c = colori
        self.layout_v.setSpacing(4)
        self.et = QLabel(etichetta.upper())
        self.et.setObjectName("EtichettaScheda")
        self.valore = QLabel("—")
        self.valore.setObjectName("ValoreScheda")
        if colore_valore:
            self.valore.setStyleSheet(f"color: {colore_valore};")
        self.nota = QLabel("")
        self.nota.setObjectName("NotaScheda")
        self.spark = Sparkline(colori)
        self.spark.colore = colore_valore or colori["accento"]
        for w in (self.et, self.valore, self.nota, self.spark):
            self.layout_v.addWidget(w)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def imposta(self, valore: float | str, nota: str = "", valuta: str = "€",
                serie: list[float] | None = None) -> None:
        self.valore.setText(euro(valore, valuta) if isinstance(valore, (int, float))
                            else str(valore))
        self.nota.setText(nota)
        if serie is not None:
            self.spark.imposta_dati(serie)


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
        modulo.addRow("Categoria", self.categoria)
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

"""Viste modulari dell'applicazione.

Ogni vista è un QWidget indipendente che riceve il database e la palette,
espone il metodo `aggiorna()` e segnala le modifiche con `dati_cambiati`.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QScrollArea, QVBoxLayout, QWidget


class VistaBase(QWidget):
    dati_cambiati = Signal()

    titolo = "Vista"
    sottotitolo = ""

    def __init__(self, db, colori: dict, parent=None):
        super().__init__(parent)
        self.db = db
        self.c = colori
        self.grafici: list = []
        self.costruisci()

    # da sovrascrivere
    def costruisci(self) -> None:
        ...

    def aggiorna(self) -> None:
        ...

    def aggiorna_tema(self, colori: dict) -> None:
        self.c = colori
        for g in self.grafici:
            if hasattr(g, "aggiorna_tema"):
                g.aggiorna_tema(colori)
        self.aggiorna()

    @property
    def valuta(self) -> str:
        return self.db.leggi("valuta", "€")

    def area_scorrevole(self) -> tuple[QScrollArea, QVBoxLayout]:
        """Contenitore verticale scorrevole pronto all'uso."""
        esterno = QVBoxLayout(self)
        esterno.setContentsMargins(0, 0, 0, 0)
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QScrollArea.NoFrame)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        interno = QWidget()
        lay = QVBoxLayout(interno)
        lay.setContentsMargins(2, 2, 6, 10)
        lay.setSpacing(14)
        area.setWidget(interno)
        esterno.addWidget(area)
        return area, lay

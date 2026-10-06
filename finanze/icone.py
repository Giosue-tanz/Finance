"""Catalogo delle icone per le categorie e selettore grafico.

Le icone sono emoji: nessun file da distribuire, nessuna dipendenza, rese a
colori dal sistema. Ogni categoria ne conserva una nel database.
"""
from __future__ import annotations

import re

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (QDialog, QGridLayout, QLabel, QLineEdit,
                               QPushButton, QToolButton, QVBoxLayout, QWidget)

ICONA_PREDEFINITA = "🏷️"

GRUPPI: dict[str, list[str]] = {
    "Denaro": ["💰", "💶", "💵", "💳", "🏦", "🪙", "📈", "📉", "💸", "🧾"],
    "Casa": ["🏠", "🛋", "🔑", "🛏", "🧹", "🪴", "🔨", "🧺"],
    "Spesa e cibo": ["🛒", "🍽", "☕", "🍕", "🥖", "🍎", "🍻", "🥗"],
    "Trasporti": ["🚗", "⛽", "🚌", "🚆", "🚲", "✈", "🛵", "🅿"],
    "Bollette": ["💡", "🔥", "💧", "📱", "🌐", "📺", "📶", "♻"],
    "Salute": ["🏥", "💊", "🦷", "👓", "🧘", "🩺", "🏋", "🧴"],
    "Tempo libero": ["🎮", "🎬", "🎵", "🎟", "🏖", "⚽", "📷", "🎨"],
    "Persona": ["👕", "💇", "🎁", "🐾", "📚", "🎓", "🧒", "💌"],
    "Lavoro": ["💼", "🏢", "🛠", "📦", "🖥", "✉", "📋", "⚖"],
    "Varie": ["⭐", "🏷", "🔖", "❓", "🌍", "🎯", "🧩", "🔔"],
}

# Icona suggerita in base al nome digitato: evita di doverla scegliere ogni volta.
SUGGERIMENTI: list[tuple[tuple[str, ...], str]] = [
    (("stipend", "salar", "busta paga"), "💼"),
    (("rimbors", "cashback", "storno"), "💸"),
    (("investim", "azion", "etf", "borsa", "dividend"), "📈"),
    (("affitt", "mutuo", "casa", "condomin"), "🏠"),
    (("spesa", "supermerc", "aliment", "cibo"), "🛒"),
    (("ristorant", "pizz", "cena", "pranzo"), "🍽"),
    (("caffè", "caffe", "bar", "colazion"), "☕"),
    (("benzin", "carburant", "diesel", "gasol"), "⛽"),
    (("auto", "macchina", "garage", "mecc"), "🚗"),
    (("treno", "bus", "metro", "trasport", "abbonamento mezzi"), "🚌"),
    (("aereo", "volo", "viagg", "vacanz", "hotel"), "✈"),
    (("bollett", "utenze"), "💡"),
    (("luce", "elettric", "energia"), "💡"),
    (("gas", "riscaldam", "caldaia"), "🔥"),
    (("acqua", "idric"), "💧"),
    (("telefon", "cellular", "sim", "ricarica"), "📱"),
    (("internet", "fibra", "wifi", "adsl"), "🌐"),
    (("netflix", "spotify", "abbonament", "streaming"), "📺"),
    (("medic", "farmac", "salute", "visita", "dottor"), "💊"),
    (("dentist",), "🦷"),
    (("occhial", "ottic"), "👓"),
    (("palestra", "sport", "fitness", "piscina"), "🏋"),
    (("tempo libero", "svago", "divertiment", "hobby", "uscite serali"), "🎬"),
    (("cinema", "teatro", "concert", "spettacol"), "🎬"),
    (("gioc", "videogioc", "console"), "🎮"),
    (("libr", "studi", "istruz", "universit", "scuola", "cors"), "📚"),
    (("vestit", "abbigliam", "scarp", "shopping"), "👕"),
    (("parrucchier", "estetis", "bellezza"), "💇"),
    (("regal", "compleann", "natal"), "🎁"),
    (("animal", "cane", "gatt", "veterinar"), "🐾"),
    (("tass", "iva", "f24", "imposte", "bollo"), "🧾"),
    (("assicuraz", "polizza"), "⚖"),
    (("risparm", "fondo", "accantonam"), "🏦"),
    (("banca", "commission", "conto"), "💳"),
    (("altro", "varie", "extra", "imprevist"), "🏷"),
]


def icona_suggerita(nome: str, tipo: str = "uscita") -> str:
    """Propone un'icona a partire dal nome della categoria.

    Il confronto parte da un confine di parola, così «etf» non viene trovato
    dentro «Netflix».
    """
    testo = (nome or "").strip().lower()
    for chiavi, icona in SUGGERIMENTI:
        if any(re.search(r"\b" + re.escape(k), testo) for k in chiavi):
            return icona
    return "💰" if tipo == "entrata" else ICONA_PREDEFINITA


def etichetta_categoria(nome: str, icona: str | None) -> str:
    """Nome preceduto dall'icona, se presente."""
    return f"{icona}  {nome}" if icona else nome


def solo_nome(etichetta: str) -> str:
    """Rimuove l'eventuale icona iniziale da un'etichetta di categoria."""
    testo = (etichetta or "").strip()
    for gruppo in GRUPPI.values():
        for icona in gruppo:
            if testo.startswith(icona):
                return testo[len(icona):].strip()
    return testo


class SelettoreIcona(QDialog):
    """Griglia di icone divise per argomento, con ricerca per nome categoria."""

    def __init__(self, corrente: str = ICONA_PREDEFINITA, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scegli un'icona")
        self.scelta = corrente
        self.setMinimumWidth(430)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        intestazione = QLabel("Clicca l'icona da assegnare alla categoria.")
        intestazione.setObjectName("NotaScheda")
        lay.addWidget(intestazione)

        for titolo, icone in GRUPPI.items():
            et = QLabel(titolo)
            et.setObjectName("EtichettaScheda")
            lay.addWidget(et)
            contenitore = QWidget()
            griglia = QGridLayout(contenitore)
            griglia.setContentsMargins(0, 0, 0, 0)
            griglia.setSpacing(6)
            for i, icona in enumerate(icone):
                b = QToolButton()
                b.setText(icona)
                b.setFixedSize(QSize(42, 38))
                b.setCheckable(True)
                b.setChecked(icona == corrente)
                b.setStyleSheet("font-size: 19px;")
                b.clicked.connect(lambda _=False, ic=icona: self._scegli(ic))
                griglia.addWidget(b, 0, i)
            lay.addWidget(contenitore)

        annulla = QPushButton("Annulla")
        annulla.clicked.connect(self.reject)
        lay.addWidget(annulla, 0, Qt.AlignRight)

    def _scegli(self, icona: str) -> None:
        self.scelta = icona
        self.accept()

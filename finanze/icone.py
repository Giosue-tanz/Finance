"""Catalogo delle icone per le categorie e selettore grafico.

Le icone sono emoji: nessun file da distribuire, nessuna dipendenza, rese a
colori dal sistema. Ogni categoria ne conserva una nel database.
"""
from __future__ import annotations

import re

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (QDialog, QGridLayout, QLabel, QLineEdit,
                               QPushButton, QScrollArea, QToolButton, QVBoxLayout,
                               QWidget)

ICONA_PREDEFINITA = "🏷️"

GRUPPI: dict[str, list[tuple[str, str]]] = {
    "Denaro": [
        ("💰", "denaro"), ("💶", "euro"), ("💵", "contanti"), ("💴", "yen"),
        ("💷", "sterline"), ("💳", "carta"), ("🏦", "banca"), ("🪙", "moneta"),
        ("📈", "investimenti"), ("📉", "perdita"), ("💸", "spesa"), ("🧾", "scontrino"),
        ("🏧", "bancomat"), ("💱", "cambio"), ("🤝", "prestito"), ("📊", "portafoglio"),
    ],
    "Casa": [
        ("🏠", "casa"), ("🏡", "villetta"), ("🏢", "condominio"), ("🛋", "arredamento"),
        ("🔑", "affitto"), ("🛏", "camera"), ("🧹", "pulizie"), ("🧺", "bucato"),
        ("🪴", "piante"), ("🔨", "lavori"), ("🪚", "fai da te"), ("🚪", "porta"),
        ("🪟", "finestre"), ("🧽", "detersivi"), ("🛁", "bagno"), ("🪑", "mobili"),
    ],
    "Spesa e cibo": [
        ("🛒", "spesa"), ("🍽", "ristorante"), ("☕", "caffè"), ("🍕", "pizza"),
        ("🥖", "panetteria"), ("🍎", "frutta"), ("🥦", "verdura"), ("🥗", "insalata"),
        ("🧀", "formaggi"), ("🥩", "carne"), ("🐟", "pesce"), ("🍰", "dolci"),
        ("🍺", "birra"), ("🍷", "vino"), ("🥤", "bevande"), ("🍫", "snack"),
        ("🥡", "asporto"), ("🍳", "colazione"),
    ],
    "Trasporti": [
        ("🚗", "auto"), ("⛽", "carburante"), ("🚌", "autobus"), ("🚆", "treno"),
        ("🚇", "metro"), ("🚲", "bicicletta"), ("🛵", "scooter"), ("🏍", "moto"),
        ("✈", "aereo"), ("🚕", "taxi"), ("🅿", "parcheggio"), ("🛻", "furgone"),
        ("🔧", "officina"), ("🛞", "gomme"), ("🚢", "traghetto"), ("🛴", "monopattino"),
    ],
    "Bollette e tecnologia": [
        ("💡", "luce"), ("🔥", "gas"), ("💧", "acqua"), ("📱", "telefono"),
        ("🌐", "internet"), ("📺", "televisione"), ("📶", "abbonamento"), ("♻", "rifiuti"),
        ("💻", "computer"), ("🖨", "stampante"), ("🎧", "audio"), ("🔌", "elettricità"),
        ("☁", "servizi online"), ("🖥", "monitor"), ("⌚", "orologio"), ("🔋", "ricarica"),
    ],
    "Salute e benessere": [
        ("🏥", "ospedale"), ("💊", "farmacia"), ("🩺", "visita"), ("🦷", "dentista"),
        ("👓", "ottico"), ("🧘", "benessere"), ("🏋", "palestra"), ("🧴", "cura"),
        ("💉", "vaccino"), ("🩹", "medicazioni"), ("🧠", "psicologo"), ("🦴", "fisioterapia"),
        ("🫀", "cardiologo"), ("🧬", "analisi"),
    ],
    "Tempo libero": [
        ("🎬", "cinema"), ("🎵", "musica"), ("🎮", "videogiochi"), ("🎟", "biglietti"),
        ("🏖", "mare"), ("⚽", "calcio"), ("🎨", "arte"), ("📷", "fotografia"),
        ("🎭", "teatro"), ("🎲", "giochi"), ("🎸", "concerti"), ("⛷", "montagna"),
        ("🏕", "campeggio"), ("🎳", "bowling"), ("🏊", "piscina"), ("🚴", "ciclismo"),
        ("📚", "libri"), ("🧩", "hobby"),
    ],
    "Viaggi": [
        ("🧳", "viaggio"), ("🏨", "hotel"), ("🗺", "escursioni"), ("🛫", "partenza"),
        ("🏝", "vacanza"), ("🚐", "camper"), ("🎡", "parchi"), ("🗽", "città"),
        ("⛱", "stabilimento"), ("🧭", "gite"),
    ],
    "Persona e famiglia": [
        ("👕", "abbigliamento"), ("👟", "scarpe"), ("💇", "parrucchiere"), ("💄", "bellezza"),
        ("🎁", "regali"), ("🧒", "figli"), ("👶", "neonato"), ("🐾", "animali"),
        ("🐕", "cane"), ("🐈", "gatto"), ("💌", "affetti"), ("🎂", "compleanni"),
        ("💍", "cerimonie"), ("👜", "accessori"), ("🧸", "giocattoli"), ("🕯", "cura di sé"),
    ],
    "Lavoro e studio": [
        ("💼", "stipendio"), ("🏢", "ufficio"), ("🛠", "attrezzi"), ("📦", "spedizioni"),
        ("🧑‍💻", "lavoro autonomo"), ("✉", "corrispondenza"), ("📋", "progetti"),
        ("⚖", "assicurazione"), ("🎓", "università"), ("📝", "corsi"),
        ("🖇", "cancelleria"), ("📠", "servizi"), ("🏭", "produzione"), ("🧑‍🏫", "formazione"),
    ],
    "Tasse e documenti": [
        ("🧾", "tasse"), ("🏛", "stato"), ("📜", "contratti"), ("🗂", "pratiche"),
        ("🔏", "bolli"), ("📄", "fatture"), ("⚠", "multe"), ("🪪", "documenti"),
    ],
    "Varie": [
        ("⭐", "preferiti"), ("🏷", "altro"), ("🔖", "etichetta"), ("❓", "da definire"),
        ("🌍", "generale"), ("🎯", "obiettivo"), ("🔔", "promemoria"), ("♦", "varie"),
        ("🧮", "conteggi"), ("🕰", "ricorrenze"), ("🔁", "ricorrente"), ("➕", "extra"),
    ],
}


def tutte_le_icone() -> list[tuple[str, str, str]]:
    """Elenco piatto di (icona, nome, gruppo)."""
    return [(ic, nome, gruppo) for gruppo, voci in GRUPPI.items()
            for ic, nome in voci]


def _insieme_icone() -> set[str]:
    return {ic for voci in GRUPPI.values() for ic, _ in voci}


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
    (("multa", "sanzion", "contravven"), "⚠"),
    (("pedagg", "autostrad", "telepass"), "🅿"),
    (("parchegg", "sosta"), "🅿"),
    (("asilo", "nido", "scuola materna", "babysitter"), "🧒"),
    (("rifiut", "spazzatura", "tari"), "♻"),
    (("condomin", "spese condominiali"), "🏢"),
    (("barbier", "barba"), "💇"),
    (("prelievo", "contanti", "bancomat"), "🏧"),
    (("software", "licenz", "hosting", "dominio"), "💻"),
    (("donazion", "beneficenz", "offerta"), "💌"),
    (("traghett", "nave", "crocier"), "🚢"),
    (("hotel", "albergo", "bnb", "soggiorno"), "🏨"),
    (("bagagl", "valigia"), "🧳"),
    (("cartoler", "cancelleri"), "🖇"),
    (("bollo", "revision"), "🪪"),
    (("mutuo", "rata casa"), "🏠"),
    (("banca", "commission", "conto"), "💳"),
    (("altro", "varie", "extra", "imprevist"), "🏷"),
]


def sinonimi() -> dict[str, str]:
    """Per ogni icona, le parole che la richiamano nei suggerimenti.

    Serve alla ricerca del catalogo: «benzina» deve trovare l'icona del
    carburante anche se il suo nome è un altro.
    """
    indice: dict[str, list[str]] = {}
    for chiavi, ic in SUGGERIMENTI:
        indice.setdefault(ic, []).extend(chiavi)
    return {ic: " ".join(parole) for ic, parole in indice.items()}


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
    for icona in _insieme_icone():
        if testo.startswith(icona):
            return testo[len(icona):].strip()
    return testo


class SelettoreIcona(QDialog):
    """Catalogo completo: gruppi, ricerca per nome e scelta con un clic."""

    COLONNE = 10

    def __init__(self, corrente: str = ICONA_PREDEFINITA, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scegli un'icona")
        self.scelta = corrente
        self.setMinimumSize(520, 520)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        self.cerca = QLineEdit()
        self.cerca.setPlaceholderText(
            f"Cerca fra {len(tutte_le_icone())} icone: casa, benzina, palestra…")
        self.cerca.setClearButtonEnabled(True)
        lay.addWidget(self.cerca)

        self.area = QScrollArea()
        self.area.setWidgetResizable(True)
        self.area.setFrameShape(QScrollArea.NoFrame)
        self.area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.contenuto = QWidget()
        self.lay_contenuto = QVBoxLayout(self.contenuto)
        self.lay_contenuto.setContentsMargins(0, 0, 6, 0)
        self.lay_contenuto.setSpacing(10)
        self.area.setWidget(self.contenuto)
        lay.addWidget(self.area, 1)

        self.et_vuoto = QLabel("Nessuna icona corrisponde alla ricerca.")
        self.et_vuoto.setObjectName("NotaScheda")
        self.et_vuoto.setAlignment(Qt.AlignCenter)
        self.et_vuoto.hide()
        lay.addWidget(self.et_vuoto)

        annulla = QPushButton("Annulla")
        annulla.clicked.connect(self.reject)
        lay.addWidget(annulla, 0, Qt.AlignRight)

        self.cerca.textChanged.connect(self._filtra)
        self._costruisci()
        self.cerca.setFocus()

    # ------------------------------------------------------------ contenuto
    def _costruisci(self) -> None:
        self.sezioni: list[dict] = []
        parole = sinonimi()
        for gruppo, voci in GRUPPI.items():
            titolo = QLabel(gruppo)
            titolo.setObjectName("EtichettaScheda")
            self.lay_contenuto.addWidget(titolo)

            contenitore = QWidget()
            griglia = QGridLayout(contenitore)
            griglia.setContentsMargins(0, 0, 0, 0)
            griglia.setSpacing(5)
            pulsanti = []
            for i, (ic, nome) in enumerate(voci):
                b = QToolButton()
                b.setText(ic)
                b.setToolTip(nome)
                b.setFixedSize(QSize(42, 38))
                b.setCheckable(True)
                b.setChecked(ic == self.scelta)
                b.setStyleSheet("font-size: 19px;")
                b.clicked.connect(lambda _=False, scelto=ic: self._scegli(scelto))
                griglia.addWidget(b, i // self.COLONNE, i % self.COLONNE)
                pulsanti.append(
                    (b, f"{nome} {gruppo} {parole.get(ic, '')}".lower()))
            for colonna in range(self.COLONNE):
                griglia.setColumnStretch(colonna, 0)
            griglia.setColumnStretch(self.COLONNE, 1)
            self.lay_contenuto.addWidget(contenitore)
            self.sezioni.append({"titolo": titolo, "contenitore": contenitore,
                                 "griglia": griglia, "pulsanti": pulsanti})
        self.lay_contenuto.addStretch(1)

    def _filtra(self, testo: str) -> None:
        """Mostra solo le icone che corrispondono, ricompattando la griglia."""
        cercato = testo.strip().lower()
        visibili = 0
        for sezione in self.sezioni:
            griglia = sezione["griglia"]
            posto = 0
            for pulsante, chiave in sezione["pulsanti"]:
                corrisponde = not cercato or cercato in chiave
                pulsante.setVisible(corrisponde)
                if corrisponde:
                    griglia.removeWidget(pulsante)
                    griglia.addWidget(pulsante, posto // self.COLONNE,
                                      posto % self.COLONNE)
                    posto += 1
            sezione["titolo"].setVisible(posto > 0)
            sezione["contenitore"].setVisible(posto > 0)
            visibili += posto
        self.et_vuoto.setVisible(visibili == 0)

    def _scegli(self, icona: str) -> None:
        self.scelta = icona
        self.accept()

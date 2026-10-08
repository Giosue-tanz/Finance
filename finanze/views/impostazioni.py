"""Impostazioni: conti, categorie, aspetto e gestione dei dati.

La pagina è divisa in quattro schede per evitare lo scorrimento: ogni azione è
raggiungibile in un clic, le modifiche si applicano subito e ogni operazione
conferma l'esito nella barra della pagina invece di aprire finestre superflue.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import date, datetime

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (QAbstractItemView, QButtonGroup, QColorDialog,
                               QComboBox, QDialog, QDialogButtonBox,
                               QDoubleSpinBox, QFileDialog, QFormLayout,
                               QHeaderView, QInputDialog, QLabel, QLineEdit,
                               QMessageBox, QPushButton, QTableWidget,
                               QGridLayout, QHBoxLayout, QScrollArea,
                               QTableWidgetItem, QTabWidget, QToolButton,
                               QVBoxLayout, QWidget)

from ..componenti import Scheda, abilita_deselezione, etichetta, riga
from ..icone import ICONA_PREDEFINITA, SelettoreIcona, icona_suggerita
from ..icone_nav import STILE_PREDEFINITO, STILI, anteprima_stile
from ..tema import ACCENTI, ACCENTO_PREDEFINITO, PALETTE_GRAFICI, SCALE
from ..utils import data_it, esporta_csv, euro, importa_csv
from . import VistaBase

TIPI_CONTO = ["Conto corrente", "Contanti", "Carta prepagata", "Risparmio",
              "Investimenti", "Altro"]
VALUTE = ["€", "$", "£", "CHF", "¥", "zł", "kr"]


# ---------------------------------------------------------------- dialoghi
class DialogoConto(QDialog):
    def __init__(self, valuta: str, conto=None, parent=None):
        super().__init__(parent)
        self.conto = dict(conto) if conto else None
        self.setWindowTitle("Modifica conto" if conto else "Nuovo conto")
        self.setMinimumWidth(380)

        self.nome = QLineEdit()
        self.nome.setPlaceholderText("es. Conto principale")
        self.tipo = QComboBox(); self.tipo.addItems(TIPI_CONTO)
        self.saldo = QDoubleSpinBox()
        self.saldo.setRange(-99_999_999, 99_999_999)
        self.saldo.setDecimals(2); self.saldo.setSingleStep(100)
        self.saldo.setGroupSeparatorShown(True)
        self.saldo.setSuffix(f" {valuta}")

        modulo = QFormLayout(); modulo.setSpacing(10)
        modulo.addRow("Nome", self.nome)
        modulo.addRow("Tipo", self.tipo)
        modulo.addRow("Saldo iniziale", self.saldo)

        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Save).setText("Salva")
        bb.button(QDialogButtonBox.Save).setObjectName("Primario")
        bb.button(QDialogButtonBox.Cancel).setText("Annulla")
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)

        lay = QVBoxLayout(self); lay.setContentsMargins(18, 18, 18, 14)
        lay.addLayout(modulo); lay.addWidget(bb)

        if self.conto:
            self.nome.setText(self.conto["nome"])
            self.tipo.setCurrentText(self.conto["tipo"])
            self.saldo.setValue(float(self.conto["saldo_iniziale"]))
        self.nome.setFocus()

    def dati(self) -> dict:
        return {"nome": self.nome.text().strip(),
                "tipo": self.tipo.currentText(),
                "saldo_iniziale": self.saldo.value()}


class DialogoCategoria(QDialog):
    def __init__(self, categoria=None, parent=None):
        super().__init__(parent)
        self.categoria = dict(categoria) if categoria else None
        self.colore = (self.categoria or {}).get("colore", PALETTE_GRAFICI[0])
        self.icona = (self.categoria or {}).get("icona", "") or ICONA_PREDEFINITA
        self.setWindowTitle("Modifica categoria" if categoria else "Nuova categoria")
        self.setMinimumWidth(380)

        self.nome = QLineEdit()
        self.nome.setPlaceholderText("es. Abbonamenti")
        self.tipo = QComboBox(); self.tipo.addItems(["uscita", "entrata"])
        self.b_colore = QPushButton("Scegli colore")
        self.b_colore.clicked.connect(self._scegli_colore)
        self.b_icona = QPushButton()
        self.b_icona.setStyleSheet("font-size: 20px;")
        self.b_icona.clicked.connect(self._scegli_icona)

        modulo = QFormLayout(); modulo.setSpacing(10)
        modulo.addRow("Nome", self.nome)
        modulo.addRow("Tipo", self.tipo)
        modulo.addRow("Icona", self.b_icona)
        modulo.addRow("Colore", self.b_colore)

        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Save).setText("Salva")
        bb.button(QDialogButtonBox.Save).setObjectName("Primario")
        bb.button(QDialogButtonBox.Cancel).setText("Annulla")
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)

        lay = QVBoxLayout(self); lay.setContentsMargins(18, 18, 18, 14)
        lay.addLayout(modulo); lay.addWidget(bb)

        if self.categoria:
            self.nome.setText(self.categoria["nome"])
            self.tipo.setCurrentText(self.categoria["tipo"])
        else:
            # per una categoria nuova l'icona segue il nome che stai scrivendo
            self.nome.textEdited.connect(self._proponi_icona)
        self._mostra_colore()
        self._mostra_icona()
        self.nome.setFocus()

    def _proponi_icona(self, testo: str) -> None:
        if not getattr(self, "_icona_scelta_a_mano", False):
            self.icona = icona_suggerita(testo, self.tipo.currentText())
            self._mostra_icona()

    def _scegli_icona(self) -> None:
        dlg = SelettoreIcona(self.icona, self)
        if dlg.exec():
            self.icona = dlg.scelta
            self._icona_scelta_a_mano = True
            self._mostra_icona()

    def _mostra_icona(self) -> None:
        self.b_icona.setText(f"  {self.icona}    cambia…")

    def _scegli_colore(self) -> None:
        scelto = QColorDialog.getColor(QColor(self.colore), self, "Colore categoria")
        if scelto.isValid():
            self.colore = scelto.name()
            self._mostra_colore()

    def _mostra_colore(self) -> None:
        self.b_colore.setText(f"   {self.colore}")
        self.b_colore.setStyleSheet(
            f"text-align: left; border-left: 22px solid {self.colore};")

    def dati(self) -> dict:
        return {"nome": self.nome.text().strip(),
                "tipo": self.tipo.currentText(),
                "colore": self.colore,
                "icona": self.icona}


# ------------------------------------------------------------------ vista
class VistaImpostazioni(VistaBase):
    titolo = "Impostazioni"
    sottotitolo = "Conti, categorie, aspetto e gestione dei dati"

    tema_cambiato = Signal(str)
    aspetto_cambiato = Signal()

    def costruisci(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(2, 2, 6, 6)
        lay.setSpacing(10)

        self.schede = QTabWidget()
        self.schede.addTab(self._tab_conti(), "Conti")
        self.schede.addTab(self._tab_categorie(), "Categorie")
        self.schede.addTab(self._scorrevole(self._tab_aspetto()), "Aspetto")
        self.schede.addTab(self._scorrevole(self._tab_dati()), "Dati e backup")
        lay.addWidget(self.schede, 1)

        self.barra_esito = QLabel("")
        self.barra_esito.setObjectName("Buono")
        lay.addWidget(self.barra_esito)

        self._timer_esito = QTimer(self)
        self._timer_esito.setSingleShot(True)
        self._timer_esito.timeout.connect(lambda: self.barra_esito.setText(""))

    @staticmethod
    def _scorrevole(pagina: QWidget) -> QScrollArea:
        """Avvolge una pagina in un'area scorrevole: senza, quando lo spazio
        manca Qt comprime le schede fino a sovrapporne i contenuti."""
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QScrollArea.NoFrame)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        area.setWidget(pagina)
        return area

    # ------------------------------------------------------------- messaggi
    def _esito(self, testo: str) -> None:
        self.barra_esito.setStyleSheet(f"color: {self.c['entrata']}; font-weight: 600;")
        self.barra_esito.setText(f"✓  {testo}")
        self._timer_esito.start(5000)

    def _avviso(self, testo: str) -> None:
        self.barra_esito.setStyleSheet(f"color: {self.c['attenzione']};")
        self.barra_esito.setText(f"•  {testo}")
        self._timer_esito.start(5000)

    # ----------------------------------------------------------------- conti
    def _tab_conti(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w); lay.setSpacing(12)
        lay.setContentsMargins(12, 14, 12, 12)

        sc = Scheda()
        self.in_conto = QLineEdit()
        self.in_conto.setPlaceholderText("Nome del nuovo conto, poi Invio")
        self.in_tipo_conto = QComboBox(); self.in_tipo_conto.addItems(TIPI_CONTO)
        self.in_saldo = QDoubleSpinBox()
        self.in_saldo.setRange(-99_999_999, 99_999_999)
        self.in_saldo.setDecimals(2); self.in_saldo.setSingleStep(100)
        self.in_saldo.setGroupSeparatorShown(True)
        self.in_saldo.setMaximumWidth(220)
        b_add = QPushButton("Aggiungi"); b_add.setObjectName("Primario")
        sc.aggiungi_layout(riga(self.in_conto, self.in_tipo_conto,
                                etichetta("saldo iniziale"), self.in_saldo, b_add))
        lay.addWidget(sc)

        sc_tab = Scheda("Conti e portafogli")
        self.tab_conti = QTableWidget(0, 5)
        self.tab_conti.setHorizontalHeaderLabels(
            ["Conto", "Tipo", "Saldo iniziale", "Saldo attuale", "Movimenti"])
        self._prepara_tabella(self.tab_conti, larghezza_prima=260)
        self.tab_conti.doubleClicked.connect(self.modifica_conto)
        sc_tab.aggiungi(self.tab_conti)

        b_mod = QPushButton("Modifica")
        b_rinomina = QPushButton("Rinomina")
        b_del = QPushButton("Elimina"); b_del.setObjectName("Pericolo")
        nota = QLabel("Doppio clic su una riga per modificarla. "
                      "Rinominando un conto i movimenti collegati vengono aggiornati.")
        nota.setObjectName("NotaScheda")
        sc_tab.aggiungi_layout(riga(b_mod, b_rinomina, b_del, None, nota))
        lay.addWidget(sc_tab, 1)

        b_add.clicked.connect(self.aggiungi_conto)
        self.in_conto.returnPressed.connect(self.aggiungi_conto)
        b_mod.clicked.connect(self.modifica_conto)
        b_rinomina.clicked.connect(self.rinomina_conto)
        b_del.clicked.connect(self.elimina_conto)
        return w

    # ------------------------------------------------------------- categorie
    def _tab_categorie(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w); lay.setSpacing(12)
        lay.setContentsMargins(12, 14, 12, 12)

        # ---------------------------------------------------- nuova categoria
        sc = Scheda("Nuova categoria")
        self._icona_nuova = ICONA_PREDEFINITA
        self._icona_scelta = False          # l'utente l'ha scelta a mano?
        self._colore_nuova = PALETTE_GRAFICI[0]

        griglia = QGridLayout()
        griglia.setHorizontalSpacing(12)
        griglia.setVerticalSpacing(4)
        for colonna, testo in enumerate(("ICONA", "NOME", "TIPO", "COLORE")):
            et = QLabel(testo)
            et.setObjectName("EtichettaScheda")
            griglia.addWidget(et, 0, colonna)

        self.b_icona_nuova = QPushButton()
        self.b_icona_nuova.setObjectName("IconaCategoria")
        self.b_icona_nuova.setFixedSize(54, 42)
        self.b_icona_nuova.setToolTip(
            "L'icona segue il nome che scrivi: clic per sceglierla fra 174")
        griglia.addWidget(self.b_icona_nuova, 1, 0)

        self.in_cat = QLineEdit()
        self.in_cat.setPlaceholderText("es. Abbonamenti, Palestra, Benzina…")
        self.in_cat.setClearButtonEnabled(True)
        self.in_cat.setMinimumHeight(42)
        self.in_cat.setMinimumWidth(260)
        griglia.addWidget(self.in_cat, 1, 1)

        self.gruppo_tipo_nuova = QButtonGroup(self)
        contenitore_tipo = QWidget()
        fila_tipo = QHBoxLayout(contenitore_tipo)
        fila_tipo.setContentsMargins(0, 0, 0, 0)
        fila_tipo.setSpacing(0)
        for i, nome in enumerate(("Uscita", "Entrata")):
            b = QPushButton(nome)
            b.setObjectName("Segmento")
            b.setCheckable(True)
            b.setChecked(i == 0)
            b.setMinimumHeight(42)
            self.gruppo_tipo_nuova.addButton(b, i)
            fila_tipo.addWidget(b)
        griglia.addWidget(contenitore_tipo, 1, 2)

        self.b_colore_nuova = QPushButton()
        self.b_colore_nuova.setObjectName("CampioneColore")
        self.b_colore_nuova.setFixedSize(54, 42)
        self.b_colore_nuova.setToolTip("Colore usato nei grafici: clic per cambiarlo")
        griglia.addWidget(self.b_colore_nuova, 1, 3)

        b_add = QPushButton("Aggiungi categoria")
        b_add.setObjectName("Primario")
        b_add.setMinimumHeight(42)
        b_add.setMinimumWidth(170)
        griglia.addWidget(b_add, 1, 4)
        griglia.setColumnStretch(1, 1)
        griglia.setColumnStretch(5, 0)
        sc.aggiungi_layout(griglia)

        sc.aggiungi(etichetta(
            "Scrivi il nome e premi Invio: icona e colore vengono scelti per te, "
            "ma puoi cambiarli con un clic prima di aggiungere.", "NotaScheda"))
        lay.addWidget(sc)

        sc_tab = Scheda("Categorie")
        self.filtro_cat = QButtonGroup(self)
        barra_filtri = riga()
        for i, testo in enumerate(("Tutte", "Uscite", "Entrate")):
            b = QPushButton(testo); b.setObjectName("Segmento"); b.setCheckable(True)
            b.setChecked(i == 0)
            self.filtro_cat.addButton(b, i)
            barra_filtri.addWidget(b)
        self.cerca_cat = QLineEdit()
        self.cerca_cat.setPlaceholderText("Cerca categoria…")
        self.cerca_cat.setClearButtonEnabled(True)
        barra_filtri.addStretch(1)
        barra_filtri.addWidget(self.cerca_cat)
        sc_tab.aggiungi_layout(barra_filtri)

        self.tab_cat = QTableWidget(0, 5)
        self.tab_cat.setHorizontalHeaderLabels(
            ["Icona", "Categoria", "Tipo", "Colore", "Movimenti"])
        self._prepara_tabella(self.tab_cat, larghezza_prima=70)
        self.tab_cat.doubleClicked.connect(self.modifica_categoria)
        sc_tab.aggiungi(self.tab_cat)

        b_mod = QPushButton("Modifica")
        b_icona = QPushButton("Icona rapida")
        b_colore = QPushButton("Colore rapido")
        b_unisci = QPushButton("Unisci in…")
        b_del = QPushButton("Elimina"); b_del.setObjectName("Pericolo")
        nota = QLabel("Doppio clic per modificare nome, icona, tipo e colore. "
                      "«Unisci» sposta tutti i movimenti in un'altra categoria.")
        nota.setObjectName("NotaScheda")
        sc_tab.aggiungi_layout(riga(b_mod, b_icona, b_colore, b_unisci, b_del, None, nota))
        lay.addWidget(sc_tab, 1)

        b_add.clicked.connect(self.aggiungi_categoria)
        self.in_cat.returnPressed.connect(self.aggiungi_categoria)
        self.in_cat.textEdited.connect(self._nome_modificato)
        self.b_icona_nuova.clicked.connect(self._scegli_icona_nuova)
        self.b_colore_nuova.clicked.connect(self._scegli_colore_nuova)
        self.gruppo_tipo_nuova.idClicked.connect(lambda _: self._aggiorna_nuova())
        b_mod.clicked.connect(self.modifica_categoria)
        b_icona.clicked.connect(self.cambia_icona)
        b_colore.clicked.connect(self.cambia_colore)
        b_unisci.clicked.connect(self.unisci_categoria)
        b_del.clicked.connect(self.elimina_categoria)
        self.filtro_cat.idClicked.connect(lambda _: self._riempi_categorie())
        self.cerca_cat.textChanged.connect(lambda _: self._riempi_categorie())
        return w

    # --------------------------------------------------------------- aspetto
    def _tab_aspetto(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w); lay.setSpacing(12)
        lay.setContentsMargins(12, 14, 12, 12)

        sc_tema = Scheda("Tema")
        self.gruppo_tema = QButtonGroup(self)
        fila = riga()
        for i, nome in enumerate(("scuro", "chiaro")):
            b = QPushButton(nome.capitalize()); b.setObjectName("Segmento")
            b.setCheckable(True)
            self.gruppo_tema.addButton(b, i)
            fila.addWidget(b)
        fila.addStretch(1)
        sc_tema.aggiungi_layout(fila)
        sc_tema.aggiungi(etichetta("Il tema si applica immediatamente a tutta "
                                   "l'applicazione. Scorciatoia: Ctrl+T da "
                                   "qualunque pagina.", "NotaScheda"))
        lay.addWidget(sc_tema)

        sc_colore = Scheda("Colore principale")
        self.gruppo_accento = QButtonGroup(self)
        self.pulsanti_accento: dict[str, QPushButton] = {}
        griglia_colori = QGridLayout()
        griglia_colori.setSpacing(8)
        for i, nome in enumerate(ACCENTI):
            b = QPushButton(nome.capitalize())
            b.setObjectName("Campione")
            b.setCheckable(True)
            b.setMinimumWidth(96)
            self.gruppo_accento.addButton(b, i)
            self.pulsanti_accento[nome] = b
            griglia_colori.addWidget(b, i // 5, i % 5)
        griglia_colori.setColumnStretch(5, 1)
        sc_colore.aggiungi_layout(griglia_colori)
        sc_colore.aggiungi(etichetta(
            "Tinta di pulsanti, selezioni, barre e grafico dell'andamento. "
            "Si applica subito a tutta l'applicazione.", "NotaScheda"))
        lay.addWidget(sc_colore)

        sc_icone = Scheda("Stile delle icone")
        self.gruppo_stile = QButtonGroup(self)
        self.pulsanti_stile: dict[str, QToolButton] = {}
        griglia_stili = QGridLayout()
        griglia_stili.setSpacing(8)
        for i, nome in enumerate(STILI):
            b = QToolButton()
            b.setObjectName("CampioneIcone")
            b.setCheckable(True)
            b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            b.setText(nome.capitalize())
            # dimensioni fissate subito: il riquadro deve nascere già alto
            # abbastanza, altrimenti la nota sotto finisce sopra le icone
            anteprima = anteprima_stile(nome, self.c["testo2"])
            dimensione = anteprima.size() / anteprima.devicePixelRatio()
            b.setIcon(QIcon(anteprima))
            b.setIconSize(dimensione)
            b.setFixedSize(dimensione.width() + 30, dimensione.height() + 42)
            self.gruppo_stile.addButton(b, i)
            self.pulsanti_stile[nome] = b
            griglia_stili.addWidget(b, i // 5, i % 5)
        griglia_stili.setColumnStretch(5, 1)
        sc_icone.aggiungi_layout(griglia_stili)
        sc_icone.aggiungi(etichetta(
            "Tratto delle icone del menu laterale. Le anteprime mostrano tutte "
            "le icone nello stile corrispondente.", "NotaScheda"))
        lay.addWidget(sc_icone)

        sc_testo = Scheda("Dimensione del testo")
        self.gruppo_scala = QButtonGroup(self)
        fila2 = riga()
        for i, nome in enumerate(SCALE):
            b = QPushButton(nome.capitalize()); b.setObjectName("Segmento")
            b.setCheckable(True)
            self.gruppo_scala.addButton(b, i)
            fila2.addWidget(b)
        fila2.addStretch(1)
        sc_testo.aggiungi_layout(fila2)
        sc_testo.aggiungi(etichetta("Utile su schermi ad alta risoluzione: "
                                    "ingrandisce testi e comandi di tutta l'app.",
                                    "NotaScheda"))
        lay.addWidget(sc_testo)

        sc_val = Scheda("Valuta")
        self.cmb_valuta = QComboBox()
        self.cmb_valuta.setEditable(True)
        self.cmb_valuta.addItems(VALUTE)
        self.cmb_valuta.setMaximumWidth(140)
        self.anteprima_valuta = QLabel("")
        self.anteprima_valuta.setObjectName("Pillola")
        sc_val.aggiungi_layout(riga(self.cmb_valuta, self.anteprima_valuta, None))
        sc_val.aggiungi(etichetta("Il simbolo viene applicato subito a importi, "
                                 "grafici e tabelle.", "NotaScheda"))
        lay.addWidget(sc_val)
        lay.addStretch(1)

        self.gruppo_tema.idClicked.connect(self._imposta_tema)
        self.gruppo_accento.idClicked.connect(self._imposta_accento)
        self.gruppo_stile.idClicked.connect(self._imposta_stile_icone)
        self.gruppo_scala.idClicked.connect(self._imposta_scala)
        self.cmb_valuta.currentTextChanged.connect(self._imposta_valuta)
        return w

    # ------------------------------------------------------------------ dati
    def _tab_dati(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w); lay.setSpacing(12)
        lay.setContentsMargins(12, 14, 12, 12)

        sc_info = Scheda("Archivio")
        self.et_info = QLabel(""); self.et_info.setWordWrap(True)
        b_apri = QPushButton("Apri cartella dati")
        sc_info.aggiungi(self.et_info)
        sc_info.aggiungi_layout(riga(b_apri, None))
        lay.addWidget(sc_info)

        sc_backup = Scheda("Backup")
        b_rapido = QPushButton("Backup immediato"); b_rapido.setObjectName("Primario")
        b_scegli = QPushButton("Backup in una cartella a scelta…")
        b_ripristina = QPushButton("Ripristina da backup…")
        sc_backup.aggiungi_layout(riga(b_rapido, b_scegli, b_ripristina, None))
        self.et_backup = QLabel(""); self.et_backup.setObjectName("NotaScheda")
        self.et_backup.setWordWrap(True)
        sc_backup.aggiungi(self.et_backup)
        lay.addWidget(sc_backup)

        sc_scambio = Scheda("Importa ed esporta")
        b_json = QPushButton("Esporta tutto in JSON")
        b_csv = QPushButton("Esporta movimenti in CSV")
        b_imp = QPushButton("Importa movimenti da CSV…")
        sc_scambio.aggiungi_layout(riga(b_json, b_csv, b_imp, None))
        sc_scambio.aggiungi(etichetta(
            "CSV atteso: data;tipo;importo;categoria;conto;descrizione — "
            "le date sono accettate come gg/mm/aaaa o aaaa-mm-gg.", "NotaScheda"))
        lay.addWidget(sc_scambio)

        sc_pericolo = Scheda("Operazioni irreversibili")
        b_azzera = QPushButton("Azzera tutti i movimenti")
        b_azzera.setObjectName("Pericolo")
        b_reset = QPushButton("Ripristina categorie predefinite")
        sc_pericolo.aggiungi_layout(riga(b_azzera, b_reset, None))
        sc_pericolo.aggiungi(etichetta(
            "Prima di ogni operazione distruttiva viene creato automaticamente "
            "un backup nella cartella dei dati.", "NotaScheda"))
        lay.addWidget(sc_pericolo)

        sc_priv = Scheda("Privacy")
        testo = QLabel("Finance funziona interamente in locale: nessun dato lascia questo "
                       "computer e non viene effettuata alcuna connessione di rete. "
                       "L'archivio è un singolo file SQLite che puoi copiare, spostare "
                       "o cifrare come qualunque altro file.")
        testo.setWordWrap(True); testo.setObjectName("NotaScheda")
        sc_priv.aggiungi(testo)
        lay.addWidget(sc_priv)
        lay.addStretch(1)

        b_apri.clicked.connect(self.apri_cartella)
        b_rapido.clicked.connect(self.backup_rapido)
        b_scegli.clicked.connect(self.backup)
        b_ripristina.clicked.connect(self.ripristina)
        b_json.clicked.connect(self.esporta_json)
        b_csv.clicked.connect(self.esporta_csv_tutto)
        b_imp.clicked.connect(self.importa_csv_dati)
        b_azzera.clicked.connect(self.azzera)
        b_reset.clicked.connect(self.ripristina_categorie)
        return w

    # ------------------------------------------------------------- supporto
    @staticmethod
    def _prepara_tabella(tab: QTableWidget, larghezza_prima: int = 300) -> None:
        """Colonne compatte: la prima di larghezza fissa, lo spazio residuo in coda."""
        tab.verticalHeader().setVisible(False)
        tab.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tab.setSelectionBehavior(QAbstractItemView.SelectRows)
        tab.setSelectionMode(QAbstractItemView.SingleSelection)
        tab.setMinimumHeight(240)
        colonne = tab.columnCount()
        tab.insertColumn(colonne)
        tab.setHorizontalHeaderItem(colonne, QTableWidgetItem(""))
        intestazione = tab.horizontalHeader()
        intestazione.setSectionResizeMode(QHeaderView.ResizeToContents)
        intestazione.setSectionResizeMode(0, QHeaderView.Interactive)
        intestazione.resizeSection(0, larghezza_prima)
        intestazione.setSectionResizeMode(colonne, QHeaderView.Stretch)
        abilita_deselezione(tab)

    def _riga_selezionata(self, tab: QTableWidget, tabella: str):
        sel = tab.selectionModel().selectedRows()
        if not sel:
            self._avviso("Seleziona prima una riga della tabella.")
            return None
        id_ = int(tab.item(sel[0].row(), 0).data(Qt.UserRole))
        righe = self.db.query(f"SELECT * FROM {tabella} WHERE id=?", (id_,))
        return righe[0] if righe else None

    # ------------------------------------------------------------------ dati
    def aggiorna(self) -> None:
        v = self.valuta

        self.in_saldo.setSuffix(f" {v}")
        self.gruppo_tema.blockSignals(True)
        self.gruppo_tema.button(0 if self.db.leggi("tema", "scuro") == "scuro" else 1
                                ).setChecked(True)
        self.gruppo_tema.blockSignals(False)

        accento = self.db.leggi("accento", ACCENTO_PREDEFINITO)
        tema = self.db.leggi("tema", "scuro")
        self.gruppo_accento.blockSignals(True)
        for nome, pulsante in self.pulsanti_accento.items():
            tinta = ACCENTI[nome]["scuro" if tema == "scuro" else "chiaro"]
            scelto = nome == accento
            pulsante.setChecked(scelto)
            bordo = self.c["testo"] if scelto else tinta
            pulsante.setStyleSheet(
                f"background: {tinta}; color: #ffffff; border: 2px solid {bordo}; "
                f"font-weight: {'700' if scelto else '500'};")
        self.gruppo_accento.blockSignals(False)

        stile_icone = self.db.leggi("stile_icone", STILE_PREDEFINITO)
        self.gruppo_stile.blockSignals(True)
        for nome, pulsante in self.pulsanti_stile.items():
            scelto = nome == stile_icone
            striscia = anteprima_stile(
                nome, self.c["accento"] if scelto else self.c["testo2"])
            pulsante.setIcon(QIcon(striscia))
            pulsante.setChecked(scelto)
        self.gruppo_stile.blockSignals(False)

        scala = self.db.leggi("scala", "normale")
        nomi = list(SCALE)
        self.gruppo_scala.blockSignals(True)
        self.gruppo_scala.button(nomi.index(scala) if scala in nomi else 1).setChecked(True)
        self.gruppo_scala.blockSignals(False)

        self.cmb_valuta.blockSignals(True)
        self.cmb_valuta.setCurrentText(v)
        self.cmb_valuta.blockSignals(False)
        self.anteprima_valuta.setText(f"anteprima:  {euro(1234.5, v)}")

        self._riempi_conti()
        self._riempi_categorie()
        self._aggiorna_nuova()
        self._riempi_info()

    def _riempi_conti(self) -> None:
        v = self.valuta
        conti = self.db.query("SELECT * FROM conti ORDER BY nome")
        self.tab_conti.setRowCount(len(conti))
        for r, c in enumerate(conti):
            n = self.db.query("SELECT COUNT(*) n FROM movimenti WHERE conto=?",
                              (c["nome"],))[0]["n"]
            attuale = self.db.saldo_conto(c["nome"])
            valori = [c["nome"], c["tipo"], euro(float(c["saldo_iniziale"]), v),
                      euro(attuale, v), str(n)]
            for col, t in enumerate(valori):
                it = QTableWidgetItem(t)
                if col == 0:
                    it.setData(Qt.UserRole, c["id"])
                if col >= 2:
                    it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if col == 3:
                    it.setForeground(QColor(self.c["entrata"] if attuale >= 0
                                            else self.c["uscita"]))
                self.tab_conti.setItem(r, col, it)

    def _riempi_categorie(self) -> None:
        filtro = self.filtro_cat.checkedId()
        cerca = self.cerca_cat.text().strip().lower()
        sql = "SELECT * FROM categorie"
        par: tuple = ()
        if filtro == 1:
            sql += " WHERE tipo='uscita'"
        elif filtro == 2:
            sql += " WHERE tipo='entrata'"
        sql += " ORDER BY tipo, nome"
        cats = [c for c in self.db.query(sql, par)
                if not cerca or cerca in c["nome"].lower()]

        self.tab_cat.setRowCount(len(cats))
        for r, c in enumerate(cats):
            n = self.db.query("SELECT COUNT(*) n FROM movimenti WHERE categoria=?",
                              (c["nome"],))[0]["n"]
            it_icona = QTableWidgetItem(c["icona"] or "")
            it_icona.setData(Qt.UserRole, c["id"])
            it_icona.setTextAlignment(Qt.AlignCenter)
            self.tab_cat.setItem(r, 0, it_icona)
            self.tab_cat.setItem(r, 1, QTableWidgetItem(c["nome"]))
            self.tab_cat.setItem(r, 2, QTableWidgetItem(c["tipo"]))
            it_col = QTableWidgetItem("  ████  " + c["colore"])
            it_col.setForeground(QColor(c["colore"]))
            self.tab_cat.setItem(r, 3, it_col)
            it_n = QTableWidgetItem(str(n))
            it_n.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tab_cat.setItem(r, 4, it_n)

    def _riempi_info(self) -> None:
        percorso = self.db.percorso
        dimensione = os.path.getsize(percorso) / 1024 if os.path.exists(percorso) else 0
        conteggi = {t: self.db.query(f"SELECT COUNT(*) n FROM {t}")[0]["n"]
                    for t in ("movimenti", "conti", "categorie", "budget",
                              "obiettivi", "ricorrenti")}
        primo = self.db.query("SELECT MIN(data) d FROM movimenti")[0]["d"]
        self.et_info.setText(
            f"File: {percorso}\n"
            f"Dimensione: {dimensione:,.0f} KB".replace(",", ".") +
            f"   ·   {conteggi['movimenti']} movimenti"
            f"   ·   {conteggi['conti']} conti"
            f"   ·   {conteggi['categorie']} categorie"
            f"   ·   {conteggi['budget']} budget"
            f"   ·   {conteggi['obiettivi']} obiettivi"
            f"   ·   {conteggi['ricorrenti']} ricorrenze" +
            (f"\nPrimo movimento registrato: {data_it(primo)}" if primo else ""))

        cartella = self.db.cartella_backup()
        backup = sorted((f for f in os.listdir(cartella)
                         if f.startswith("finanze-backup-")), reverse=True)
        if backup:
            quando = datetime.fromtimestamp(
                os.path.getmtime(os.path.join(cartella, backup[0])))
            self.et_backup.setText(
                f"Ultimo backup: {backup[0]}  ({quando:%d/%m/%Y %H:%M})   ·   "
                f"{len(backup)} copie in {cartella}")
        else:
            self.et_backup.setText(f"Nessun backup presente in {cartella}.")

    # ----------------------------------------------------------------- conti
    def aggiungi_conto(self) -> None:
        nome = self.in_conto.text().strip()
        if not nome:
            return
        if self.db.query("SELECT id FROM conti WHERE nome=?", (nome,)):
            self._avviso(f"Il conto «{nome}» esiste già.")
            return
        self.db.esegui("INSERT INTO conti(nome, saldo_iniziale, tipo) VALUES(?,?,?)",
                       (nome, self.in_saldo.value(), self.in_tipo_conto.currentText()))
        self.in_conto.clear(); self.in_saldo.setValue(0)
        self._esito(f"Conto «{nome}» aggiunto.")
        self.dati_cambiati.emit()

    def modifica_conto(self) -> None:
        c = self._riga_selezionata(self.tab_conti, "conti")
        if c is None:
            return
        dlg = DialogoConto(self.valuta, c, self)
        if not dlg.exec():
            return
        d = dlg.dati()
        if not d["nome"]:
            return
        if d["nome"] != c["nome"]:
            if self.db.query("SELECT id FROM conti WHERE nome=?", (d["nome"],)):
                self._avviso(f"Esiste già un conto chiamato «{d['nome']}».")
                return
            self.db.esegui("UPDATE movimenti SET conto=? WHERE conto=?",
                           (d["nome"], c["nome"]))
            self.db.esegui("UPDATE ricorrenti SET conto=? WHERE conto=?",
                           (d["nome"], c["nome"]))
        self.db.esegui("UPDATE conti SET nome=?, tipo=?, saldo_iniziale=? WHERE id=?",
                       (d["nome"], d["tipo"], d["saldo_iniziale"], c["id"]))
        self._esito(f"Conto «{d['nome']}» aggiornato.")
        self.dati_cambiati.emit()

    def rinomina_conto(self) -> None:
        c = self._riga_selezionata(self.tab_conti, "conti")
        if c is None:
            return
        nuovo, ok = QInputDialog.getText(self, "Rinomina conto", "Nuovo nome:",
                                         text=c["nome"])
        nuovo = (nuovo or "").strip()
        if not ok or not nuovo or nuovo == c["nome"]:
            return
        if self.db.query("SELECT id FROM conti WHERE nome=?", (nuovo,)):
            self._avviso(f"Esiste già un conto chiamato «{nuovo}».")
            return
        self.db.esegui("UPDATE conti SET nome=? WHERE id=?", (nuovo, c["id"]))
        self.db.esegui("UPDATE movimenti SET conto=? WHERE conto=?", (nuovo, c["nome"]))
        self.db.esegui("UPDATE ricorrenti SET conto=? WHERE conto=?", (nuovo, c["nome"]))
        self._esito(f"Conto rinominato in «{nuovo}».")
        self.dati_cambiati.emit()

    def elimina_conto(self) -> None:
        c = self._riga_selezionata(self.tab_conti, "conti")
        if c is None:
            return
        if len(self.db.query("SELECT id FROM conti")) == 1:
            self._avviso("Deve restare almeno un conto.")
            return
        usati = self.db.query("SELECT COUNT(*) n FROM movimenti WHERE conto=?",
                              (c["nome"],))[0]["n"]
        if usati:
            altri = [r["nome"] for r in self.db.query(
                "SELECT nome FROM conti WHERE nome<>? ORDER BY nome", (c["nome"],))]
            destinazione, ok = QInputDialog.getItem(
                self, "Sposta i movimenti",
                f"Il conto «{c['nome']}» ha {usati} movimenti.\n"
                "Su quale conto vuoi spostarli?", altri, 0, False)
            if not ok:
                return
            self.db.esegui("UPDATE movimenti SET conto=? WHERE conto=?",
                           (destinazione, c["nome"]))
            self.db.esegui("UPDATE ricorrenti SET conto=? WHERE conto=?",
                           (destinazione, c["nome"]))
        elif QMessageBox.question(self, "Conferma", f"Eliminare il conto «{c['nome']}»?",
                                  QMessageBox.Yes | QMessageBox.No,
                                  QMessageBox.No) != QMessageBox.Yes:
            return
        self.db.elimina("conti", c["id"])
        self._esito(f"Conto «{c['nome']}» eliminato.")
        self.dati_cambiati.emit()

    # ------------------------------------------------------------- categorie
    # ------------------------------------------------- creazione categoria
    def _tipo_nuova(self) -> str:
        return "uscita" if self.gruppo_tipo_nuova.checkedId() == 0 else "entrata"

    def _nome_modificato(self, testo: str) -> None:
        """Mentre scrivi, l'icona segue il nome (finché non la scegli a mano)."""
        if not self._icona_scelta:
            self._icona_nuova = icona_suggerita(testo, self._tipo_nuova())
        self._aggiorna_nuova()

    def _scegli_icona_nuova(self) -> None:
        dlg = SelettoreIcona(self._icona_nuova, self)
        if dlg.exec():
            self._icona_nuova = dlg.scelta
            self._icona_scelta = True
            self._aggiorna_nuova()

    def _scegli_colore_nuova(self) -> None:
        colore = QColorDialog.getColor(QColor(self._colore_nuova), self,
                                       "Colore della categoria")
        if colore.isValid():
            self._colore_nuova = colore.name()
            self._aggiorna_nuova()

    def _colore_libero(self) -> str:
        """Primo colore libero della tavolozza; esaurita, ne genera uno nuovo."""
        usati = {r["colore"].lower() for r in self.db.query("SELECT colore FROM categorie")}
        for colore in PALETTE_GRAFICI:
            if colore.lower() not in usati:
                return colore
        # tavolozza finita: tinte distribuite sul cerchio dei colori
        for passo in range(len(usati) + 1):
            tinta = QColor.fromHsv((passo * 47) % 360, 150, 215).name()
            if tinta.lower() not in usati:
                return tinta
        return PALETTE_GRAFICI[len(usati) % len(PALETTE_GRAFICI)]

    def _aggiorna_nuova(self) -> None:
        """Riallinea icona e colore della categoria che si sta creando."""
        if not self._icona_scelta:
            self._icona_nuova = icona_suggerita(self.in_cat.text(), self._tipo_nuova())
        self.b_icona_nuova.setText(self._icona_nuova)
        self.b_colore_nuova.setStyleSheet(
            f"background: {self._colore_nuova}; border: 2px solid {self.c['bordo']};"
            "border-radius: 10px;")

    def _crea(self, nome: str, tipo: str, icona: str = "",
              colore: str = "") -> bool:
        if self.db.query("SELECT id FROM categorie WHERE nome=? AND tipo=?",
                         (nome, tipo)):
            self._avviso(f"La categoria «{nome}» esiste già tra le {tipo}.")
            return False
        icona = icona or icona_suggerita(nome, tipo)
        self.db.esegui(
            "INSERT INTO categorie(nome, tipo, colore, icona) VALUES(?,?,?,?)",
            (nome, tipo, colore or self._colore_libero(), icona))
        self._esito(f"Categoria «{icona} {nome}» aggiunta.")
        self.dati_cambiati.emit()
        return True

    def aggiungi_categoria(self) -> None:
        nome = self.in_cat.text().strip()
        if not nome:
            self._avviso("Scrivi il nome della categoria da aggiungere.")
            self.in_cat.setFocus()
            return
        tipo = self._tipo_nuova()
        if not self._crea(nome, tipo, self._icona_nuova, self._colore_nuova):
            return
        # pronto per la prossima: nome svuotato, icona e colore di nuovo automatici
        self.in_cat.clear()
        self._icona_scelta = False
        self._colore_nuova = self._colore_libero()
        self.in_cat.setFocus()

    def modifica_categoria(self) -> None:
        c = self._riga_selezionata(self.tab_cat, "categorie")
        if c is None:
            return
        dlg = DialogoCategoria(c, self)
        if not dlg.exec():
            return
        d = dlg.dati()
        if not d["nome"]:
            return
        if d["nome"] != c["nome"]:
            self.db.esegui("UPDATE movimenti SET categoria=? WHERE categoria=?",
                           (d["nome"], c["nome"]))
            self.db.esegui("UPDATE budget SET categoria=? WHERE categoria=?",
                           (d["nome"], c["nome"]))
            self.db.esegui("UPDATE ricorrenti SET categoria=? WHERE categoria=?",
                           (d["nome"], c["nome"]))
        self.db.esegui(
            "UPDATE categorie SET nome=?, tipo=?, colore=?, icona=? WHERE id=?",
            (d["nome"], d["tipo"], d["colore"], d["icona"], c["id"]))
        self._esito(f"Categoria «{d['nome']}» aggiornata.")
        self.dati_cambiati.emit()

    def cambia_icona(self) -> None:
        c = self._riga_selezionata(self.tab_cat, "categorie")
        if c is None:
            return
        dlg = SelettoreIcona(c["icona"] or ICONA_PREDEFINITA, self)
        if dlg.exec():
            self.db.esegui("UPDATE categorie SET icona=? WHERE id=?",
                           (dlg.scelta, c["id"]))
            self._esito(f"Icona di «{c['nome']}» aggiornata: {dlg.scelta}")
            self.dati_cambiati.emit()

    def cambia_colore(self) -> None:
        c = self._riga_selezionata(self.tab_cat, "categorie")
        if c is None:
            return
        colore = QColorDialog.getColor(QColor(c["colore"]), self, "Colore categoria")
        if colore.isValid():
            self.db.esegui("UPDATE categorie SET colore=? WHERE id=?",
                           (colore.name(), c["id"]))
            self._esito(f"Colore di «{c['nome']}» aggiornato.")
            self.dati_cambiati.emit()

    def unisci_categoria(self) -> None:
        c = self._riga_selezionata(self.tab_cat, "categorie")
        if c is None:
            return
        altre = [r["nome"] for r in self.db.query(
            "SELECT nome FROM categorie WHERE tipo=? AND nome<>? ORDER BY nome",
            (c["tipo"], c["nome"]))]
        if not altre:
            self._avviso("Non ci sono altre categorie dello stesso tipo.")
            return
        destinazione, ok = QInputDialog.getItem(
            self, "Unisci categoria",
            f"Spostare tutti i movimenti di «{c['nome']}» in:", altre, 0, False)
        if not ok:
            return
        n = self.db.query("SELECT COUNT(*) n FROM movimenti WHERE categoria=?",
                          (c["nome"],))[0]["n"]
        self.db.esegui("UPDATE movimenti SET categoria=? WHERE categoria=?",
                       (destinazione, c["nome"]))
        self.db.esegui("DELETE FROM budget WHERE categoria=?", (c["nome"],))
        self.db.esegui("UPDATE ricorrenti SET categoria=? WHERE categoria=?",
                       (destinazione, c["nome"]))
        self.db.elimina("categorie", c["id"])
        self._esito(f"{n} movimenti spostati in «{destinazione}».")
        self.dati_cambiati.emit()

    def elimina_categoria(self) -> None:
        c = self._riga_selezionata(self.tab_cat, "categorie")
        if c is None:
            return
        usati = self.db.query("SELECT COUNT(*) n FROM movimenti WHERE categoria=?",
                              (c["nome"],))[0]["n"]
        testo = (f"La categoria «{c['nome']}» è usata da {usati} movimenti, che "
                 "verranno riassegnati a «Altro».\nIn alternativa annulla e usa "
                 "«Unisci in…» per scegliere la destinazione.\n\nProcedere?"
                 if usati else f"Eliminare la categoria «{c['nome']}»?")
        if QMessageBox.question(self, "Conferma", testo,
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No) != QMessageBox.Yes:
            return
        if usati:
            self.db.esegui("UPDATE movimenti SET categoria='Altro' WHERE categoria=?",
                           (c["nome"],))
        self.db.esegui("DELETE FROM budget WHERE categoria=?", (c["nome"],))
        self.db.elimina("categorie", c["id"])
        self._esito(f"Categoria «{c['nome']}» eliminata.")
        self.dati_cambiati.emit()

    def ripristina_categorie(self) -> None:
        from ..db import CATEGORIE_DEFAULT
        if QMessageBox.question(
                self, "Categorie predefinite",
                "Le categorie predefinite mancanti verranno ricreate.\n"
                "Quelle che hai aggiunto restano invariate. Procedere?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        aggiunte = 0
        for nome, tipo, colore, icona in CATEGORIE_DEFAULT:
            if not self.db.query("SELECT id FROM categorie WHERE nome=? AND tipo=?",
                                 (nome, tipo)):
                self.db.esegui(
                    "INSERT INTO categorie(nome, tipo, colore, icona) VALUES(?,?,?,?)",
                    (nome, tipo, colore, icona))
                aggiunte += 1
        self._esito(f"{aggiunte} categorie predefinite ripristinate."
                    if aggiunte else "Tutte le categorie predefinite erano già presenti.")
        self.dati_cambiati.emit()

    # --------------------------------------------------------------- aspetto
    def _imposta_tema(self, indice: int) -> None:
        nome = "scuro" if indice == 0 else "chiaro"
        self.db.imposta("tema", nome)
        self.tema_cambiato.emit(nome)
        self._esito(f"Tema {nome} applicato.")

    def _imposta_accento(self, indice: int) -> None:
        nome = list(ACCENTI)[indice]
        self.db.imposta("accento", nome)
        self.tema_cambiato.emit(self.db.leggi("tema", "scuro"))
        self._esito(f"Colore principale: {nome}.")

    def _imposta_stile_icone(self, indice: int) -> None:
        nome = list(STILI)[indice]
        self.db.imposta("stile_icone", nome)
        self.aspetto_cambiato.emit()
        self._esito(f"Stile delle icone: {nome}.")

    def _imposta_scala(self, indice: int) -> None:
        nome = list(SCALE)[indice]
        self.db.imposta("scala", nome)
        self.aspetto_cambiato.emit()
        self._esito(f"Dimensione del testo: {nome}.")

    def _imposta_valuta(self, testo: str) -> None:
        simbolo = testo.strip()
        if not simbolo:
            return
        self.db.imposta("valuta", simbolo)
        self.anteprima_valuta.setText(f"anteprima:  {euro(1234.5, simbolo)}")
        self.dati_cambiati.emit()

    # ------------------------------------------------------------------ dati
    def apri_cartella(self) -> None:
        cartella = os.path.dirname(self.db.percorso)
        try:
            subprocess.Popen(["xdg-open", cartella])
            self._esito("Cartella dati aperta nel gestore file.")
        except Exception as e:
            QMessageBox.information(self, "Cartella dati", f"{cartella}\n\n{e}")

    def backup_rapido(self) -> None:
        dest = self.db.backup(self.db.cartella_backup())
        self._esito(f"Backup creato: {os.path.basename(dest)}")
        self._riempi_info()

    def backup(self) -> None:
        percorso, _ = QFileDialog.getSaveFileName(
            self, "Salva backup",
            os.path.join(os.path.expanduser("~"),
                         f"finance-backup-{date.today().isoformat()}.db"),
            "Database SQLite (*.db)")
        if not percorso:
            return
        dest = self.db.backup(percorso)
        self._esito(f"Backup salvato in {dest}")

    def ripristina(self) -> None:
        percorso, _ = QFileDialog.getOpenFileName(
            self, "Seleziona backup", self.db.cartella_backup(),
            "Database SQLite (*.db)")
        if not percorso:
            return
        if QMessageBox.question(
                self, "Confermi il ripristino?",
                "I dati attuali verranno sostituiti con quelli del backup.\n"
                "Una copia di sicurezza dell'archivio corrente viene creata "
                "automaticamente nella cartella dei backup.",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        self.db.backup(self.db.cartella_backup())
        self.db.chiudi()
        shutil.copy2(percorso, self.db.percorso)
        QMessageBox.information(
            self, "Ripristino completato",
            "Riavvia Finance per caricare l'archivio ripristinato.")

    def esporta_json(self) -> None:
        percorso, _ = QFileDialog.getSaveFileName(
            self, "Esporta tutto", f"finance-{date.today().isoformat()}.json",
            "File JSON (*.json)")
        if not percorso:
            return
        dati = {t: [dict(r) for r in self.db.query(f"SELECT * FROM {t}")]
                for t in ("conti", "categorie", "movimenti", "budget", "obiettivi",
                          "ricorrenti", "impostazioni")}
        with open(percorso, "w", encoding="utf-8") as f:
            json.dump(dati, f, ensure_ascii=False, indent=2)
        self._esito(f"Archivio esportato in {percorso}")

    def esporta_csv_tutto(self) -> None:
        percorso, _ = QFileDialog.getSaveFileName(
            self, "Esporta movimenti", f"movimenti-{date.today().isoformat()}.csv",
            "File CSV (*.csv)")
        if not percorso:
            return
        n = esporta_csv(percorso, self.db.query("SELECT * FROM movimenti ORDER BY data"),
                        ["data", "tipo", "importo", "categoria", "conto",
                         "descrizione", "etichette"])
        self._esito(f"{n} movimenti esportati in {percorso}")

    def importa_csv_dati(self) -> None:
        percorso, _ = QFileDialog.getOpenFileName(
            self, "Importa movimenti da CSV", "", "File CSV (*.csv *.txt)")
        if not percorso:
            return
        try:
            righe = importa_csv(percorso)
        except Exception as e:
            QMessageBox.critical(self, "Errore di lettura", str(e))
            return
        if not righe:
            QMessageBox.warning(
                self, "Nessun dato",
                "Il file non contiene righe riconoscibili.\n"
                "Colonne attese: data;tipo;importo;categoria;conto;descrizione")
            return
        for r in righe:
            self.db.salva_movimento(r)
        self._esito(f"{len(righe)} movimenti importati.")
        self.dati_cambiati.emit()

    def azzera(self) -> None:
        n = self.db.query("SELECT COUNT(*) n FROM movimenti")[0]["n"]
        if not n:
            self._avviso("Non ci sono movimenti da eliminare.")
            return
        conferma, ok = QInputDialog.getText(
            self, "Azzera movimenti",
            f"Stai per eliminare {n} movimenti in modo definitivo.\n"
            "Conti, categorie, budget e obiettivi restano invariati.\n"
            "Un backup viene creato automaticamente.\n\n"
            "Scrivi AZZERA per confermare:")
        if not ok or conferma.strip().upper() != "AZZERA":
            self._avviso("Operazione annullata.")
            return
        self.db.backup(self.db.cartella_backup())
        self.db.esegui("DELETE FROM movimenti")
        self._esito(f"{n} movimenti eliminati. Backup creato automaticamente.")
        self.dati_cambiati.emit()

"""Budget mensili: limiti per categoria, ritmo di spesa e proiezioni.

La pagina risponde a tre domande: quanto posso ancora spendere, su cosa sto
esagerando e quanto dovrei mettere a budget. Gli importi si impostano con un
Invio, si correggono con un doppio clic e l'app propone i limiti partendo dalla
tua spesa media.
"""
from __future__ import annotations

from PySide6.QtCore import QByteArray, QRectF, QTimer, Qt
from PySide6.QtGui import QColor, QKeySequence, QPainter, QShortcut
from PySide6.QtWidgets import (QAbstractItemView, QButtonGroup, QComboBox,
                               QDoubleSpinBox, QHeaderView, QInputDialog, QLabel,
                               QMenu, QMessageBox, QPushButton, QSplitter, QStyle,
                               QStyledItemDelegate, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget)

from ..componenti import Scheda, SchedaStat, etichetta, riga
from ..grafici import GraficoBarre
from ..icone import etichetta_categoria
from ..utils import euro, giorni_mese, mese_corrente
from . import VistaBase

FILTRI = ["Tutti", "Sotto controllo", "Vicino al limite", "Oltre il limite"]
MESI_STORICO = 3


class CellaBudget(QTableWidgetItem):
    """Cella con chiave di ordinamento numerica."""

    def __init__(self, testo: str, chiave=None):
        super().__init__(testo)
        self.chiave = testo if chiave is None else chiave

    def __lt__(self, altra):
        if isinstance(altra, CellaBudget):
            try:
                return self.chiave < altra.chiave
            except TypeError:
                pass
        return super().__lt__(altra)


class DelegatoAvanzamento(QStyledItemDelegate):
    """Disegna la barra di utilizzo dentro la cella.

    Un QProgressBar inserito come widget non seguirebbe il riordino della
    tabella: disegnarla qui la tiene sempre sulla riga giusta.
    """

    def __init__(self, colori: dict, parent=None):
        super().__init__(parent)
        self.c = colori

    def paint(self, pittore: QPainter, opzione, indice):
        dati = indice.data(Qt.UserRole + 1)
        if not dati:
            super().paint(pittore, opzione, indice)
            return
        quota, colore = dati
        pittore.save()
        if opzione.state & QStyle.State_Selected:
            pittore.fillRect(opzione.rect, opzione.palette.highlight())
        pittore.setRenderHint(QPainter.Antialiasing, True)
        area = QRectF(opzione.rect).adjusted(8, 8, -8, -8)
        pittore.setPen(Qt.NoPen)
        pittore.setBrush(QColor(self.c["pannello2"]))
        pittore.drawRoundedRect(area, 6, 6)
        larghezza = area.width() * min(100.0, max(0.0, quota)) / 100
        if larghezza > 1:
            pittore.setBrush(QColor(colore))
            pittore.drawRoundedRect(
                QRectF(area.x(), area.y(), larghezza, area.height()), 6, 6)
        pittore.setPen(QColor(self.c["testo"]))
        pittore.drawText(opzione.rect, Qt.AlignCenter, f"{quota:.0f}%")
        pittore.restore()

    def sizeHint(self, opzione, indice):
        dimensione = super().sizeHint(opzione, indice)
        dimensione.setHeight(max(30, dimensione.height()))
        return dimensione


class VistaBudget(VistaBase):
    titolo = "Budget"
    sottotitolo = "Limiti di spesa mensili per categoria"

    def costruisci(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(2, 2, 6, 6)
        lay.setSpacing(10)

        lay.addLayout(self._indicatori())
        lay.addWidget(self._barra_inserimento())

        # le tre sezioni sono ridimensionabili: in poco spazio nessuna schiaccia
        # le altre e la disposizione resta quella scelta dall'utente
        self.divisore = QSplitter(Qt.Vertical)
        self.divisore.setHandleWidth(8)
        self.divisore.setChildrenCollapsible(True)
        for sezione, minimo in ((self._tabella_budget(), 170),
                                (self._senza_budget(), 196),
                                (self._grafico(), 150)):
            sezione.setMinimumHeight(minimo)
            self.divisore.addWidget(sezione)
        self.divisore.setStretchFactor(0, 3)
        self.divisore.setStretchFactor(1, 1)
        self.divisore.setStretchFactor(2, 2)
        stato = self.db.leggi("budget_divisore", "")
        if stato:
            self.divisore.restoreState(QByteArray.fromBase64(stato.encode()))
        self.divisore.splitterMoved.connect(
            lambda *_: self.db.imposta(
                "budget_divisore",
                bytes(self.divisore.saveState().toBase64()).decode()))
        lay.addWidget(self.divisore, 1)

        self.et_stato = QLabel("")
        lay.addWidget(self.et_stato)
        self._timer = QTimer(self); self._timer.setSingleShot(True)
        self._timer.timeout.connect(lambda: self.et_stato.setText(""))

        QShortcut(QKeySequence("Delete"), self.tab, self.elimina)
        QShortcut(QKeySequence("Return"), self.tab, self.modifica)

    # ---------------------------------------------------------- indicatori
    def _indicatori(self):
        self.s_pianificato = SchedaStat("Budget pianificato", self.c, self.c["accento"])
        self.s_speso = SchedaStat("Speso questo mese", self.c, self.c["uscita"])
        self.s_residuo = SchedaStat("Residuo disponibile", self.c, self.c["entrata"])
        self.s_giorno = SchedaStat("Puoi spendere al giorno", self.c, self.c["attenzione"])
        fila = riga()
        for s in (self.s_pianificato, self.s_speso, self.s_residuo, self.s_giorno):
            fila.addWidget(s)
        return fila

    # ------------------------------------------------------- inserimento
    def _barra_inserimento(self) -> QWidget:
        sc = Scheda()
        self.cmb_categoria = QComboBox()
        self.cmb_categoria.setMinimumWidth(200)
        self.sp_importo = QDoubleSpinBox()
        self.sp_importo.setRange(0, 9_999_999)
        self.sp_importo.setDecimals(2)
        self.sp_importo.setSingleStep(25)
        self.sp_importo.setGroupSeparatorShown(True)
        self.sp_importo.setMaximumWidth(190)
        self.sp_importo.setSuffix(f" {self.valuta}")

        b_salva = QPushButton("Imposta budget"); b_salva.setObjectName("Primario")
        b_media = QPushButton("Proponi dalla media")
        b_media.setToolTip(
            f"Calcola il limite dalla spesa media degli ultimi {MESI_STORICO} mesi")
        b_modifica = QPushButton("Modifica")
        b_elimina = QPushButton("Rimuovi"); b_elimina.setObjectName("Pericolo")

        sc.aggiungi_layout(riga(etichetta("Categoria"), self.cmb_categoria,
                                etichetta("Limite mensile"), self.sp_importo,
                                b_salva, b_media, None, b_modifica, b_elimina))

        self.gruppo_filtri = QButtonGroup(self)
        fila = riga()
        for i, nome in enumerate(FILTRI):
            b = QPushButton(nome); b.setObjectName("Segmento"); b.setCheckable(True)
            b.setChecked(i == 0)
            self.gruppo_filtri.addButton(b, i)
            fila.addWidget(b)
        aiuto = etichetta(
            "Doppio clic per cambiare un limite · Canc per rimuoverlo · "
            "«Fine mese» è la stima al ritmo attuale", "NotaScheda")
        fila.addWidget(aiuto)
        fila.addStretch(1)
        self.et_avvisi = QLabel(""); self.et_avvisi.setObjectName("NotaScheda")
        fila.addWidget(self.et_avvisi)
        sc.aggiungi_layout(fila)

        b_salva.clicked.connect(self.salva)
        b_media.clicked.connect(self.proponi_media)
        b_modifica.clicked.connect(self.modifica)
        b_elimina.clicked.connect(self.elimina)
        self.cmb_categoria.currentIndexChanged.connect(self._precompila)
        self.gruppo_filtri.idClicked.connect(lambda _: self.aggiorna())
        return sc

    # ---------------------------------------------------------- tabella
    def _tabella_budget(self) -> QWidget:
        sc = Scheda("Stato dei budget")
        self.tab = QTableWidget(0, 7)
        self.tab.setHorizontalHeaderLabels(
            ["Categoria", "Limite", "Speso", "Residuo", "Utilizzo",
             "Fine mese (stima)", "Stato"])
        self.tab.verticalHeader().setVisible(False)
        self.tab.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tab.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tab.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tab.setAlternatingRowColors(True)
        self.tab.setSortingEnabled(True)
        self.tab.setMinimumHeight(110)
        self.tab.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tab.customContextMenuRequested.connect(self._menu)
        self.tab.doubleClicked.connect(self.modifica)
        self.tab.itemSelectionChanged.connect(self._selezione)
        h = self.tab.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeToContents)
        h.setSectionResizeMode(4, QHeaderView.Stretch)
        self.delegato = DelegatoAvanzamento(self.c, self.tab)
        self.tab.setItemDelegateForColumn(4, self.delegato)
        sc.aggiungi(self.tab, 1)
        return sc

    def _senza_budget(self) -> QWidget:
        self.sc_senza = Scheda("Categorie senza budget")
        self.tab_senza = QTableWidget(0, 4)
        self.tab_senza.setHorizontalHeaderLabels(
            ["Categoria", "Speso questo mese", f"Media {MESI_STORICO} mesi", "Budget proposto"])
        self.tab_senza.verticalHeader().setVisible(False)
        self.tab_senza.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tab_senza.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tab_senza.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tab_senza.setMinimumHeight(76)
        self.tab_senza.doubleClicked.connect(self.adotta_proposta)
        hs = self.tab_senza.horizontalHeader()
        hs.setSectionResizeMode(QHeaderView.ResizeToContents)
        hs.setSectionResizeMode(0, QHeaderView.Stretch)
        b_adotta = QPushButton("Imposta il budget proposto")
        b_adotta.clicked.connect(self.adotta_proposta)
        b_tutti = QPushButton("Imposta tutti i proposti")
        b_tutti.clicked.connect(self.adotta_tutte)
        self.sc_senza.aggiungi(self.tab_senza, 1)
        self.sc_senza.aggiungi_layout(riga(b_adotta, b_tutti, None))
        return self.sc_senza

    def _grafico(self) -> QWidget:
        sc = Scheda("Utilizzo dei budget")
        self.g_barre = GraficoBarre(self.c)
        self.g_barre.orizzontale = True
        self.g_barre.setMinimumHeight(110)
        sc.aggiungi(self.g_barre, 1)
        self.grafici = [self.g_barre]
        return sc

    # --------------------------------------------------------------- utilità
    def _messaggio(self, testo: str, positivo: bool = True) -> None:
        colore = self.c["entrata"] if positivo else self.c["attenzione"]
        self.et_stato.setStyleSheet(f"color: {colore};")
        self.et_stato.setText(("✓  " if positivo else "•  ") + testo)
        self._timer.start(6000)

    def _media_storica(self, categoria: str) -> float:
        """Spesa media mensile della categoria nei mesi precedenti."""
        righe = self.db.query(
            "SELECT substr(data,1,7) m, SUM(importo) tot FROM movimenti "
            "WHERE tipo='uscita' AND categoria=? AND substr(data,1,7) < ? "
            "GROUP BY m ORDER BY m DESC LIMIT ?",
            (categoria, mese_corrente()[0][:7], MESI_STORICO))
        if not righe:
            return 0.0
        return sum(float(r["tot"]) for r in righe) / len(righe)

    @staticmethod
    def _arrotonda(valore: float) -> float:
        """Arrotonda la proposta a una cifra comoda."""
        if valore <= 0:
            return 0.0
        passo = 5 if valore < 100 else (10 if valore < 500 else 50)
        return float(int(valore / passo + 0.999) * passo)

    def _speso(self, categoria: str, dal: str, al: str) -> float:
        return float(self.db.query(
            "SELECT COALESCE(SUM(importo),0) s FROM movimenti "
            "WHERE tipo='uscita' AND categoria=? AND data BETWEEN ? AND ?",
            (categoria, dal, al))[0]["s"])

    def _categoria_selezionata(self) -> str:
        sel = self.tab.selectionModel().selectedRows()
        if not sel:
            return ""
        return self.tab.item(sel[0].row(), 0).data(Qt.UserRole) or ""

    def _selezione(self) -> None:
        categoria = self._categoria_selezionata()
        if not categoria:
            return
        idx = self.cmb_categoria.findData(categoria)
        if idx >= 0:
            self.cmb_categoria.blockSignals(True)
            self.cmb_categoria.setCurrentIndex(idx)
            self.cmb_categoria.blockSignals(False)
        r = self.db.query("SELECT mensile FROM budget WHERE categoria=?", (categoria,))
        if r:
            self.sp_importo.setValue(float(r[0]["mensile"]))

    def _precompila(self) -> None:
        """Mostra il limite esistente, o la proposta dalla media, alla selezione."""
        categoria = self.cmb_categoria.currentData()
        if not categoria:
            return
        r = self.db.query("SELECT mensile FROM budget WHERE categoria=?", (categoria,))
        if r:
            self.sp_importo.setValue(float(r[0]["mensile"]))
        else:
            self.sp_importo.setValue(self._arrotonda(self._media_storica(categoria)))

    def _menu(self, posizione) -> None:
        categoria = self._categoria_selezionata()
        if not categoria:
            return
        menu = QMenu(self)
        menu.addAction("Modifica limite…", self.modifica)
        menu.addAction("Allinea alla media storica",
                       lambda: self._imposta(categoria,
                                             self._arrotonda(self._media_storica(categoria))))
        menu.addAction("Aumenta del 10%",
                       lambda: self._scala(categoria, 1.1))
        menu.addAction("Riduci del 10%", lambda: self._scala(categoria, 0.9))
        menu.addSeparator()
        menu.addAction("Rimuovi budget", self.elimina)
        menu.exec(self.tab.viewport().mapToGlobal(posizione))

    # ------------------------------------------------------------------ dati
    def aggiorna(self) -> None:
        v = self.valuta
        self.sp_importo.setSuffix(f" {v}")
        dal, al = mese_corrente()
        trascorsi, totali, rimanenti = giorni_mese()
        icone = self.db.icone_categorie()
        colori = self.db.colori_categorie()

        scelta = self.cmb_categoria.currentData()
        self.cmb_categoria.blockSignals(True)
        self.cmb_categoria.clear()
        for r in self.db.query(
                "SELECT nome, icona FROM categorie WHERE tipo='uscita' ORDER BY nome"):
            self.cmb_categoria.addItem(etichetta_categoria(r["nome"], r["icona"]), r["nome"])
        idx = self.cmb_categoria.findData(scelta) if scelta else 0
        self.cmb_categoria.setCurrentIndex(max(0, idx))
        self.cmb_categoria.blockSignals(False)

        righe = self.db.query("SELECT * FROM budget ORDER BY mensile DESC")
        filtro = self.gruppo_filtri.checkedId()
        tot_limite = tot_speso = 0.0
        dati_grafico, colori_grafico = [], []
        visibili = []
        oltre = vicini = 0

        for b in righe:
            limite = float(b["mensile"])
            speso = self._speso(b["categoria"], dal, al)
            tot_limite += limite
            tot_speso += speso
            quota = (speso / limite * 100) if limite else 0
            if quota >= 100:
                oltre += 1
            elif quota >= 75:
                vicini += 1
            if filtro == 1 and quota >= 75:
                continue
            if filtro == 2 and not (75 <= quota < 100):
                continue
            if filtro == 3 and quota < 100:
                continue
            visibili.append((b, limite, speso, quota))

        self.tab.setSortingEnabled(False)
        self.tab.setRowCount(len(visibili))
        for r, (b, limite, speso, quota) in enumerate(visibili):
            categoria = b["categoria"]
            residuo = limite - speso
            proiezione = (speso / trascorsi * totali) if trascorsi else speso
            colore = (self.c["entrata"] if quota < 75 else
                      self.c["attenzione"] if quota < 100 else self.c["uscita"])
            stato = ("oltre il limite" if quota >= 100 else
                     "attenzione" if quota >= 75 else "sotto controllo")

            it_cat = CellaBudget(etichetta_categoria(categoria, icone.get(categoria)))
            it_cat.setData(Qt.UserRole, categoria)
            self.tab.setItem(r, 0, it_cat)
            for col, valore in ((1, limite), (2, speso), (3, residuo)):
                it = CellaBudget(euro(valore, v), valore)
                it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if col == 3:
                    it.setForeground(QColor(colore))
                self.tab.setItem(r, col, it)

            it_barra = CellaBudget("", quota)
            it_barra.setData(Qt.UserRole + 1, (quota, colore))
            self.tab.setItem(r, 4, it_barra)

            it_proiezione = CellaBudget(euro(proiezione, v), proiezione)
            it_proiezione.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if limite and proiezione > limite:
                it_proiezione.setForeground(QColor(self.c["uscita"]))
            self.tab.setItem(r, 5, it_proiezione)

            it_stato = CellaBudget(stato, quota)
            it_stato.setForeground(QColor(colore))
            self.tab.setItem(r, 6, it_stato)

            dati_grafico.append((etichetta_categoria(categoria, icone.get(categoria)),
                                 [quota]))
            colori_grafico.append((categoria, colore))
        self.tab.setSortingEnabled(True)

        giorno = (tot_limite - tot_speso) / rimanenti if rimanenti > 0 else 0.0
        self.s_pianificato.imposta(
            tot_limite, f"{len(righe)} categorie con budget", v)
        self.s_speso.imposta(
            tot_speso,
            f"{(tot_speso/tot_limite*100 if tot_limite else 0):.0f}% del budget  ·  "
            f"giorno {trascorsi} di {totali}", v)
        self.s_residuo.imposta(
            tot_limite - tot_speso, f"{rimanenti} giorni alla fine del mese", v)
        self.s_giorno.imposta(
            max(0.0, giorno),
            "ritmo sostenibile da qui a fine mese" if giorno > 0
            else "budget del mese esaurito", v)

        avvisi = []
        if oltre:
            avvisi.append(f"{oltre} oltre il limite")
        if vicini:
            avvisi.append(f"{vicini} vicine al limite")
        self.et_avvisi.setText("   ·   ".join(avvisi) if avvisi
                               else ("tutti i budget sotto controllo" if righe else ""))

        self.g_barre.imposta_dati(dati_grafico, colori_grafico)
        self._aggiorna_senza_budget(dal, al, icone)

    def _aggiorna_senza_budget(self, dal: str, al: str, icone: dict) -> None:
        v = self.valuta
        con_budget = {r["categoria"] for r in self.db.query("SELECT categoria FROM budget")}
        candidate = []
        for r in self.db.query(
                "SELECT nome FROM categorie WHERE tipo='uscita' ORDER BY nome"):
            nome = r["nome"]
            if nome in con_budget:
                continue
            speso = self._speso(nome, dal, al)
            media = self._media_storica(nome)
            if speso <= 0 and media <= 0:
                continue
            candidate.append((nome, speso, media, self._arrotonda(max(media, speso))))

        self.tab_senza.setRowCount(len(candidate))
        for r, (nome, speso, media, proposta) in enumerate(candidate):
            it = QTableWidgetItem(etichetta_categoria(nome, icone.get(nome)))
            it.setData(Qt.UserRole, nome)
            self.tab_senza.setItem(r, 0, it)
            for col, valore in ((1, speso), (2, media), (3, proposta)):
                cella = QTableWidgetItem(euro(valore, v))
                cella.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if col == 3:
                    cella.setForeground(QColor(self.c["accento"]))
                self.tab_senza.setItem(r, col, cella)
        self.sc_senza.setVisible(bool(candidate))

    # ----------------------------------------------------------------- azioni
    def _imposta(self, categoria: str, importo: float, messaggio: bool = True) -> None:
        if importo <= 0:
            self.db.esegui("DELETE FROM budget WHERE categoria=?", (categoria,))
        else:
            self.db.esegui(
                "INSERT INTO budget(categoria, mensile) VALUES(?,?) "
                "ON CONFLICT(categoria) DO UPDATE SET mensile=excluded.mensile",
                (categoria, importo))
        if messaggio:
            self._messaggio(f"Budget di «{categoria}»: {euro(importo, self.valuta)}"
                            if importo > 0 else f"Budget di «{categoria}» rimosso.")
        self.dati_cambiati.emit()

    def _scala(self, categoria: str, fattore: float) -> None:
        r = self.db.query("SELECT mensile FROM budget WHERE categoria=?", (categoria,))
        if not r:
            return
        self._imposta(categoria, round(float(r[0]["mensile"]) * fattore, 2))

    def salva(self) -> None:
        categoria = self.cmb_categoria.currentData()
        if not categoria:
            return
        importo = self.sp_importo.value()
        if importo <= 0:
            self._messaggio("Imposta un limite maggiore di zero.", positivo=False)
            return
        self._imposta(categoria, importo)

    def proponi_media(self) -> None:
        categoria = self.cmb_categoria.currentData()
        if not categoria:
            return
        media = self._media_storica(categoria)
        if media <= 0:
            self._messaggio(
                f"Nessuna spesa registrata in «{categoria}» nei mesi precedenti.",
                positivo=False)
            return
        proposta = self._arrotonda(media)
        self.sp_importo.setValue(proposta)
        self._messaggio(
            f"Media di «{categoria}»: {euro(media, self.valuta)} al mese  →  "
            f"proposta {euro(proposta, self.valuta)}. Premi «Imposta budget» per "
            "confermare.")

    def modifica(self) -> None:
        categoria = self._categoria_selezionata()
        if not categoria:
            self._messaggio("Seleziona prima una riga della tabella.", positivo=False)
            return
        corrente = float(self.db.query(
            "SELECT mensile FROM budget WHERE categoria=?", (categoria,))[0]["mensile"])
        media = self._media_storica(categoria)
        suggerimento = (f"\nSpesa media degli ultimi {MESI_STORICO} mesi: "
                        f"{euro(media, self.valuta)}" if media > 0 else "")
        nuovo, ok = QInputDialog.getDouble(
            self, "Modifica budget",
            f"Limite mensile per «{categoria}»:{suggerimento}",
            corrente, 0.0, 9_999_999.0, 2)
        if ok:
            self._imposta(categoria, nuovo)

    def elimina(self) -> None:
        categoria = self._categoria_selezionata()
        if not categoria:
            self._messaggio("Seleziona prima una riga della tabella.", positivo=False)
            return
        if QMessageBox.question(
                self, "Conferma", f"Rimuovere il budget di «{categoria}»?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        self.db.esegui("DELETE FROM budget WHERE categoria=?", (categoria,))
        self._messaggio(f"Budget di «{categoria}» rimosso.")
        self.dati_cambiati.emit()

    def adotta_proposta(self) -> None:
        sel = self.tab_senza.selectionModel().selectedRows()
        if not sel:
            self._messaggio("Seleziona una categoria dall'elenco in basso.",
                            positivo=False)
            return
        r = sel[0].row()
        categoria = self.tab_senza.item(r, 0).data(Qt.UserRole)
        proposta = self._arrotonda(max(
            self._media_storica(categoria),
            self._speso(categoria, *mese_corrente())))
        self._imposta(categoria, proposta)

    def adotta_tutte(self) -> None:
        n = self.tab_senza.rowCount()
        if not n:
            return
        if QMessageBox.question(
                self, "Conferma",
                f"Impostare il budget proposto per {n} categorie?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes) != QMessageBox.Yes:
            return
        for r in range(n):
            categoria = self.tab_senza.item(r, 0).data(Qt.UserRole)
            proposta = self._arrotonda(max(
                self._media_storica(categoria),
                self._speso(categoria, *mese_corrente())))
            self._imposta(categoria, proposta, messaggio=False)
        self._messaggio(f"Impostati {n} budget dalle proposte.")

    def aggiorna_tema(self, colori: dict) -> None:
        super().aggiorna_tema(colori)
        self.delegato.c = colori
        self.tab.viewport().update()

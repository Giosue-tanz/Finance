"""Sezioni trascinabili per i pannelli configurabili.

Ogni sezione è una scheda con una maniglia in alto: si prende e si porta dove
serve, anche in una riga nuova. Il contenitore gestisce righe e colonne con
divisori ridimensionabili e sa salvare e ricaricare l'intera disposizione.
"""
from __future__ import annotations

import json

from PySide6.QtCore import QMimeData, QPoint, QRect, Qt, Signal
from PySide6.QtGui import QDrag, QFont, QPainter, QPixmap
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QSizePolicy, QSplitter,
                               QVBoxLayout, QWidget)

from .lingue import t

MIME = "application/x-finance-sezione"
BORDO_RIGA = 18          # zona in cui il rilascio crea una riga nuova
LARGHEZZA_MINIMA = 150
ALTEZZA_MINIMA = 108


class Intestazione(QWidget):
    """Barra pulita: titolo, periodo come testo discreto, comandi al passaggio.

    Tutta la barra è l'area di trascinamento, così non serve una maniglia fissa:
    gli unici elementi sempre visibili sono il titolo e il periodo.
    """

    chiusura_richiesta = Signal()
    periodo_richiesto = Signal(QPoint)
    menu_richiesto = Signal(QPoint)

    def __init__(self, titolo: str, stile: str = "Sezione", parent=None):
        super().__init__(parent)
        self.setCursor(Qt.OpenHandCursor)
        self.setFixedHeight(24)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        self.titolo = QLabel(titolo)
        self.titolo.setObjectName(stile)
        self.periodo = QLabel("")
        self.periodo.setObjectName("Periodo")
        self.periodo.setCursor(Qt.PointingHandCursor)
        self.periodo.hide()
        self.azioni = QLabel("⋯")
        self.azioni.setObjectName("AzioniSezione")
        self.azioni.setCursor(Qt.PointingHandCursor)
        self.azioni.setToolTip(t("Altre azioni"))
        self.azioni.setVisible(False)

        lay.addWidget(self.titolo)
        lay.addWidget(self.periodo)
        lay.addStretch(1)
        lay.addWidget(self.azioni)
        self._premuto: QPoint | None = None

    # -------------------------------------------------------------- aspetto
    def imposta_periodo(self, testo: str) -> None:
        self.periodo.setText(testo)
        self.periodo.setVisible(bool(testo))

    def imposta_scala(self, px: int) -> None:
        """Dimensione del titolo in pixel: vince sul foglio di stile globale."""
        self.titolo.setStyleSheet(f"font-size: {px}px;")
        self.periodo.setStyleSheet(f"font-size: {max(10, px - 3)}px;")

    def enterEvent(self, ev):
        self.azioni.setVisible(True)
        super().enterEvent(ev)

    def leaveEvent(self, ev):
        self.azioni.setVisible(False)
        super().leaveEvent(ev)

    # ---------------------------------------------------------- interazione
    def _dentro(self, widget: QLabel, punto: QPoint) -> bool:
        return widget.isVisible() and widget.geometry().adjusted(
            -4, -6, 4, 6).contains(punto)

    def mousePressEvent(self, ev):
        punto = ev.position().toPoint()
        if ev.button() == Qt.RightButton:
            self.menu_richiesto.emit(self.mapToGlobal(punto))
            return
        if ev.button() != Qt.LeftButton:
            return
        if self._dentro(self.periodo, punto):
            self.periodo_richiesto.emit(
                self.periodo.mapToGlobal(QPoint(0, self.periodo.height())))
            return
        if self._dentro(self.azioni, punto):
            self.menu_richiesto.emit(
                self.azioni.mapToGlobal(QPoint(0, self.azioni.height())))
            return
        self._premuto = punto
        self.setCursor(Qt.ClosedHandCursor)

    def mouseReleaseEvent(self, _):
        self._premuto = None
        self.setCursor(Qt.OpenHandCursor)

    def mouseMoveEvent(self, ev):
        if self._premuto is None:
            return
        if (ev.position().toPoint() - self._premuto).manhattanLength() < 12:
            return
        sezione = self.parent()
        while sezione is not None and not isinstance(sezione, Sezione):
            sezione = sezione.parent()
        if sezione is None:
            return
        self._premuto = None
        self.setCursor(Qt.OpenHandCursor)

        dati = QMimeData()
        dati.setData(MIME, sezione.chiave.encode())
        trascina = QDrag(self)
        trascina.setMimeData(dati)
        anteprima = sezione.grab().scaledToWidth(
            min(320, sezione.width()), Qt.SmoothTransformation)
        ombra = QPixmap(anteprima.size())
        ombra.fill(Qt.transparent)
        pittore = QPainter(ombra)
        pittore.setOpacity(0.85)
        pittore.drawPixmap(0, 0, anteprima)
        pittore.end()
        trascina.setPixmap(ombra)
        trascina.setHotSpot(QPoint(40, 14))
        trascina.exec(Qt.MoveAction)


class Sezione(QFrame):
    """Scheda spostabile: intestazione trascinabile più contenuto."""

    chiusura_richiesta = Signal(str)
    periodo_richiesto = Signal(str, QPoint)
    menu_richiesto = Signal(str, QPoint)

    def __init__(self, chiave: str, titolo: str, contenuto: QWidget,
                 stile_titolo: str = "Sezione", parent=None):
        super().__init__(parent)
        self.setObjectName("Scheda")
        self.chiave = chiave
        self.contenuto = contenuto
        self.setMinimumSize(LARGHEZZA_MINIMA, ALTEZZA_MINIMA)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 12)
        lay.setSpacing(8)
        self.intestazione = Intestazione(titolo, stile_titolo, self)
        self.intestazione.chiusura_richiesta.connect(
            lambda: self.chiusura_richiesta.emit(self.chiave))
        self.intestazione.periodo_richiesto.connect(
            lambda punto: self.periodo_richiesto.emit(self.chiave, punto))
        self.intestazione.menu_richiesto.connect(
            lambda punto: self.menu_richiesto.emit(self.chiave, punto))
        lay.addWidget(self.intestazione)
        lay.addWidget(contenuto, 1)

    def imposta_periodo(self, testo: str) -> None:
        self.intestazione.imposta_periodo(testo)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        # il titolo si adatta alla larghezza della scheda
        px = int(max(10, min(17, self.width() / 26)))
        self.intestazione.imposta_scala(px)
        if hasattr(self.contenuto, "adatta_dimensioni"):
            self.contenuto.adatta_dimensioni(self.contenuto.size())


class Indicatore(QFrame):
    """Linea luminosa che mostra dove finirà la sezione trascinata."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("IndicatoreRilascio")
        self.hide()

    def mostra(self, rettangolo: QRect) -> None:
        self.setGeometry(rettangolo)
        self.show()
        self.raise_()


class ContenitoreSezioni(QWidget):
    """Righe di sezioni affiancate, tutte ridimensionabili e riordinabili."""

    disposizione_cambiata = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.sezioni: dict[str, Sezione] = {}
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.verticale = QSplitter(Qt.Vertical)
        self.verticale.setHandleWidth(8)
        self.verticale.setChildrenCollapsible(True)
        self.verticale.splitterMoved.connect(
            lambda *_: self.disposizione_cambiata.emit())
        lay.addWidget(self.verticale)
        self.indicatore = Indicatore(self)

    # ------------------------------------------------------------ costruzione
    def registra(self, sezione: Sezione) -> None:
        self.sezioni[sezione.chiave] = sezione

    def _nuova_riga(self, indice: int = -1) -> QSplitter:
        riga = QSplitter(Qt.Horizontal)
        riga.setHandleWidth(8)
        riga.setChildrenCollapsible(True)
        riga.splitterMoved.connect(lambda *_: self.disposizione_cambiata.emit())
        if indice < 0 or indice >= self.verticale.count():
            self.verticale.addWidget(riga)
        else:
            self.verticale.insertWidget(indice, riga)
        return riga

    def applica_disposizione(self, righe: list[list[str]]) -> None:
        """Ricostruisce la griglia a partire dall'elenco di righe di chiavi."""
        for s in self.sezioni.values():
            s.setParent(None)
        while self.verticale.count():
            vecchia = self.verticale.widget(0)
            vecchia.setParent(None)
            vecchia.deleteLater()

        for chiavi in righe:
            presenti = [k for k in chiavi if k in self.sezioni]
            if not presenti:
                continue
            riga = self._nuova_riga()
            for k in presenti:
                riga.addWidget(self.sezioni[k])
                self.sezioni[k].show()
        self._pulisci()

    def disposizione(self) -> list[list[str]]:
        righe = []
        for i in range(self.verticale.count()):
            riga = self.verticale.widget(i)
            if not isinstance(riga, QSplitter):
                continue
            chiavi = [riga.widget(j).chiave for j in range(riga.count())
                      if isinstance(riga.widget(j), Sezione)]
            if chiavi:
                righe.append(chiavi)
        return righe

    def stato(self) -> str:
        """Disposizione e dimensioni, pronte per essere salvate."""
        dati = {
            "righe": self.disposizione(),
            "verticale": self.verticale.sizes(),
            "orizzontali": [self.verticale.widget(i).sizes()
                            for i in range(self.verticale.count())
                            if isinstance(self.verticale.widget(i), QSplitter)],
            "nascoste": [k for k, s in self.sezioni.items() if s.isHidden()],
        }
        return json.dumps(dati)

    def ripristina_stato(self, testo: str) -> bool:
        try:
            dati = json.loads(testo)
            righe = [list(map(str, r)) for r in dati["righe"]]
        except Exception:
            return False
        note = {k for r in righe for k in r}
        mancanti = [k for k in self.sezioni if k not in note]
        if mancanti:
            righe.append(mancanti)
        self.applica_disposizione(righe)
        for k in dati.get("nascoste", []):
            if k in self.sezioni:
                self.sezioni[k].hide()
        self._pulisci()
        if dati.get("verticale"):
            self.verticale.setSizes(dati["verticale"])
        for i, dimensioni in enumerate(dati.get("orizzontali", [])):
            if i < self.verticale.count() and isinstance(self.verticale.widget(i), QSplitter):
                self.verticale.widget(i).setSizes(dimensioni)
        return True

    # --------------------------------------------------------------- rilascio
    def _righe(self) -> list[QSplitter]:
        return [self.verticale.widget(i) for i in range(self.verticale.count())
                if isinstance(self.verticale.widget(i), QSplitter)
                and not self.verticale.widget(i).isHidden()]

    def _bersaglio(self, punto: QPoint):
        """Dove finirebbe il rilascio: (riga, indice, crea_nuova_riga)."""
        righe = self._righe()
        if not righe:
            return None, 0, True
        for riga in righe:
            alto = riga.mapTo(self, QPoint(0, 0)).y()
            basso = alto + riga.height()
            if punto.y() < alto:
                return riga, 0, True
            if alto <= punto.y() <= basso:
                if punto.y() - alto < BORDO_RIGA:
                    return riga, 0, True
                if basso - punto.y() < BORDO_RIGA:
                    return riga, 1, True
                indice = riga.count()
                for j in range(riga.count()):
                    w = riga.widget(j)
                    if w.isHidden():
                        continue
                    centro = w.mapTo(self, QPoint(w.width() // 2, 0)).x()
                    if punto.x() < centro:
                        indice = j
                        break
                return riga, indice, False
        return righe[-1], 1, True

    def dragEnterEvent(self, ev):
        if ev.mimeData().hasFormat(MIME):
            ev.acceptProposedAction()

    def dragMoveEvent(self, ev):
        if not ev.mimeData().hasFormat(MIME):
            return
        ev.acceptProposedAction()
        riga, indice, nuova = self._bersaglio(ev.position().toPoint())
        if riga is None:
            self.indicatore.hide()
            return
        if nuova:
            y = riga.mapTo(self, QPoint(0, 0)).y()
            y = y - 4 if indice == 0 else y + riga.height() - 2
            self.indicatore.mostra(QRect(2, y, self.width() - 4, 5))
        else:
            if indice >= riga.count():
                ultimo = riga.widget(riga.count() - 1)
                x = ultimo.mapTo(self, QPoint(ultimo.width(), 0)).x()
            else:
                w = riga.widget(indice)
                x = w.mapTo(self, QPoint(0, 0)).x()
            y = riga.mapTo(self, QPoint(0, 0)).y()
            self.indicatore.mostra(QRect(x - 2, y + 2, 5, riga.height() - 4))

    def dragLeaveEvent(self, _):
        self.indicatore.hide()

    def dropEvent(self, ev):
        self.indicatore.hide()
        if not ev.mimeData().hasFormat(MIME):
            return
        chiave = bytes(ev.mimeData().data(MIME)).decode()
        sezione = self.sezioni.get(chiave)
        if sezione is None:
            return
        riga, indice, nuova = self._bersaglio(ev.position().toPoint())
        ev.acceptProposedAction()

        if nuova:
            posizione = self.verticale.indexOf(riga) + (0 if indice == 0 else 1) \
                if riga is not None else -1
            destinazione = self._nuova_riga(posizione)
            destinazione.addWidget(sezione)
        else:
            if riga.indexOf(sezione) == indice:
                return
            riga.insertWidget(indice, sezione)
        sezione.show()
        self._pulisci()
        self._distribuisci(riga if not nuova else None)
        self.disposizione_cambiata.emit()

    # --------------------------------------------------------------- utilità
    def _pulisci(self) -> None:
        """Elimina le righe rimaste senza sezioni."""
        for i in reversed(range(self.verticale.count())):
            w = self.verticale.widget(i)
            if isinstance(w, QSplitter) and w.count() == 0:
                w.setParent(None)
                w.deleteLater()
            elif isinstance(w, QSplitter):
                w.setVisible(any(not w.widget(j).isHidden() for j in range(w.count())))

    def _distribuisci(self, riga: QSplitter | None) -> None:
        """Riparte lo spazio in modo che nessuna sezione resti a dimensione zero."""
        righe = [riga] if riga is not None else self._righe()
        for r in righe:
            if r is None or r.count() == 0:
                continue
            visibili = [j for j in range(r.count()) if not r.widget(j).isHidden()]
            if not visibili:
                continue
            quota = max(LARGHEZZA_MINIMA, r.width() // len(visibili))
            r.setSizes([quota if j in visibili else 0 for j in range(r.count())])
        altezze = self.verticale.sizes()
        if altezze and min(altezze) < ALTEZZA_MINIMA:
            totale = sum(altezze) or self.height()
            self.verticale.setSizes([max(ALTEZZA_MINIMA, totale // max(1, len(altezze)))
                                     for _ in altezze])

    def mostra_sezione(self, chiave: str, visibile: bool) -> None:
        sezione = self.sezioni.get(chiave)
        if sezione is None:
            return
        sezione.setVisible(visibile)
        self._pulisci()
        if visibile:
            riga = sezione.parent()
            while riga is not None and not isinstance(riga, QSplitter):
                riga = riga.parent()
            self._distribuisci(riga if riga is not self.verticale else None)
        self.disposizione_cambiata.emit()

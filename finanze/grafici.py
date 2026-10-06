"""Grafici disegnati con QPainter: nessuna libreria esterna, tutto offline."""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QColor, QFont, QFontMetrics, QLinearGradient, QPainter,
                           QPainterPath, QPen)
from PySide6.QtWidgets import QSizePolicy, QToolTip, QWidget

from .tema import PALETTE_GRAFICI
from .utils import compatto, euro


class BaseGrafico(QWidget):
    def __init__(self, colori: dict, titolo: str = "", parent=None):
        super().__init__(parent)
        self.c = colori
        self.titolo = titolo
        self.setMinimumHeight(220)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)
        self._zone: list[tuple[QRectF, str]] = []

    def aggiorna_tema(self, colori: dict) -> None:
        self.c = colori
        self.update()

    def _pittore(self) -> QPainter:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.TextAntialiasing, True)
        return p

    def _vuoto(self, p: QPainter, messaggio: str = "Nessun dato da mostrare") -> None:
        p.setPen(QColor(self.c["testo2"]))
        f = QFont(); f.setPointSize(10); p.setFont(f)
        p.drawText(self.rect(), Qt.AlignCenter, messaggio)

    def mouseMoveEvent(self, ev):
        for rect, testo in self._zone:
            if rect.contains(ev.position()):
                QToolTip.showText(ev.globalPosition().toPoint(), testo, self)
                return
        QToolTip.hideText()
        super().mouseMoveEvent(ev)


class GraficoLinea(BaseGrafico):
    """Andamento temporale con area sfumata."""

    def __init__(self, colori: dict, parent=None):
        super().__init__(colori, parent=parent)
        self.punti: list[tuple[str, float]] = []
        self.colore = colori["accento"]

    def imposta_dati(self, punti: list[tuple[str, float]], colore: str | None = None) -> None:
        self.punti = punti
        if colore:
            self.colore = colore
        self.update()

    def paintEvent(self, _):
        p = self._pittore()
        self._zone.clear()
        if len(self.punti) < 2:
            self._vuoto(p); return

        compatto_x = self.height() < 150
        ml, mr, mt, mb = 62, 14, 16, (10 if compatto_x else 30)
        w, h = self.width(), self.height()
        area = QRectF(ml, mt, max(10, w - ml - mr), max(10, h - mt - mb))
        valori = [v for _, v in self.punti]
        vmin, vmax = min(valori), max(valori)
        if vmin == vmax:
            vmin -= 1; vmax += 1
        margine = (vmax - vmin) * 0.12
        vmin -= margine; vmax += margine

        f = QFont(); f.setPointSize(8); p.setFont(f)
        # griglia + asse Y
        for i in range(5):
            y = area.top() + area.height() * i / 4
            p.setPen(QPen(QColor(self.c["griglia"]), 1, Qt.DotLine))
            p.drawLine(QPointF(area.left(), y), QPointF(area.right(), y))
            val = vmax - (vmax - vmin) * i / 4
            p.setPen(QColor(self.c["testo2"]))
            p.drawText(QRectF(0, y - 9, ml - 8, 18),
                       Qt.AlignRight | Qt.AlignVCenter, compatto(val))

        def xy(i: int, v: float) -> QPointF:
            x = area.left() + area.width() * i / (len(self.punti) - 1)
            y = area.bottom() - (v - vmin) / (vmax - vmin) * area.height()
            return QPointF(x, y)

        linea = QPainterPath(xy(0, valori[0]))
        for i, v in enumerate(valori[1:], start=1):
            linea.lineTo(xy(i, v))

        area_path = QPainterPath(linea)
        area_path.lineTo(QPointF(area.right(), area.bottom()))
        area_path.lineTo(QPointF(area.left(), area.bottom()))
        area_path.closeSubpath()
        grad = QLinearGradient(0, area.top(), 0, area.bottom())
        col = QColor(self.colore)
        grad.setColorAt(0, QColor(col.red(), col.green(), col.blue(), 110))
        grad.setColorAt(1, QColor(col.red(), col.green(), col.blue(), 8))
        p.setPen(Qt.NoPen); p.setBrush(grad); p.drawPath(area_path)

        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(self.colore), 2.2))
        p.drawPath(linea)

        # punti + etichette X + zone tooltip
        passo = max(1, len(self.punti) // 8)
        p.setPen(Qt.NoPen)
        for i, (etic, v) in enumerate(self.punti):
            pt = xy(i, v)
            p.setBrush(QColor(self.colore))
            p.drawEllipse(pt, 3.0, 3.0)
            self._zone.append((QRectF(pt.x() - 12, area.top(), 24, area.height()),
                               f"{etic}: {euro(v)}"))
            if not compatto_x and (i % passo == 0 or i == len(self.punti) - 1):
                p.setPen(QColor(self.c["testo2"]))
                p.drawText(QRectF(pt.x() - 34, area.bottom() + 6, 68, 18),
                           Qt.AlignCenter, etic)
                p.setPen(Qt.NoPen)


class GraficoBarre(BaseGrafico):
    """Barre raggruppate (entrate vs uscite) oppure singole."""

    def __init__(self, colori: dict, parent=None):
        super().__init__(colori, parent=parent)
        self.dati: list[tuple[str, list[float]]] = []
        self.serie: list[tuple[str, str]] = []   # (nome, colore)
        self.orizzontale = False

    def imposta_dati(self, dati, serie) -> None:
        self.dati, self.serie = dati, serie
        self.update()

    def paintEvent(self, _):
        p = self._pittore()
        self._zone.clear()
        if not self.dati:
            self._vuoto(p); return
        if self.orizzontale:
            self._orizzontale(p); return

        ridotto = self.height() < 170
        ml, mr, mt, mb = 62, 14, (12 if ridotto else 34), (10 if ridotto else 32)
        area = QRectF(ml, mt, max(10, self.width() - ml - mr),
                      max(10, self.height() - mt - mb))
        massimo = max((max(v) if v else 0) for _, v in self.dati) or 1
        massimo *= 1.15
        f = QFont(); f.setPointSize(8); p.setFont(f)

        for i in range(5):
            y = area.top() + area.height() * i / 4
            p.setPen(QPen(QColor(self.c["griglia"]), 1, Qt.DotLine))
            p.drawLine(QPointF(area.left(), y), QPointF(area.right(), y))
            p.setPen(QColor(self.c["testo2"]))
            p.drawText(QRectF(0, y - 9, ml - 8, 18), Qt.AlignRight | Qt.AlignVCenter,
                       compatto(massimo - massimo * i / 4))

        # legenda
        x_leg = area.left()
        for nome, colore in ([] if ridotto else self.serie):
            p.setPen(Qt.NoPen); p.setBrush(QColor(colore))
            p.drawRoundedRect(QRectF(x_leg, 10, 10, 10), 3, 3)
            p.setPen(QColor(self.c["testo2"]))
            larg = QFontMetrics(f).horizontalAdvance(nome)
            p.drawText(QRectF(x_leg + 15, 6, larg + 12, 18), Qt.AlignLeft | Qt.AlignVCenter, nome)
            x_leg += 15 + larg + 20

        n_gruppi = len(self.dati)
        n_serie = max(1, len(self.serie))
        larghezza_gruppo = area.width() / n_gruppi
        larghezza_barra = min(26, (larghezza_gruppo * 0.68) / n_serie)

        for g, (etic, valori) in enumerate(self.dati):
            centro = area.left() + larghezza_gruppo * (g + 0.5)
            inizio = centro - (larghezza_barra * n_serie) / 2
            for s, v in enumerate(valori):
                altezza = max(1.0, (v / massimo) * area.height())
                rect = QRectF(inizio + s * larghezza_barra + 1.5,
                              area.bottom() - altezza, larghezza_barra - 3, altezza)
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(self.serie[s][1] if s < len(self.serie)
                                  else PALETTE_GRAFICI[s % 12]))
                p.drawRoundedRect(rect, 4, 4)
                nome_s = self.serie[s][0] if s < len(self.serie) else ""
                self._zone.append((rect.adjusted(-2, -6, 2, 6),
                                   f"{etic} · {nome_s}: {euro(v)}"))
            if not ridotto:
                p.setPen(QColor(self.c["testo2"]))
                p.drawText(QRectF(centro - larghezza_gruppo / 2, area.bottom() + 6,
                                  larghezza_gruppo, 18), Qt.AlignCenter, etic)

    def _orizzontale(self, p: QPainter):
        ml, mr, mt, mb = 130, 70, 8, 8
        area = QRectF(ml, mt, max(10, self.width() - ml - mr),
                      max(10, self.height() - mt - mb))
        massimo = max((max(v) if v else 0) for _, v in self.dati) or 1
        f = QFont(); f.setPointSize(9); p.setFont(f)
        n = len(self.dati)
        altezza = min(30.0, area.height() / max(1, n))
        for i, (etic, valori) in enumerate(self.dati):
            v = valori[0] if valori else 0
            y = area.top() + i * altezza + altezza * 0.18
            h = altezza * 0.64
            colore = self.serie[i][1] if i < len(self.serie) else PALETTE_GRAFICI[i % 12]
            p.setPen(QColor(self.c["testo"]))
            p.drawText(QRectF(4, y - 3, ml - 12, h + 6),
                       Qt.AlignRight | Qt.AlignVCenter, etic[:24])
            larghezza = max(2.0, (v / massimo) * area.width())
            rect = QRectF(area.left(), y, larghezza, h)
            p.setPen(Qt.NoPen); p.setBrush(QColor(colore))
            p.drawRoundedRect(rect, 5, 5)
            p.setPen(QColor(self.c["testo2"]))
            p.drawText(QRectF(area.left() + larghezza + 8, y - 3, mr, h + 6),
                       Qt.AlignLeft | Qt.AlignVCenter, compatto(v))
            self._zone.append((rect, f"{etic}: {euro(v)}"))


class GraficoCiambella(BaseGrafico):
    """Ripartizione percentuale con legenda laterale."""

    def __init__(self, colori: dict, parent=None):
        super().__init__(colori, parent=parent)
        self.dati: list[tuple[str, float, str]] = []   # (nome, valore, colore)
        self.centro_testo = ""
        self.centro_nota = ""

    def imposta_dati(self, dati, centro_testo="", centro_nota="") -> None:
        self.dati = dati
        self.centro_testo = centro_testo
        self.centro_nota = centro_nota
        self.update()

    def paintEvent(self, _):
        p = self._pittore()
        self._zone.clear()
        totale = sum(v for _, v, _ in self.dati)
        if totale <= 0:
            self._vuoto(p); return

        lato = min(self.width() * 0.52, self.height()) - 16
        lato = max(90.0, lato)
        rect = QRectF(14, (self.height() - lato) / 2, lato, lato)
        spessore = lato * 0.21
        interno = rect.adjusted(spessore, spessore, -spessore, -spessore)

        angolo = 90 * 16
        for i, (nome, valore, colore) in enumerate(self.dati):
            esteso = int(-360 * 16 * (valore / totale))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(colore or PALETTE_GRAFICI[i % 12]))
            p.drawPie(rect, angolo, esteso)
            angolo += esteso
        p.setBrush(QColor(self.c["pannello"]))
        p.drawEllipse(interno)

        # il testo centrale si adatta al diametro: niente scritte fuori dal cerchio
        f = QFont(); f.setBold(True)
        dimensione = max(7, min(14, int(interno.width() / 7)))
        f.setPointSize(dimensione)
        while dimensione > 6 and QFontMetrics(f).horizontalAdvance(
                self.centro_testo) > interno.width() - 10:
            dimensione -= 1
            f.setPointSize(dimensione)
        p.setFont(f)
        p.setPen(QColor(self.c["testo"]))
        spazio_nota = interno.height() > 54 and self.centro_nota
        p.drawText(interno.adjusted(0, -8 if spazio_nota else 0, 0, -8 if spazio_nota else 0),
                   Qt.AlignCenter, self.centro_testo)
        if spazio_nota:
            f.setPointSize(max(6, dimensione - 5)); f.setBold(False); p.setFont(f)
            p.setPen(QColor(self.c["testo2"]))
            if QFontMetrics(f).horizontalAdvance(self.centro_nota) <= interno.width() - 6:
                p.drawText(interno.adjusted(0, 16, 0, 16), Qt.AlignCenter, self.centro_nota)

        # legenda
        x = rect.right() + 22
        f.setPointSize(9); p.setFont(f)
        massimo_righe = max(1, int((self.height() - 10) // 21))
        for i, (nome, valore, colore) in enumerate(self.dati[:massimo_righe]):
            y = 8 + i * 21
            p.setPen(Qt.NoPen); p.setBrush(QColor(colore or PALETTE_GRAFICI[i % 12]))
            p.drawRoundedRect(QRectF(x, y + 4, 10, 10), 3, 3)
            p.setPen(QColor(self.c["testo"]))
            quota = valore / totale * 100
            testo = f"{nome[:22]}  ·  {quota:.0f}%"
            p.drawText(QRectF(x + 16, y, max(40.0, self.width() - x - 24), 18),
                       Qt.AlignLeft | Qt.AlignVCenter, testo)
            self._zone.append((QRectF(x, y, self.width() - x, 20),
                               f"{nome}: {euro(valore)} ({quota:.1f}%)"))


class Sparkline(QWidget):
    """Micro-grafico per le schede riepilogative."""

    def __init__(self, colori: dict, parent=None):
        super().__init__(parent)
        self.c = colori
        self.valori: list[float] = []
        self.colore = colori["accento"]
        self.setFixedHeight(34)

    def imposta_dati(self, valori: list[float], colore: str | None = None) -> None:
        self.valori = valori
        if colore:
            self.colore = colore
        self.update()

    def paintEvent(self, _):
        if len(self.valori) < 2:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        vmin, vmax = min(self.valori), max(self.valori)
        if vmin == vmax:
            vmin -= 1; vmax += 1
        w, h = self.width(), self.height() - 6
        path = QPainterPath()
        for i, v in enumerate(self.valori):
            x = w * i / (len(self.valori) - 1)
            y = 3 + h - (v - vmin) / (vmax - vmin) * h
            path.moveTo(x, y) if i == 0 else path.lineTo(x, y)
        p.setPen(QPen(QColor(self.colore), 1.8))
        p.drawPath(path)

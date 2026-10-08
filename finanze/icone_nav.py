"""Icone della barra di navigazione, disegnate con QPainter.

I simboli tipografici hanno metriche diverse fra loro e risultano disallineati
dentro i pulsanti. Qui ogni icona è disegnata dentro un riquadro quadrato, così
restano tutte centrate sia a barra aperta sia a barra chiusa.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QColor, QIcon, QPainter, QPainterPath, QPen,
                           QPixmap)

LATO = 20

# Stili disponibili: spessore del tratto e riempimento delle forme chiuse
# nome -> (spessore del tratto, opacità del riempimento 0-255)
STILI = {
    "sottile": (1.25, 0),
    "medio": (1.7, 0),
    "spesso": (2.3, 0),
    "tenue": (1.6, 70),
    "pieno": (1.4, 255),
}
STILE_PREDEFINITO = "medio"


def _fattore_schermo() -> float:
    """Densità dello schermo: senza, le icone risultano sfocate sui display HiDPI."""
    from PySide6.QtGui import QGuiApplication

    app = QGuiApplication.instance()
    if app is None:
        return 1.0
    schermo = app.primaryScreen()
    return float(schermo.devicePixelRatio()) if schermo else 1.0


def _pittore(pixmap: QPixmap, colore: str, stile: str = STILE_PREDEFINITO,
             scala: float = 1.0) -> QPainter:
    spessore, opacita = STILI.get(stile, STILI[STILE_PREDEFINITO])
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.scale(scala, scala)
    penna = QPen(QColor(colore))
    penna.setWidthF(spessore)
    penna.setCapStyle(Qt.RoundCap)
    penna.setJoinStyle(Qt.RoundJoin)
    p.setPen(penna)
    if opacita:
        riempimento = QColor(colore)
        riempimento.setAlpha(opacita)
        p.setBrush(riempimento)
    else:
        p.setBrush(Qt.NoBrush)
    return p


def _solo_contorno(p: QPainter):
    """Esegue il disegno senza riempimento, mantenendo il tratto."""
    pennello = p.brush()
    p.setBrush(Qt.NoBrush)
    return pennello


def _cruscotto(p: QPainter, r: QRectF) -> None:
    """Quattro riquadri: la griglia del pannello."""
    m = r.width() * 0.09
    larghezza = (r.width() - m) / 2
    for i in (0, 1):
        for j in (0, 1):
            p.drawRoundedRect(
                QRectF(r.left() + i * (larghezza + m), r.top() + j * (larghezza + m),
                       larghezza, larghezza), 2, 2)


def _movimenti(p: QPainter, r: QRectF) -> None:
    """Righe di un elenco con il punto a sinistra."""
    for i in range(3):
        y = r.top() + r.height() * (0.17 + i * 0.33)
        pennello = p.brush()
        p.setBrush(p.pen().color())
        p.drawEllipse(QPointF(r.left() + 1.5, y), 1.2, 1.2)
        p.setBrush(pennello)
        p.drawLine(QPointF(r.left() + 5.5, y), QPointF(r.right(), y))


def _budget(p: QPainter, r: QRectF) -> None:
    """Due barre di avanzamento."""
    altezza = r.height() * 0.2
    p.drawRoundedRect(QRectF(r.left(), r.top() + r.height() * 0.16,
                             r.width(), altezza), 3, 3)
    p.drawRoundedRect(QRectF(r.left(), r.top() + r.height() * 0.62,
                             r.width() * 0.6, altezza), 3, 3)


def _obiettivi(p: QPainter, r: QRectF) -> None:
    """Bersaglio: anello esterno vuoto, centro pieno."""
    centro = r.center()
    pennello = _solo_contorno(p)
    p.drawEllipse(centro, r.width() / 2, r.height() / 2)
    p.setBrush(pennello if pennello.style() != Qt.NoBrush else p.pen().color())
    p.drawEllipse(centro, r.width() / 5, r.height() / 5)
    p.setBrush(pennello)


def _ricorrenti(p: QPainter, r: QRectF) -> None:
    """Freccia circolare: arco aperto con la punta sull'estremità."""
    angolo = 55
    p.drawArc(QRectF(r), angolo * 16, 300 * 16)
    radianti = math.radians(angolo)
    cx, cy = r.center().x(), r.center().y()
    x = cx + r.width() / 2 * math.cos(radianti)
    y = cy - r.height() / 2 * math.sin(radianti)
    lato = max(2.6, r.width() * 0.16)
    # triangolo orientato lungo la tangente dell'arco
    tx, ty = math.sin(radianti), math.cos(radianti)      # direzione tangente
    nx, ny = math.cos(radianti), -math.sin(radianti)     # direzione radiale
    punta = QPainterPath()
    punta.moveTo(x + tx * lato, y + ty * lato)
    punta.lineTo(x - nx * lato * 0.75, y - ny * lato * 0.75)
    punta.lineTo(x + nx * lato * 0.75, y + ny * lato * 0.75)
    punta.closeSubpath()
    p.fillPath(punta, p.pen().color())


def _rapporti(p: QPainter, r: QRectF) -> None:
    """Istogramma."""
    larghezza = r.width() * 0.2
    for i, quota in enumerate((0.45, 0.8, 0.6)):
        x = r.left() + i * (r.width() - larghezza) / 2
        p.drawRoundedRect(QRectF(x, r.bottom() - r.height() * quota,
                                 larghezza, r.height() * quota), 2, 2)


def _strumenti(p: QPainter, r: QRectF) -> None:
    """Calcolatrice: cornice e display a contorno, tasti pieni."""
    pennello = _solo_contorno(p)
    p.drawRoundedRect(QRectF(r.left() + r.width() * 0.12, r.top(),
                             r.width() * 0.76, r.height()), 3, 3)
    p.drawRoundedRect(QRectF(r.left() + r.width() * 0.26, r.top() + r.height() * 0.13,
                             r.width() * 0.48, r.height() * 0.2), 1.5, 1.5)
    p.setBrush(p.pen().color())
    raggio = max(0.9, r.width() * 0.055)
    for j in (0.57, 0.8):
        for i in (0.3, 0.5, 0.7):
            p.drawEllipse(QPointF(r.left() + r.width() * i, r.top() + r.height() * j),
                          raggio, raggio)
    p.setBrush(pennello)


def _impostazioni(p: QPainter, r: QRectF) -> None:
    """Cursori di regolazione."""
    for i, posizione in enumerate((0.35, 0.65)):
        y = r.top() + r.height() * (0.28 + i * 0.44)
        p.drawLine(QPointF(r.left(), y), QPointF(r.right(), y))
        pennello = p.brush()
        p.setBrush(p.pen().color())
        p.drawEllipse(QPointF(r.left() + r.width() * posizione, y), 2.5, 2.5)
        p.setBrush(pennello)


DISEGNI = {
    "cruscotto": _cruscotto,
    "movimenti": _movimenti,
    "budget": _budget,
    "obiettivi": _obiettivi,
    "ricorrenti": _ricorrenti,
    "rapporti": _rapporti,
    "strumenti": _strumenti,
    "impostazioni": _impostazioni,
}


def _pixmap(nome: str, colore: str, lato: int = LATO,
            stile: str = STILE_PREDEFINITO, densita: float | None = None) -> QPixmap:
    """Disegna l'icona alla densità dello schermo, così resta nitida."""
    dpr = _fattore_schermo() if densita is None else densita
    pixmap = QPixmap(int(lato * dpr), int(lato * dpr))
    pixmap.fill(Qt.transparent)
    pixmap.setDevicePixelRatio(dpr)
    p = _pittore(pixmap, colore, stile, dpr)
    margine = lato * 0.16
    DISEGNI[nome](p, QRectF(margine, margine, lato - 2 * margine, lato - 2 * margine))
    p.end()
    return pixmap


def icona(nome: str, colore_normale: str, colore_attivo: str,
          lato: int = LATO, stile: str = STILE_PREDEFINITO) -> QIcon:
    """Icona con una versione per la voce a riposo e una per quella attiva."""
    ic = QIcon()
    ic.addPixmap(_pixmap(nome, colore_normale, lato, stile), QIcon.Normal, QIcon.Off)
    ic.addPixmap(_pixmap(nome, colore_attivo, lato, stile), QIcon.Normal, QIcon.On)
    ic.addPixmap(_pixmap(nome, colore_attivo, lato, stile), QIcon.Active, QIcon.Off)
    return ic


def icona_menu(colore: str, aperta: bool, lato: int = 20,
               stile: str = STILE_PREDEFINITO) -> QIcon:
    """Pulsante del menu laterale: pannello con la freccia nel verso giusto."""
    dpr = _fattore_schermo()
    pixmap = QPixmap(int(lato * dpr), int(lato * dpr))
    pixmap.fill(Qt.transparent)
    pixmap.setDevicePixelRatio(dpr)
    p = _pittore(pixmap, colore, stile, dpr)
    p.setBrush(Qt.NoBrush)
    r = QRectF(lato * 0.12, lato * 0.18, lato * 0.76, lato * 0.64)
    p.drawRoundedRect(r, 3, 3)
    x = r.left() + r.width() * 0.34
    p.drawLine(QPointF(x, r.top()), QPointF(x, r.bottom()))
    punta_x = r.left() + r.width() * (0.72 if aperta else 0.55)
    verso = -1 if aperta else 1
    centro_y = r.center().y()
    p.drawLine(QPointF(punta_x, centro_y - 2.6),
               QPointF(punta_x + verso * 2.6, centro_y))
    p.drawLine(QPointF(punta_x + verso * 2.6, centro_y),
               QPointF(punta_x, centro_y + 2.6))
    p.end()
    ic = QIcon()
    ic.addPixmap(pixmap)
    return ic

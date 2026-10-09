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
# Ogni stile è una famiglia di disegni a sé: cambia il segno, non lo spessore.
# nome -> (spessore del tratto, opacità del riempimento 0-255)
STILI = {
    "sottile": (1.25, 0),
    "pieno": (1.0, 255),
    "geometrico": (1.9, 0),
}
STILE_PREDEFINITO = "sottile"


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
    famiglia = FAMIGLIE.get(stile, FAMIGLIE[STILE_PREDEFINITO])
    famiglia[nome](p, QRectF(margine, margine,
                             lato - 2 * margine, lato - 2 * margine))
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


def anteprima_stile(stile: str, colore: str, lato: int = 19,
                    spaziatura: int = 8, colonne: int = 4) -> QPixmap:
    """Tutte le icone di un certo stile, disposte su una griglia compatta."""
    dpr = _fattore_schermo()
    nomi = list(DISEGNI)
    righe = (len(nomi) + colonne - 1) // colonne
    larghezza = colonne * lato + (colonne - 1) * spaziatura
    altezza = righe * lato + (righe - 1) * spaziatura
    tela = QPixmap(int(larghezza * dpr), int(altezza * dpr))
    tela.fill(Qt.transparent)
    tela.setDevicePixelRatio(dpr)
    p = QPainter(tela)
    p.setRenderHint(QPainter.Antialiasing, True)
    for i, nome in enumerate(nomi):
        x = (i % colonne) * (lato + spaziatura)
        y = (i // colonne) * (lato + spaziatura)
        p.drawPixmap(x, y, _pixmap(nome, colore, lato, stile))
    p.end()
    return tela


# ---------------------------------------------------------------------------
# Famiglia «pieno»: sagome compatte, con metafore diverse da quelle lineari
# ---------------------------------------------------------------------------

def _p_cruscotto(p: QPainter, r: QRectF) -> None:
    """Tachimetro: arco pieno con lancetta."""
    p.setBrush(p.pen().color())
    arco = QRectF(r.left(), r.top() + r.height() * 0.1,
                  r.width(), r.height() * 1.25)
    strada = QPainterPath()
    strada.moveTo(arco.center())
    strada.arcTo(arco, 20, 140)
    strada.closeSubpath()
    p.drawPath(strada)
    penna = QPen(p.pen())
    penna.setWidthF(2.0)
    p.setPen(penna)
    centro = QPointF(r.center().x(), r.center().y() + r.height() * 0.22)
    p.drawLine(centro, QPointF(r.center().x() + r.width() * 0.3,
                               r.top() + r.height() * 0.08))


def _p_movimenti(p: QPainter, r: QRectF) -> None:
    """Due frecce affiancate: entrate che salgono, uscite che scendono."""
    p.setBrush(p.pen().color())
    larghezza = r.width() * 0.3
    for i, verso in enumerate((-1, 1)):
        x = r.left() + i * (r.width() - larghezza)
        alto = r.top() if verso < 0 else r.top() + r.height() * 0.3
        gambo = QRectF(x + larghezza * 0.3, alto + r.height() * 0.22,
                       larghezza * 0.4, r.height() * 0.48)
        p.drawRect(gambo)
        punta = QPainterPath()
        y = alto if verso < 0 else alto + r.height() * 0.7
        punta.moveTo(x + larghezza / 2, y)
        punta.lineTo(x, y + verso * -r.height() * 0.28)
        punta.lineTo(x + larghezza, y + verso * -r.height() * 0.28)
        punta.closeSubpath()
        p.fillPath(punta, p.pen().color())


def _p_budget(p: QPainter, r: QRectF) -> None:
    """Portafoglio: sagoma piena con la chiusura ritagliata."""
    sagoma = QPainterPath()
    sagoma.setFillRule(Qt.OddEvenFill)
    sagoma.addRoundedRect(
        QRectF(r.left(), r.top() + r.height() * 0.16,
               r.width(), r.height() * 0.7), 3, 3)
    sagoma.addEllipse(QPointF(r.right() - r.width() * 0.26, r.center().y()),
                      r.width() * 0.1, r.width() * 0.1)
    p.fillPath(sagoma, p.pen().color())


def _p_obiettivi(p: QPainter, r: QRectF) -> None:
    """Bandierina su asta."""
    penna = QPen(p.pen()); penna.setWidthF(1.8); p.setPen(penna)
    asta = r.left() + r.width() * 0.2
    p.drawLine(QPointF(asta, r.top()), QPointF(asta, r.bottom()))
    drappo = QPainterPath()
    drappo.moveTo(asta, r.top() + r.height() * 0.06)
    drappo.lineTo(r.right(), r.top() + r.height() * 0.22)
    drappo.lineTo(asta, r.top() + r.height() * 0.42)
    drappo.closeSubpath()
    p.fillPath(drappo, p.pen().color())


def _p_ricorrenti(p: QPainter, r: QRectF) -> None:
    """Orologio: quadrante pieno con le lancette ritagliate."""
    quadrante = QPainterPath()
    quadrante.setFillRule(Qt.OddEvenFill)
    quadrante.addEllipse(r.center(), r.width() / 2, r.height() / 2)
    c = r.center()
    spessore = max(1.0, r.width() * 0.08)
    quadrante.addRect(QRectF(c.x() - spessore / 2, c.y() - r.height() * 0.3,
                             spessore, r.height() * 0.34))
    quadrante.addRect(QRectF(c.x() - spessore / 2, c.y() - spessore / 2,
                             r.width() * 0.3, spessore))
    p.fillPath(quadrante, p.pen().color())


def _p_rapporti(p: QPainter, r: QRectF) -> None:
    """Torta a spicchi."""
    p.setBrush(p.pen().color())
    fetta = QPainterPath()
    fetta.moveTo(r.center())
    fetta.arcTo(QRectF(r), 60, 300)
    fetta.closeSubpath()
    p.drawPath(fetta)


def _p_strumenti(p: QPainter, r: QRectF) -> None:
    """Chiave inglese."""
    penna = QPen(p.pen()); penna.setWidthF(3.4); p.setPen(penna)
    p.setBrush(Qt.NoBrush)
    p.drawLine(QPointF(r.left() + r.width() * 0.3, r.bottom() - r.height() * 0.18),
               QPointF(r.right() - r.width() * 0.22, r.top() + r.height() * 0.26))
    penna.setWidthF(1.6); p.setPen(penna)
    p.setBrush(p.pen().color())
    testa = QRectF(r.left(), r.top(), r.width() * 0.46, r.height() * 0.46)
    p.drawEllipse(testa)


def _p_impostazioni(p: QPainter, r: QRectF) -> None:
    """Ingranaggio pieno."""
    p.setBrush(p.pen().color())
    centro = r.center()
    raggio = r.width() / 2
    denti = QPainterPath()
    for i in range(8):
        angolo = math.radians(i * 45)
        larghezza = math.radians(13)
        for passo in (-larghezza, larghezza):
            x = centro.x() + raggio * math.cos(angolo + passo)
            y = centro.y() - raggio * math.sin(angolo + passo)
            if i == 0 and passo < 0:
                denti.moveTo(x, y)
            else:
                denti.lineTo(x, y)
        interno = raggio * 0.72
        for passo in (larghezza * 1.6, -larghezza * 1.6):
            x = centro.x() + interno * math.cos(angolo + math.radians(22.5) + passo)
            y = centro.y() - interno * math.sin(angolo + math.radians(22.5) + passo)
            denti.lineTo(x, y)
    denti.closeSubpath()
    p.fillPath(denti, p.pen().color())


# ---------------------------------------------------------------------------
# Famiglia «geometrico»: segno squadrato, costruito su rette e angoli
# ---------------------------------------------------------------------------

def _g_cruscotto(p: QPainter, r: QRectF) -> None:
    """Riquadro diviso in pannelli disuguali."""
    p.drawRect(r)
    x = r.left() + r.width() * 0.58
    p.drawLine(QPointF(x, r.top()), QPointF(x, r.bottom()))
    p.drawLine(QPointF(x, r.center().y()), QPointF(r.right(), r.center().y()))


def _g_movimenti(p: QPainter, r: QRectF) -> None:
    """Scambio: due frecce squadrate in direzioni opposte."""
    for i, verso in enumerate((1, -1)):
        y = r.top() + r.height() * (0.26 if i == 0 else 0.74)
        p.drawLine(QPointF(r.left(), y), QPointF(r.right(), y))
        x = r.right() if verso > 0 else r.left()
        p.drawLine(QPointF(x, y), QPointF(x - verso * r.width() * 0.26,
                                          y - r.height() * 0.17))
        p.drawLine(QPointF(x, y), QPointF(x - verso * r.width() * 0.26,
                                          y + r.height() * 0.17))


def _g_budget(p: QPainter, r: QRectF) -> None:
    """Barra segmentata dentro una cornice."""
    p.drawRect(QRectF(r.left(), r.top() + r.height() * 0.28,
                      r.width(), r.height() * 0.44))
    for frazione in (0.38, 0.62):
        x = r.left() + r.width() * frazione
        p.drawLine(QPointF(x, r.top() + r.height() * 0.28),
                   QPointF(x, r.bottom() - r.height() * 0.28))


def _g_obiettivi(p: QPainter, r: QRectF) -> None:
    """Rombi concentrici."""
    for fattore in (1.0, 0.45):
        rombo = QPainterPath()
        mx, my = r.width() / 2 * fattore, r.height() / 2 * fattore
        c = r.center()
        rombo.moveTo(c.x(), c.y() - my)
        rombo.lineTo(c.x() + mx, c.y())
        rombo.lineTo(c.x(), c.y() + my)
        rombo.lineTo(c.x() - mx, c.y())
        rombo.closeSubpath()
        p.drawPath(rombo)


def _g_ricorrenti(p: QPainter, r: QRectF) -> None:
    """Percorso quadrato che torna su sé stesso."""
    p.drawRect(r)
    p.drawLine(QPointF(r.center().x(), r.top()),
               QPointF(r.center().x(), r.center().y()))
    p.drawLine(QPointF(r.center().x(), r.center().y()),
               QPointF(r.right(), r.center().y()))


def _g_rapporti(p: QPainter, r: QRectF) -> None:
    """Spezzata su assi."""
    p.drawLine(QPointF(r.left(), r.top()), QPointF(r.left(), r.bottom()))
    p.drawLine(QPointF(r.left(), r.bottom()), QPointF(r.right(), r.bottom()))
    punti = [(0.12, 0.66), (0.42, 0.3), (0.66, 0.5), (0.95, 0.12)]
    precedente = None
    for fx, fy in punti:
        corrente = QPointF(r.left() + r.width() * fx, r.top() + r.height() * fy)
        if precedente is not None:
            p.drawLine(precedente, corrente)
        precedente = corrente


def _g_strumenti(p: QPainter, r: QRectF) -> None:
    """Squadra da disegno."""
    squadra = QPainterPath()
    squadra.moveTo(r.left(), r.top())
    squadra.lineTo(r.left(), r.bottom())
    squadra.lineTo(r.right(), r.bottom())
    squadra.closeSubpath()
    p.drawPath(squadra)
    p.drawLine(QPointF(r.left() + r.width() * 0.28, r.bottom()),
               QPointF(r.left() + r.width() * 0.28, r.bottom() - r.height() * 0.2))
    p.drawLine(QPointF(r.left() + r.width() * 0.56, r.bottom()),
               QPointF(r.left() + r.width() * 0.56, r.bottom() - r.height() * 0.2))


def _g_impostazioni(p: QPainter, r: QRectF) -> None:
    """Interruttori a levetta squadrati."""
    for i, posizione in enumerate((0.0, 0.52)):
        y = r.top() + r.height() * (0.2 + i * 0.46)
        p.drawRect(QRectF(r.left(), y, r.width(), r.height() * 0.26))
        maniglia = QRectF(r.left() + r.width() * posizione, y,
                          r.width() * 0.48, r.height() * 0.26)
        p.fillRect(maniglia, p.pen().color())


FAMIGLIE = {
    "sottile": DISEGNI,
    "pieno": {
        "cruscotto": _p_cruscotto, "movimenti": _p_movimenti,
        "budget": _p_budget, "obiettivi": _p_obiettivi,
        "ricorrenti": _p_ricorrenti, "rapporti": _p_rapporti,
        "strumenti": _p_strumenti, "impostazioni": _p_impostazioni,
    },
    "geometrico": {
        "cruscotto": _g_cruscotto, "movimenti": _g_movimenti,
        "budget": _g_budget, "obiettivi": _g_obiettivi,
        "ricorrenti": _g_ricorrenti, "rapporti": _g_rapporti,
        "strumenti": _g_strumenti, "impostazioni": _g_impostazioni,
    },
}

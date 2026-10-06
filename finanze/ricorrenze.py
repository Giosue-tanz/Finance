"""Calcolo delle scadenze per i movimenti ricorrenti (solo stdlib)."""
from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta


def _d(testo: str) -> date | None:
    try:
        a, m, g = (int(x) for x in testo.split("-"))
        return date(a, m, g)
    except Exception:
        return None


def giorno_valido(anno: int, mese: int, giorno: int) -> date:
    ultimo = monthrange(anno, mese)[1]
    return date(anno, mese, min(max(giorno, 1), ultimo))


def scadenze_dovute(frequenza: str, inizio: str, giorno: int,
                    ultima: str, fino_a: date) -> list[date]:
    """Elenco delle date da generare, estremi inclusi, in ordine crescente."""
    d_inizio = _d(inizio) or fino_a
    d_ultima = _d(ultima)
    cursore = d_inizio
    risultato: list[date] = []
    guardia = 0

    while cursore <= fino_a and guardia < 1200:
        guardia += 1
        if d_ultima is None or cursore > d_ultima:
            risultato.append(cursore)
        cursore = prossima(frequenza, cursore, giorno)
    return risultato


def prossima(frequenza: str, corrente: date, giorno: int) -> date:
    if frequenza == "settimanale":
        return corrente + timedelta(days=7)
    if frequenza == "quindicinale":
        return corrente + timedelta(days=14)
    if frequenza == "annuale":
        return giorno_valido(corrente.year + 1, corrente.month, giorno or corrente.day)
    if frequenza == "trimestrale":
        mese = corrente.month + 3
        anno = corrente.year + (mese - 1) // 12
        return giorno_valido(anno, (mese - 1) % 12 + 1, giorno or corrente.day)
    # mensile (default)
    mese = corrente.month + 1
    anno = corrente.year + (mese - 1) // 12
    return giorno_valido(anno, (mese - 1) % 12 + 1, giorno or corrente.day)

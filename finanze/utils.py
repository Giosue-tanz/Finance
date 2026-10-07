"""Funzioni di supporto: formattazione, date, CSV."""
from __future__ import annotations

import csv
from calendar import monthrange
from datetime import date, timedelta

MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
        "agosto", "settembre", "ottobre", "novembre", "dicembre"]


def euro(valore: float, valuta: str = "€") -> str:
    segno = "-" if valore < 0 else ""
    testo = f"{abs(valore):,.2f}".replace(",", "~").replace(".", ",").replace("~", ".")
    return f"{segno}{testo} {valuta}"


def compatto(valore: float) -> str:
    a = abs(valore)
    if a >= 1_000_000:
        return f"{valore/1_000_000:.1f}M".replace(".", ",")
    if a >= 1_000:
        return f"{valore/1_000:.1f}k".replace(".", ",")
    return f"{valore:.0f}"


def data_it(iso: str) -> str:
    try:
        a, m, g = iso.split("-")
        return f"{g}/{m}/{a}"
    except Exception:
        return iso


def mese_corrente() -> tuple[str, str]:
    o = date.today()
    return (date(o.year, o.month, 1).isoformat(),
            date(o.year, o.month, monthrange(o.year, o.month)[1]).isoformat())


def mese_precedente() -> tuple[str, str]:
    o = date.today()
    anno, mese = (o.year - 1, 12) if o.month == 1 else (o.year, o.month - 1)
    return (date(anno, mese, 1).isoformat(),
            date(anno, mese, monthrange(anno, mese)[1]).isoformat())


def anno_corrente() -> tuple[str, str]:
    a = date.today().year
    return date(a, 1, 1).isoformat(), date(a, 12, 31).isoformat()


# Periodi selezionabili sui singoli riquadri del cruscotto
PERIODI = {
    "mese": "Mese corrente",
    "mese_scorso": "Mese scorso",
    "tre_mesi": "Ultimi 3 mesi",
    "sei_mesi": "Ultimi 6 mesi",
    "anno": "Anno corrente",
    "dodici_mesi": "Ultimi 12 mesi",
    "tutto": "Tutto",
}

# Finestre temporali per i grafici mensili
FINESTRE = {"6": "6 mesi", "12": "12 mesi", "24": "24 mesi", "36": "36 mesi"}


def _indietro_mesi(riferimento: date, mesi: int) -> date:
    """Primo giorno del mese situato «mesi» prima di quello di riferimento."""
    totale = riferimento.year * 12 + (riferimento.month - 1) - mesi
    return date(totale // 12, totale % 12 + 1, 1)


def intervallo(periodo: str) -> tuple[str, str]:
    """(dal, al) in formato ISO per una delle chiavi di PERIODI."""
    oggi = date.today()
    if periodo == "mese":
        return mese_corrente()
    if periodo == "mese_scorso":
        return mese_precedente()
    if periodo == "anno":
        return anno_corrente()
    if periodo == "tutto":
        return "0001-01-01", "9999-12-31"
    mesi = {"tre_mesi": 2, "sei_mesi": 5, "dodici_mesi": 11}.get(periodo, 0)
    return _indietro_mesi(oggi, mesi).isoformat(), oggi.isoformat()


def intervallo_precedente(periodo: str) -> tuple[str, str]:
    """Finestra precedente della stessa ampiezza, per i confronti."""
    if periodo == "mese":
        return mese_precedente()
    if periodo == "tutto":
        return "0001-01-01", "0001-01-01"
    dal, al = intervallo(periodo)
    d = date.fromisoformat(dal)
    a = date.fromisoformat(al)
    durata = (a - d).days + 1
    return (d - timedelta(days=durata)).isoformat(), (d - timedelta(days=1)).isoformat()


def giorni_mese() -> tuple[int, int, int]:
    """(giorni trascorsi, giorni totali, giorni rimanenti) del mese corrente."""
    o = date.today()
    totali = monthrange(o.year, o.month)[1]
    return o.day, totali, totali - o.day


def etichetta_mese(iso_mese: str) -> str:
    try:
        a, m = iso_mese.split("-")
        return f"{MESI[int(m)-1][:3]} {a[2:]}"
    except Exception:
        return iso_mese


def esporta_csv(percorso: str, righe, intestazioni: list[str]) -> int:
    with open(percorso, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(intestazioni)
        n = 0
        for r in righe:
            w.writerow([r[c] for c in intestazioni])
            n += 1
    return n


def importa_csv(percorso: str) -> list[dict]:
    """Legge un CSV con colonne data;tipo;importo;categoria;conto;descrizione."""
    risultato = []
    with open(percorso, newline="", encoding="utf-8-sig") as f:
        campione = f.read(2048)
        f.seek(0)
        try:
            dialetto = csv.Sniffer().sniff(campione, delimiters=";,\t")
        except csv.Error:
            dialetto = csv.excel
            dialetto.delimiter = ";"
        for riga in csv.DictReader(f, dialect=dialetto):
            norm = { (k or "").strip().lower(): (v or "").strip() for k, v in riga.items() }
            data_v = norm.get("data", "")
            if "/" in data_v:
                p = data_v.split("/")
                if len(p) == 3:
                    data_v = f"{p[2]}-{p[1].zfill(2)}-{p[0].zfill(2)}"
            imp = norm.get("importo", "0").replace(".", "").replace(",", ".")
            try:
                imp_f = abs(float(imp))
            except ValueError:
                continue
            tipo = norm.get("tipo", "").lower()
            if tipo not in ("entrata", "uscita"):
                tipo = "uscita" if norm.get("importo", "").strip().startswith("-") else "entrata"
            risultato.append({
                "data": data_v or date.today().isoformat(),
                "tipo": tipo,
                "importo": imp_f,
                "categoria": norm.get("categoria") or "Altro",
                "conto": norm.get("conto") or "Principale",
                "descrizione": norm.get("descrizione") or norm.get("note") or "",
                "etichette": "importato",
            })
    return risultato

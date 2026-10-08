"""Livello dati: SQLite locale, nessuna connessione di rete."""
from __future__ import annotations

import os
import shutil
import sqlite3
from datetime import date, datetime

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# I dati dell'utente vivono FUORI dalla cartella del codice: così aggiornare
# l'applicazione (git pull, nuova copia, reinstallazione) non li tocca mai.
DATA_DIR = os.path.join(
    os.environ.get("XDG_DATA_HOME", os.path.join(os.path.expanduser("~"), ".local", "share")),
    "Finance")
DB_PATH = os.path.join(DATA_DIR, "finanze.db")
BACKUP_DIR = os.path.join(DATA_DIR, "backup")

# Archivio delle versioni precedenti, quando i dati stavano dentro al progetto.
VECCHIO_DB = os.path.join(APP_DIR, "dati", "finanze.db")


def migra_archivio_storico() -> str | None:
    """Sposta l'archivio dalla vecchia posizione interna al progetto, se presente.

    Restituisce il percorso di origine se la migrazione è avvenuta.
    """
    if os.path.exists(DB_PATH) or not os.path.exists(VECCHIO_DB):
        return None
    os.makedirs(DATA_DIR, exist_ok=True)
    shutil.copy2(VECCHIO_DB, DB_PATH)
    try:
        os.replace(VECCHIO_DB, VECCHIO_DB + ".migrato")
    except OSError:
        pass
    return VECCHIO_DB

SCHEMA = """
CREATE TABLE IF NOT EXISTS conti (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    saldo_iniziale REAL NOT NULL DEFAULT 0,
    tipo TEXT NOT NULL DEFAULT 'Conto corrente'
);
CREATE TABLE IF NOT EXISTS categorie (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    tipo TEXT NOT NULL,            -- 'entrata' | 'uscita'
    colore TEXT NOT NULL DEFAULT '#6c8cff',
    icona TEXT NOT NULL DEFAULT '',
    UNIQUE(nome, tipo)
);
CREATE TABLE IF NOT EXISTS movimenti (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL,            -- YYYY-MM-DD
    tipo TEXT NOT NULL,            -- 'entrata' | 'uscita'
    importo REAL NOT NULL,
    categoria TEXT NOT NULL DEFAULT 'Altro',
    conto TEXT NOT NULL DEFAULT 'Principale',
    descrizione TEXT NOT NULL DEFAULT '',
    etichette TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS budget (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria TEXT NOT NULL UNIQUE,
    mensile REAL NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS obiettivi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    obiettivo REAL NOT NULL,
    accantonato REAL NOT NULL DEFAULT 0,
    scadenza TEXT NOT NULL DEFAULT '',
    note TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS ricorrenti (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descrizione TEXT NOT NULL,
    tipo TEXT NOT NULL,
    importo REAL NOT NULL,
    categoria TEXT NOT NULL DEFAULT 'Altro',
    conto TEXT NOT NULL DEFAULT 'Principale',
    frequenza TEXT NOT NULL DEFAULT 'mensile',   -- mensile | settimanale | annuale
    giorno INTEGER NOT NULL DEFAULT 1,
    inizio TEXT NOT NULL,
    ultima_generazione TEXT NOT NULL DEFAULT '',
    attiva INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS impostazioni (
    chiave TEXT PRIMARY KEY,
    valore TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_mov_data ON movimenti(data);
CREATE INDEX IF NOT EXISTS idx_mov_cat ON movimenti(categoria);
"""

CATEGORIE_DEFAULT = [
    # entrate
    ("Stipendio", "entrata", "#2fbf71", "💼"),
    ("Rimborsi", "entrata", "#4cc9a4", "💸"),
    ("Investimenti", "entrata", "#86d39b", "📈"),
    ("Bonus", "entrata", "#6ddfa0", "💰"),
    ("Vendite", "entrata", "#39b88a", "🏷"),
    ("Affitti", "entrata", "#8fd4b0", "🏠"),
    ("Interessi", "entrata", "#5fcf9e", "🏦"),
    ("Altre entrate", "entrata", "#b7e4c7", "💰"),
    # uscite
    ("Casa", "uscita", "#ef6f6c", "🏠"),
    ("Spesa alimentare", "uscita", "#f2994a", "🛒"),
    ("Trasporti", "uscita", "#f2c14e", "🚗"),
    ("Carburante", "uscita", "#e8a33d", "⛽"),
    ("Bollette", "uscita", "#c77dff", "💡"),
    ("Abbonamenti", "uscita", "#b388eb", "📺"),
    ("Salute", "uscita", "#56cfe1", "💊"),
    ("Farmacia", "uscita", "#64c7d8", "💊"),
    ("Palestra", "uscita", "#4cb5c4", "🏋"),
    ("Tempo libero", "uscita", "#ff9ecd", "🎬"),
    ("Ristoranti", "uscita", "#f08a7a", "🍽"),
    ("Viaggi", "uscita", "#7ec8e3", "✈"),
    ("Abbigliamento", "uscita", "#f58fb0", "👕"),
    ("Regali", "uscita", "#ffb4a2", "🎁"),
    ("Animali", "uscita", "#c9a227", "🐾"),
    ("Istruzione", "uscita", "#7f8cff", "📚"),
    ("Assicurazioni", "uscita", "#8d99ae", "⚖"),
    ("Tasse", "uscita", "#a8763e", "🧾"),
    ("Manutenzione", "uscita", "#9c7b9c", "🔨"),
    ("Altro", "uscita", "#9aa0a6", "🏷"),
]


class Database:
    def __init__(self, percorso: str = DB_PATH):
        os.makedirs(os.path.dirname(percorso), exist_ok=True)
        if percorso == DB_PATH:
            migra_archivio_storico()
        self.percorso = percorso
        self.conn = sqlite3.connect(percorso)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self._aggiorna_schema()
        self._semina()
        self.conn.commit()

    # ------------------------------------------------------------------ base
    def _aggiorna_schema(self) -> None:
        """Aggiunge le colonne introdotte dalle versioni successive.

        Permette di aggiornare l'applicazione senza perdere né convertire i dati.
        """
        colonne = {r["name"] for r in self.conn.execute("PRAGMA table_info(categorie)")}
        if "icona" not in colonne:
            self.conn.execute(
                "ALTER TABLE categorie ADD COLUMN icona TEXT NOT NULL DEFAULT ''")
            from .icone import icona_suggerita
            ufficiali = {(n, t): i for n, t, _, i in CATEGORIE_DEFAULT}
            for r in self.conn.execute("SELECT id, nome, tipo FROM categorie").fetchall():
                icona = (ufficiali.get((r["nome"], r["tipo"]))
                         or icona_suggerita(r["nome"], r["tipo"]))
                self.conn.execute(
                    "UPDATE categorie SET icona=? WHERE id=?", (icona, r["id"]))
            self.conn.commit()

    def _semina(self) -> None:
        cur = self.conn.execute("SELECT COUNT(*) c FROM categorie")
        if cur.fetchone()["c"] == 0:
            self.conn.executemany(
                "INSERT INTO categorie(nome, tipo, colore, icona) VALUES (?,?,?,?)",
                CATEGORIE_DEFAULT,
            )
        cur = self.conn.execute("SELECT COUNT(*) c FROM conti")
        if cur.fetchone()["c"] == 0:
            self.conn.execute(
                "INSERT INTO conti(nome, saldo_iniziale, tipo) VALUES (?,?,?)",
                ("Principale", 0.0, "Conto corrente"),
            )
        self.imposta("valuta", self.leggi("valuta", "€"))

    def query(self, sql: str, par: tuple = ()) -> list[sqlite3.Row]:
        return self.conn.execute(sql, par).fetchall()

    def esegui(self, sql: str, par: tuple = ()) -> int:
        cur = self.conn.execute(sql, par)
        self.conn.commit()
        return cur.lastrowid

    # ----------------------------------------------------------- impostazioni
    def leggi(self, chiave: str, default: str = "") -> str:
        r = self.conn.execute(
            "SELECT valore FROM impostazioni WHERE chiave=?", (chiave,)
        ).fetchone()
        return r["valore"] if r else default

    def imposta(self, chiave: str, valore: str) -> None:
        self.esegui(
            "INSERT INTO impostazioni(chiave,valore) VALUES(?,?) "
            "ON CONFLICT(chiave) DO UPDATE SET valore=excluded.valore",
            (chiave, str(valore)),
        )

    # -------------------------------------------------------------- movimenti
    def movimenti(self, dal: str = "", al: str = "", tipo: str = "",
                  categoria: str = "", conto: str = "", testo: str = "") -> list[sqlite3.Row]:
        sql = "SELECT * FROM movimenti WHERE 1=1"
        par: list = []
        if dal:
            sql += " AND data >= ?"; par.append(dal)
        if al:
            sql += " AND data <= ?"; par.append(al)
        if tipo:
            sql += " AND tipo = ?"; par.append(tipo)
        if categoria:
            sql += " AND categoria = ?"; par.append(categoria)
        if conto:
            sql += " AND conto = ?"; par.append(conto)
        if testo:
            sql += " AND (descrizione LIKE ? OR etichette LIKE ?)"
            par += [f"%{testo}%", f"%{testo}%"]
        sql += " ORDER BY data DESC, id DESC"
        return self.query(sql, tuple(par))

    def salva_movimento(self, dati: dict) -> int:
        if dati.get("id"):
            self.esegui(
                "UPDATE movimenti SET data=?, tipo=?, importo=?, categoria=?, "
                "conto=?, descrizione=?, etichette=? WHERE id=?",
                (dati["data"], dati["tipo"], float(dati["importo"]), dati["categoria"],
                 dati["conto"], dati["descrizione"], dati.get("etichette", ""), dati["id"]),
            )
            return int(dati["id"])
        return self.esegui(
            "INSERT INTO movimenti(data,tipo,importo,categoria,conto,descrizione,etichette) "
            "VALUES(?,?,?,?,?,?,?)",
            (dati["data"], dati["tipo"], float(dati["importo"]), dati["categoria"],
             dati["conto"], dati["descrizione"], dati.get("etichette", "")),
        )

    def elimina(self, tabella: str, id_: int) -> None:
        if tabella not in {"movimenti", "conti", "categorie", "budget", "obiettivi", "ricorrenti"}:
            raise ValueError("tabella non valida")
        self.esegui(f"DELETE FROM {tabella} WHERE id=?", (id_,))

    # ------------------------------------------------------------------ saldi
    def saldo_totale(self) -> float:
        iniz = self.query("SELECT COALESCE(SUM(saldo_iniziale),0) s FROM conti")[0]["s"]
        ent = self.query("SELECT COALESCE(SUM(importo),0) s FROM movimenti WHERE tipo='entrata'")[0]["s"]
        usc = self.query("SELECT COALESCE(SUM(importo),0) s FROM movimenti WHERE tipo='uscita'")[0]["s"]
        return float(iniz) + float(ent) - float(usc)

    def saldo_conto(self, nome: str) -> float:
        r = self.query("SELECT COALESCE(saldo_iniziale,0) s FROM conti WHERE nome=?", (nome,))
        base = float(r[0]["s"]) if r else 0.0
        ent = self.query(
            "SELECT COALESCE(SUM(importo),0) s FROM movimenti WHERE tipo='entrata' AND conto=?",
            (nome,))[0]["s"]
        usc = self.query(
            "SELECT COALESCE(SUM(importo),0) s FROM movimenti WHERE tipo='uscita' AND conto=?",
            (nome,))[0]["s"]
        return base + float(ent) - float(usc)

    def totali_periodo(self, dal: str, al: str) -> tuple[float, float]:
        ent = self.query(
            "SELECT COALESCE(SUM(importo),0) s FROM movimenti "
            "WHERE tipo='entrata' AND data BETWEEN ? AND ?", (dal, al))[0]["s"]
        usc = self.query(
            "SELECT COALESCE(SUM(importo),0) s FROM movimenti "
            "WHERE tipo='uscita' AND data BETWEEN ? AND ?", (dal, al))[0]["s"]
        return float(ent), float(usc)

    def per_categoria(self, tipo: str, dal: str, al: str) -> list[tuple[str, float]]:
        rows = self.query(
            "SELECT categoria, SUM(importo) tot FROM movimenti "
            "WHERE tipo=? AND data BETWEEN ? AND ? GROUP BY categoria ORDER BY tot DESC",
            (tipo, dal, al))
        return [(r["categoria"], float(r["tot"])) for r in rows]

    def serie_mensile(self, mesi: int = 12) -> list[tuple[str, float, float]]:
        rows = self.query(
            "SELECT substr(data,1,7) m, "
            "SUM(CASE WHEN tipo='entrata' THEN importo ELSE 0 END) e, "
            "SUM(CASE WHEN tipo='uscita'  THEN importo ELSE 0 END) u "
            "FROM movimenti GROUP BY m ORDER BY m DESC LIMIT ?", (mesi,))
        return [(r["m"], float(r["e"]), float(r["u"])) for r in reversed(rows)]

    def colori_categorie(self) -> dict[str, str]:
        return {r["nome"]: r["colore"] for r in self.query("SELECT nome, colore FROM categorie")}

    def icone_categorie(self) -> dict[str, str]:
        return {r["nome"]: r["icona"]
                for r in self.query("SELECT nome, icona FROM categorie")}

    # ------------------------------------------------------------- ricorrenti
    def genera_ricorrenti(self) -> int:
        """Crea i movimenti dovuti dalle regole ricorrenti fino a oggi."""
        from .ricorrenze import scadenze_dovute

        creati = 0
        oggi = date.today()
        for r in self.query("SELECT * FROM ricorrenti WHERE attiva=1"):
            ultima = r["ultima_generazione"] or ""
            date_dovute = scadenze_dovute(
                r["frequenza"], r["inizio"], r["giorno"], ultima, oggi)
            for d in date_dovute:
                self.esegui(
                    "INSERT INTO movimenti(data,tipo,importo,categoria,conto,descrizione,etichette) "
                    "VALUES(?,?,?,?,?,?,?)",
                    (d.isoformat(), r["tipo"], float(r["importo"]), r["categoria"],
                     r["conto"], r["descrizione"], "ricorrente"))
                creati += 1
            if date_dovute:
                self.esegui("UPDATE ricorrenti SET ultima_generazione=? WHERE id=?",
                            (date_dovute[-1].isoformat(), r["id"]))
        return creati

    # ----------------------------------------------------------------- backup
    def cartella_backup(self) -> str:
        """Cartella dei backup automatici, accanto all'archivio."""
        cartella = (BACKUP_DIR if self.percorso == DB_PATH
                    else os.path.join(os.path.dirname(self.percorso), "backup"))
        os.makedirs(cartella, exist_ok=True)
        return cartella

    def backup(self, destinazione: str) -> str:
        self.conn.commit()
        if os.path.isdir(destinazione):
            destinazione = os.path.join(
                destinazione, f"finanze-backup-{datetime.now():%Y%m%d-%H%M%S}.db")
        shutil.copy2(self.percorso, destinazione)
        return destinazione

    def chiudi(self) -> None:
        self.conn.commit()
        self.conn.close()

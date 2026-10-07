# Finance

![licenza](https://img.shields.io/badge/licenza-MIT-green) ![python](https://img.shields.io/badge/python-3.10%2B-blue) ![offline](https://img.shields.io/badge/rete-nessuna-success)

Applicazione desktop nativa per la gestione delle finanze personali.
**Funziona interamente offline**: nessuna connessione di rete, nessun account,
nessun servizio esterno. I dati restano in un unico file SQLite dentro la cartella
`dati/`.

## Installazione

```bash
git clone git@github.com:Giosue-tanz/Finance.git
cd Finance
./installa.sh
```

`installa.sh` crea la voce nel menu applicazioni e l'icona sul Desktop puntando
alla cartella in cui hai clonato il progetto. Requisiti: Python 3 e PySide6
(`sudo pacman -S pyside6` su Arch, `sudo apt install python3-pyside6` su Debian/Ubuntu).

## Avvio

- Doppio clic sull'icona **Finance** sul Desktop, oppure
- dal menu applicazioni (categoria Ufficio), oppure
- da terminale: `./avvia.sh`

## Aggiornamento

```bash
./aggiorna.sh
```

Lo script fa un backup dell'archivio, scarica l'ultima versione con `git pull`,
elenca le novità e rigenera il collegamento. **I dati non vengono mai toccati**:
vivono fuori dalla cartella del codice.

## Dove stanno i dati

| Cosa | Percorso |
|---|---|
| Archivio | `~/.local/share/Finance/finanze.db` |
| Backup automatici | `~/.local/share/Finance/backup/` |

Il codice (questo repository) e i dati sono separati: puoi cancellare, spostare o
riclonare la cartella del progetto senza perdere nulla. Chi usava una versione
precedente, con l'archivio dentro `dati/`, lo vede migrare da solo al primo avvio
(l'originale resta come `dati/finanze.db.migrato`).
Il file `.gitignore` esclude database e backup: i tuoi movimenti non finiscono
su GitHub.

## Sezioni

| Sezione | Cosa fa |
|---|---|
| **Cruscotto** | Saldo, entrate/uscite del mese, andamento a 12 mesi, ripartizione per categoria, stato dei budget, ultimi movimenti. Ogni sezione è ridimensionabile trascinando i divisori e si può nascondere dal menu «Sezioni»: la disposizione viene salvata |
| **Movimenti** | Barra di inserimento rapido (importo + Invio), filtri a un clic (oggi, 7 giorni, mese, anno, tutto, intervallo), ricerca istantanea, menu contestuale, eliminazione annullabile con Ctrl+Z, ordinamento per data e importo reali, import ed export CSV |
| **Budget** | Limiti mensili per categoria, ritmo di spesa («puoi spendere X al giorno»), stima di fine mese, proposte calcolate dalla tua media storica, filtri per stato e azioni rapide (±10%, allinea alla media) |
| **Obiettivi** | Traguardi di risparmio con avanzamento, accantonamenti e quota mensile necessaria per rispettare la scadenza |
| **Ricorrenti** | Canoni, stipendi e abbonamenti: generazione automatica dei movimenti dovuti, flusso fisso netto normalizzato su base mensile |
| **Rapporti** | Analisi per periodo: ripartizioni, classifica delle categorie, risparmio netto mensile, dettaglio per categoria e riepilogo mese per mese |
| **Strumenti** | Calcolatrici: prestito/mutuo con piano di ammortamento, interesse composto, piano di risparmio, regola 50/30/20, IVA e sconti, divisione spese |
| **Impostazioni** | Quattro schede: **Conti** (aggiunta rapida, modifica, rinomina con aggiornamento dei movimenti, eliminazione con spostamento dei movimenti), **Categorie** (filtri entrate/uscite, ricerca, icone, colori, unione di categorie), **Aspetto** (tema, dimensione del testo, valuta — applicati subito), **Dati e backup** (riepilogo archivio, backup immediato, ripristino, import/export, operazioni protette) |

## Scorciatoie

| Tasti | Azione |
|---|---|
| `Ctrl+N` | Nuovo movimento (finestra completa) |
| `Invio` nella barra rapida | Salva il movimento e resta pronto per il successivo |
| `Ctrl+F` | Vai alla ricerca |
| `Ctrl+D` | Duplica il movimento selezionato a oggi |
| `Ctrl+Z` | Annulla l'ultima eliminazione |
| `Ctrl+1` … `Ctrl+8` | Passa alla sezione corrispondente |
| `Ctrl+R` | Ricarica la vista corrente |
| `Ctrl+T` | Cambia tema chiaro/scuro (le preferenze stanno in Impostazioni → Aspetto) |
| `Ctrl+B` | Apre o chiude il menu laterale |
| `Canc` | Elimina i movimenti selezionati |
| `Ctrl+Q` | Esci |

## Struttura del progetto

```
Finance/
├── main.py                 avvio dell'applicazione
├── avvia.sh                lanciatore
├── installa.sh             crea icona e voce di menu
├── aggiorna.sh             aggiorna da GitHub preservando i dati
├── Finance.desktop         voce di menu / icona desktop
├── risorse/                icone
└── finanze/
    ├── db.py               livello dati e query
    ├── ricorrenze.py       calcolo delle scadenze ricorrenti
    ├── utils.py            formattazione, date, CSV
    ├── tema.py             palette e foglio di stile
    ├── grafici.py          grafici disegnati con QPainter
    ├── componenti.py       widget riutilizzabili e finestre di dialogo
    ├── finestra.py         finestra principale e navigazione
    └── views/              una vista per sezione, indipendenti tra loro
```

Ogni vista eredita da `VistaBase` ed espone `aggiorna()`: per aggiungere una
nuova sezione basta creare un modulo in `views/` e registrarlo nella lista
`VISTE` di `finestra.py`.

## Formato CSV per l'importazione

Separatore `;` o `,`, prima riga con le intestazioni:

```
data;tipo;importo;categoria;conto;descrizione
06/10/2026;uscita;42,50;Spesa alimentare;Principale;Supermercato
```

Le date sono accettate sia come `gg/mm/aaaa` sia come `aaaa-mm-gg`.

## Menu laterale

Il pulsante `☰` in cima alla barra (o `Ctrl+B`) la riduce a una colonna di icone:
restano le voci di navigazione, con il nome nel suggerimento, la sezione attiva
evidenziata e il saldo complessivo in forma compatta in basso. Lo stato aperto o
chiuso viene ricordato al riavvio.

## Cruscotto su misura

Il cruscotto è composto da nove riquadri indipendenti: saldo, entrate, uscite,
risparmio, andamento, ripartizione, barre mensili, budget e ultimi movimenti.

L'intestazione di ogni riquadro resta essenziale: solo il titolo e, accanto, il
periodo scritto in piccolo. Il resto compare quando serve.

- **Periodo per riquadro** — clic sul periodo accanto al titolo per cambiarlo: oggi,
  ultimi 7 giorni, mese corrente, mese scorso, ultimi 3 o 6 mesi, anno, ultimi 12 mesi,
  tutto (6/12/24/36 mesi per i due grafici temporali, mese corrente o scorso per il
  budget). Puoi quindi vedere le uscite della settimana accanto alle entrate del mese.
  Il saldo totale non ha periodo: è un valore puntuale, e mostra la variazione del mese
  come nota.
- **Sposta** — trascina un riquadro prendendolo dal titolo: in un'altra posizione
  della stessa riga, in un'altra riga, oppure sul bordo tra due righe per crearne una
  nuova. Una linea luminosa mostra dove finirà.
- **Ridimensiona** — i divisori tra i riquadri si trascinano in orizzontale e in
  verticale; tirandoli a fondo la sezione si collassa.
- **Altri comandi** — il `⋯` che appare passando sul titolo (o il tasto destro)
  apre periodo, «nascondi questa sezione» e ripristino della disposizione; le spunte
  del menu **Sezioni** in alto fanno lo stesso per tutti i riquadri.
- **Si ricorda tutto** — posizioni, dimensioni, periodi scelti e sezioni nascoste
  vengono salvati nell'archivio e ritrovati al riavvio.

Testi e grafici si adattano allo spazio: il valore di una scheda cresce o si
riduce con il riquadro (e si rimpicciolisce ancora se il numero non ci sta),
nota e mini-grafico scompaiono quando l'altezza non basta, i grafici tolgono
legende ed etichette degli assi quando sono molto bassi e il testo al centro
della ciambella si ridimensiona da sé.

## Budget che si imposta da solo

La pagina risponde a tre domande pratiche:

- **Quanto posso ancora spendere?** Le schede in alto mostrano pianificato, speso,
  residuo e soprattutto **quanto puoi spendere al giorno** da qui a fine mese.
- **Su cosa sto esagerando?** Ogni riga ha la barra di utilizzo, lo stato
  (sotto controllo / attenzione / oltre il limite) e la **stima di fine mese**
  calcolata sul ritmo attuale. I filtri *Sotto controllo · Vicino al limite ·
  Oltre il limite* isolano subito i casi critici.
- **Quanto dovrei mettere a budget?** «Proponi dalla media» calcola il limite dalla
  spesa media degli ultimi 3 mesi, arrotondata a una cifra comoda. La sezione
  **Categorie senza budget** elenca le categorie su cui spendi senza un limite, con
  la proposta già pronta: doppio clic per adottarla, o «Imposta tutti i proposti».

Scorciatoie: doppio clic su una riga per cambiare il limite, `Canc` per rimuoverlo,
tasto destro per allineare alla media o variare il limite del ±10%.

## Impostazioni

La pagina è divisa in quattro schede, così ogni comando è a un clic di distanza:

- **Conti** — campo di aggiunta rapida (scrivi il nome e premi Invio), doppio clic su
  una riga per modificarla, rinomina che aggiorna automaticamente i movimenti
  collegati, eliminazione che chiede su quale conto spostare i movimenti esistenti.
- **Categorie** — filtri *Tutte / Uscite / Entrate*, ricerca per nome, **icona** e colore
  visibili in tabella, conteggio dei movimenti per categoria, **Unisci in…** per spostare
  tutti i movimenti in un'altra categoria ed eliminare quella vecchia in un solo passaggio.
  Ogni categoria ha un'icona: creandone una nuova l'app ne propone una in base al nome
  («Benzina» → ⛽, «Netflix» → 📺, «Dentista» → 🦷) e il pulsante *Icona rapida* apre una
  griglia di 82 icone divise per argomento. Le icone compaiono poi in tutta
  l'applicazione: movimenti, budget, grafici e rapporti.
- **Aspetto** — tutte le preferenze visive in un posto solo: tema chiaro/scuro,
  **colore principale** fra nove tinte (verde di default, poi blu, turchese, viola,
  magenta, arancio, rosso, ambra, grafite), dimensione del testo (compatta, normale,
  grande, molto grande) e simbolo di valuta con anteprima. Ogni scelta si applica
  immediatamente all'intera applicazione e viene salvata.
- **Dati e backup** — percorso e dimensione dell'archivio, conteggi, data dell'ultimo
  backup, backup immediato in un clic, apertura della cartella dati, ripristino,
  export JSON/CSV, import CSV, ripristino delle categorie predefinite e azzeramento
  protetto (richiede di scrivere `AZZERA` e crea prima un backup).

Ogni operazione conferma l'esito in fondo alla pagina, senza finestre da chiudere.

## Backup

`Impostazioni → Crea backup del database` copia l'archivio dove preferisci.
Prima di un ripristino o di un azzeramento l'app crea automaticamente una copia
di sicurezza in `dati/`.

## Licenza

MIT — vedi [LICENSE](LICENSE).

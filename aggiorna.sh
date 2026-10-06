#!/usr/bin/env bash
# Aggiorna Finance all'ultima versione pubblicata su GitHub.
# I dati personali stanno fuori dal repository e non vengono toccati:
# in più, prima di ogni aggiornamento viene creata una copia di sicurezza.
set -euo pipefail

REPO="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
DATI="${XDG_DATA_HOME:-$HOME/.local/share}/Finance"
DB="$DATI/finanze.db"
BACKUP="$DATI/backup"

cd "$REPO"

if [ ! -d .git ]; then
    echo "Questa copia non è un clone git: scarica il progetto con"
    echo "  git clone git@github.com:Giosue-tanz/Finance.git"
    exit 1
fi

if [ -f "$DB" ]; then
    mkdir -p "$BACKUP"
    COPIA="$BACKUP/finanze-backup-$(date +%Y%m%d-%H%M%S).db"
    cp -p "$DB" "$COPIA"
    echo "Backup dei dati creato: $COPIA"
fi

PRIMA="$(git rev-parse --short HEAD)"
echo "Scarico gli aggiornamenti…"
git pull --ff-only
DOPO="$(git rev-parse --short HEAD)"

if [ "$PRIMA" = "$DOPO" ]; then
    echo "Sei già all'ultima versione ($DOPO)."
else
    echo
    echo "Aggiornato da $PRIMA a $DOPO. Novità:"
    git log --oneline "$PRIMA..$DOPO"
    ./installa.sh >/dev/null
    echo
    echo "Fatto. I tuoi dati in $DATI sono rimasti invariati."
fi

#!/usr/bin/env bash
# Installa Finance per l'utente corrente: voce di menu, icona sul Desktop e
# collegamento all'eseguibile. Non tocca i dati personali.
set -euo pipefail

REPO="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
APPS="$HOME/.local/share/applications"
DESKTOP="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
DATI="${XDG_DATA_HOME:-$HOME/.local/share}/Finance"

chmod +x "$REPO/avvia.sh" "$REPO/aggiorna.sh" "$REPO/main.py" 2>/dev/null || true
mkdir -p "$APPS" "$DATI"

VOCE="$APPS/finance.desktop"
cat > "$VOCE" <<DESKTOPFILE
[Desktop Entry]
Type=Application
Version=1.0
Name=Finance
GenericName=Gestione finanziaria
Comment=Entrate, uscite, budget, grafici e strumenti finanziari — tutto offline
Exec=$REPO/avvia.sh
Path=$REPO
Icon=$REPO/risorse/icona.png
Terminal=false
Categories=Office;Finance;
Keywords=finanze;budget;spese;entrate;uscite;contabilita;
StartupNotify=true
StartupWMClass=main.py
DESKTOPFILE
chmod +x "$VOCE"

if [ -d "$DESKTOP" ]; then
    cp "$VOCE" "$DESKTOP/Finance.desktop"
    chmod +x "$DESKTOP/Finance.desktop"
fi

update-desktop-database "$APPS" 2>/dev/null || true
kbuildsycoca6 --noincremental >/dev/null 2>&1 || true

echo "Finance installato."
echo "  codice:  $REPO"
echo "  dati:    $DATI   (non vengono mai sovrascritti dagli aggiornamenti)"
echo "  avvio:   icona sul Desktop, menu applicazioni, oppure $REPO/avvia.sh"

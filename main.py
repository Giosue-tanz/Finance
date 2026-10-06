#!/usr/bin/env python3
"""Finance — gestione finanziaria personale, interamente offline.

Avvio:  python3 main.py
"""
from __future__ import annotations

import os
import sys

# Nessuna connessione di rete: l'app lavora solo su file locali.
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.*=false")

from PySide6.QtCore import QLocale, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from finanze.db import APP_DIR, Database
from finanze.finestra import FinestraPrincipale


def main() -> int:
    QApplication.setAttribute(Qt.AA_DontUseNativeMenuBar, False)
    QLocale.setDefault(QLocale(QLocale.Italian, QLocale.Italy))
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("Finance")
    app.setApplicationDisplayName("Finance")
    app.setDesktopFileName("finance")
    icona = os.path.join(APP_DIR, "risorse", "icona.png")
    if os.path.exists(icona):
        app.setWindowIcon(QIcon(icona))

    db = Database()
    creati = db.genera_ricorrenti()      # allinea i movimenti ricorrenti dovuti

    finestra = FinestraPrincipale(db)
    finestra.show()
    if creati:
        finestra.statusBar().showMessage(
            f"Generati {creati} movimenti ricorrenti in attesa", 6000)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

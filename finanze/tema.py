"""Palette e foglio di stile Qt: tema chiaro/scuro e colore principale scelto."""
from __future__ import annotations

SCURO = {
    "fondo": "#13151c",
    "pannello": "#1b1e27",
    "pannello2": "#222634",
    "bordo": "#2c313f",
    "testo": "#e7e9ee",
    "testo2": "#9aa1b1",
    "accento": "#6c8cff",
    "entrata": "#2fbf71",
    "uscita": "#ef5f5c",
    "attenzione": "#f2c14e",
    "griglia": "#2a2f3d",
}

CHIARO = {
    "fondo": "#f3f4f8",
    "pannello": "#ffffff",
    "pannello2": "#f7f8fc",
    "bordo": "#dfe2ec",
    "testo": "#1b1e27",
    "testo2": "#687084",
    "accento": "#3b5bdb",
    "entrata": "#1f9d57",
    "uscita": "#d64540",
    "attenzione": "#b9880f",
    "griglia": "#e4e7f0",
}

# Colore principale selezionabile dalle impostazioni: una tinta per tema.
ACCENTI: dict[str, dict[str, str]] = {
    "verde":     {"scuro": "#2ec27e", "chiaro": "#158a4f"},
    "blu":       {"scuro": "#6c8cff", "chiaro": "#3b5bdb"},
    "turchese":  {"scuro": "#35c4d7", "chiaro": "#0e8ea3"},
    "viola":     {"scuro": "#b07cff", "chiaro": "#7641c8"},
    "magenta":   {"scuro": "#f06fb4", "chiaro": "#c02b84"},
    "arancio":   {"scuro": "#f7913a", "chiaro": "#c25e0a"},
    "rosso":     {"scuro": "#f4716d", "chiaro": "#c0392b"},
    "ambra":     {"scuro": "#e8b43a", "chiaro": "#a37408"},
    "grafite":   {"scuro": "#9aa6bf", "chiaro": "#5a6782"},
}
ACCENTO_PREDEFINITO = "verde"


def colori(tema: str = "scuro", accento: str = ACCENTO_PREDEFINITO) -> dict:
    """Palette completa del tema richiesto con il colore principale scelto."""
    base = dict(SCURO if tema == "scuro" else CHIARO)
    tinta = ACCENTI.get(accento, ACCENTI[ACCENTO_PREDEFINITO])
    base["accento"] = tinta["scuro" if tema == "scuro" else "chiaro"]
    return base


PALETTE_GRAFICI = [
    "#6c8cff", "#2fbf71", "#f2994a", "#c77dff", "#56cfe1",
    "#ef5f5c", "#f2c14e", "#ff9ecd", "#7f8cff", "#4cc9a4",
    "#b388eb", "#9aa0a6",
]


SCALE = {"compatta": 0.9, "normale": 1.0, "grande": 1.15, "molto grande": 1.3}


def trasparente(colore: str, opacita: float) -> str:
    """Converte #rrggbb in rgba(): in Qt l'esadecimale a 8 cifre è #AARRGGBB,
    quindi scriverlo a mano porta a colori sbagliati."""
    colore = colore.lstrip("#")
    r, v, b = (int(colore[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {v}, {b}, {opacita:.2f})"


def foglio_stile(c: dict, scala: float = 1.0) -> str:
    def p(px: float) -> str:
        """Dimensione in pixel adattata alla scala del testo."""
        return f"{px * scala:.1f}px"

    selezione = trasparente(c["accento"], 0.33)
    velo = trasparente("#ffffff", 0.22)

    return f"""
    * {{ font-family: "Inter", "Noto Sans", "Segoe UI", sans-serif; font-size: {p(13)}; }}
    QWidget {{ background: {c['fondo']}; color: {c['testo']}; }}
    QLabel, QCheckBox, QRadioButton {{ background: transparent; }}

    #Barra {{ background: {c['pannello']}; border-right: 1px solid {c['bordo']}; }}
    #Titolo {{ font-size: {p(18)}; font-weight: 700; color: {c['testo']}; }}
    #Sottotitolo {{ color: {c['testo2']}; font-size: {p(12)}; }}
    #Logo {{ font-size: {p(16)}; font-weight: 800; color: {c['accento']}; }}

    QPushButton#Navigazione {{
        background: transparent; border: none; border-radius: 9px;
        padding: 10px 14px; text-align: left; color: {c['testo2']}; font-size: {p(13.5)};
    }}
    QPushButton#Navigazione:hover {{ background: {c['pannello2']}; color: {c['testo']}; }}
    QPushButton#Navigazione:checked {{
        background: {c['accento']}; color: #ffffff; font-weight: 600;
    }}

    QFrame#Scheda {{
        background: {c['pannello']}; border: 1px solid {c['bordo']}; border-radius: 14px;
    }}
    QFrame#Separatore {{ background: {c['bordo']}; max-height: 1px; border: none; }}

    QLabel#EtichettaScheda {{ color: {c['testo2']}; font-size: {p(11.5)}; font-weight: 600;
                              letter-spacing: 0.4px; }}
    QLabel#ValoreScheda {{ font-size: {p(23)}; font-weight: 700; }}
    QLabel#NotaScheda {{ color: {c['testo2']}; font-size: {p(11)}; }}
    QLabel#Sezione {{ font-size: {p(15)}; font-weight: 700; padding: 2px 0; }}

    QPushButton {{
        background: {c['pannello2']}; color: {c['testo']}; border: 1px solid {c['bordo']};
        border-radius: 9px; padding: 8px 14px;
    }}
    QPushButton:hover {{ border-color: {c['accento']}; }}
    QPushButton:disabled {{ color: {c['testo2']}; }}
    QPushButton#Primario {{
        background: {c['accento']}; color: #ffffff; border: none; font-weight: 600;
    }}
    QPushButton#Primario:hover {{ background: {c['accento']}; border: 1px solid {velo}; }}
    QPushButton#Pericolo {{ background: {c['uscita']}; color: #ffffff; border: none; }}

    QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QSpinBox, QTextEdit, QPlainTextEdit {{
        background: {c['pannello2']}; border: 1px solid {c['bordo']}; border-radius: 9px;
        padding: 7px 9px; selection-background-color: {c['accento']};
    }}
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus,
    QSpinBox:focus, QTextEdit:focus {{ border-color: {c['accento']}; }}
    QComboBox::drop-down {{ border: none; width: 22px; }}
    QSpinBox::up-button, QDoubleSpinBox::up-button,
    QSpinBox::down-button, QDoubleSpinBox::down-button {{
        background: {c['pannello']}; border: 1px solid {c['bordo']}; width: 18px;
        subcontrol-origin: border;
    }}
    QSpinBox::up-button, QDoubleSpinBox::up-button {{
        subcontrol-position: top right; border-top-right-radius: 8px;
    }}
    QSpinBox::down-button, QDoubleSpinBox::down-button {{
        subcontrol-position: bottom right; border-bottom-right-radius: 8px;
    }}
    QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
    QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
        background: {c['accento']};
    }}
    QDateEdit::drop-down {{ border: none; width: 22px; }}
    QComboBox QAbstractItemView {{
        background: {c['pannello']}; border: 1px solid {c['bordo']};
        selection-background-color: {c['accento']}; outline: none;
    }}

    QTableWidget, QTableView {{
        background: {c['pannello']}; border: 1px solid {c['bordo']}; border-radius: 12px;
        gridline-color: {c['griglia']}; selection-background-color: {selezione};
        selection-color: {c['testo']}; alternate-background-color: {c['pannello2']};
    }}
    QHeaderView::section {{
        background: {c['pannello2']}; color: {c['testo2']}; border: none;
        border-bottom: 1px solid {c['bordo']}; padding: 9px; font-weight: 600;
    }}
    QTableWidget::item {{ padding: 5px; }}

    QProgressBar {{
        background: {c['pannello2']}; border: none; border-radius: 7px;
        height: 12px; text-align: center; color: transparent;
    }}
    QProgressBar::chunk {{ background: {c['accento']}; border-radius: 7px; }}

    QLabel#Periodo {{
        color: {c['testo2']}; font-size: {p(11)};
        padding: 1px 7px; border-radius: 7px;
    }}
    QLabel#Periodo:hover {{ background: {c['pannello2']}; color: {c['accento']}; }}
    QLabel#AzioniSezione {{
        color: {c['testo2']}; font-size: {p(14)}; font-weight: 700;
        padding: 0 6px; border-radius: 6px;
    }}
    QLabel#AzioniSezione:hover {{ background: {c['pannello2']}; color: {c['testo']}; }}
    QFrame#IndicatoreRilascio {{
        background: {c['accento']}; border: none; border-radius: 2px;
    }}

    QSplitter::handle {{ background: transparent; }}
    QSplitter::handle:hover {{ background: {selezione}; border-radius: 3px; }}
    QSplitter::handle:pressed {{ background: {c['accento']}; }}

    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: {c['bordo']}; border-radius: 5px; min-height: 30px; }}
    QScrollBar::handle:vertical:hover {{ background: {c['testo2']}; }}
    QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
    QScrollBar::handle:horizontal {{ background: {c['bordo']}; border-radius: 5px; min-width: 30px; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}

    QTabWidget::pane {{ border: 1px solid {c['bordo']}; border-radius: 12px; top: -1px; }}
    QTabBar::tab {{
        background: transparent; color: {c['testo2']}; padding: 9px 16px;
        border-top-left-radius: 10px; border-top-right-radius: 10px;
    }}
    QTabBar::tab:selected {{ background: {c['pannello']}; color: {c['testo']}; font-weight: 600; }}

    QToolTip {{
        background: {c['pannello2']}; color: {c['testo']};
        border: 1px solid {c['bordo']}; padding: 6px; border-radius: 6px;
    }}
    QCheckBox::indicator {{
        width: 16px; height: 16px; border-radius: 4px;
        border: 1px solid {c['bordo']}; background: {c['pannello2']};
    }}
    QCheckBox::indicator:checked {{ background: {c['accento']}; border-color: {c['accento']}; }}
    QLabel#Pillola {{
        background: {c['pannello2']}; border: 1px solid {c['bordo']}; border-radius: 9px;
        padding: 7px 11px; color: {c['testo2']};
    }}
    QPushButton#Segmento {{
        background: {c['pannello2']}; border: 1px solid {c['bordo']}; border-radius: 9px;
        padding: 7px 16px; color: {c['testo2']};
    }}
    QPushButton#Campione {{
        border-radius: 9px; padding: 9px 14px; font-size: {p(12.5)};
    }}
    QPushButton#Segmento:checked {{
        background: {c['accento']}; color: #ffffff; border-color: {c['accento']};
        font-weight: 600;
    }}
    QLabel#Buono {{ color: {c['entrata']}; font-weight: 600; }}
    QMenu {{ background: {c['pannello']}; border: 1px solid {c['bordo']}; padding: 6px; }}
    QMenu::item {{ padding: 7px 18px; border-radius: 6px; }}
    QMenu::item:selected {{ background: {c['accento']}; color: #fff; }}
    """

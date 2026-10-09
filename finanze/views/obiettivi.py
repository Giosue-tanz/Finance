"""Obiettivi di risparmio con avanzamento e stima temporale."""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (QDateEdit, QDialog, QDialogButtonBox, QDoubleSpinBox,
                               QSizePolicy,
                               QFormLayout, QGridLayout, QHBoxLayout, QLabel,
                               QLineEdit, QMessageBox, QProgressBar, QPushButton,
                               QVBoxLayout, QWidget)

from ..componenti import Scheda, etichetta, riga
from ..utils import data_it, euro
from . import VistaBase
from ..lingue import t


class DialogoObiettivo(QDialog):
    def __init__(self, valuta: str, obiettivo=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Modifica obiettivo" if obiettivo else "Nuovo obiettivo")
        self.setMinimumWidth(400)
        self.obiettivo = dict(obiettivo) if obiettivo else None

        self.nome = QLineEdit()
        self.nome.setPlaceholderText(t("es. Fondo emergenza"))
        self.target = QDoubleSpinBox(); self.target.setRange(1, 99_999_999)
        self.target.setDecimals(2); self.target.setSuffix(f" {valuta}")
        self.target.setValue(1000)
        self.accantonato = QDoubleSpinBox(); self.accantonato.setRange(0, 99_999_999)
        self.accantonato.setDecimals(2); self.accantonato.setSuffix(f" {valuta}")
        self.scadenza = QDateEdit(QDate.currentDate().addYears(1))
        self.scadenza.setCalendarPopup(True)
        self.scadenza.setDisplayFormat("dd/MM/yyyy")
        self.note = QLineEdit()

        modulo = QFormLayout()
        modulo.setSpacing(10)
        modulo.addRow("Nome", self.nome)
        modulo.addRow("Importo obiettivo", self.target)
        modulo.addRow("Già accantonato", self.accantonato)
        modulo.addRow("Scadenza", self.scadenza)
        modulo.addRow("Note", self.note)

        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Save).setText(t("Salva"))
        bb.button(QDialogButtonBox.Save).setObjectName("Primario")
        bb.button(QDialogButtonBox.Cancel).setText(t("Annulla"))
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 18, 18, 14)
        lay.addLayout(modulo); lay.addWidget(bb)

        if self.obiettivo:
            o = self.obiettivo
            self.nome.setText(o["nome"])
            self.target.setValue(float(o["obiettivo"]))
            self.accantonato.setValue(float(o["accantonato"]))
            if o["scadenza"]:
                try:
                    a, m, g = (int(x) for x in o["scadenza"].split("-"))
                    self.scadenza.setDate(QDate(a, m, g))
                except ValueError:
                    pass
            self.note.setText(o["note"])

    def dati(self) -> dict:
        return {
            "id": self.obiettivo["id"] if self.obiettivo else None,
            "nome": self.nome.text().strip() or "Obiettivo",
            "obiettivo": self.target.value(),
            "accantonato": self.accantonato.value(),
            "scadenza": self.scadenza.date().toString("yyyy-MM-dd"),
            "note": self.note.text().strip(),
        }


class VistaObiettivi(VistaBase):
    titolo = "Obiettivi"
    sottotitolo = "Traguardi di risparmio e avanzamento"

    def costruisci(self) -> None:
        _, lay = self.area_scorrevole()
        b_nuovo = QPushButton(t("+  Nuovo obiettivo")); b_nuovo.setObjectName("Primario")
        self.et_totale = QLabel(""); self.et_totale.setObjectName("NotaScheda")
        lay.addLayout(riga(b_nuovo, None, self.et_totale))

        self.contenitore = QWidget()
        self.griglia = QGridLayout(self.contenitore)
        self.griglia.setSpacing(12)
        self.griglia.setContentsMargins(0, 0, 0, 0)
        for colonna in range(3):
            self.griglia.setColumnStretch(colonna, 1)
        lay.addWidget(self.contenitore)
        lay.addStretch(1)
        b_nuovo.clicked.connect(self.nuovo)

    def aggiorna(self) -> None:
        while self.griglia.count():
            item = self.griglia.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

        v = self.valuta
        righe = self.db.query("SELECT * FROM obiettivi ORDER BY id DESC")
        if not righe:
            sc = Scheda()
            sc.aggiungi(etichetta(t("Nessun obiettivo di risparmio."), "NotaScheda"))
            self.griglia.addWidget(sc, 0, 0)
            self.et_totale.setText("")
            return

        tot_target = tot_acc = 0.0
        for i, o in enumerate(righe):
            target = float(o["obiettivo"]); acc = float(o["accantonato"])
            tot_target += target; tot_acc += acc
            quota = min(100, int(acc / target * 100)) if target else 0
            sc = Scheda()
            titolo = QLabel(o["nome"]); titolo.setObjectName("Sezione")
            valori = QLabel(f"{euro(acc, v)}  di  {euro(target, v)}")
            barra = QProgressBar(); barra.setRange(0, 100); barra.setValue(quota)
            barra.setFormat(f"{quota}%")
            colore = self.c["entrata"] if quota >= 100 else self.c["accento"]
            barra.setStyleSheet(
                f"QProgressBar {{ color: {self.c['testo']}; }}"
                f"QProgressBar::chunk {{ background: {colore}; border-radius: 7px; }}")
            nota = QLabel(self._stima(o, target - acc)); nota.setObjectName("NotaScheda")
            nota.setWordWrap(True)

            b_versa = QPushButton(t("Accantona…"))
            b_mod = QPushButton(t("Modifica"))
            b_del = QPushButton(t("Elimina")); b_del.setObjectName("Pericolo")
            b_versa.clicked.connect(lambda _=False, r=o: self.accantona(r))
            b_mod.clicked.connect(lambda _=False, r=o: self.modifica(r))
            b_del.clicked.connect(lambda _=False, r=o: self.elimina(r))

            for w in (titolo, valori, barra, nota):
                sc.aggiungi(w)
            sc.aggiungi_layout(riga(b_versa, b_mod, b_del, None))
            sc.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            self.griglia.addWidget(sc, i // 3, i % 3, Qt.AlignTop)

        self.et_totale.setText(
            f"{len(righe)} obiettivi   ·   accantonato {euro(tot_acc, v)} su "
            f"{euro(tot_target, v)}   ·   mancano {euro(max(0.0, tot_target - tot_acc), v)}")

    def _stima(self, o, mancante: float) -> str:
        if mancante <= 0:
            return "Obiettivo raggiunto 🎉"
        testo = []
        if o["scadenza"]:
            try:
                a, m, g = (int(x) for x in o["scadenza"].split("-"))
                giorni = (date(a, m, g) - date.today()).days
                if giorni > 0:
                    mesi = max(1, giorni / 30.4)
                    testo.append(f"{euro(mancante / mesi, self.valuta)} al mese "
                                 f"entro il {data_it(o['scadenza'])}")
                else:
                    testo.append(f"scadenza superata ({data_it(o['scadenza'])})")
            except ValueError:
                pass
        testo.append(f"mancano {euro(mancante, self.valuta)}")
        if o["note"]:
            testo.append(o["note"])
        return "  ·  ".join(testo)

    def nuovo(self) -> None:
        dlg = DialogoObiettivo(self.valuta, None, self)
        if dlg.exec():
            d = dlg.dati()
            self.db.esegui(
                "INSERT INTO obiettivi(nome,obiettivo,accantonato,scadenza,note) "
                "VALUES(?,?,?,?,?)",
                (d["nome"], d["obiettivo"], d["accantonato"], d["scadenza"], d["note"]))
            self.dati_cambiati.emit()

    def modifica(self, o) -> None:
        dlg = DialogoObiettivo(self.valuta, o, self)
        if dlg.exec():
            d = dlg.dati()
            self.db.esegui(
                "UPDATE obiettivi SET nome=?, obiettivo=?, accantonato=?, scadenza=?, "
                "note=? WHERE id=?",
                (d["nome"], d["obiettivo"], d["accantonato"], d["scadenza"],
                 d["note"], o["id"]))
            self.dati_cambiati.emit()

    def accantona(self, o) -> None:
        from PySide6.QtWidgets import QInputDialog
        importo, ok = QInputDialog.getDouble(
            self, "Accantona", f"Quanto aggiungere a «{o['nome']}»?",
            50.0, 0.0, 9_999_999.0, 2)
        if not ok or importo <= 0:
            return
        self.db.esegui("UPDATE obiettivi SET accantonato = accantonato + ? WHERE id=?",
                       (importo, o["id"]))
        self.dati_cambiati.emit()

    def elimina(self, o) -> None:
        if QMessageBox.question(self, "Conferma", f"Eliminare «{o['nome']}»?",
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No) == QMessageBox.Yes:
            self.db.elimina("obiettivi", o["id"])
            self.dati_cambiati.emit()

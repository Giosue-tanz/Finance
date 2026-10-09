"""Traduzione dell'interfaccia.

Le stringhe sono raccolte qui per chiave: ogni voce elenca le cinque lingue
previste. La funzione `t()` restituisce la traduzione nella lingua scelta e,
se manca, ripiega sull'italiano in modo che l'interfaccia resti sempre leggibile.
"""
from __future__ import annotations

LINGUE = {
    "it": "Italiano",
    "en": "English",
    "es": "Español",
    "fr": "Français",
    "zh": "中文",
}
LINGUA_PREDEFINITA = "it"

# chiave -> {lingua: testo}
TESTI: dict[str, dict[str, str]] = {
    # ---------------------------------------------------------- navigazione
    "Cruscotto": {"en": "Dashboard", "es": "Panel", "fr": "Tableau de bord", "zh": "仪表盘"},
    "Movimenti": {"en": "Transactions", "es": "Movimientos", "fr": "Opérations", "zh": "交易"},
    "Budget": {"en": "Budgets", "es": "Presupuestos", "fr": "Budgets", "zh": "预算"},
    "Obiettivi": {"en": "Goals", "es": "Objetivos", "fr": "Objectifs", "zh": "目标"},
    "Ricorrenti": {"en": "Recurring", "es": "Recurrentes", "fr": "Récurrents", "zh": "定期"},
    "Rapporti": {"en": "Reports", "es": "Informes", "fr": "Rapports", "zh": "报表"},
    "Strumenti": {"en": "Tools", "es": "Herramientas", "fr": "Outils", "zh": "工具"},
    "Impostazioni": {"en": "Settings", "es": "Ajustes", "fr": "Réglages", "zh": "设置"},

    # ------------------------------------------------------ sottotitoli viste
    "Panoramica della tua situazione finanziaria": {
        "en": "An overview of your finances",
        "es": "Panorama de tu situación financiera",
        "fr": "Vue d'ensemble de vos finances",
        "zh": "您的财务概览"},
    "Entrate e uscite registrate": {
        "en": "Recorded income and expenses",
        "es": "Ingresos y gastos registrados",
        "fr": "Recettes et dépenses enregistrées",
        "zh": "已记录的收入与支出"},
    "Limiti di spesa mensili per categoria": {
        "en": "Monthly spending limits by category",
        "es": "Límites de gasto mensuales por categoría",
        "fr": "Plafonds de dépenses mensuels par catégorie",
        "zh": "各类别的每月支出上限"},
    "Traguardi di risparmio": {
        "en": "Savings goals", "es": "Metas de ahorro",
        "fr": "Objectifs d'épargne", "zh": "储蓄目标"},
    "Movimenti che si ripetono nel tempo": {
        "en": "Transactions that repeat over time",
        "es": "Movimientos que se repiten en el tiempo",
        "fr": "Opérations qui se répètent dans le temps",
        "zh": "周期性重复的交易"},
    "Analisi per periodo": {
        "en": "Analysis by period", "es": "Análisis por periodo",
        "fr": "Analyse par période", "zh": "按时间段分析"},
    "Calcolatrici finanziarie e utilità": {
        "en": "Financial calculators and utilities",
        "es": "Calculadoras financieras y utilidades",
        "fr": "Calculatrices financières et utilitaires",
        "zh": "财务计算器与工具"},
    "Conti, categorie, aspetto e gestione dei dati": {
        "en": "Accounts, categories, appearance and data",
        "es": "Cuentas, categorías, apariencia y datos",
        "fr": "Comptes, catégories, apparence et données",
        "zh": "账户、类别、外观与数据"},

    # ------------------------------------------------------------- comandi
    "+  Nuovo movimento": {
        "en": "+  New transaction", "es": "+  Nuevo movimiento",
        "fr": "+  Nouvelle opération", "zh": "+  新建交易"},
    "Sezioni": {"en": "Sections", "es": "Secciones", "fr": "Sections", "zh": "版块"},
    "Aggiungi": {"en": "Add", "es": "Añadir", "fr": "Ajouter", "zh": "添加"},
    "Modifica": {"en": "Edit", "es": "Editar", "fr": "Modifier", "zh": "编辑"},
    "Elimina": {"en": "Delete", "es": "Eliminar", "fr": "Supprimer", "zh": "删除"},
    "Duplica": {"en": "Duplicate", "es": "Duplicar", "fr": "Dupliquer", "zh": "复制"},
    "Annulla": {"en": "Cancel", "es": "Cancelar", "fr": "Annuler", "zh": "取消"},
    "Salva": {"en": "Save", "es": "Guardar", "fr": "Enregistrer", "zh": "保存"},
    "Crea": {"en": "Create", "es": "Crear", "fr": "Créer", "zh": "创建"},
    "Esporta CSV": {"en": "Export CSV", "es": "Exportar CSV",
                    "fr": "Exporter CSV", "zh": "导出 CSV"},
    "Importa CSV": {"en": "Import CSV", "es": "Importar CSV",
                    "fr": "Importer CSV", "zh": "导入 CSV"},

    # ------------------------------------------------------------- generali
    "Uscita": {"en": "Expense", "es": "Gasto", "fr": "Dépense", "zh": "支出"},
    "Entrata": {"en": "Income", "es": "Ingreso", "fr": "Recette", "zh": "收入"},
    "Uscite": {"en": "Expenses", "es": "Gastos", "fr": "Dépenses", "zh": "支出"},
    "Entrate": {"en": "Income", "es": "Ingresos", "fr": "Recettes", "zh": "收入"},
    "Tutti": {"en": "All", "es": "Todos", "fr": "Tous", "zh": "全部"},
    "Tutte": {"en": "All", "es": "Todas", "fr": "Toutes", "zh": "全部"},
    "Oggi": {"en": "Today", "es": "Hoy", "fr": "Aujourd'hui", "zh": "今天"},
    "7 giorni": {"en": "7 days", "es": "7 días", "fr": "7 jours", "zh": "7 天"},
    "Mese": {"en": "Month", "es": "Mes", "fr": "Mois", "zh": "本月"},
    "Anno": {"en": "Year", "es": "Año", "fr": "Année", "zh": "本年"},
    "Tutto": {"en": "Everything", "es": "Todo", "fr": "Tout", "zh": "全部"},
    "Data": {"en": "Date", "es": "Fecha", "fr": "Date", "zh": "日期"},
    "Tipo": {"en": "Type", "es": "Tipo", "fr": "Type", "zh": "类型"},
    "Descrizione": {"en": "Description", "es": "Descripción",
                    "fr": "Description", "zh": "说明"},
    "Categoria": {"en": "Category", "es": "Categoría", "fr": "Catégorie", "zh": "类别"},
    "Conto": {"en": "Account", "es": "Cuenta", "fr": "Compte", "zh": "账户"},
    "Importo": {"en": "Amount", "es": "Importe", "fr": "Montant", "zh": "金额"},
    "Etichette": {"en": "Tags", "es": "Etiquetas", "fr": "Étiquettes", "zh": "标签"},
    "SALDO TOTALE": {"en": "TOTAL BALANCE", "es": "SALDO TOTAL",
                     "fr": "SOLDE TOTAL", "zh": "总余额"},

    # -------------------------------------------------------- impostazioni
    "Conti": {"en": "Accounts", "es": "Cuentas", "fr": "Comptes", "zh": "账户"},
    "Categorie": {"en": "Categories", "es": "Categorías",
                  "fr": "Catégories", "zh": "类别"},
    "Aspetto": {"en": "Appearance", "es": "Apariencia",
                "fr": "Apparence", "zh": "外观"},
    "Dati e backup": {"en": "Data and backup", "es": "Datos y copias",
                      "fr": "Données et sauvegarde", "zh": "数据与备份"},
    "Tema": {"en": "Theme", "es": "Tema", "fr": "Thème", "zh": "主题"},
    "Scuro": {"en": "Dark", "es": "Oscuro", "fr": "Sombre", "zh": "深色"},
    "Chiaro": {"en": "Light", "es": "Claro", "fr": "Clair", "zh": "浅色"},
    "Colore principale": {"en": "Accent colour", "es": "Color principal",
                          "fr": "Couleur principale", "zh": "主色调"},
    "Stile delle icone": {"en": "Icon style", "es": "Estilo de los iconos",
                          "fr": "Style des icônes", "zh": "图标风格"},
    "Dimensione del testo": {"en": "Text size", "es": "Tamaño del texto",
                             "fr": "Taille du texte", "zh": "文字大小"},
    "Lingua": {"en": "Language", "es": "Idioma", "fr": "Langue", "zh": "语言"},
    "Valuta": {"en": "Currency", "es": "Moneda", "fr": "Devise", "zh": "货币"},
    "Nuova categoria": {"en": "New category", "es": "Nueva categoría",
                        "fr": "Nouvelle catégorie", "zh": "新建类别"},
    "Nome della categoria": {"en": "Category name", "es": "Nombre de la categoría",
                             "fr": "Nom de la catégorie", "zh": "类别名称"},
    "sottile": {"en": "thin", "es": "fino", "fr": "fin", "zh": "细线"},
    "pieno": {"en": "solid", "es": "sólido", "fr": "plein", "zh": "实心"},
    "geometrico": {"en": "geometric", "es": "geométrico",
                   "fr": "géométrique", "zh": "几何"},
    "compatta": {"en": "compact", "es": "compacta", "fr": "compacte", "zh": "紧凑"},
    "normale": {"en": "normal", "es": "normal", "fr": "normale", "zh": "标准"},
    "grande": {"en": "large", "es": "grande", "fr": "grande", "zh": "大"},
    "molto grande": {"en": "very large", "es": "muy grande",
                     "fr": "très grande", "zh": "特大"},
}

_corrente = LINGUA_PREDEFINITA


def imposta_lingua(codice: str) -> None:
    """Fissa la lingua usata da `t()` per il resto della sessione."""
    global _corrente
    _corrente = codice if codice in LINGUE else LINGUA_PREDEFINITA


def lingua() -> str:
    return _corrente


def t(testo: str) -> str:
    """Traduce un testo italiano nella lingua scelta.

    L'italiano è la chiave: se la traduzione manca, torna il testo originale
    invece di una stringa vuota o di un segnaposto.
    """
    if _corrente == LINGUA_PREDEFINITA:
        return testo
    return TESTI.get(testo, {}).get(_corrente, testo)

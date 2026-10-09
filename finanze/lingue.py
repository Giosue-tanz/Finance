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

    # ------------------------------------------- resto dell'interfaccia
    'Conti e portafogli': {"en": 'Accounts and wallets', "es": 'Cuentas y carteras', "fr": 'Comptes et portefeuilles', "zh": '账户与钱包'},
    'Nome del conto': {"en": 'Account name', "es": 'Nombre de la cuenta', "fr": 'Nom du compte', "zh": '账户名称'},
    'Saldo iniziale': {"en": 'Opening balance', "es": 'Saldo inicial', "fr": 'Solde initial', "zh": '初始余额'},
    'saldo iniziale': {"en": 'opening balance', "es": 'saldo inicial', "fr": 'solde initial', "zh": '初始余额'},
    'Saldo attuale': {"en": 'Current balance', "es": 'Saldo actual', "fr": 'Solde actuel', "zh": '当前余额'},
    'Rinomina': {"en": 'Rename', "es": 'Renombrar', "fr": 'Renommer', "zh": '重命名'},
    'Rimuovi': {"en": 'Remove', "es": 'Quitar', "fr": 'Retirer', "zh": '移除'},
    'Icona': {"en": 'Icon', "es": 'Icono', "fr": 'Icône', "zh": '图标'},
    'Icona rapida': {"en": 'Quick icon', "es": 'Icono rápido', "fr": 'Icône rapide', "zh": '快速图标'},
    'Colore': {"en": 'Colour', "es": 'Color', "fr": 'Couleur', "zh": '颜色'},
    'Colore rapido': {"en": 'Quick colour', "es": 'Color rápido', "fr": 'Couleur rapide', "zh": '快速颜色'},
    'Scegli colore': {"en": 'Choose colour', "es": 'Elegir color', "fr": 'Choisir la couleur', "zh": '选择颜色'},
    "Scegli un'icona": {"en": 'Choose an icon', "es": 'Elegir un icono', "fr": 'Choisir une icône', "zh": '选择图标'},
    'Nessuna icona corrisponde alla ricerca.': {"en": 'No icon matches your search.', "es": 'Ningún icono coincide con la búsqueda.', "fr": 'Aucune icône ne correspond.', "zh": '没有匹配的图标。'},
    'Unisci in…': {"en": 'Merge into…', "es": 'Fusionar en…', "fr": 'Fusionner dans…', "zh": '合并到…'},
    'Cerca categoria…': {"en": 'Search category…', "es": 'Buscar categoría…', "fr": 'Rechercher une catégorie…', "zh": '搜索类别…'},
    'Cerca…': {"en": 'Search…', "es": 'Buscar…', "fr": 'Rechercher…', "zh": '搜索…'},
    'Archivio': {"en": 'Archive', "es": 'Archivo', "fr": 'Archive', "zh": '归档'},
    'Backup': {"en": 'Backup', "es": 'Copia de seguridad', "fr": 'Sauvegarde', "zh": '备份'},
    'Backup immediato': {"en": 'Back up now', "es": 'Copia inmediata', "fr": 'Sauvegarder maintenant', "zh": '立即备份'},
    'Backup in una cartella a scelta…': {"en": 'Back up to a chosen folder…', "es": 'Copia en una carpeta elegida…', "fr": 'Sauvegarder dans un dossier choisi…', "zh": '备份到指定文件夹…'},
    'Ripristina da backup…': {"en": 'Restore from backup…', "es": 'Restaurar desde copia…', "fr": 'Restaurer depuis une sauvegarde…', "zh": '从备份恢复…'},
    'Apri cartella dati': {"en": 'Open data folder', "es": 'Abrir carpeta de datos', "fr": 'Ouvrir le dossier de données', "zh": '打开数据文件夹'},
    'Importa ed esporta': {"en": 'Import and export', "es": 'Importar y exportar', "fr": 'Importer et exporter', "zh": '导入与导出'},
    'Esporta tutto in JSON': {"en": 'Export everything to JSON', "es": 'Exportar todo a JSON', "fr": 'Tout exporter en JSON', "zh": '全部导出为 JSON'},
    'Esporta movimenti in CSV': {"en": 'Export transactions to CSV', "es": 'Exportar movimientos a CSV', "fr": 'Exporter les opérations en CSV', "zh": '导出交易为 CSV'},
    'Importa movimenti da CSV…': {"en": 'Import transactions from CSV…', "es": 'Importar movimientos desde CSV…', "fr": 'Importer des opérations depuis un CSV…', "zh": '从 CSV 导入交易…'},
    'Operazioni irreversibili': {"en": 'Irreversible actions', "es": 'Acciones irreversibles', "fr": 'Actions irréversibles', "zh": '不可撤销的操作'},
    'Azzera tutti i movimenti': {"en": 'Delete all transactions', "es": 'Borrar todos los movimientos', "fr": 'Supprimer toutes les opérations', "zh": '清空所有交易'},
    'Ripristina categorie predefinite': {"en": 'Restore default categories', "es": 'Restaurar categorías predeterminadas', "fr": 'Restaurer les catégories par défaut', "zh": '恢复默认类别'},
    'Privacy': {"en": 'Privacy', "es": 'Privacidad', "fr": 'Confidentialité', "zh": '隐私'},
    'Azzera filtri': {"en": 'Clear filters', "es": 'Limpiar filtros', "fr": 'Réinitialiser les filtres', "zh": '清除筛选'},
    'Altri campi…': {"en": 'More fields…', "es": 'Más campos…', "fr": 'Plus de champs…', "zh": '更多字段…'},
    'Periodo': {"en": 'Period', "es": 'Periodo', "fr": 'Période', "zh": '时间段'},
    'Personalizzato': {"en": 'Custom', "es": 'Personalizado', "fr": 'Personnalisé', "zh": '自定义'},
    'Mese corrente': {"en": 'This month', "es": 'Mes actual', "fr": 'Mois en cours', "zh": '本月'},
    'Mese precedente': {"en": 'Last month', "es": 'Mes anterior', "fr": 'Mois précédent', "zh": '上月'},
    'Anno corrente': {"en": 'This year', "es": 'Año actual', "fr": 'Année en cours', "zh": '本年'},
    'Ultimi 12 mesi': {"en": 'Last 12 months', "es": 'Últimos 12 meses', "fr": '12 derniers mois', "zh": '最近 12 个月'},
    'dal': {"en": 'from', "es": 'desde', "fr": 'du', "zh": '自'},
    'al': {"en": 'to', "es": 'hasta', "fr": 'au', "zh": '至'},
    'Vista': {"en": 'View', "es": 'Vista', "fr": 'Vue', "zh": '视图'},
    'Voce': {"en": 'Item', "es": 'Concepto', "fr": 'Poste', "zh": '项目'},
    'Totale': {"en": 'Total', "es": 'Total', "fr": 'Total', "zh": '合计'},
    'Media': {"en": 'Average', "es": 'Media', "fr": 'Moyenne', "zh": '平均'},
    'Quota': {"en": 'Share', "es": 'Cuota', "fr": 'Part', "zh": '占比'},
    'Stato': {"en": 'Status', "es": 'Estado', "fr": 'État', "zh": '状态'},
    'Limite': {"en": 'Limit', "es": 'Límite', "fr": 'Plafond', "zh": '上限'},
    'Limite mensile': {"en": 'Monthly limit', "es": 'Límite mensual', "fr": 'Plafond mensuel', "zh": '每月上限'},
    'Speso': {"en": 'Spent', "es": 'Gastado', "fr": 'Dépensé', "zh": '已花费'},
    'Speso questo mese': {"en": 'Spent this month', "es": 'Gastado este mes', "fr": 'Dépensé ce mois-ci', "zh": '本月已花费'},
    'Speso realmente nel mese': {"en": 'Actually spent this month', "es": 'Gastado realmente en el mes', "fr": 'Réellement dépensé ce mois-ci', "zh": '本月实际花费'},
    'Residuo': {"en": 'Remaining', "es": 'Restante', "fr": 'Restant', "zh": '剩余'},
    'Utilizzo': {"en": 'Usage', "es": 'Uso', "fr": 'Utilisation', "zh": '使用率'},
    'Utilizzo dei budget': {"en": 'Budget usage', "es": 'Uso de los presupuestos', "fr": 'Utilisation des budgets', "zh": '预算使用情况'},
    'Stato dei budget': {"en": 'Budget status', "es": 'Estado de los presupuestos', "fr": 'État des budgets', "zh": '预算状态'},
    'Fine mese (stima)': {"en": 'End of month (estimate)', "es": 'Fin de mes (estimado)', "fr": 'Fin de mois (estimation)', "zh": '月末（预估）'},
    'Proiezione': {"en": 'Projection', "es": 'Proyección', "fr": 'Projection', "zh": '预测'},
    'Categorie senza budget': {"en": 'Categories without a budget', "es": 'Categorías sin presupuesto', "fr": 'Catégories sans budget', "zh": '无预算的类别'},
    'Budget proposto': {"en": 'Suggested budget', "es": 'Presupuesto propuesto', "fr": 'Budget proposé', "zh": '建议预算'},
    'Imposta budget': {"en": 'Set budget', "es": 'Fijar presupuesto', "fr": 'Définir le budget', "zh": '设定预算'},
    'Imposta il budget proposto': {"en": 'Apply suggested budget', "es": 'Aplicar el presupuesto propuesto', "fr": 'Appliquer le budget proposé', "zh": '应用建议预算'},
    'Imposta tutti i proposti': {"en": 'Apply all suggestions', "es": 'Aplicar todas las propuestas', "fr": 'Appliquer toutes les propositions', "zh": '应用全部建议'},
    'Proponi dalla media': {"en": 'Suggest from average', "es": 'Proponer según la media', "fr": "Proposer d'après la moyenne", "zh": '按平均值建议'},
    'Nessun budget impostato.': {"en": 'No budget set.', "es": 'Sin presupuesto definido.', "fr": 'Aucun budget défini.', "zh": '尚未设定预算。'},
    'Nessun obiettivo di risparmio.': {"en": 'No savings goal.', "es": 'Sin metas de ahorro.', "fr": "Aucun objectif d'épargne.", "zh": '尚无储蓄目标。'},
    'Traguardi di risparmio e avanzamento': {"en": 'Savings goals and progress', "es": 'Metas de ahorro y avance', "fr": "Objectifs d'épargne et progression", "zh": '储蓄目标与进度'},
    '+  Nuovo obiettivo': {"en": '+  New goal', "es": '+  Nueva meta', "fr": '+  Nouvel objectif', "zh": '+  新建目标'},
    'Accantona…': {"en": 'Set aside…', "es": 'Apartar…', "fr": 'Mettre de côté…', "zh": '存入…'},
    'Importo consigliato': {"en": 'Suggested amount', "es": 'Importe recomendado', "fr": 'Montant conseillé', "zh": '建议金额'},
    '+  Nuova ricorrenza': {"en": '+  New recurring item', "es": '+  Nueva recurrencia', "fr": '+  Nouvelle récurrence', "zh": '+  新建定期项'},
    'Movimenti automatici periodici': {"en": 'Automatic periodic transactions', "es": 'Movimientos automáticos periódicos', "fr": 'Opérations périodiques automatiques', "zh": '自动周期交易'},
    'Regole configurate': {"en": 'Configured rules', "es": 'Reglas configuradas', "fr": 'Règles configurées', "zh": '已配置规则'},
    'Genera movimenti dovuti': {"en": 'Generate due transactions', "es": 'Generar movimientos pendientes', "fr": 'Générer les opérations dues', "zh": '生成到期交易'},
    'Attiva / sospendi': {"en": 'Enable / pause', "es": 'Activar / pausar', "fr": 'Activer / suspendre', "zh": '启用 / 暂停'},
    'Frequenza': {"en": 'Frequency', "es": 'Frecuencia', "fr": 'Fréquence', "zh": '频率'},
    'Prossima': {"en": 'Next', "es": 'Próxima', "fr": 'Prochaine', "zh": '下一次'},
    'Analisi approfondita di entrate e uscite': {"en": 'In-depth analysis of income and expenses', "es": 'Análisis detallado de ingresos y gastos', "fr": 'Analyse approfondie des recettes et dépenses', "zh": '收支深度分析'},
    'Ripartizione uscite': {"en": 'Expense breakdown', "es": 'Reparto de gastos', "fr": 'Répartition des dépenses', "zh": '支出构成'},
    'Ripartizione entrate': {"en": 'Income breakdown', "es": 'Reparto de ingresos', "fr": 'Répartition des recettes', "zh": '收入构成'},
    'Classifica categorie di spesa': {"en": 'Spending categories ranking', "es": 'Ranking de categorías de gasto', "fr": 'Classement des postes de dépense', "zh": '支出类别排行'},
    'Dettaglio per categoria': {"en": 'Detail by category', "es": 'Detalle por categoría', "fr": 'Détail par catégorie', "zh": '按类别明细'},
    'Riepilogo mensile': {"en": 'Monthly summary', "es": 'Resumen mensual', "fr": 'Récapitulatif mensuel', "zh": '月度汇总'},
    'Risparmio': {"en": 'Savings', "es": 'Ahorro', "fr": 'Épargne', "zh": '储蓄'},
    'Tasso di risparmio': {"en": 'Savings rate', "es": 'Tasa de ahorro', "fr": "Taux d'épargne", "zh": '储蓄率'},
    'Risparmio netto mensile': {"en": 'Monthly net savings', "es": 'Ahorro neto mensual', "fr": 'Épargne nette mensuelle', "zh": '每月净储蓄'},
    'Prestito / Mutuo': {"en": 'Loan / Mortgage', "es": 'Préstamo / Hipoteca', "fr": 'Prêt / Crédit immobilier', "zh": '贷款 / 按揭'},
    'Dati del finanziamento': {"en": 'Loan details', "es": 'Datos del préstamo', "fr": 'Données du prêt', "zh": '贷款信息'},
    'Piano di ammortamento (primi 24 mesi)': {"en": 'Amortisation schedule (first 24 months)', "es": 'Cuadro de amortización (primeros 24 meses)', "fr": "Tableau d'amortissement (24 premiers mois)", "zh": '还款计划（前 24 个月）'},
    'Rata': {"en": 'Instalment', "es": 'Cuota', "fr": 'Échéance', "zh": '期数'},
    'Rata totale': {"en": 'Total instalment', "es": 'Cuota total', "fr": 'Échéance totale', "zh": '每期总额'},
    'Quota capitale': {"en": 'Principal', "es": 'Capital', "fr": 'Capital', "zh": '本金'},
    'Quota interessi': {"en": 'Interest', "es": 'Intereses', "fr": 'Intérêts', "zh": '利息'},
    'Debito residuo': {"en": 'Outstanding debt', "es": 'Deuda pendiente', "fr": 'Capital restant dû', "zh": '剩余本金'},
    'Interesse composto': {"en": 'Compound interest', "es": 'Interés compuesto', "fr": 'Intérêts composés', "zh": '复利'},
    'Capitale e versamenti': {"en": 'Capital and contributions', "es": 'Capital y aportaciones', "fr": 'Capital et versements', "zh": '本金与存入'},
    'Piano di risparmio': {"en": 'Savings plan', "es": 'Plan de ahorro', "fr": "Plan d'épargne", "zh": '储蓄计划'},
    'Quanto devo mettere da parte?': {"en": 'How much should I set aside?', "es": '¿Cuánto debo apartar?', "fr": 'Combien dois-je mettre de côté ?', "zh": '我该存多少？'},
    'Regola 50/30/20': {"en": '50/30/20 rule', "es": 'Regla 50/30/20', "fr": 'Règle 50/30/20', "zh": '50/30/20 法则'},
    'Ripartizione consigliata del reddito netto': {"en": 'Suggested split of net income', "es": 'Reparto recomendado del ingreso neto', "fr": 'Répartition conseillée du revenu net', "zh": '净收入建议分配'},
    'Usa le entrate reali del mese': {"en": "Use this month's actual income", "es": 'Usar los ingresos reales del mes', "fr": 'Utiliser les recettes réelles du mois', "zh": '使用本月实际收入'},
    'IVA e sconti': {"en": 'VAT and discounts', "es": 'IVA y descuentos', "fr": 'TVA et remises', "zh": '增值税与折扣'},
    'Calcolo IVA': {"en": 'VAT calculation', "es": 'Cálculo de IVA', "fr": 'Calcul de TVA', "zh": '增值税计算'},
    "L'importo è con IVA (lordo)": {"en": 'Amount includes VAT (gross)', "es": 'El importe incluye IVA (bruto)', "fr": 'Le montant inclut la TVA (brut)', "zh": '金额含税（总额）'},
    "L'importo è senza IVA (netto)": {"en": 'Amount excludes VAT (net)', "es": 'El importe no incluye IVA (neto)', "fr": 'Le montant exclut la TVA (net)', "zh": '金额不含税（净额）'},
    'Sconto': {"en": 'Discount', "es": 'Descuento', "fr": 'Remise', "zh": '折扣'},
    'Dividi spese': {"en": 'Split expenses', "es": 'Dividir gastos', "fr": 'Partager les dépenses', "zh": '分摊费用'},
    'Dividi una spesa tra più persone': {"en": 'Split an expense among several people', "es": 'Dividir un gasto entre varias personas', "fr": 'Partager une dépense entre plusieurs personnes', "zh": '在多人之间分摊一笔费用'},
    'Calcola': {"en": 'Calculate', "es": 'Calcular', "fr": 'Calculer', "zh": '计算'},
    'Risultato': {"en": 'Result', "es": 'Resultado', "fr": 'Résultat', "zh": '结果'},
    'es. Conto principale': {"en": 'e.g. Main account', "es": 'p. ej. Cuenta principal', "fr": 'p. ex. Compte principal', "zh": '例如：主账户'},
    'es. Abbonamenti': {"en": 'e.g. Subscriptions', "es": 'p. ej. Suscripciones', "fr": 'p. ex. Abonnements', "zh": '例如：订阅'},
    'es. Affitto': {"en": 'e.g. Rent', "es": 'p. ej. Alquiler', "fr": 'p. ex. Loyer', "zh": '例如：房租'},
    'es. Fondo emergenza': {"en": 'e.g. Emergency fund', "es": 'p. ej. Fondo de emergencia', "fr": "p. ex. Fonds d'urgence", "zh": '例如：应急基金'},
    'es. Spesa settimanale': {"en": 'e.g. Weekly groceries', "es": 'p. ej. Compra semanal', "fr": 'p. ex. Courses hebdomadaires', "zh": '例如：每周采购'},
    'etichette separate da virgola (opzionale)': {"en": 'comma-separated tags (optional)', "es": 'etiquetas separadas por comas (opcional)', "fr": 'étiquettes séparées par des virgules (facultatif)', "zh": '以逗号分隔的标签（可选）'},
}

# Lingue che richiedono glifi non presenti nei font latini
ALFABETI = {"zh": "仪"}

_corrente = LINGUA_PREDEFINITA


def alfabeto_disponibile(codice: str) -> bool:
    """Verifica che il sistema sappia disegnare i caratteri della lingua.

    Senza un font adatto (per il cinese serve un font CJK) l'interfaccia
    mostrerebbe rettangoli vuoti: meglio accorgersene prima di proporla.
    """
    prova = ALFABETI.get(codice)
    if not prova:
        return True
    from PySide6.QtGui import QFontDatabase, QFontMetrics

    if QFontDatabase.families(QFontDatabase.SimplifiedChinese):
        return True
    return QFontMetrics(QFontDatabase.systemFont(
        QFontDatabase.GeneralFont)).inFont(prova)


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

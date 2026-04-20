import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
import numpy as np
from io import StringIO
from scipy.stats import pearsonr, spearmanr, shapiro
from great_tables import GT


def scatter_regression(ax, df, x_col, y_col, x_label, y_label, color, n_outliers=3):
    """
    Trace un nuage de points avec droite de régression et annotation des outliers.

    Les outliers annotés sont les départements dont l'écart à la droite de
    régression (résidu) est le plus grand en valeur absolue.

    Paramètres
    ----------
    ax         : axe matplotlib sur lequel tracer
    df         : DataFrame contenant les données
    x_col      : nom de la colonne en abscisse
    y_col      : nom de la colonne en ordonnée
    x_label    : libellé affiché sur l'axe X et dans le titre
    y_label    : libellé affiché sur l'axe Y et dans le titre
    color      : couleur des points
    n_outliers : nombre de départements extrêmes à annoter (défaut : 3)
    """
    # Suppression des lignes avec valeurs manquantes
    tmp = df[[x_col, y_col, "departement"]].dropna()

    # Nuage de points
    ax.scatter(tmp[x_col], tmp[y_col], alpha=0.6, color=color, edgecolors="white", s=50)

    # Droite de régression (degré 1 = linéaire)
    pente, ordonnee = np.polyfit(tmp[x_col], tmp[y_col], 1)
    x_range = np.linspace(tmp[x_col].min(), tmp[x_col].max(), 100)
    ax.plot(
        x_range,
        pente * x_range + ordonnee,
        "k--",
        linewidth=1.5,
        label="Régression linéaire",
    )

    # Annotation des outliers les plus éloignés de la droite
    # Calcul des résidus : écart entre valeur réelle et valeur prédite
    residus = tmp[y_col] - (pente * tmp[x_col] + ordonnee)
    outliers = residus.abs().nlargest(n_outliers).index
    for idx in outliers:
        ax.annotate(
            tmp.loc[idx, "departement"],
            xy=(tmp.loc[idx, x_col], tmp.loc[idx, y_col]),
            fontsize=7,
            xytext=(4, 4),
            textcoords="offset points",
        )

    # Corrélation de Pearson affichée dans le titre
    r, p = pearsonr(tmp[x_col], tmp[y_col])
    ax.set_title(f"{y_label} ~ {x_label}\nr = {r:.3f}  (p = {p:.4f})", fontsize=9)
    ax.legend(fontsize=8)


def attribuer_profil(row, med_valo, med_rural):
    """
    Attribue un profil territorial à un département.

    Croise deux critères binaires (au-dessus/en-dessous de la médiane) :
    - Ruralité      : part de communes rurales vs médiane nationale
    - Valorisation  : taux de valorisation total vs médiane nationale

    Retourne une chaîne parmi :
    - "Urbain / valorisation faible"
    - "Urbain / valorisation forte"
    - "Rural  / valorisation faible"
    - "Rural  / valorisation forte"
    """
    valo = row["taux_valo_total_pct"] >= med_valo
    rural = row["part_communes_rurales_pct"] >= med_rural

    if not rural and not valo:
        return "Urbain / valorisation faible"
    elif not rural and valo:
        return "Urbain / valorisation forte"
    elif rural and not valo:
        return "Rural  / valorisation faible"
    else:
        return "Rural  / valorisation forte"


def afficher_correlations(df, x_col, y_col, x_label, y_label):
    """
    Calcule et affiche les corrélations de Pearson et Spearman.

    Pearson  : mesure l'association LINÉAIRE. Sensible aux outliers.
    Spearman : mesure l'association MONOTONE (sur les rangs). Plus robuste.

    Si les deux divergent → la relation n'est pas strictement linéaire,
    ou des départements extrêmes "tirent" la corrélation de Pearson.
    """
    tmp = df[[x_col, y_col]].dropna()
    r_p, p_p = pearsonr(tmp[x_col], tmp[y_col])
    r_s, p_s = spearmanr(tmp[x_col], tmp[y_col])
    sig = "significatif" if p_p < 0.05 else "non significatif"

    print(f"  {x_label} × {y_label}")
    print(f"  Pearson  r = {r_p:.3f}  (p = {p_p:.6f})")
    print(f"  Spearman ρ = {r_s:.3f}  (p = {p_s:.6f})")
    print(f"  → {sig} au seuil 5 %\n")


def regression_ols(df, var_y, label_y):
    """
    Estime 3 modèles OLS emboîtés et affiche un tableau de synthèse.

    Modèle 1 : ruralité seule
    Modèle 2 : ruralité + niveau de vie
    Modèle 3 : ruralité + niveau de vie + interaction

    Les modèles sont « emboîtés » : chaque modèle ajoute une variable au précédent.
    On compare le R² ajusté pour évaluer l'apport marginal de chaque variable.
    Si le R² ajusté n'augmente pas, la variable ajoutée n'est pas utile.
    """
    cols = [var_y, "part_communes_rurales_pct", "niveau_vie_median", "interaction_rural_revenu"]
    tmp = df[cols].dropna()
    y = tmp[var_y]

    # sm.add_constant() ajoute une colonne de 1 pour estimer l'ordonnée à l'origine
    X1 = sm.add_constant(tmp[["part_communes_rurales_pct"]])
    X2 = sm.add_constant(tmp[["part_communes_rurales_pct", "niveau_vie_median"]])
    X3 = sm.add_constant(
        tmp[["part_communes_rurales_pct", "niveau_vie_median", "interaction_rural_revenu"]]
    )

    # Estimation des modèles par OLS (moindres carrés ordinaires)
    mod1 = sm.OLS(y, X1).fit()
    mod2 = sm.OLS(y, X2).fit()
    mod3 = sm.OLS(y, X3).fit()

    def fmt(mod, var):
        if var not in mod.params:
            return "—"
        sig = "*" if mod.pvalues[var] < 0.05 else "ns"
        return f"{mod.params[var]:.4f} ({sig})"

    # Tableau de synthèse des 3 modèles
    synthese = pd.DataFrame(
        {
            "Modèle 1 (ruralité)": [
                fmt(mod1, "part_communes_rurales_pct"),
                "—",
                "—",
                f"{mod1.rsquared:.3f}",
                f"{mod1.rsquared_adj:.3f}",
            ],
            "Modèle 2 (+revenu)": [
                fmt(mod2, "part_communes_rurales_pct"),
                fmt(mod2, "niveau_vie_median"),
                "—",
                f"{mod2.rsquared:.3f}",
                f"{mod2.rsquared_adj:.3f}",
            ],
            "Modèle 3 (+interaction)": [
                fmt(mod3, "part_communes_rurales_pct"),
                fmt(mod3, "niveau_vie_median"),
                fmt(mod3, "interaction_rural_revenu"),
                f"{mod3.rsquared:.3f}",
                f"{mod3.rsquared_adj:.3f}",
            ],
        },
        index=["Part communes rurales", "Niveau de vie médian", "Interaction", "R²", "R² ajusté"],
    )

    print(f"\n{'=' * 60}")
    print(f"RÉGRESSION OLS — {label_y}")
    print("=" * 60)
    print(synthese.to_string())
    print("* = significatif à 5 % | ns = non significatif")
    return mod1, mod2, mod3


def diagnostics_ols(modele, titre):
    """
    Vérifie les deux hypothèses principales de la régression OLS.

    1. Homoscédasticité (variance constante des résidus)
       → Graphique résidus vs valeurs ajustées : le nuage doit être aléatoire
         autour de 0, sans forme en entonnoir.

    2. Normalité des résidus
       → Q-Q plot : les points doivent suivre la diagonale.
       → Test de Shapiro-Wilk : H0 = normalité. Si p < 0.05 → non normal.
         Dans ce cas, les p-values de la régression sont à interpréter avec prudence.
    """
    residus = modele.resid
    fitted = modele.fittedvalues

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    # Graphique 1 : résidus vs valeurs ajustées
    axes[0].scatter(fitted, residus, alpha=0.6, color="#7f8c8d", edgecolors="white", s=40)
    axes[0].axhline(0, color="red", linestyle="--", linewidth=1)
    axes[0].set_xlabel("Valeurs ajustées (prédites par le modèle)")
    axes[0].set_ylabel("Résidus (observé - prédit)")
    axes[0].set_title("Résidus vs valeurs ajustées")

    # Graphique 2 : Q-Q plot
    # line="s" : droite de référence basée sur l'écart-type des résidus
    sm.qqplot(residus, line="s", ax=axes[1], alpha=0.6)
    axes[1].set_title("Q-Q plot (normalité des résidus)")

    # Graphique 3 : histogramme des résidus
    axes[2].hist(residus, bins=15, color="#95a5a6", edgecolor="white")
    axes[2].set_xlabel("Résidus")
    axes[2].set_ylabel("Fréquence")
    axes[2].set_title("Distribution des résidus")

    plt.suptitle(f"Diagnostics — {titre}", fontsize=12)
    plt.tight_layout()
    plt.show()

    # Test de Shapiro-Wilk
    # H0 : les résidus suivent une loi normale
    # Si p < 0.05 → on rejette H0 → résidus non normaux
    stat, p_sw = shapiro(residus)
    print(f"Shapiro-Wilk : W = {stat:.4f}, p = {p_sw:.4f}")
    if p_sw > 0.05:
        print("→ Résidus normaux (p > 0.05)")
    else:
        print("→ Résidus non normaux (p < 0.05) — interpréter les IC avec prudence")


def afficher_gt_part_modale(df_pct, annee):
    """
    Formate et affiche une table Great Tables des parts modales par département.
    """
    df_plot = df_pct.reset_index()

    # Normalisation des noms de colonnes (gestion des MultiIndex éventuels)
    new_cols = ["Département"]
    for col in df_plot.columns[1:]:
        new_cols.append(col[1] if isinstance(col, tuple) else col)
    df_plot.columns = new_cols

    cols_numeriques = [c for c in df_plot.columns if c != "Département"]

    return (
        GT(df_plot)
        .tab_header(
            title=f"Parts de chaque mode de transport par département en {annee}",
            subtitle="Répartition en % des actifs",
        )
        .fmt_number(columns=cols_numeriques, decimals=1)
        .tab_options(table_width="100%", heading_align="left")
    )


def extraire_extremes(data, nom_mode):
    if isinstance(data, pd.DataFrame):
        serie = data.iloc[:, 0]
    else:
        serie = data

    # Tri des valeurs (maintenant on est sûr que c'est une Series)
    top_progression = serie.sort_values(ascending=False).head(5)
    top_recul = serie.sort_values(ascending=True).head(5)

    print(f"\n--- {nom_mode.upper()} : Les plus fortes PROGRESSIONS ---")
    print(top_progression.to_string())
    print(f"\n--- {nom_mode.upper()} : Les plus forts RECULS ---")
    print(top_recul.to_string())

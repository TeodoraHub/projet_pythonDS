# Recyclage et territoire : à la recherche d'un profil écologique géographique ?

Projet de data science explorant les liens entre **caractéristiques territoriales** (ruralité, niveau de vie, transport)
et **taux de valorisation des déchets ménagers** en France métropolitaine.

---

## Problématique

Les performances de valorisation des déchets varient considérablement d'un
département à l'autre. Ce projet cherche à répondre à deux hypothèses :

1. **Hypothèse territoriale** : les départements ruraux valorisent mieux leurs
   déchets (compostage, gestion différenciée).
2. **Hypothèse socio-économique** : les départements plus aisés investissent
   davantage dans les infrastructures de tri.

La valorisation est analysée en **deux composantes séparées** :
- **Valorisation matière** : recyclage (plastique, verre, papier, métal...)
- **Valorisation organique** : compostage, méthanisation

On s'interesse aussi à l'effet "transport" (type de déplacement).


---

## Données utilisées

| Source        | Fichier                                       | Description                                | Accès |
|---------------|-----------------------------------------------|--------------------------------------------|-------|
| ADEME / SINOE | `SINOE04_DestinationDmaParTypeTraitement.csv`  | Tonnages DMA par type de traitement        | [data.ademe.fr](https://data.ademe.fr) |
| INSEE         | `FET2021-19.xlsx`                             | Grille de densité communale (urbain/rural) | [insee.fr](https://insee.fr) |
| INSEE         | `niv2021.xlsx`                                | Niveau de vie médian annuel par département| [insee.fr](https://insee.fr) |

>  Les 3 premières lignes de `niv2021.xlsx` ont été supprimées manuellement.
Les fichiers de données sont sur onyxia avec un lien directement dans le notebook.
> Les données SINOE peuvent aussi être chargées directement via l'API ADEME
> (voir cellule dédiée dans le notebook).

---

## Structure du projet

```
projet_pythonDS/
├── notebook_recyclage_projet_python.ipynb  # Notebook principal
├── fonctions.py                            # Fonctions réutilisables
├── Requirements.txt                        # Dépendances Python
├── README.md                               # Ce fichier
├── .gitignore                              # Fichiers exclus de Git
├── SINOE04_DestinationDmaParTypeTraitement.csv
├── FET2021-19.xlsx
└── niv2021.xlsx
```

### Contenu de `fonctions.py`

| Fonction | Description |
|---|---|
| `charger_sinoe(path)` | lit et nettoie le fichier SINOE, calcule les taux de valorisation |
| `get_ademe_data()` | Télécharge le fichier SINOE directement depuis l'API ADEME |
| `charger_ruralite(path)` | Charge la grille de densité INSEE, calcule la part de communes rurales |
| `charger_niveau_vie(path)` | Charge le niveau de vie médian par département |
| `scatter_regression(ax, df, ...)` | Nuage de points avec droite de régression et annotation des outliers |
| `attribuer_profil(row, med_valo, med_rural)` | Attribue un profil territorial à un département |
| `afficher_correlations(df, ...)` | Calcule et affiche les corrélations de Pearson et Spearman |
| `regression_ols(df, var_y, label_y)` | Estime 3 modèles OLS emboîtés et affiche un tableau de synthèse |
| `diagnostics_ols(modele, titre)` | Graphiques de diagnostic du modèle OLS (résidus, Q-Q plot, Shapiro-Wilk) |

---

## Installation

```bash
# 1. Cloner le dépôt
git clone <url-du-repo>
cd projet_pythonDS

# 2. Installer les dépendances
pip install -r Requirements.txt
```

---

## Lancement

Ouvrir `notebook_recyclage_projet_python2.ipynb` dans VS Code, puis :

- **Tout exécuter** : bouton `Run All` en haut du notebook
- **Repartir de zéro** : `Restart Kernel and Run All Cells`

---

## Plan du notebook

| Section | Contenu |
|---|---|
| 0 | Imports et paramètres |
| 1 | Chargement et nettoyage des 3 sources de données |
| 2 | Analyse descriptive (statistiques, top/flop départements) |
| 3 | Visualisations (distributions, nuages de points, heatmap, cartes) |
| 4 | Modélisation (corrélations, régressions OLS, diagnostics) |
| 5 | Conclusion |

---
## Les variables importantes
| Variable | Source | Description | Unité |
|---|---|---|---|
| `taux_valo_total_pct` | SINOE | Taux de valorisation total (matière + organique) | % du tonnage total |
| `taux_valo_matiere_pct` | SINOE | Taux de valorisation matière (recyclage) | % du tonnage total |
| `taux_valo_organique_pct` | SINOE | Taux de valorisation organique (compostage, méthanisation) | % du tonnage total |
| `part_communes_rurales_pct` | FET INSEE | Part de communes peu ou très peu denses dans le département | % du nombre de communes |
| `niveau_vie_median` | Filosofi INSEE | Niveau de vie annuel médian par département | € / an / UC |
| `interaction_rural_revenu` | Calculée | Produit ruralité × niveau de vie (terme d'interaction pour la régression) | — |

> **UC** = unité de consommation (mesure INSEE du revenu par ménage ajustée à sa taille)

## Choix du modèle

Nous avons opté pour une **régression linéaire OLS** (moindres carrés ordinaires) pour deux raisons :

- La variable à expliquer (taux de valorisation) est **continue**
- On cherche à mesurer l'**effet marginal** de chaque variable explicative


### Trois modèles emboîtés

| Modèle | Variables | Objectif |
|---|---|---|
| Modèle 1 | Ruralité | Tester l'hypothèse territoriale seule |
| Modèle 2 | Ruralité + niveau de vie | Tester l'hypothèse socio-économique |
| Modèle 3 | Ruralité + niveau de vie + interaction | Tester si les deux effets sont interdépendants |

Le **R² ajusté** permet de comparer les modèles : si l'ajout d'une variable ne l'améliore pas, elle n'est pas utile.

### Limites du modèle

- Le **R² reste modéré** (~18% pour la valorisation totale) : d'autres facteurs non mesurés ici jouent un rôle (densité de déchèteries, politiques locales, part de maisons individuelles)
- Les **résidus ne sont pas parfaitement normaux** (test de Shapiro-Wilk p < 0.05) : les p-values sont à interpréter avec prudence
- L'analyse est **transversale** (une seule année) : elle ne permet pas de conclure sur des effets causaux

## Résultats principaux

- La **ruralité** est positivement et significativement associée à la valorisation,
  portée principalement par la **valorisation organique** (compostage).
- La **valorisation matière** (recyclage) est moins sensible à la ruralité.
- Le **niveau de vie médian** n'est pas un déterminant significatif.
- Le **terme d'interaction** ruralité × revenu n'est pas significatif :
  l'effet de la ruralité est indépendant de la richesse du département.

---

## Auteurs

Projet réalisé par Teodora Moldovan, Delphine Monnier Ragaigne et Mounene Kpakou dans le cadre du cours de Python pour la data science.

## Sources des données (pour aller plus loin)

- [SINOE — ADEME](https://data.ademe.fr/datasets/sinoe-(r)-destination-des-dma-collectes-par-type-de-traitement) : données complètes sur les déchets ménagers
- [Grille de densité communale — INSEE](https://www.insee.fr/fr/information/6439600) : méthodologie et téléchargement FET
- [Filosofi — INSEE](https://www.insee.fr/fr/metadonnees/source/serie/s1172) : revenus et niveaux de vie des ménages
- [API ADEME data.ademe.fr](https://data.ademe.fr/api-doc) : documentation de l'API utilisée pour charger les données SINOE

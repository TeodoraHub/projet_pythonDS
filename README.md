# Recyclage et déplacements : à la recherche d'un profil écologique géographique ?
Analyse croisée de la valorisation des déchets et des modes de transport (2016-2022)

## Problématique

Les questions écologiques constituent une thématique importante notamment dans la gestion des territoires. Partant de ce constat, nous avons cherché un indicateur de comportement écologique que l'on pourrait croiser avec des données géographiques liés à la population francaise. Nous avons donc décidé de nous interesser à la **valorisation des déchets ménagers et assimilés (DMA)**, et aux **modes de déplacement**.

Nous allons montrer que tant la valorisation que les modes de transport varient considérablement d'un département à l'autre, et nous présenterons quelques facteurs territoriaux et socio-économiques expliquant ces disparités.

Nous cherchons à identifier si certains départements se distinguent par un "profil écologique complet" :

Côté Déchets : Quels départements valorisent le mieux leurs déchets ménagers (Recyclage & Compostage) ? Est-ce lié à la richesse ou à la ruralité ?

Ce notebook explore deux hypothèses principales :
1. **Hypothèse territoriale** : les départements ruraux, bénéficiant d'une gestion différente des déchets (compostage, valorisation organique), présenteraient de meilleurs taux de valorisation.
2. **Hypothèse socio-économique** : les départements plus aisés investiraient davantage dans les infrastructures de tri et de recyclage.

Nous nous sommes aussi intéressés aux deux composantes de la valorisation :
- **Valorisation de la matière** : recyclage
- **Valorisation organique** : compostage et méthanisation

Côté Mobilité : Comment l'usage du vélo et des transports en commun a-t-il évolué entre 2016 et 2022 ?
Comprendre comment les **modes de transport** utilisés pour aller travailler ont évolué entre **2016 et 2022** en France métropolitaine, à l'échelle des départements.

Synthèse : Existe-t-il une corrélation entre les zones qui recyclent le plus et celles qui utilisent le moins la voiture ?

## Données utilisées

| Source | Fichier | Description |
|--------|---------|-------------|
| ADEME / SINOE | `SINOE04_DestinationDmaParTypeTraitement.csv` | Tonnages de déchets par type de traitement et département |
| INSEE | `DS_RP_NAVETTES_PRINC_2022_data.csv` | Déplacements domicile-travail selon le mode de transport, source **Recensement de la Population** (RP) de l'INSEE, disponibles sur data.gouv.fr.
| INSEE | `FET2021-19.xlsx` | Grille de densité communale (urbain/rural) |
| INSEE | `niv2021.xlsx` | Niveau de vie médian annuel par département(légèrement revu, les 3 premiers lignes ont été supprimées |


>  Les 3 premières lignes de `niv2021.xlsx` ont été supprimées manuellement.
Les fichiers de données sont sur onyxia avec un lien directement dans le notebook.
> Les données SINOE peuvent aussi être chargées directement via l'API ADEME
> (voir cellule dédiée dans le notebook).

---

## 3. Structure du projet

```
projet_pythonDS/
├── recyclage_et_deplacements.ipynb  # Notebook principal
├── fonctions.py                     # Fonctions réutilisables
├── requirements.txt                 # Dépendances Python
├── README.md                        # Ce fichier
├── .gitignore                       # Fichiers exclus de Git
```

### Contenu de `fonctions.py`

| Fonction | Description |
|---|---|
| `scatter_regression(ax, df, ...)` | Nuage de points avec droite de régression et annotation des outliers |
| `attribuer_profil(row, med_valo, med_rural)` | Attribue un profil territorial à un département |
| `afficher_correlations(df, ...)` | Calcule et affiche les corrélations de Pearson et Spearman |
| `regression_ols(df, var_y, label_y)` | Estime 3 modèles OLS emboîtés et affiche un tableau de synthèse |
| `diagnostics_ols(modele, titre)` | Graphiques de diagnostic du modèle OLS (résidus, Q-Q plot, Shapiro-Wilk) |
| `afficher_gt_part_modale(df_pct, annee)` | Formate et affiche une table Great Tables des modes de transport (en %) par département|
| `extraire_extremes(data, nom_mode)` | Tri et affiche le top 5 des modes de transport (en %) par département|

---

## 3. Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/TeodoraHub/projet_pythonDS.git
cd projet_pythonDS

# 2. Installer les dépendances manulement ou executer tout le code.
pip install -r Requirements.txt
```

---

## 4. Lancement

Ouvrir `notebook_recyclage_projet_python2.ipynb` dans VS Code, puis :

- **Tout exécuter** : bouton `Run All` en haut du notebook
- **Repartir de zéro** : `Restart Kernel and Run All Cells`

---

## 5. Plan du notebook

| Section | Contenu |
|---|---|
| 0 | Imports et paramètres |
| 1 | Chargement et nettoyage des sources de données |
| 2 | Analyse descriptive (statistiques, top/flop départements) |
| 3 | Visualisations (distributions, nuages de points, heatmap, cartes) |
| 4 | Modélisation (corrélations, régressions OLS, diagnostics) |
| 5 | Conclusion |

---
## 6. Les variables importantes
| Variable | Source | Description | Unité |
|---|---|---|---|
| `taux_valo_total_pct` | SINOE | Taux de valorisation total (matière + organique) | % du tonnage total |
| `taux_valo_matiere_pct` | SINOE | Taux de valorisation matière (recyclage) | % du tonnage total |
| `taux_valo_organique_pct` | SINOE | Taux de valorisation organique (compostage, méthanisation) | % du tonnage total |
| `part_communes_rurales_pct` | FET INSEE | Part de communes peu ou très peu denses dans le département | % du nombre de communes |
| `niveau_vie_median` | Filosofi INSEE | Niveau de vie annuel médian par département | € / an / UC |
| `interaction_rural_revenu` | Calculée | Produit ruralité × niveau de vie (terme d'interaction pour la régression) | 
| `part_mode_transport` | Calculée | Part de chaque mode de transport dans le total|
— |

> **UC** = unité de consommation (mesure INSEE du revenu par ménage ajustée à sa taille)

# Modes de transport dans la base:

| Code | Signification |
| :--- | :--- |
| 1 | Pas de transport (Télétravail / Travail à domicile) |
| 2 | Marche à pied |
| 3 | Vélo
| 4 | Deux-roues motorisé (Scooter, Moto) |
| 3T4 | Regroupement "Deux-roues" (Vélo + Moto) |
| 5 | Voiture, camion ou fourgonnette |
| 6 | Transport en commun |
| _T | Total (tous modes confondus) |

## 7. Visualisations

### Distributions (section 3.1)
Les histogrammes montrent la distribution de chaque variable sur les 96 départements.
La valorisation organique est très asymétrique — quelques départements composent
beaucoup plus que la moyenne. La ruralité présente une distribution bimodale :
beaucoup de départements très ruraux (>90%) et quelques très urbains (<20%).

### Nuages de points (section 3.2)
Six graphiques croisant les 3 indicateurs de valorisation (total, matière, organique)
avec les 2 variables explicatives (ruralité, niveau de vie).
La droite de régression et la corrélation de Pearson sont affichées sur chaque graphique.
Les 3 départements les plus atypiques (outliers) sont annotés.

### Matrice de corrélation (section 3.3)
Heatmap des corrélations de Pearson entre toutes les variables.
Permet de repérer d'un coup d'œil les relations fortes et la colinéarité éventuelle
entre variables explicatives.

### Cartes choroplèthes (section 3.4)
5 cartes de France colorant chaque département selon l'intensité d'une variable.
Permet de vérifier si les patterns statistiques ont une cohérence géographique.

### Carte typologique (section 3.5)
Croisement manuel de deux critères binaires (rural/urbain × valorisation forte/faible)
donnant 4 profils territoriaux. Les cas "rural / valorisation faible" sont
particulièrement intéressants car ils montrent que la ruralité seule ne suffit pas.

## 6. Clustering K-Means

En complément de l'analyse par régression, un clustering K-Means a été réalisé
pour regrouper automatiquement les départements sans définir de seuils à la main.

### Variables utilisées
- `taux_valo_total_pct`
- `part_communes_rurales_pct`
- `niveau_vie_median`

> Les variables sont normalisées avant le clustering (StandardScaler)
> pour éviter que le niveau de vie (20 000-30 000€) n'écrase les autres variables (0-100%).

### Choix du nombre de clusters
Le nombre de clusters k=4 a été retenu via la **méthode du coude**
(graphique inertie vs k) et pour permettre la comparaison avec les 4 profils manuels de la carte typologique.

### Résultats

| Cluster | Couleur | Profil | Valorisation | Ruralité | Niveau de vie |
|---|---|---|---|---|---|
| 0 | Vert clair | Rural / valorisation moyenne | 46% | 90% | 22 386€ |
| 1 | Rouge | Urbain / riche | 39% | 31% | 28 925€ |
| 2 | Vert foncé | Rural / valorisation forte | 63% | 90% | 22 383€ |
| 3 | Jaune | Urbain / revenu intermédiaire | 38% | 31% | 23 170€ |

### Enseignement principal
Les clusters 0 et 2 ont le même profil territorial et socio-économique
mais des performances très différentes. C'est donc **l'organisation des
filières locales** qui explique les écarts, pas la ruralité ni le revenu.

## 7. Choix du modèle

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

## 8. Résultats principaux

- La **ruralité** est positivement et significativement associée à la valorisation,
  portée principalement par la **valorisation organique** (compostage).
- La **valorisation matière** (recyclage) est moins sensible à la ruralité.
- Le **niveau de vie médian** n'est pas un déterminant significatif.
- Le **terme d'interaction** ruralité × revenu n'est pas significatif :
  l'effet de la ruralité est indépendant de la richesse du département.
- Le **clustering K-Means** confirme et affine ces résultats : les clusters 0 et 2
  ont exactement le même profil (ruraux, revenus modestes) mais des taux de
  valorisation différents , ce qui suggère que **l'organisation locale des filières de tri** est le facteur clé non capté par nos variables.

---

## Auteurs

Projet réalisé par Teodora Moldovan, Delphine Monnier Ragaigne et M'Mounéné Kpakou dans le cadre du cours de Python pour la data science.

## Sources des données (pour aller plus loin)

- [SINOE — ADEME](https://data.ademe.fr/datasets/sinoe-(r)-destination-des-dma-collectes-par-type-de-traitement) : données complètes sur les déchets ménagers
- [Grille de densité communale — INSEE](https://www.insee.fr/fr/information/6439600) : méthodologie et téléchargement FET
- [Filosofi — INSEE](https://www.insee.fr/fr/metadonnees/source/serie/s1172) : revenus et niveaux de vie des ménages
- [API ADEME data.ademe.fr](https://data.ademe.fr/api-doc) : documentation de l'API utilisée pour charger les données SINOE

## Références

Galiana, L. (2025). [*Python pour la data science*](https://pythonds.linogaliana.fr/). DOI : [10.5281/zenodo.8229676](https://doi.org/10.5281/zenodo.8229676)

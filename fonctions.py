import pandas as pd
import requests
from io import StringIO


# URL directe du fichier CSV ADEME sur data.ademe.fr
ADEME_CSV_URL = (
    "https://data.ademe.fr/data-fair/api/v1/datasets/"
    "sinoe-(r)-destination-des-dma-collectes-par-type-de-traitement/"
    "data-files/SINOE04_DestinationDmaParTypeTraitement.csv"
)


def get_ademe_data() -> pd.DataFrame:
    """
    Télécharge le fichier SINOE directement depuis l'API ADEME.

    Avantage : pas besoin d'avoir le fichier CSV en local.
    Inconvénient : nécessite une connexion internet.

    Retourne un DataFrame brut (non nettoyé).
    """
    # Téléchargement du fichier via une requête HTTP GET
    response = requests.get(ADEME_CSV_URL)

    # raise_for_status() : lève une erreur si le téléchargement a échoué
    # (ex : erreur 404 fichier introuvable, 500 serveur indisponible)
    response.raise_for_status()

    # StringIO permet de lire le texte téléchargé comme si c'était un fichier
    # sep=None + engine='python' : détection automatique du séparateur
    df = pd.read_csv(StringIO(response.text), sep=None, engine='python')
    print(f"Fichier ADEME chargé : {df.shape[0]} lignes × {df.shape[1]} colonnes")
    return df
def charger_sinoe(path: str) -> pd.DataFrame:
    """Charge et nettoie les données SINOE.
    
    Retourne un DataFrame avec une ligne par département et les colonnes :
    - tonnage_total, tonnage_valo_matiere, tonnage_valo_organique
    - taux_valo_total_pct, taux_valo_matiere_pct, taux_valo_organique_pct
    """
    # lecture du fichier csv
    df = pd.read_csv(path, sep=",", encoding="utf-8")
    print(f"Dimensions brutes : {df.shape}")
    print(f"Années disponibles : {sorted(df['ANNEE'].unique())}")
    print(f"Types de traitement : {df['L_TYP_REG_SERVICE'].unique().tolist()}")

    # Nettoyage du tonnage (virgule devient point pour python). On passe ensuite en float
    df["TONNAGE_DMA"] = (
        df["TONNAGE_DMA"]
        .astype(str)                          # s'assurer que c'est du texte
        .str.replace(",", ".", regex=False)   # "98575,13" → "98575.13"
        .astype(float)                        # conversion en nombre décimal
    )

    # Les codes département doivent être sur 2 caractères pour les jointures
    df["code_dept"]   = df["C_DEPT"].astype(str).str.zfill(2)
    df["departement"] = df["N_DEPT"]

    # Conserver la dernière année disponible
    annee_max = df["ANNEE"].max()
    df        = df[df["ANNEE"] == annee_max].copy()
    print(f"\nAnnée retenue : {annee_max}  ({len(df)} lignes après filtre)")

    # Marquage des lignes par type de valorisation
    # Deux colonnes booléennes (True/False) pour distinguer les composantes
    df["est_valo_matiere"]   = df["L_TYP_REG_SERVICE"] == "Valorisation matière"
    df["est_valo_organique"] = df["L_TYP_REG_SERVICE"] == "Valorisation organique"

    # On crée des colonnes de tonnage conditionnelles AVANT le groupby.
    # where(condition, 0) : garde le tonnage si la condition est vraie, sinon met 0.
    df["tonnage_si_matiere"]   = df["TONNAGE_DMA"].where(df["est_valo_matiere"],   0)
    df["tonnage_si_organique"] = df["TONNAGE_DMA"].where(df["est_valo_organique"], 0)

    # Pour chaque département, on somme les tonnages selon leur type.
    dept = (
        df.groupby(["code_dept", "departement"], as_index=False)
        .agg(
            tonnage_total          = ("TONNAGE_DMA",          "sum"),
            tonnage_valo_matiere   = ("tonnage_si_matiere",   "sum"),
            tonnage_valo_organique = ("tonnage_si_organique", "sum"),
        )
    )

    # Calcul des taux de valorisation (en %)
    # Taux = tonnage valorisé / tonnage total × 100
    dept["tonnage_valo_total"]      = dept["tonnage_valo_matiere"] + dept["tonnage_valo_organique"]
    dept["taux_valo_total_pct"]     = dept["tonnage_valo_total"]    / dept["tonnage_total"] * 100
    dept["taux_valo_matiere_pct"]   = dept["tonnage_valo_matiere"]  / dept["tonnage_total"] * 100
    dept["taux_valo_organique_pct"] = dept["tonnage_valo_organique"]/ dept["tonnage_total"] * 100

    print(f"{len(dept)} départements après agrégation")
    return dept

"""Fonctions de contrôle qualité des données de régularité TGV."""

import pandas as pd


def get_dataset_overview(data: pd.DataFrame) -> dict[str, int]:
    """Retourne les dimensions du jeu de données.

    Args:
        data: DataFrame contenant les données à analyser.

    Returns:
        Dictionnaire contenant le nombre de lignes
        et le nombre de colonnes.
    """
    return {
        "n_rows": len(data),
        "n_columns": len(data.columns),
    }


def get_missing_values(data: pd.DataFrame) -> pd.DataFrame:
    """Calcule le nombre et le pourcentage de valeurs manquantes.

    Args:
        data: DataFrame contenant les données à analyser.

    Returns:
        DataFrame contenant, pour chaque variable,
        le nombre et le pourcentage de valeurs manquantes.
    """
    missing_count = data.isna().sum()

    if data.empty:
        missing_percentage = missing_count.astype(float)
    else:
        missing_percentage = missing_count / len(data) * 100

    return pd.DataFrame(
        {
            "missing_count": missing_count,
            "missing_percentage": missing_percentage,
        }
    )


def count_duplicates(
    data: pd.DataFrame,
    subset: list[str] | None = None,
) -> int:
    """Compte les lignes dupliquées dans le jeu de données.

    Args:
        data: DataFrame contenant les données à analyser.
        subset: Liste facultative des colonnes utilisées
            pour identifier les doublons. Par défaut,
            toutes les colonnes sont prises en compte.

    Returns:
        Nombre de lignes dupliquées, sans compter
        la première occurrence de chaque ligne.
    """
    return int(data.duplicated(subset=subset).sum())


def get_column_types(data: pd.DataFrame) -> pd.DataFrame:
    """Identifie le type de données de chaque variable.

    Args:
        data: DataFrame contenant les données à analyser.

    Returns:
        DataFrame contenant le nom des variables
        et leur type de données Python/pandas.
    """
    return pd.DataFrame(
        {
            "column": data.columns,
            "dtype": data.dtypes.astype(str).to_numpy(),
        }
    )


def check_identifiers(data: pd.DataFrame) -> pd.DataFrame:
    """Contrôle les identifiants des observations SNCF.

    Vérifie la présence des informations d'identification,
    la validité des dates et l'unicité des observations.

    Les vérifications:

    date	        Date présente et interprétable
    service	        Service renseigné, non vide
    gare_depart	    Gare de départ renseignée
    gare_arrivee	Gare d'arrivée renseignée

    Args:
        data: DataFrame contenant les observations SNCF.

    Returns:
        DataFrame récapitulant le nombre d'anomalies
        détectées pour chaque règle.

    Raises:
        ValueError: Si une colonne obligatoire est absente.
    """
    columns = [
        "date",
        "service",
        "gare_depart",
        "gare_arrivee",
    ]

    missing_columns = sorted(set(columns) - set(data.columns))

    if missing_columns:
        raise ValueError(f"Colonnes manquantes : {missing_columns}")

    # Contrôler les valeurs absentes ou composées d'espaces.
    missing_identifiers = {}

    for column in columns[1:]:
        values = data[column].astype("string")

        missing_identifiers[f"{column}_manquant"] = (
            values.isna() | values.str.strip().eq("")
        ).fillna(True)

    # Les dates attendues sont exprimées au format AAAA-MM.
    date_values = data["date"].astype("string")
    # Vérifie avec une expression régulière que la date est au format AAAA-MM.
    valid_format = date_values.str.fullmatch(r"\d{4}-(0[1-9]|1[0-2])").fillna(False)

    parsed_dates = pd.to_datetime(
        date_values.where(valid_format) + "-01",
        format="%Y-%m-%d",
        errors="coerce",  # coerce signifie que les dates invalides seront converties en NaT (Not a Time)
    )

    invalid_dates = parsed_dates.isna()

    # La clé métier est la combinaison des quatre colonnes.
    duplicated_keys = data.duplicated(subset=columns)

    checks = {
        "date_invalide": invalid_dates,
        **missing_identifiers,
        "doublon_metier": duplicated_keys,
    }

    return pd.DataFrame(
        [
            {
                "regle": rule,
                "nombre_anomalies": int(mask.sum()),
            }
            for rule, mask in checks.items()
        ]
    )

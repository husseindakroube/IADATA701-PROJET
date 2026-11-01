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

'Indicateurs qualité non destructifs pour chaque observation SNCF.'

from __future__ import annotations

import polars as pl

COUNT_COLUMNS = (
    "nb_train_prevu",
    "nb_annulation",
    "nb_train_depart_retard",
    "nb_train_retard_arrivee",
    "nb_train_retard_sup_15",
    "nb_train_retard_sup_30",
    "nb_train_retard_sup_60",
)

FLAG_COLUMNS = (
    "flag_negative_count",
    "flag_sup30_lt_sup60",
    "flag_sup15_lt_sup30",
    "flag_cancellations_gt_planned",
)


def clean_data(df: pl.DataFrame) -> pl.DataFrame:
    """Renvoie une copie d’analyse non destructive avec des indicateurs qualité par ligne.
    
    Toutes les colonnes, valeurs, lignes et leur ordre sont conservés. Quatre colonnes
    booléennes de diagnostic sont ajoutées, sans correction, suppression ou autre
    transformation. L’utilisation de Polars correspond à l’audit existant ; le contrat
    commun n’impose pas aux consommateurs Pandas de migrer vers Polars.
    
    Toutes les colonnes de comptage requises doivent être présentes. Seuls les types
    entiers ou entièrement nuls sont acceptés pour ne pas ignorer silencieusement une
    comparaison impossible. Une colonne portant déjà le nom d’un indicateur réservé
    est refusée afin de ne pas écraser les données sources.
    
    :param df: Données SNCF sous forme de DataFrame Polars.
    :type df: polars.DataFrame
    :returns: Nouvelle table avec les données d’origine et les indicateurs de diagnostic ; ceux-ci signalent des observations à examiner, sans déterminer de valeur corrigée.
    :rtype: polars.DataFrame
    :raises TypeError: Si ``df`` n’est pas un DataFrame Polars.
    :raises ValueError: Si un comptage requis manque, a un type autre qu’entier ou ``pl.Null``, ou entre en conflit avec un nom d’indicateur."""
    if not isinstance(df, pl.DataFrame):
        raise TypeError('df doit être un DataFrame Polars.')

    missing_columns = sorted(set(COUNT_COLUMNS) - set(df.columns))
    if missing_columns:
        raise ValueError(
            f"Colonnes de comptage requises pour les indicateurs qualité absentes : {missing_columns}"
        )

    conflicting_flags = sorted(set(FLAG_COLUMNS) & set(df.columns))
    if conflicting_flags:
        raise ValueError(
            'L’entrée contient déjà des colonnes réservées aux indicateurs de diagnostic : '
            f"{conflicting_flags}"
        )

    invalid_types = {
        column: str(df.schema[column])
        for column in COUNT_COLUMNS
        if df.schema[column] != pl.Null and not df.schema[column].is_integer()
    }
    if invalid_types:
        raise ValueError(
            'Les colonnes de comptage doivent être entières ou entièrement nulles : '
            f"{invalid_types}"
        )

    negative_count_checks = [
        (pl.col(column) < 0).fill_null(False) for column in COUNT_COLUMNS
    ]

    return df.with_columns(
        pl.any_horizontal(negative_count_checks)
        .fill_null(False)
        .alias("flag_negative_count"),
        (pl.col("nb_train_retard_sup_30") < pl.col("nb_train_retard_sup_60"))
        .fill_null(False)
        .alias("flag_sup30_lt_sup60"),
        (pl.col("nb_train_retard_sup_15") < pl.col("nb_train_retard_sup_30"))
        .fill_null(False)
        .alias("flag_sup15_lt_sup30"),
        (pl.col("nb_annulation") > pl.col("nb_train_prevu"))
        .fill_null(False)
        .alias("flag_cancellations_gt_planned"),
    )

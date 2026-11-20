"""Flags non destructifs de qualité des données SNCF au niveau des lignes."""

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
    """Retourner une copie d’analyse non destructive munie de flags qualité par ligne.

    La fonction conserve toutes les colonnes et valeurs d’entrée, l’ordre des
    lignes et leur nombre. Elle ajoute quatre colonnes diagnostiques booléennes ;
    elle ne corrige, ne supprime ni ne transforme autrement les données source.
    Polars est utilisé ici pour correspondre à l’implémentation actuelle de
    l’audit, mais le contrat de données partagé n’impose pas aux consommateurs
    Pandas de migrer vers Polars.

    Toutes les colonnes de compte utilisées par les flags doivent être
    présentes. Les colonnes entières et celles qui ne contiennent que des
    valeurs manquantes (type ``pl.Null``) sont acceptées ; les autres types sont
    rejetés afin qu’une comparaison impossible ne soit pas silencieusement ignorée. Les colonnes
    d’entrée portant déjà le nom d’un flag diagnostique sont rejetées pour
    éviter d’écraser les données source.

    :param df: Données SNCF d’entrée sous forme de DataFrame Polars.
    :type df: polars.DataFrame
    :returns: Nouveau DataFrame contenant les données d’origine et les flags
        diagnostiques. Les flags signalent les enregistrements à examiner sans
        définir de valeurs corrigées.
    :rtype: polars.DataFrame
    :raises TypeError: Si ``df`` n’est pas un DataFrame Polars.
    :raises ValueError: Si une colonne de compte obligatoire est absente, si
        son type n’est pas entier ni ``pl.Null``, ou si son nom entre en
        conflit avec celui d’un flag diagnostique.
    """
    if not isinstance(df, pl.DataFrame):
        raise TypeError("df doit être un DataFrame Polars.")

    missing_columns = sorted(set(COUNT_COLUMNS) - set(df.columns))
    if missing_columns:
        raise ValueError(
            f"Colonnes de compte manquantes pour les flags de nettoyage : {missing_columns}"
        )

    conflicting_flags = sorted(set(FLAG_COLUMNS) & set(df.columns))
    if conflicting_flags:
        raise ValueError(
            "L’entrée contient déjà des colonnes réservées aux flags diagnostiques : "
            f"{conflicting_flags}"
        )

    invalid_types = {
        column: str(df.schema[column])
        for column in COUNT_COLUMNS
        if df.schema[column] != pl.Null and not df.schema[column].is_integer()
    }
    if invalid_types:
        raise ValueError(
            "Les colonnes de compte obligatoires doivent être entières ou contenir uniquement des "
            "valeurs manquantes (type Null) : "
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

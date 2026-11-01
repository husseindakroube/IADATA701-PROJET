"""Fonctions de contrôle qualité des données de régularité TGV."""

import pandas as pd
import numpy as np


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


def check_train_counts(data: pd.DataFrame) -> pd.DataFrame:
    """Contrôle la cohérence des comptages de trains SNCF.

    Vérifie les nombres de trains, les annulations et
    les différents indicateurs de retard.

    Les verifications:
    nb_train_prevu	        Nombre positif ou nul, entier
    nb_annulation	        Nombre entre 0 et le nombre de trains prévus
    nb_train_depart_retard	Nombre positif ou nul, ne dépassant pas les trains ayant circulé
    nb_train_retard_arrivee	Même contrôle pour les retards à l'arrivée
    nb_train_retard_sup_15	Nombre positif ou nul, ne dépassant pas les trains ayant circulé
    nb_train_retard_sup_30	Ne dépasse pas le nombre de retards de plus de 15 minutes
    nb_train_retard_sup_60	Ne dépasse pas le nombre de retards de plus de 30 minutes

    Args:
        data: DataFrame contenant les observations SNCF.

    Returns:
        DataFrame présentant le nombre d'anomalies
        détectées pour chaque règle.

    Raises:
        ValueError: Si une colonne obligatoire est absente.
    """
    columns = [
        "nb_train_prevu",
        "nb_annulation",
        "nb_train_depart_retard",
        "nb_train_retard_arrivee",
        "nb_train_retard_sup_15",
        "nb_train_retard_sup_30",
        "nb_train_retard_sup_60",
    ]

    missing_columns = sorted(set(columns) - set(data.columns))

    if missing_columns:
        raise ValueError(f"Colonnes manquantes : {missing_columns}")

    # Convertir les valeurs en nombres pour effectuer
    # les comparaisons et identifier les valeurs invalides.
    counts = data[columns].apply(
        pd.to_numeric,
        errors="coerce",
    )

    # Les trains ayant circulé correspondent aux
    # circulations prévues moins les annulations.
    trains_running = counts["nb_train_prevu"] - counts["nb_annulation"]

    checks = {
        "comptage_manquant_ou_invalide": (counts.isna().any(axis=1)),
        "comptage_negatif": (counts.lt(0).any(axis=1)),
        "comptage_non_entier": (counts.notna() & counts.mod(1).ne(0)).any(axis=1),
        "annulations_excessives": (counts["nb_annulation"] > counts["nb_train_prevu"]),
        "retards_depart_excessifs": (counts["nb_train_depart_retard"] > trains_running),
        "retards_arrivee_excessifs": (
            counts["nb_train_retard_arrivee"] > trains_running
        ),
        "retards_15_excessifs": (counts["nb_train_retard_sup_15"] > trains_running),
        "retards_30_excessifs": (counts["nb_train_retard_sup_30"] > trains_running),
        "retards_60_excessifs": (counts["nb_train_retard_sup_60"] > trains_running),
        "seuil_60_superieur_30": (
            counts["nb_train_retard_sup_60"] > counts["nb_train_retard_sup_30"]
        ),
    }

    # Chaque masque contient True si la ligne
    # ne respecte pas la règle correspondante.
    return pd.DataFrame(
        [
            {
                "regle": rule,
                "nombre_anomalies": int(mask.sum()),
            }
            for rule, mask in checks.items()
        ]
    )


def check_durations(data: pd.DataFrame) -> pd.DataFrame:
    """Contrôle les durées et retards moyens des données SNCF.

    Vérifie les valeurs manquantes, les valeurs non numériques
    et certaines contraintes de cohérence sur les durées.

    duree_moyenne	                    Durée du trajet strictement positive et entière
    retard_moyen_depart	Retard          moyen des trains retardés au départ, non négatif
    retard_moyen_tous_trains_depart	    Valeur numérique finie
    retard_moyen_arrivee	            Retard moyen des trains retardés à l'arrivée, non négatif
    retard_moyen_tous_trains_arrivee	Valeur numérique finie
    retard_moyen_trains_retard_sup15	Valeur numérique finie, avec contrôle complémentaire à prévoir

    Args:
        data: DataFrame contenant les observations SNCF.

    Returns:
        DataFrame contenant le nombre d'anomalies détectées
        pour chaque règle de contrôle.

    Raises:
        ValueError: Si une colonne obligatoire est absente.
    """
    columns = [
        "duree_moyenne",
        "retard_moyen_depart",
        "retard_moyen_tous_trains_depart",
        "retard_moyen_arrivee",
        "retard_moyen_tous_trains_arrivee",
        "retard_moyen_trains_retard_sup15",
    ]

    missing_columns = sorted(set(columns) - set(data.columns))

    if missing_columns:
        raise ValueError(f"Colonnes manquantes : {missing_columns}")

    # Convertir les valeurs en nombres.
    durations = data[columns].apply(
        pd.to_numeric,
        errors="coerce",
    )

    # Repérer les valeurs non numériques ou manquantes.
    missing_values = durations.isna().any(axis=1)

    # Repérer les valeurs infinies.
    infinite_values = pd.Series(
        np.isinf(durations.to_numpy(dtype=float)).any(axis=1),
        index=data.index,
    )

    # La durée prévue d'un trajet doit être positive.
    invalid_trip_duration = durations["duree_moyenne"] <= 0

    # La durée moyenne prévue est définie comme un entier.
    non_integer_trip_duration = durations["duree_moyenne"].notna() & durations[
        "duree_moyenne"
    ].mod(1).ne(0)

    # Contrôler les moyennes des trains effectivement retardés.
    negative_delayed_average = (
        durations[["retard_moyen_depart", "retard_moyen_arrivee"]].lt(0).any(axis=1)
    )

    checks = {
        "duree_manquante_ou_non_numerique": missing_values,
        "duree_infinie": infinite_values,
        "trajet_duree_invalide": invalid_trip_duration,
        "trajet_duree_non_entiere": non_integer_trip_duration,
        "moyenne_trains_retardes_negative": negative_delayed_average,
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


def check_percentages(
    data: pd.DataFrame,
    tolerance: float = 0.1,
) -> pd.DataFrame:
    """Contrôle les pourcentages des causes de retard SNCF.

    Vérifie les valeurs manquantes, non numériques,
    les bornes des pourcentages et leur somme.

    Valeurs manquantes	    Détecter NaN
    Valeurs non numériques	Détecter les conversions impossibles
    Pourcentages négatifs	Valeur inférieure à 0
    Pourcentages excessifs	Valeur supérieure à 100
    Somme des causes	    Vérifier si la somme vaut environ 100 %

    Args:
        data: DataFrame contenant les données SNCF.
        tolerance: Écart maximal accepté autour de 100
            pour la somme des pourcentages, en points.

    Returns:
        DataFrame contenant le nombre d'observations
        signalées pour chaque règle.

    Raises:
        ValueError: Si une colonne obligatoire est absente
            ou si la tolérance est négative.
    """
    columns = [
        "prct_cause_externe",
        "prct_cause_infra",
        "prct_cause_gestion_trafic",
        "prct_cause_materiel_roulant",
        "prct_cause_gestion_gare",
        "prct_cause_prise_en_charge_voyageurs",
    ]

    missing_columns = sorted(set(columns) - set(data.columns))

    if missing_columns:
        raise ValueError(f"Colonnes manquantes : {missing_columns}")

    if tolerance < 0:
        raise ValueError("La tolérance doit être positive ou nulle.")

    # Convertir les valeurs en nombres.
    percentages = data[columns].apply(
        pd.to_numeric,
        errors="coerce",
    )

    # Distinguer les valeurs réellement absentes
    # des valeurs impossibles à convertir.
    missing_values = data[columns].isna().any(axis=1)

    invalid_numeric = (percentages.isna() & data[columns].notna()).any(axis=1)

    # Vérifier les bornes autorisées des pourcentages.
    negative_values = percentages.lt(0).any(axis=1)
    excessive_values = percentages.gt(100).any(axis=1)

    # Ne calculer une somme complète que si les
    # six pourcentages sont numériques et valides.
    complete_rows = percentages.notna().all(axis=1)

    valid_bounds = percentages.ge(0).all(axis=1) & (percentages.le(100).all(axis=1))

    valid_rows = complete_rows & valid_bounds

    # Utiliser min_count pour éviter de traiter
    # des valeurs manquantes comme des zéros.
    total = percentages.sum(axis=1, min_count=len(columns))

    invalid_total = valid_rows & (total - 100).abs().gt(tolerance)

    checks = {
        "pourcentage_manquant": missing_values,
        "pourcentage_non_numerique": invalid_numeric,
        "pourcentage_negatif": negative_values,
        "pourcentage_superieur_100": excessive_values,
        "somme_causes_differente_100": invalid_total,
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


def check_comments(data: pd.DataFrame) -> pd.DataFrame:
    """Analyse la complétude des commentaires SNCF.

    Distingue les commentaires manquants, les textes vides
    et les commentaires réellement renseignés.

    commentaire_annulation	    Nombre de commentaires présents, absents ou vides
    commentaire_retards_depart	Même contrôle pour les retards au départ
    commentaires_retard_arrivee	Même contrôle pour les retards à l'arrivée

    Args:
        data: DataFrame contenant les observations SNCF.

    Returns:
        DataFrame récapitulant, pour chaque colonne,
        les commentaires manquants, vides et renseignés.

    Raises:
        ValueError: Si une colonne attendue est absente.
    """
    columns = [
        "commentaire_annulation",
        "commentaire_retards_depart",
        "commentaires_retard_arrivee",
    ]

    missing_columns = sorted(set(columns) - set(data.columns))

    if missing_columns:
        raise ValueError(f"Colonnes manquantes : {missing_columns}")

    results = []

    for column in columns:
        # Convertir en chaîne tout en conservant les valeurs manquantes.
        values = data[column].astype("string")

        # Identifier les trois catégories de commentaires.
        missing = values.isna()
        empty = values.notna() & values.str.strip().eq("").fillna(False)
        present = values.notna() & ~empty

        results.append(
            {
                "colonne": column,
                "nb_manquants": int(missing.sum()),
                "nb_vides": int(empty.sum()),
                "nb_renseignes": int(present.sum()),
                "pourcentage_renseignes": (
                    round(present.sum() / len(data) * 100, 2) if len(data) > 0 else 0.0
                ),
            }
        )

    return pd.DataFrame(results)

"""Fonctions de validation et de filtrage des résultats d'association enregistrés."""

import pandas as pd

SCOPES = {
    "Ensemble (Overall)": ("overall", "Overall"),
    "National": ("service", "National"),
    "International": ("service", "International"),
}

PREDICTOR_LABELS = {
    "edge_betweenness": "Betweenness de l’arête",
    "source_degree": "Degré du nœud de départ",
    "target_degree": "Degré du nœud d’arrivée",
    "source_betweenness_centrality": "Betweenness Centrality du nœud de départ",
    "target_betweenness_centrality": "Betweenness Centrality du nœud d’arrivée",
    "source_pagerank": "PageRank du nœud de départ",
    "target_pagerank": "PageRank du nœud d’arrivée",
}

OUTCOME_LABELS = {
    "retard_moyen_tous_trains_arrivee": "Retard moyen à l’arrivée, tous les trains (min)",
    "retard_moyen_arrivee": "Retard moyen à l’arrivée des trains retardés (min)",
    "cancellation_rate": "Taux d’annulation",
}

METHOD_LABELS = {
    "spearman": "Corrélation de Spearman",
    "pearson": "Corrélation de Pearson",
}

CORRELATION_COLUMNS = {
    "analysis_scope",
    "service",
    "predictor",
    "outcome",
    "method",
    "coefficient",
    "p_value",
    "n_valid",
}
QUANTILE_COLUMNS = {
    "analysis_scope",
    "service",
    "predictor",
    "outcome",
    "group_label",
    "grouping_strategy",
    "n",
    "median",
    "mean",
    "std",
    "q25",
    "q75",
    "iqr",
}
ROBUSTNESS_COLUMNS = {
    "analysis_scope",
    "service",
    "predictor",
    "outcome",
    "method",
    "full_coefficient",
    "sensitivity_coefficient",
    "coefficient_difference",
    "full_n_valid",
    "sensitivity_n_valid",
}


def validate_result_table(
    frame: pd.DataFrame, required: set[str], label: str
) -> tuple[pd.DataFrame, str | None]:
    """Valide les colonnes d'une table enregistrée sans modifier ses valeurs."""
    if frame.empty:
        return frame.copy(), f"La table {label} est vide ou indisponible."
    missing = required - set(frame.columns)
    if missing:
        return (
            pd.DataFrame(),
            f"La table {label} ne peut pas être affichée : champs absents "
            f"({', '.join(sorted(missing))}).",
        )
    return frame.copy(), None


def _filter_scope(frame: pd.DataFrame, scope_label: str) -> pd.DataFrame:
    analysis_scope, service = SCOPES[scope_label]
    return frame.loc[
        frame.analysis_scope.eq(analysis_scope) & frame.service.eq(service)
    ].copy()


def filter_correlations(
    frame: pd.DataFrame,
    scope: str,
    method: str,
    predictor: str | None = None,
    outcome: str | None = None,
) -> pd.DataFrame:
    """Filtre les coefficients enregistrés selon les choix de l'interface."""
    result = _filter_scope(frame, scope)
    result = result.loc[result.method.eq(method)]
    if predictor is not None:
        result = result.loc[result.predictor.eq(predictor)]
    if outcome is not None:
        result = result.loc[result.outcome.eq(outcome)]
    return result.copy()


def filter_quantiles(
    frame: pd.DataFrame,
    scope: str,
    predictor: str,
    outcome: str,
) -> pd.DataFrame:
    """Filtre les résumés de groupes sans recalculer les quantiles."""
    result = _filter_scope(frame, scope)
    result = result.loc[result.predictor.eq(predictor) & result.outcome.eq(outcome)]
    return result.copy()


def filter_robustness(
    frame: pd.DataFrame,
    scope: str,
    method: str,
    predictor: str | None = None,
) -> pd.DataFrame:
    """Filtre les comparaisons complètes et de sensibilité enregistrées."""
    result = _filter_scope(frame, scope)
    result = result.loc[result.method.eq(method)]
    if predictor is not None:
        result = result.loc[result.predictor.eq(predictor)]
    return result.copy()

"""Définition des variables et des modèles de prédiction des retards TGV."""

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

# Variables utilisées dans tous les modèles
BASE_FEATURES = [
    "service",
    "departure",
    "arrival",
    "month",
]

# Caractéristiques calculées pour chaque gare
STATION_FEATURES = [
    "in_degree",
    "out_degree",
    "total_degree",
    "betweenness",
    "pagerank",
    "in_strength",
    "out_strength",
    "weighted_pagerank",
]

# Caractéristiques des gares de départ et d'arrivée
GRAPH_FEATURES = [
    f"{direction}_{feature}"
    for direction in ("departure", "arrival")
    for feature in STATION_FEATURES
]

# Caractéristiques historiques des liaisons
EDGE_FEATURES = [
    "edge_volume",
    "edge_traffic_share",
    "edge_reverse_volume",
]

# Historique de ponctualité
HISTORY_FEATURES = [
    "historical_delay_rate_15",
]

# Variable à prédire
TARGET = "delay_rate_15"


def build_preprocessor(
    numeric_features: list[str] | None = None,
) -> ColumnTransformer:
    """Prépare les variables catégorielles et numériques pour le modèle.

    Args:
        numeric_features: Variables numériques supplémentaires
            à intégrer aux variables de base.

    Returns:
        Transformateur scikit-learn avec encodage des catégories
        et imputation des valeurs numériques manquantes.
    """
    categorical_features = [
        "service",
        "departure",
        "arrival",
    ]

    transformers = [
        (
            "categorical",
            OneHotEncoder(
                handle_unknown="ignore",
                sparse_output=False,
            ),
            categorical_features,
        ),
        (
            "month",
            "passthrough",
            ["month"],
        ),
    ]

    if numeric_features:
        numeric_pipeline = Pipeline(
            steps=[
                (
                    "imputer",
                    SimpleImputer(
                        strategy="constant",
                        fill_value=0,
                        add_indicator=True,
                    ),
                ),
            ]
        )

        transformers.append(("numeric", numeric_pipeline, numeric_features))

    return ColumnTransformer(
        transformers=transformers,
        remainder="drop",
    )


def build_model(
    numeric_features: list[str] | None = None,
    max_iter: int = 150,
    learning_rate: float = 0.05,
    max_leaf_nodes: int = 15,
) -> Pipeline:
    """Construit le pipeline de régression des taux de retard.

    Args:
        numeric_features: Variables numériques supplémentaires.
        max_iter: Nombre maximal d'itérations de boosting.
        learning_rate: Taux d'apprentissage.
        max_leaf_nodes: Nombre maximal de feuilles par arbre.

    Returns:
        Pipeline combinant prétraitement et HistGradientBoostingRegressor.
    """
    return Pipeline(
        steps=[
            (
                "preprocessor",
                build_preprocessor(
                    numeric_features=numeric_features,
                ),
            ),
            (
                "regressor",
                HistGradientBoostingRegressor(
                    max_iter=max_iter,
                    learning_rate=learning_rate,
                    max_leaf_nodes=max_leaf_nodes,
                    random_state=42,
                    early_stopping=False,
                ),
            ),
        ]
    )

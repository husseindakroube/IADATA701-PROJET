"""Public APIs for constructing and exporting SNCF route graphs."""

from projet_kit_data.graph.analysis import (
    ResearchDataResult,
    prepare_research_dataset,
    run_research_data_preparation_pipeline,
)
from projet_kit_data.graph.construction import (
    DEFAULT_INPUT_PATH,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REPORT_PATH,
    GraphConstructionResult,
    construct_graph_data,
    export_graph_artifacts,
    reconstruct_monthly_graph,
    run_graph_construction_pipeline,
)
from projet_kit_data.graph.descriptive import (
    DescriptiveResult,
    build_descriptive_summaries,
    run_descriptive_analysis,
)
from projet_kit_data.graph.metrics import GraphMetricsResult, run_graph_metrics_pipeline
from projet_kit_data.graph.visualization import (
    generate_visualizations,
    run_visualization_pipeline,
)

__all__ = [
    "DEFAULT_INPUT_PATH",
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_REPORT_PATH",
    "DescriptiveResult",
    "GraphConstructionResult",
    "GraphMetricsResult",
    "ResearchDataResult",
    "build_descriptive_summaries",
    "construct_graph_data",
    "export_graph_artifacts",
    "generate_visualizations",
    "prepare_research_dataset",
    "reconstruct_monthly_graph",
    "run_descriptive_analysis",
    "run_graph_construction_pipeline",
    "run_graph_metrics_pipeline",
    "run_research_data_preparation_pipeline",
    "run_visualization_pipeline",
]

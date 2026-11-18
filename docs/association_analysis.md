# Association analysis for Streamlit integration

The association module reads the existing Phase 2 file
`data/processed/research_dataset.parquet`. It does not rerun upstream
preparation and does not modify input data. The outputs are three compact
Parquet tables, metadata, reusable PNG figures, and an updated marked section
in the unified French research report. The module has no Streamlit dependency.

## Run

```powershell
uv run python -c "from projet_kit_data.graph import run_association_analysis_pipeline; result = run_association_analysis_pipeline()"
```

## Analysis

Pearson and Spearman correlations use pairwise finite observations.
Cancellation-rate observations are included only when the existing
`cancellation_rate_valid` flag is true. The correlation table keeps raw
p-values as optional exploratory fields; no multiple-testing correction is
applied, and p-values are not confirmatory evidence. Monthly observations for
the same directed liaison are repeated observations, so ordinary p-values may
overstate the statistical evidence.

The outcomes are mean arrival delay of all trains, valid cancellation rate, and
mean arrival delay among delayed trains. The predictors are existing edge
betweenness and source/target degree, betweenness centrality, and PageRank. The
restricted-scope `nb_train_retard_sup_15` is not an outcome;
`arrival_delay_rate` is not created. National and International are reported
separately. Overall is provided only as a pooled descriptive overview.

Outcome summaries are available across centrality groups. Group boundaries
retain ties; a zero group is separated when zero values meet the existing 5%
threshold, and the existing minimum sample and distinct-value requirements
remain in force. Summaries include sample size, median, mean, standard
deviation, quartiles, and IQR.

A robustness table compares full-data correlations for the primary outcome
with correlations after excluding values below -15 minutes for that comparison
alone. The underlying observations remain unchanged.

## Output contract

Files are written to `data/processed/graph/phase3b/`:

- `correlations.parquet`: one row per scope, service, predictor, outcome, and
  method; includes coefficient, raw p-value, and effective sample size.
- `quantile_comparisons.parquet`: one row per group and scope/service, with
  group label, grouping strategy, sample size, median, mean, standard
  deviation, Q1, Q3, and IQR.
- `robustness_comparisons.parquet`: full and sensitivity coefficients,
  coefficient difference, method, and both effective sample sizes.
- `association_metadata.json`: input dimensions and period, service liaison
  counts, grouping rules, interpretation limits, and output schemas.

Four reusable figures are written to
`data/processed/graph/visualizations/phase3b/`: two service-specific scatter
plots, a centrality-group outcome plot, and a Spearman overview. The generated
report section is bounded by dedicated association markers in
`data/reports/graph/research_report.md`; text outside those markers is retained.

## Interpretation limits

Associations do not establish causality. National and International have
different route compositions and network structures, so their operational
outcomes should not be compared without qualification. International has fewer
distinct OD connections. OD liaisons are not necessarily adjacent physical rail
segments or confirmed train itineraries. The data do not establish passenger
volume or delay propagation.

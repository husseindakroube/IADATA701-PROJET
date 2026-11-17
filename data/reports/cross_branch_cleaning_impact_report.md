# Cross-Branch Data Usage Audit and Cleaning Impact Assessment

## 1. Scope and method

This is a read-only comparison of the current checkout, locally available Git refs, and remote branch commit snapshots. No branch was checked out. The only artifact created for this task is this report.

The active branch is `mian_ETL_GRAPH`. At inspection start it already had a modified `pyproject.toml` and untracked `data/`, `image/`, `src/projet_kit_data/{etl,graph,ingestion}/`, `tests/`, and `uv.lock`. The local `main`, feature branch, and `origin/main` refs were stale at the initial commit (`a51e31d`). Remote branch heads were inspected by hash: `Test_Shihao` (`cfed3df`), `hussein-eda` (`a7855d2`), `marius-eda` (`fc28172`), and `main` (`6dcf4be`). Their commit objects were fetched for read-only inspection; no refs or worktree were updated. Branch names are not treated as proof of ownership.

The raw snapshot `data/raw/regularite-mensuelle-tgv-aqst.json` was read locally and independently rechecked: 12,907 records, 26 fields, 105 month values. Existing audit outputs were read without editing: `data/reports/data_quality_report.txt` and `data/reports/anomaly_investigation_report.md`. Percentages below use 12,907 total rows, or the relevant month total where specified. Existing anomaly rules are diagnostics, not accepted correction rules.

## 2. Branch and module inventory

| Branch snapshot | Relevant files and observed use | Relation to current checkout |
| --- | --- | --- |
| `mian_ETL_GRAPH` (current) | `src/projet_kit_data/etl/audit.py` audits the 26 raw fields and generates diagnostics. Current `etl/cleaning.py`, `etl/preprocessing.py`, and `graph/{construction,metrics,analysis}.py` are zero-byte files in this checkout; there is no current downstream implementation to assess. | Preserved as-is. Working tree was already dirty before this audit. |
| `hussein-eda` (`a7855d2`) | `src/sncf_tgv/eda/quality.py` implements quality checks; `src/sncf_tgv/eda/report.py` aggregates them. `notebooks/01_eda_qualite.ipynb` audits data; `notebooks/02_eda_analyse.ipynb` calculates punctuality rates by route and month. | EDA branch uses a different `sncf_tgv` package and a CSV path (`data/brut/...csv`). Its commit is not in the current checkout’s history. |
| `marius-eda` (`fc28172`) | Shares the EDA package and notebooks above; adds `notebooks/04_ml_baseline.ipynb`, which describes planned prediction work but contains only one prose cell. `notebooks/05_ml_graph_comparison.ipynb` is empty (zero bytes). | The baseline and graph-comparison notebooks do not yet provide implemented consumers to trace. |
| `Test_Shihao` (`cfed3df`) | Streamlit app pages and a separate CSV at `data/initial/regularite-mensuelle-tgv-aqst.csv`. Python app code inspected is introductory/dashboard copy; no use of the suspicious fields or cleaning operation was found in those files. | No evidence that this snapshot’s app imports the current `projet_kit_data` modules. |
| remote `main` (`6dcf4be`) | Tip message is `reinitialiser le projet`; it has no EDA modules, analysis notebooks, or raw data matching the current project layout. | Its tree differs substantially from current local branch; remote head and local `main` are not the same commit. |

**Verified branch-source references:**

- `hussein-eda` / `marius-eda`: `src/sncf_tgv/eda/quality.py`, lines 190–260 (count checks), 285–345 (delay checks); `src/sncf_tgv/eda/report.py`, function `generate_quality_report`.
- `notebooks/01_eda_qualite.ipynb`: code cells 2 (downloads a CSV from the API), 15 (count checks), 25–30 (zero durations and excessive cancellations), 33 (threshold checks), 41 (exports a diagnostic CSV).
- `notebooks/02_eda_analyse.ipynb`: code cell 3 reads `data/brut/regularite-mensuelle-tgv-aqst.csv`; cell 10 defines `circules = nb_train_prevu - nb_annulation` and filters to `circules > 0`; cells 12, 15, 21, 26 use `nb_train_retard_sup_15`, `nb_train_retard_arrivee`, and train totals for route, month, and year metrics.
- `notebooks/04_ml_baseline.ipynb` on `marius-eda` is a prose-only plan to model delay rates. The graph comparison notebook is empty, so model feature usage and graph inputs are not verifiable yet.
- The EDA source module and notebook files do not exist on the inspected `Test_Shihao`/remote `main` trees. The Streamlit files inspected did not access the suspicious variables.

## 3. Rechecked anomaly counts

| Check | Affected records | Share of all 12,907 records | Distribution / interpretation |
| --- | ---: | ---: | --- |
| `nb_train_retard_sup_30 < 0` | 43 | 0.33% | Jan 2025: 18/121 (14.88%); Feb: 15/121 (12.40%); Mar: 10/121 (8.26%). Across the period, 29 service-route identities. Not confined to January. |
| `nb_train_retard_sup_30 < nb_train_retard_sup_60` | 354 | 2.74% | Jan: 118/121 (97.52%); Feb: 117/121 (96.69%); Mar: 119/121 (98.35%). All in Q1 2025; 354 of the 363 rows in these months. |
| `nb_train_retard_sup_15 < nb_train_retard_sup_30` | 3 | 0.02% | May 2020: 2; Mar 2025: 1. The schema’s >15 measure has a route-applicability caveat and the data has no applicability flag. |
| `nb_annulation > nb_train_prevu` | 63 | 0.49% | Apr 2020: 50/123; May: 9/123; Jun: 4/123. All 63 have planned trains = 0 and positive cancellations; delay counts and reported delay means are zero. Not April only. |
| Any investigated average delay `< -15` | 12 unique rows | 0.09% | 11 all-train arrival rows, 5 all-train departure rows, and 2 conditional arrival rows, with overlap. 10 of 11 arrival extremes and all 5 departure extremes lie in Oct–Dec 2019; both conditional-arrival extremes are in Nov 2019. |

For context, the existing audit report finds 8 negative `retard_moyen_trains_retard_sup15` values in 2018–2019. They are also not count fields and should not be mechanically set to zero. These counts match the existing audit/investigation report; direct calculation from the raw JSON confirmed the key totals and month counts above.

## 4. Where the fields affect existing analysis

The strongest directly observable downstream dependency is the EDA notebook on the `hussein-eda` and `marius-eda` snapshots:

1. It derives the denominator `circules = nb_train_prevu - nb_annulation`, then keeps only rows where `circules > 0` (cell 10). Thus all 63 cancellation-over-plan rows, each with a negative derived denominator, are excluded from its punctuality-rate data. This prevents division by a non-positive denominator in those calculations, but the blanket row filter also excludes any zero-running-service row whether or not it met the audit predicate.
2. It uses `nb_train_retard_sup_15` as its main fixed-threshold numerator and `nb_train_retard_arrivee` as the official-threshold comparison (cells 12, 15, 21, and 26). Altering or dropping rows in Q1 2025 therefore changes month and route-level delay rates and annual route rankings; the underlying report identifies a broader threshold anomaly in 354/363 rows in that quarter.
3. It also sums `nb_annulation` for monthly/year summaries (cell 15). A row filter applied earlier can change those totals even when excluded rows do not enter the denominator. Dropping all flagged cancellation rows would omit their positive cancellations from this calculation.
4. `quality.py` independently treats negative values in required count fields, cancellations beyond planned counts, and >60 counts exceeding >30 counts as diagnostic flags (lines 190–260). Its duration checks flag negative means for *delayed* trains (lines 285–345), but do not establish that negative average delays for all trains are invalid.
5. No implemented consumer was found in the graph package on the current branch: its three graph modules are empty. `marius-eda`’s prospective graph-comparison notebook is also empty. Any graph impact is therefore prospective: removing a route-month can change edge availability, weights, or temporal coverage if later graph construction uses these rows; no current implementation allows that effect to be quantified.

The quality notebook cell 41 creates a *separate* anomaly-tracking table with flags and an original row index; it does not mutate the source DataFrame in that cell. This is the closest precedent in the inspected branch snapshots for a non-destructive handoff to ETL.

## 5. Cleaning operation impact assessment

Impacts below are direct consequences of the current data shape and observed notebook formulas. “Impact” does not mean a change is recommended.

| Candidate operation | Data/analysis impact | Evidence and assessment |
| --- | --- | --- |
| Drop rows with negative `nb_train_retard_sup_30` | Removes 43/12,907 rows, concentrated in Q1 2025. Those rows are also among the >30/<60 ordering anomaly set. Month and route rates, graph coverage, and any supervised target assembled from the same table can change. | Strong evidence supports a **row-level quality flag**, but not dropping the whole record: its other indicators and route fields remain populated. No verified corrected count is available. |
| Replace negative `nb_train_retard_sup_30` with zero | Changes 43 observed source values and downstream count totals. It does not resolve the main ordering anomaly: the 354-row >30/<60 violation count is based on the ordering predicate and values still below `sup_60` in records where the original >30 was negative. | A zero is plausible as a non-negative count constraint, but there is no evidence that zero is the true count. Avoid irreversible replacement; if needed, add a derived, explicitly labeled analysis value and retain the raw field. |
| Drop all rows where `sup_30 < sup_60` | Removes 354 records (2.74% of the dataset), including 97.52% of Jan 2025 rows and 96.69% of Feb / 98.35% of Mar. This is effectively removal of almost the whole quarter for temporal/route analyses, and would discard valid-looking planned counts, cancellations, and other delay indicators. | A period-scoped warning is strongly supported. Row deletion is not: anomaly concerns one field family, and the rows still contain useful data. The broad continuity across routes and months suggests a source-period issue but cannot identify corrected values. |
| Force `sup_30` to be at least `sup_60` (or use `sup_60` as `sup_30`) | Alters a large share of Q1 values. Counts then become internally ordered but would be imputed from another metric; totals and delay rates by threshold cease to represent the observed source. | Not supported. The file does not state that the smaller threshold count can be reconstructed from the larger threshold count. Escalate source documentation/version question. |
| Enforce `sup_15 >= sup_30` or alter the three flagged rows | Small observed set (3 rows), but the >15 measure applies only to a subset of routes per schema and the dataset has no scope indicator. | Insufficient basis for an unconditional cleaning rule. Keep a conditional diagnostic until route eligibility is known. |
| Drop rows with cancellations exceeding planned trains | Removes 63/12,907 rows. In the existing EDA rate notebook these rows already fail `circules > 0`, but deleting them earlier also erases positive cancellations from cancellation totals and removes their route-month observations. | Keeping them while excluding non-positive denominators from punctuality rates is already consistent with the notebook’s arithmetic. The producer’s cancellation/planned schedule convention remains unresolved; do not delete from reusable raw/cleaned tables. |
| Replace `nb_train_prevu` with cancellations, or zero cancellations | Would create an assumed timetable/count interpretation and materially change the derived `circules` and cancellation rates for 63 rows. | No support in the JSON alone. Keep raw counts; use explicit eligibility masks for each metric and show excluded denominators. |
| Drop/clip negative average-delay rows or set negative delays to zero | The extreme cutoff applies to 12 unique records (0.09%), concentrated on a small group of routes and mainly Oct–Dec 2019. Clipping changes mean/median/rank metrics; row removal also removes counts and route-month observations. Negative delay can represent early running, so sign alone is not proof of invalidity. | The mismatch between some all-train averages (e.g. Nîmes → Paris Lyon, Oct 2019: arrival mean -90.63, departure mean -92.77) and positive delayed-train averages/late counts merits a source-definition review. Evidence supports review flags, not a universal lower bound or correction. |
| Remove only an extreme average value (set to null) but retain row | Preserves route/month counts and other features; metrics using that mean change only by excluding the field value. | A reasonable *reversible analysis option* for sensitivity analysis after defining the metric’s semantics; it still requires recording a mask and comparing results to the raw baseline. Not yet a cleaning decision. |
| Add anomaly indicator columns / publish a separate analysis view | Retains all source values and allows each metric/model to opt into explicit row or value masks. | Best-supported next design direction. It aligns with the quality notebook’s anomaly tracking table and avoids making every downstream use inherit one global deletion/imputation decision. |

### Approximate exposure in known analysis

- Dropping all `sup_30 < sup_60` rows would leave only 3/121 Jan, 4/121 Feb, and 2/121 Mar 2025 records from the three affected months (9 total). Any Q1 2025 month or route comparison would be dominated by selective exclusion.
- The existing EDA rate calculation already excludes rows with `circules <= 0`; cancellation flags are consequently excluded from those punctuality denominators. This is a specific behavior of that notebook, not a guarantee for future ETL, cancellation summaries, or graph edges.
- Removing the 12 unique extreme-delay rows would affect 9 distinct service-route identities, with repeated Nîmes, Valence Alixan TGV, and Montpellier to Paris Lyon records. Route-level analysis could be disproportionately affected even though the global row share is small.
- These rows may overlap anomaly categories. Category counts must not be added to estimate unique rows; the verified extreme-delay union is 12, not 18.

## 6. Recommendations and decision needs

### Suitable to move into a cleaning-design proposal

- Keep the source JSON immutable and make a separate, versioned analysis dataset or view.
- Add row-level flags for negative count values and threshold-ordering failures. Preserve the observed values alongside flags and the raw row identity.
- Define denominator validity per metric. For punctuality rates, require a documented positive `circules`; report excluded row counts and preserve cancellation totals separately.
- Run sensitivity outputs: (a) raw observed values, (b) flagged rows excluded only for the metric under review, and (c) any proposed replacement only as a separate scenario. Compare monthly trends, route rankings, and graph coverage before adopting a rule.
- Ask the data owner for the Q1 2025 meaning/version of `nb_train_retard_sup_30` and `nb_train_retard_sup_60`; ask how cancellations are counted when the reported planned count is zero; confirm the definitions and units of all-train average delay columns for Oct–Dec 2019.

### Not supported yet

- Replacing negative counts with zero; deriving `sup_30` from `sup_60`; enforcing `sup_15 >= sup_30`; deleting cancellation-over-plan rows; clipping or replacing negative delay means; and deleting all flagged route-month rows.
- The >30/<60 issue has enough evidence to justify a date-scoped validation rule or warning, but not an imputation rule.
- Negative count values are impossible as literal counts, so they can be marked invalid for count-based calculations. The desired treatment of affected rows and any corrected count require producer evidence.
- The April 2020 cancellation pattern is internally consistent (zero plan/delays with positive cancellations), but whether it is an error cannot be decided without the producer’s schedule/cancellation definitions.
- Extreme negative average delays warrant a targeted source check. Magnitude plus disagreement with other indicators is evidence of inconsistency, not identification of which field to correct.

## 7. Limitations

- Remote branch snapshots were inspected by immutable commit IDs. Because the local `main` and `origin/main` tracking refs were stale, this report identifies the fetched remote heads explicitly; it does not claim they match any local branch ref. `git ls-remote` succeeded before fetching commit objects; no branch checkout was performed.
- Branch EDA CSV files are separate snapshots and may not be byte-for-byte identical to the current local JSON snapshot. Numerical impact counts in this report were recomputed from the current local JSON; branch code paths and formulas were read from branch commits.
- Notebook references use zero-based cell indices because notebooks do not have stable source line numbers. Notebook outputs may be stale; reported numerical counts are independently recomputed from the current local raw JSON where stated.
- The current branch’s graph and cleaning/preprocessing modules are empty, so impact on graph topology, graph weights, or model outputs cannot be measured yet. The graph section is a prospective impact assessment only.
- The data cannot establish the cause of any anomaly, upstream changes to the source system, or intended replacement values.

## 8. State after inspection

No source code, raw dataset, notebook, configuration, existing report, Git branch, branch pointer, or worktree state was changed. Remote commit objects were added to the local Git object database for inspection only. This new Markdown report is the sole file added by the task.

## 9. Shared data contract and compatibility assessment

This section describes actual readers found in the current checkout and inspected branch snapshots. A proposed contract specifies field meaning and representation; it does not require every team to use the same DataFrame library or force the current Polars audit format on downstream consumers.

### 9.1 Current module consumption

| Module / snapshot | Input format and location | Library and expected names/types | Required vs optional | Date and missing values | Module-specific transformations |
| --- | --- | --- | --- | --- | --- |
| Current ingestion, `src/projet_kit_data/ingestion/sncf_api.py` | SNCF Explore v2.1 JSON export; saves/loads `data/raw/regularite-mensuelle-tgv-aqst.json` by default. | Requests fetches a JSON array into `list[dict[str, Any]]`; no DataFrame dependency or field renaming. JSON scalar types are preserved. | Fetch/load validate only top-level array and that each element is an object; they do not require a fixed list of columns. All original response fields are preserved. | `date` stays the source string (`YYYY-MM` in the checked snapshot). JSON `null` stays `None`. | No cleaning, type coercion, or feature engineering. Save is JSON with UTF-8 and `ensure_ascii=False`. |
| Current audit, `src/projet_kit_data/etl/audit.py` | Raw JSON path above; report at `data/reports/data_quality_report.txt`. | Polars DataFrame after reading records; checks all 26 expected short/canonical names. Audit is diagnostic; results are also a structured dictionary. | The report compares present fields with the 26-field expected schema. Individual checks run when relevant columns are present; missing/unexpected fields are reported. | The checked raw snapshot uses string month keys. JSON nulls remain missing; in this snapshot both comment fields are 100% null and arrival comments 94.59% null. | Schema/type summaries, missingness, duplicates, negative values, numeric stats, logical flags, and anomaly examples; does not alter source records. |
| Current ETL/graph package | `src/projet_kit_data/etl/cleaning.py`, `etl/preprocessing.py`, `graph/construction.py`, `graph/metrics.py`, `graph/analysis.py` are zero-byte in the current checkout. | No active reader, library, or schema contract can be established from these files. | Undetermined. | Undetermined. | No implemented transformations found. Do not infer compatibility from empty module placeholders. |
| `hussein-eda` / `marius-eda` quality module | `src/sncf_tgv/eda/quality.py` consumes a caller-supplied `pandas.DataFrame`; it does not itself load a file. Its notebook caller downloads CSV or reads `data/brut/regularite-mensuelle-tgv-aqst.csv`. | Pandas; short/canonical field names such as `date`, `nb_train_prevu`, `nb_annulation`, all count and delay fields, all six `prct_cause_*`, and comment fields. It calls `pd.to_numeric(..., errors="coerce")` for numeric check groups. | `check_identifiers`: 4 key columns; `check_train_counts`: 7 count columns; `check_durations`: duration plus 5 average-delay columns; `check_percentages`: all 6 cause percentages; `check_comments`: all 3 comment fields. The report aggregator calls all these checks, so the complete 26-field schema is required for `generate_quality_report`. | Expects source `date` as a string parseable by its identifier check; the notebook’s rename map preserves `YYYY-MM`. Uses pandas `isna()` / nullable values and numeric coercion; nonnumeric text is treated as invalid for numeric validation. | Counts duplicate keys; checks dates/identifiers, count consistency, negative delayed-train means, percentage bounds/sums, and comment completeness. It returns quality summaries, not cleaned rows. |
| `hussein-eda` / `marius-eda` analysis notebook `notebooks/02_eda_analyse.ipynb` | Semicolon-separated CSV, UTF-8-SIG, at `data/brut/regularite-mensuelle-tgv-aqst.csv`. | Pandas DataFrame. The file has human-readable French headers, then cell 4 maps these to short names (including all 26 field names). Numerical columns are used arithmetically and expected to be numeric after CSV parsing; the notebook does not declare a formal dtype schema. | In practice the 26-column name map expects the complete export; calculations use identifiers/routes, date, duration, planned/cancelled counts, `nb_train_retard_sup_15`, `nb_train_retard_arrivee`, and `nb_train_prevu`. Comments and cause percentages are not central to the core rate analysis. | Date is kept as `YYYY-MM` text and sliced/grouped as such; converted to a pandas datetime index only for plotting. Default `read_csv` NA parsing yields missing values; calculations assume required numeric values are present/usable. | Creates `liaison`, `circules = planned - cancelled`, filters `circules > 0`, and computes rates, route/month/year aggregates, duration bins, rankings and directional comparisons. This is analytical feature construction, not a shared cleaning rule. |
| `Test_Shihao` app snapshot | A distinct CSV exists at `data/initial/regularite-mensuelle-tgv-aqst.csv`. | Inspected Python app pages did not contain a dataset loader or references to the suspicious SNCF fields. Actual consumption path/types could not be verified. | Undetermined from available code. | Undetermined. | No module-specific data transformation could be verified in the inspected app source. |
| Remote `main` snapshot | No matching EDA inputs or analysis modules in the inspected tree. | No dataset consumer found. | N/A. | N/A. | N/A. |
| `marius-eda` ML / graph notebooks | Baseline notebook is a one-cell prose plan; graph comparison notebook is empty. | No executable DataFrame loader or implemented feature list to inspect. | Undetermined. | Undetermined. | No transformation implemented in these two notebooks. |

The current raw snapshot has these actual Polars inferred types: identity/comment text and `date` are strings; count fields and `duree_moyenne` are integers; delay means and cause percentages are floating point; JSON null-only columns infer as Polars `Null`. The JSON source itself does not declare a schema. The proposed contract below uses nullable logical types so an all-null comment field is still a nullable string field rather than a permanent `Null`-typed column.

### 9.2 Proposed shared semantic contract

**Grain and identity.** One row represents one monthly service-route observation as published by SNCF. The recommended business key is `(date, service, gare_depart, gare_arrivee)`. Route direction matters: origin and destination are ordered, not interchangeable. `service` must remain in the key because National and International observations may share a route and month.

**Date.** `date` is a calendar month in ISO `YYYY-MM` form, not a day-level timestamp. Validate the pattern and calendar month; do not silently convert it to a day or timezone. Consumers may create a first-of-month timestamp as a derived plotting/index column while retaining the contract date.

**Canonical field names and logical types.** Keep the existing API short names as the canonical names. These are already used by the current audit and the EDA quality module after its mapping step. All fields below are nullable at the contract level; snapshot-specific completeness is not a guarantee for later exports.

| Canonical field(s) | Logical type | Meaning and unit |
| --- | --- | --- |
| `date` | string, ISO month `YYYY-MM` | Reporting month. |
| `service` | string | SNCF service category, e.g. National or International; categorical, not an identifier to normalize away. |
| `gare_depart`, `gare_arrivee` | string | Origin and destination station labels, preserving direction and source spelling. |
| `duree_moyenne` | nullable integer | Mean planned journey duration, minutes. |
| `nb_train_prevu`, `nb_annulation`, `nb_train_depart_retard`, `nb_train_retard_arrivee`, `nb_train_retard_sup_15`, `nb_train_retard_sup_30`, `nb_train_retard_sup_60` | nullable integer counts | Monthly numbers of planned trains, cancellations, trains late at departure/arrival, or late beyond the stated minute threshold. Negative values violate count semantics and should be flagged; do not infer a corrected value. The >15 field has limited route applicability according to the dataset description. |
| `retard_moyen_depart`, `retard_moyen_tous_trains_depart`, `retard_moyen_arrivee`, `retard_moyen_tous_trains_arrivee`, `retard_moyen_trains_retard_sup15` | nullable decimal number, minutes | Average delay measure. Preserve the distinction between delayed-train averages, all-train averages, and the >15 conditional measure. A negative number can indicate early running depending on the official definition; sign alone is not a cleaning rule. |
| `prct_cause_externe`, `prct_cause_infra`, `prct_cause_gestion_trafic`, `prct_cause_materiel_roulant`, `prct_cause_gestion_gare`, `prct_cause_prise_en_charge_voyageurs` | nullable decimal number, percent points on 0–100 scale | Share of delay attributed to each cause. These are percentages, not fractions between 0 and 1. Keep unknown/null distinct from zero. |
| `commentaire_annulation`, `commentaire_retards_depart`, `commentaires_retard_arrivee` | nullable string | Source free-text commentary. Preserve original spelling/text; empty string and null should not be conflated without an explicit presentation rule. |

**Missing values and types.** Represent absent source values as null/NA in tabular outputs; never fill nulls with zero just to make a numeric calculation work. Zero is an observed numeric value and has meaning distinct from unknown. JSON null maps naturally to Python `None`, pandas nullable/NA values or Polars null. Numeric text from CSV inputs should be explicitly parsed against the field groups above, with parse failures flagged and counted rather than silently accepted as strings. DataFrame implementations may use their native nullable dtypes; the semantic contract is library-neutral.

**Storage compatibility.** Keep the existing raw JSON array as the immutable, lossless source artifact. The contract should apply to a derived analysis table independent of the serialization or DataFrame library. If a shared file is needed immediately, publish a canonical-name CSV with UTF-8, documented null encoding, `date` as `YYYY-MM`, integer count columns, decimal numeric measures and all 26 columns. Keep a compatibility export for the older EDA branch with its semicolon delimiter and French headings (or add a small Pandas adapter that renames canonical columns) until that notebook is migrated. Do not make Polars a mandatory consumer library. A Parquet artifact could be considered later if the team agrees on an engine/dependency and schemas; it is not needed to establish this first contract.

### 9.3 Compatibility and minimum changes

| Consumer | Can use a proposed canonical-name JSON/CSV artifact unchanged? | Minimum compatibility action |
| --- | --- | --- |
| Current ingestion `load_raw_data()` | Yes, if the artifact remains the existing JSON array of objects with the same field names. | None for raw JSON. It intentionally returns Python records, not a DataFrame. |
| Current audit | Yes for the JSON input with canonical names; the audit already loads that contract and uses Polars internally. | For CSV output, change only the input adapter/path or keep audit pointed at raw JSON. Do not change its predicates just to match a consumer. |
| `sncf_tgv.eda.quality` | Yes after data is loaded as a Pandas DataFrame with canonical names and all fields its report aggregator requires. | For canonical JSON, `pd.read_json` plus explicit numeric type coercion may suffice; for canonical CSV, `pd.read_csv` with schema-aware dtype handling. If using the legacy French-header CSV, retain the existing rename mapping. Missing required columns must be handled explicitly; the current report aggregator raises if any required group is absent. No Pandas-to-Polars migration is necessary. |
| `notebooks/02_eda_analyse.ipynb` | Not directly from raw JSON or a comma-separated canonical CSV. | Minimum: keep a Pandas loader and either (a) export semicolon CSV with its French headers, or (b) update only the loader/header adapter to read the canonical artifact and map to short names. Retain date string format and document the numeric/null behavior. Then review its `circules > 0` eligibility mask as module-specific rate logic. |
| Current cleaning/preprocessing and graph modules | Cannot assess runtime compatibility: there is no implementation in the current branch. | When implemented, accept the shared canonical logical schema at a boundary, then keep module-specific derived features local. No need to commit to Pandas or Polars until concrete interfaces exist. |
| `Test_Shihao` app | Cannot establish from inspected source whether the data artifact can be consumed unchanged. | First identify the actual loader/input schema. If the app uses French headers, add a boundary rename/export adapter; do not change its internal library based only on branch association. |
| Baseline / graph comparison notebooks on `marius-eda` | Not yet applicable; neither has implemented data consumption/features. | Agree the target and feature list after the loader exists; consume canonical fields through a notebook-local Pandas adapter if the EDA notebooks remain Pandas. |
| remote `main` | No dataset consumer found in inspected tree. | None until a consumer is introduced. |

### 9.4 Separate shared preprocessing from module-specific features

**Shared contract-level preparation** should be limited to stable, reusable tasks: preserve source values and row lineage; confirm required field names; parse typed columns without destructive coercion; normalize missing values to null while distinguishing zero; validate `YYYY-MM`; retain the service-route-month grain; and publish quality flags/metadata separately from source fields. These steps make inputs interoperable but do not decide whether a suspicious row is usable for every analysis.

**Module-specific feature engineering** belongs with the consumer and its stated objective:

- EDA rate analysis may derive `circules = nb_train_prevu - nb_annulation`, require a positive denominator for a particular rate, and choose a numerator threshold. Record the resulting eligibility/exclusion counts alongside its result.
- Graph construction may decide whether an edge exists for a month, whether direction is represented, which delay/rate metric becomes an edge weight, and how missing or flagged values affect graph topology. No such policy is implemented yet.
- Predictive modeling may choose a target, feature window, temporal split, and leakage controls. The current baseline notebook is only prose; do not pre-engineer model features into a global cleaned table.
- Quality audit should continue reporting diagnostic flags and counts, rather than returning an implicitly cleaned dataset.

### 9.5 Low-risk migration path

1. Keep the downloaded JSON immutable and treat its 26 canonical field names and source values as the raw contract.
2. Publish a small schema/mapping note and a typed loader/adapter at each consumer boundary. Keep each team's existing DataFrame library.
3. For the EDA branch, first provide a compatibility CSV matching its current `sep=";"`, French header and UTF-8-SIG input, or update just its loader to use the canonical schema. Compare row counts, parsed nulls, dates, and core aggregate outputs against the current CSV before switching.
4. Let each module own its eligibility masks and derived features. During transition, produce old and new outputs side by side and compare rates, route rankings, cancellations, and graph coverage; do not replace the legacy artifact until the comparison is reviewed.
5. Only after consumers have migrated should the team consider deprecating the French-header CSV. Keep raw and compatibility outputs versioned or reproducibly generated, and document schema version and source snapshot date.

**Evidence boundary:** The canonical field/type table expresses the verified export and the existing 26-field audit schema. Field semantics and minutes/percentage units reflect the dataset descriptions and current team analysis conventions; before enforcing a range or correction, confirm definitions against the current authoritative SNCF data dictionary. The cross-branch inspection verifies readers and transformations present in those commit snapshots, not uncommitted future work or modules absent from the inspected trees.

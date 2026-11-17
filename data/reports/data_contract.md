# SNCF TGV Monthly Regularity: Shared Data Contract

**Status:** Proposed shared interface, version 1.0 for team review  
**Scope:** Raw and reusable tabular representation of the SNCF monthly TGV regularity export. This document defines shared field semantics and interchange expectations. It does not implement cleaning or require any particular DataFrame library.

## 1. Purpose and scope

EDA, graph analysis, machine learning, audit, and future ETL work need to agree on what a row and each source field mean. A shared contract reduces accidental differences in field names, date interpretation, missing-value handling, and units when data passes between modules.

The contract is **library-neutral**. Consumers may use Pandas, Polars, or another suitable tool and provide a small adapter at their boundary. The shared schema concerns field names, logical types, meaning, and preservation rules; it does not prescribe one in-memory DataFrame type or force the current Polars audit implementation on other modules.

This proposal follows `data/reports/cross_branch_cleaning_impact_report.md`, especially sections 9.1–9.5. Where the current SNCF data dictionary is needed to confirm exact field definitions or units, the item is explicitly marked as requiring confirmation. Field descriptions below are working interpretations based on the export names and existing project analysis, not new claims of official definitions.

## 2. Data grain and business key

One record represents **one monthly service-route observation** in the SNCF dataset.

The business key is:

```text
(date, service, gare_depart, gare_arrivee)
```

The route is directed: `gare_depart` and `gare_arrivee` must not be swapped or collapsed into an undirected pair. The `service` category must also be preserved. The same month and station pair can appear for different service categories, and those are distinct observations. Keep the source values and spellings for these key fields; any normalized route labels should be derived fields.

## 3. Canonical schema

The canonical field names are the 26 short names in the SNCF JSON export and current audit schema. Every field is **nullable** in the shared contract, even if it has no nulls in a particular snapshot. Counts and planned duration use logical integers; averages and percentages use decimal numeric values. Physical Pandas/Polars dtypes may differ as long as they preserve these logical types and nulls.

Descriptions and units marked “confirm” should be verified against the authoritative SNCF data dictionary before they are used to enforce corrections or validity ranges.

| Canonical name | Logical type | Working meaning | Unit | Nullability and semantic caveats |
| --- | --- | --- | --- | --- |
| `date` | String, `YYYY-MM` | Reporting month for the observation. | Calendar month | Nullable by contract; a null or malformed value is an invalid key. Do not replace it with a day-level source date. |
| `service` | String | Service category attached to the observation. | None | Nullable by contract; preserve category labels and include it in the business key. Official category definitions require the SNCF dictionary. |
| `gare_depart` | String | Origin station label. | None | Nullable by contract; preserve source spelling. It is directional and part of the key. |
| `gare_arrivee` | String | Destination station label. | None | Nullable by contract; preserve source spelling. It is directional and part of the key. |
| `duree_moyenne` | Nullable integer | Mean planned journey duration, according to the field name. | Minutes (confirm exact definition) | May be zero in exceptional records; do not treat zero as null. Exact calculation and scope require SNCF confirmation. |
| `nb_train_prevu` | Nullable integer count | Number of trains/circulations planned for the month, according to the field name. | Trains | Negative values conflict with count semantics and should be flagged. A zero value is distinct from missing. Confirm which timetable version is counted. |
| `nb_annulation` | Nullable integer count | Number of cancelled trains/circulations, according to the field name. | Trains | Negative values conflict with count semantics and should be flagged. It may exceed `nb_train_prevu` in the observed source; do not globally delete or rewrite such rows without confirming SNCF counting conventions. |
| `commentaire_annulation` | Nullable string | Source commentary associated with cancellations. | None | Preserve text exactly. Null and empty string are distinct unless a display-only rule says otherwise. |
| `nb_train_depart_retard` | Nullable integer count | Number of trains reported late at departure. | Trains | Negative values conflict with count semantics and should be flagged. Exact delay threshold and scope require SNCF confirmation. |
| `retard_moyen_depart` | Nullable decimal number | Mean delay for the subset described as late at departure, according to the field name. | Minutes (confirm exact definition) | Negative values may represent early running under some definitions; do not reject or clip on sign alone. Confirm the population and weighting. |
| `retard_moyen_tous_trains_depart` | Nullable decimal number | Mean departure delay over the population indicated as all trains. | Minutes (confirm exact definition) | “All trains” population and treatment of cancellations/early running require SNCF confirmation. Preserve negative values pending that confirmation. |
| `commentaire_retards_depart` | Nullable string | Source commentary associated with departure delays. | None | Preserve source text; null is not the same as an empty string. |
| `nb_train_retard_arrivee` | Nullable integer count | Number of trains reported late at arrival. | Trains | Negative values conflict with count semantics and should be flagged. The exact “official” arrival threshold may depend on journey duration; confirm in the data dictionary. |
| `retard_moyen_arrivee` | Nullable decimal number | Mean arrival delay for the subset described as late at arrival. | Minutes (confirm exact definition) | Do not automatically clip negative values; verify the definition and eligible population first. |
| `retard_moyen_tous_trains_arrivee` | Nullable decimal number | Mean arrival delay over the population indicated as all trains. | Minutes (confirm exact definition) | “All trains” population and weighting require SNCF confirmation. Extreme negative values are diagnostic flags, not proof of the correct replacement. |
| `commentaires_retard_arrivee` | Nullable string | Source commentary associated with arrival delays. | None | Preserve source text; missingness is high in the checked snapshot. Null is not an observed zero or an empty explanation. |
| `nb_train_retard_sup_15` | Nullable integer count | Number of trains beyond the 15-minute threshold, according to the field name. | Trains | The dataset description limits applicability to routes competing with air travel. There is no applicability flag in this dataset; do not universally enforce `sup_15 >= sup_30`. Confirm exact scope with SNCF. |
| `retard_moyen_trains_retard_sup15` | Nullable decimal number | Average delay for the >15-minute group, according to the field name. | Minutes (confirm exact definition) | The >15 applicability limitation also applies here. A negative value may reflect the published definition or inconsistent source values; do not automatically change it. |
| `nb_train_retard_sup_30` | Nullable integer count | Number of trains beyond the 30-minute threshold, according to the field name. | Trains | Negative values conflict with count semantics and must be flagged, but not changed to zero without evidence. The Q1 2025 relationship with `sup_60` requires source-version/definition review. |
| `nb_train_retard_sup_60` | Nullable integer count | Number of trains beyond the 60-minute threshold, according to the field name. | Trains | Negative values conflict with count semantics and should be flagged. Do not overwrite `sup_30` or infer it from this field. Confirm threshold and population definitions. |
| `prct_cause_externe` | Nullable decimal number | Percentage attributed to external causes, according to the field name. | Percent points, expected scale 0–100 (confirm definition) | Null means unknown/unreported, not zero. Check bounds and total diagnostically; do not fill missing causes with zero. |
| `prct_cause_infra` | Nullable decimal number | Percentage attributed to infrastructure causes. | Percent points, expected scale 0–100 (confirm definition) | Null means unknown/unreported, not zero. Exact category boundary and denominator require SNCF confirmation. |
| `prct_cause_gestion_trafic` | Nullable decimal number | Percentage attributed to traffic-management causes. | Percent points, expected scale 0–100 (confirm definition) | Null means unknown/unreported, not zero. Exact category boundary and denominator require SNCF confirmation. |
| `prct_cause_materiel_roulant` | Nullable decimal number | Percentage attributed to rolling-stock causes. | Percent points, expected scale 0–100 (confirm definition) | Null means unknown/unreported, not zero. Exact category boundary and denominator require SNCF confirmation. |
| `prct_cause_gestion_gare` | Nullable decimal number | Percentage attributed to station-management causes, according to the field name. | Percent points, expected scale 0–100 (confirm definition) | Null means unknown/unreported, not zero. The precise included causes and denominator require SNCF confirmation. |
| `prct_cause_prise_en_charge_voyageurs` | Nullable decimal number | Percentage attributed to passenger handling/care, according to the field name. | Percent points, expected scale 0–100 (confirm definition) | Null means unknown/unreported, not zero. The precise included causes and denominator require SNCF confirmation. |

### Field groups and expected logical types

- **Identifiers and category:** `date`, `service`, `gare_depart`, `gare_arrivee` are strings.
- **Planned duration and counts:** `duree_moyenne`, `nb_train_prevu`, `nb_annulation`, `nb_train_depart_retard`, `nb_train_retard_arrivee`, `nb_train_retard_sup_15`, `nb_train_retard_sup_30`, and `nb_train_retard_sup_60` are nullable integers. Counts should be whole numbers; invalid numeric strings or fractional values should be flagged.
- **Delay averages:** `retard_moyen_depart`, `retard_moyen_tous_trains_depart`, `retard_moyen_arrivee`, `retard_moyen_tous_trains_arrivee`, and `retard_moyen_trains_retard_sup15` are nullable decimal numbers, interpreted in minutes pending exact SNCF definitions.
- **Cause percentages:** the six `prct_cause_*` fields are nullable decimal numbers represented in percent points, not proportions from 0 to 1. Confirm their precise denominator and category definitions in the official dictionary.
- **Comments:** the three comment fields are nullable strings.

## 4. Date conventions

`date` must remain a month string in `YYYY-MM` format, for example `2025-01`.

Validate both the shape and calendar month: the month component must be from `01` through `12`. Do not silently convert the contract field into a day-level date or timezone-aware timestamp. A consumer may derive a separate first-of-month datetime column for plotting or time-series operations, while retaining the original `date` value and grain.

## 5. Missing values and type handling

1. **Null is not zero.** Preserve absent values as null/NA. A measured count or percentage of zero is an observed value and must remain distinguishable from unknown or unreported data.
2. **No silent filling.** Do not fill nulls with zero to make arithmetic possible. A calculation that needs complete inputs should define its own eligibility mask and report how many rows were excluded.
3. **Logical types are library-independent.** Use nullable string, integer, decimal-number, and comment-string types as specified above. Pandas may use nullable extension dtypes; Polars may use its native types. The wire representation or physical DataFrame dtype does not change the logical contract.
4. **Parse errors are visible.** When reading CSV or other typed text, parse numeric fields according to their groups. A non-empty value that cannot be parsed, or a fractional value in a count field, must be recorded as a parse/validation failure with field and row context. Do not silently leave it as text or coerce it to zero. Preserve the original representation in the immutable source so the issue can be traced.
5. **Null-only columns still have a logical type.** In the checked 12,907-record snapshot, `commentaire_annulation` and `commentaire_retards_depart` are entirely null (100% each), while `commentaires_retard_arrivee` is null in 12,209 records (94.59%) and populated in 698. The first two remain nullable strings under this contract even if Polars infers a physical `Null` type from this snapshot. Do not drop these columns or treat the snapshot’s missingness as proof that they are permanently unused.

## 6. Data quality and anomaly policy

The raw export is evidence. Audit findings are flags for review and for metric-specific eligibility decisions; they are not, by themselves, instructions to rewrite source values.

### Validation rules versus correction rules

**Validation rules** may report that a field is missing, has an unexpected type, violates a shape or logical constraint, or participates in a suspicious relationship. A validation result should identify the predicate, affected fields/rows, and counts without changing the record.

**Correction rules** change a value, remove a row, or replace a source representation. Apply one only when supported by an authoritative definition or a documented, reviewed decision. Keep the original value, correction rationale, rule/version, and a way to trace the output row to its raw source.

The following investigation policy applies:

- Preserve the original JSON as an immutable source artifact and preserve observed values in all derived data.
- Add diagnostic flags or separate quality metadata instead of automatically deleting suspicious rows.
- Do not replace negative count values with zero without source evidence. Negative counts conflict with count semantics and should be flagged for count-based calculations, but the correct replacement is unknown.
- Do not force `nb_train_retard_sup_30 >= nb_train_retard_sup_60`. The 2025 Q1 pattern is a strong diagnostic signal, but it does not establish corrected `sup_30` values.
- Do not automatically enforce `nb_train_retard_sup_15 >= nb_train_retard_sup_30`. The >15 field has limited route applicability, and this export has no field identifying eligible routes.
- Do not globally delete records where `nb_annulation > nb_train_prevu`. Their exact interpretation depends on SNCF’s timetable and cancellation counting convention.
- Do not automatically clip negative average delays. Early running may be represented as negative delay, and exact definitions/populations require confirmation.
- For calculations, define explicit metric-specific eligibility conditions (for example, a positive denominator) and report excluded rows. Such exclusions should not delete the source row from the shared dataset.

## 7. Shared preprocessing and module-specific transformations

| Layer | Responsibility under this contract |
| --- | --- |
| Ingestion | Retrieve the source export and preserve its field names, values, and JSON nulls. Store the downloaded JSON without ETL changes. |
| Audit | Diagnose schema, missingness, duplicates, types, and logical anomalies. Emit findings/flags without modifying source records. |
| Cleaning | Apply only confirmed, documented correction rules. Preserve raw values and row lineage; make changes reproducible and reviewable. No such rule is authorized by this document alone. |
| Preprocessing | Provide a typed, reusable representation that follows the canonical schema, date convention, and null policy. Keep shared preparation limited to parsing, type validation, and traceability. |
| EDA | Choose analysis-specific numerator definitions, eligible populations, and denominators; record exclusions and derived measures with the analysis. |
| Graph | Choose edge inclusion, direction representation, aggregation window, edge weights, and handling of missing or flagged measures. Preserve the source route direction unless an explicitly undirected view is required. |
| ML | Define target, predictors, temporal feature windows, train/validation/test splits, and leakage controls. Keep model features local to the modeling workflow. |

Shared preprocessing must not absorb EDA rate definitions, graph edge engineering, or ML targets/features. Those choices answer module-specific questions and may use different valid populations.

## 8. Storage and compatibility

- **Raw source:** Keep `data/raw/regularite-mensuelle-tgv-aqst.json` as the immutable JSON array downloaded from the verified SNCF export. Do not rewrite it during cleaning or preprocessing.
- **Logical schema:** Use the 26 canonical short field names listed in section 3 in shared typed outputs and APIs. Avoid creating alternate source-field names; compatibility mappings belong at input/output boundaries.
- **Legacy EDA compatibility:** The inspected EDA notebook reads a semicolon-separated CSV with UTF-8-SIG encoding and French display headers, then maps those headers to canonical short names. If that legacy input is retained, provide a reproducible export with `;`, UTF-8-SIG, and the existing French headers, or keep the notebook’s Pandas adapter to map canonical names. Do not make the canonical contract depend on that legacy file format.
- **Pandas and Polars:** Allow adapters to construct the same logical schema in each library. No library migration is required. Keep the quality module’s Pandas interface if it remains useful; the current audit may continue to use Polars.
- **Parquet:** Parquet may be considered later if the team agrees on schema metadata and the required engine/dependency. It is not required for this contract or current migration.
- **Null serialization:** Document the null encoding of any derived CSV. Avoid an encoding that makes a real zero or empty comment indistinguishable from missing data.

## 9. Versioning and migration

This document proposes a simple contract version independent of the source dataset’s publication version. Keep the contract version in documentation or artifact-level metadata; do not add it as a fabricated SNCF source column.

Recommended migration sequence:

1. Keep raw JSON unchanged and identify it by source snapshot/date or checksum where reproducibility requires it.
2. Adopt the 26-field canonical names and logical types at module boundaries before changing any consumer’s internal implementation.
3. Implement typed loaders/adapters for Pandas and Polars as needed. Explicitly report parse failures and preserve nulls.
4. Preserve the legacy EDA CSV interface during transition, either with a compatibility export (`;`, UTF-8-SIG, French headers) or a small loader/header adapter.
5. Run the old and new loaders side by side. Compare row counts, key/date coverage, null counts, and the EDA’s core rates and route summaries before switching that consumer. For future graph/ML consumers, compare edge coverage/weights or target/feature populations as applicable.
6. Switch consumers individually after review; do not require a coordinated library migration. Keep module-specific eligibility and feature choices local.
7. Document future schema changes with the contract version, changed fields/types/semantics, compatibility impact, and any migration mapping. Never silently repurpose an existing field name.

## 10. Open semantic questions

The following details require confirmation from the authoritative SNCF data dictionary before they can underpin strict correction rules:

- Exact population, calculation, and weighting for each `retard_moyen_*` field, especially “tous trains” and the >15 conditional measure.
- Exact threshold and applicability definitions for `nb_train_depart_retard`, `nb_train_retard_arrivee`, and `nb_train_retard_sup_15`.
- Why `nb_train_retard_sup_30` and `nb_train_retard_sup_60` have the observed order inversion in Q1 2025, and whether the field definition or source process changed then.
- Whether `nb_annulation` refers to cancellations against an earlier timetable while `nb_train_prevu` reflects a later/current timetable, explaining records with zero planned counts and positive cancellations.
- The exact duration definition for `duree_moyenne` and the denominator/category boundaries for the six cause percentages.
- The intended representation of negative delay averages and the SNCF meaning of negative values at very large magnitudes.

Until resolved, these remain documented uncertainties. This contract does not assert causality, prescribe replacement values, or claim that the current snapshot is representative of future exports.

# Test evidence (Stage 2)

**Clean run:** `dbt build` → PASS=86, WARN=1, ERROR=0 (87 nodes).
The one warning is by design: Table 61 sits ~0.2% above Figure 4 (3 year-rows). Recorded, not hidden.

**Independent check:** four metrics recomputed straight from raw text tables match `metrics.metric_values` exactly; `first_class_rate` matches for all five years.

**Deliberate breakage** (copy of the database, four known faults):

| Fault injected | Caught by |
|---|---|
| Figure 4 first-degree full-time England count inflated by 50 (still a multiple of 5) | assert_f04_detail_sums_to_published_total, assert_f04_country_sums_to_published, plus Figure 7 reconciliations |
| Level label `First Degree` (capitalised) not in the governed mapping | assert_every_label_is_mapped |
| Duplicated Figure 9 row | unique_combination on stg_hesa__f09_domicile |
| Figure 16 count `123457` (not rounded to 5) | multiple_of(5) on stg_hesa__f16_classification |

Result on broken copy: PASS=60, WARN=1, ERROR=7, SKIP=19. Downstream marts and `metrics.metric_values` were skipped, so a dashboard reading them would never see the bad data.

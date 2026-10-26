{{ config(severity='warn') }}
-- Table 61's stated total vs Figure 4's higher education total, within 0.1%.
-- Severity is warn: the gap is real and unexplained (quality log DQ-01), and this test keeps it visible.
with f4 as (
    select academic_year, enrolments as f4_total
    from {{ ref('stg_hesa__f04_enrolments') }}
    where level_label = 'Total HE Providers' and provider_type = 'Total HE'
      and mode_of_study = 'All' and country = 'All'
)
select p.source_table, p.academic_year, f4.f4_total, p.published_total,
       abs(f4.f4_total - p.published_total) * 1.0 / f4.f4_total as relative_gap
from {{ ref('stg_hesa__published_totals') }} p
join f4 using (academic_year)
where p.source_table like 'table_61_%'
  and abs(f4.f4_total - p.published_total) * 1.0 / f4.f4_total > 0.001

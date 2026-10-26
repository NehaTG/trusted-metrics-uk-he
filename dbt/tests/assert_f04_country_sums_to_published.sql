-- Same reconciliation for each nation: detail rows vs HESA's published country total
-- (two aggregation steps: level and mode, so tolerance is 2 x 5 = 10).
with detail as (
    select academic_year, country, sum(enrolments) as detail_sum
    from {{ ref('fct_he_enrolments') }}
    group by 1, 2
),
published as (
    select academic_year, country, enrolments as published_value
    from {{ ref('stg_hesa__f04_enrolments') }}
    where level_label = 'Total HE Providers' and provider_type = 'Total HE'
      and mode_of_study = 'All' and country <> 'All'
)
select d.academic_year, d.country, d.detail_sum, p.published_value
from detail d join published p using (academic_year, country)
where abs(d.detail_sum - p.published_value) > 10

-- Detail rows (24 per year: 3 levels x 2 modes x 4 countries) must add to the 'Total HE Providers'
-- row that HESA publishes. Counts are rounded to the nearest 5 and there are three aggregation
-- steps, so the tolerance is 3 x 5 = 15. The largest gap observed in the data is 5.
with detail as (
    select academic_year, sum(enrolments) as detail_sum
    from {{ ref('fct_he_enrolments') }}
    group by 1
),
published as (
    select academic_year, enrolments as published_value
    from {{ ref('stg_hesa__f04_enrolments') }}
    where level_label = 'Total HE Providers' and provider_type = 'Total HE'
      and mode_of_study = 'All' and country = 'All'
)
select d.academic_year, d.detail_sum, p.published_value, abs(d.detail_sum - p.published_value) as gap
from detail d join published p using (academic_year)
where abs(d.detail_sum - p.published_value) > 15

-- For every provider, the level x mode detail rows must add to the provider's own 'All' row
-- (two aggregation steps, tolerance 10).
with detail as (
    select ukprn, sum(enrolments) as detail_sum
    from {{ ref('fct_provider_enrolments') }}
    group by 1
),
published as (
    select ukprn, enrolments as published_value
    from {{ ref('stg_hesa__f07_provider_enrolments') }}
    where not is_grand_total_row and level_label = 'All' and mode_of_study = 'All'
      and country = 'All' and region = 'All' and permanent_address = 'Total'
)
select d.ukprn, d.detail_sum, p.published_value
from detail d join published p using (ukprn)
where abs(d.detail_sum - p.published_value) > 10

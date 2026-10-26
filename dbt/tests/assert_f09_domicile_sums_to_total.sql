-- UK + Non-UK + Not known must add to the Figure 9 total (one aggregation step, tolerance 5 x 2).
with d as (select academic_year, sum(enrolments) as detail_sum from {{ ref('fct_domicile') }} group by 1),
p as (select academic_year, enrolments as published_value
      from {{ ref('stg_hesa__f09_domicile') }}
      where permanent_address = 'Total' and entrant_marker = 'All' and level_label = 'All'
        and mode_of_study = 'All' and country = 'All')
select d.academic_year, d.detail_sum, p.published_value
from d join p using (academic_year)
where abs(d.detail_sum - p.published_value) > 10

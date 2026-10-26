-- The four classifications must add to HESA's 'Total classified' (tolerance 10).
with d as (select academic_year, sum(qualifiers) as detail_sum
           from {{ ref('fct_first_degree_classification') }} group by 1),
p as (select academic_year, qualifiers as published_value
      from {{ ref('stg_hesa__f16_classification') }}
      where classification = 'Total classified' and mode_of_study = 'All'
        and sex = 'All' and country = 'All')
select d.academic_year, d.detail_sum, p.published_value
from d join p using (academic_year)
where abs(d.detail_sum - p.published_value) > 10

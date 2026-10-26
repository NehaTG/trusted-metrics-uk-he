-- All providers together should match the total stated in the Figure 7 header, within 0.01%
-- (303 rounded provider counts can drift by a few multiples of 5).
with s as (select sum(enrolments) as provider_sum
           from {{ ref('fct_provider_enrolments') }}),
t as (select published_total from {{ ref('stg_hesa__published_totals') }}
      where source_table = 'figure_07')
select s.provider_sum, t.published_total,
       abs(s.provider_sum - t.published_total) * 1.0 / t.published_total as relative_gap
from s cross join t
where abs(s.provider_sum - t.published_total) * 1.0 / t.published_total > 0.0001

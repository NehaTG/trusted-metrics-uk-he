-- Shares and rates must lie between 0 and 1.
select metric_name, academic_year, geography, value
from {{ ref('metric_values') }}
where (metric_name like '%share' or metric_name like '%rate')
  and (value < 0 or value > 1)

-- Every metric with values has a written definition, and every definition has values.
select 'value without definition' as problem, v.metric_name
from (select distinct metric_name from {{ ref('metric_values') }}) v
left join {{ ref('metric_definitions') }} d using (metric_name)
where d.metric_name is null
union all
select 'definition without values', d.metric_name
from {{ ref('metric_definitions') }} d
left join (select distinct metric_name from {{ ref('metric_values') }}) v using (metric_name)
where v.metric_name is null

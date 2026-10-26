-- Every level-of-study label used by a staging model must exist in the governed mapping.
with used as (
    select 'figure_04' as source_file, level_label from {{ ref('stg_hesa__f04_enrolments') }}
    union
    select 'figure_07', level_label from {{ ref('stg_hesa__f07_provider_enrolments') }}
    union
    select 'figure_09', level_label from {{ ref('stg_hesa__f09_domicile') }}
)
select u.source_file, u.level_label
from used u
left join {{ ref('level_of_study_map') }} m
  on m.source_file = u.source_file and m.raw_label = u.level_label
where m.raw_label is null

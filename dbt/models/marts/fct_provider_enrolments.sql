-- Provider detail grain, 2023/24: provider x level x mode. One row per combination, taken
-- from the base view (country = All, region = All, address = Total) so the file's repeated
-- views are not counted again.
select
    s.ukprn,
    (select academic_years from {{ source('hesa_raw', 'file_meta') }} where table_name = 'figure_07') as academic_year,
    m.standard_level as level,
    m.level_group,
    s.mode_of_study  as mode,
    s.enrolments
from {{ ref('stg_hesa__f07_provider_enrolments') }} s
join {{ ref('level_of_study_map') }} m
  on m.source_file = 'figure_07' and m.raw_label = s.level_label
where not s.is_grand_total_row
  and m.label_grain = 'detail'
  and s.mode_of_study in ('Full-time', 'Part-time')
  and s.country = 'All' and s.region = 'All'
  and s.permanent_address = 'Total'

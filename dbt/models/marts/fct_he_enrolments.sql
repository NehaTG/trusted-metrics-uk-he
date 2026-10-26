-- Detail grain only: academic year x country x level x mode, higher education providers.
-- 5 years x 4 countries x 3 levels x 2 modes = 120 rows. No total or 'All' rows.
select
    f.academic_year,
    f.country,
    m.standard_level   as level,
    m.level_group,
    f.mode_of_study    as mode,
    f.enrolments
from {{ ref('stg_hesa__f04_enrolments') }} f
join {{ ref('level_of_study_map') }} m
  on m.source_file = 'figure_04' and m.raw_label = f.level_label
where f.row_grain = 'detail'
  and f.provider_type = 'HE providers'

-- Figure 9: enrolments by permanent address (2019/20 to 2023/24).
select
    trim(academic_year)             as academic_year,
    trim(permanent_address)         as permanent_address,
    trim(entrant_marker)            as entrant_marker,
    trim(level_of_study)            as level_label,
    trim(mode_of_study)             as mode_of_study,
    trim(country_of_he_provider)    as country,
    cast(number as integer)         as enrolments
from {{ source('hesa_raw', 'figure_09') }}

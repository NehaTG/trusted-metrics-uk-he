-- Figure 4: enrolments by level, provider type, mode and country (2019/20 to 2023/24).
-- Text is trimmed, counts are cast to integer, and each row is tagged as detail or aggregate
-- so nothing downstream can sum an aggregate row by accident.
select
    trim(academic_year)        as academic_year,
    trim(level_of_study)       as level_label,
    trim(provider_type)        as provider_type,
    trim(mode_of_study)        as mode_of_study,
    trim(country_of_provider)  as country,
    cast(number as integer)    as enrolments,
    case
        when trim(provider_type) in ('HE providers', 'FE providers')
         and trim(level_of_study) in ('Postgraduate', 'First degree', 'Other undergraduate')
         and trim(mode_of_study) in ('Full-time', 'Part-time')
         and trim(country_of_provider) in ('England', 'Northern Ireland', 'Scotland', 'Wales')
        then 'detail'
        else 'aggregate'
    end                        as row_grain
from {{ source('hesa_raw', 'figure_04') }}

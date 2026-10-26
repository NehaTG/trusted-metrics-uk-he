-- Figure 16: first degree classifications (2019/20 to 2023/24).
select
    trim(academic_year)                   as academic_year,
    trim(mode_of_study)                   as mode_of_study,
    trim(sex)                             as sex,
    trim(country_of_he_provider)          as country,
    trim(classification_of_first_degree)  as classification,
    cast(number as integer)               as qualifiers
from {{ source('hesa_raw', 'figure_16') }}

-- Figure 7: enrolments by provider (2023/24). The file repeats each figure under several
-- country and region views and includes a grand-total row with a blank UKPRN.
select
    nullif(trim(ukprn), '')            as ukprn,
    trim(he_provider)                  as provider_name,
    trim(level_of_study)               as level_label,
    trim(mode_of_study)                as mode_of_study,
    trim(country_of_he_provider)       as country,
    trim(region_of_he_provider)        as region,
    trim(permanent_address)            as permanent_address,
    cast(number as integer)            as enrolments,
    nullif(trim(ukprn), '') is null    as is_grand_total_row
from {{ source('hesa_raw', 'figure_07') }}

-- One row per provider. A provider that reports in several nations (the Open University)
-- takes the nation and region where it has the most students; the flag marks those cases.
with views as (
    select ukprn, provider_name, country, region, enrolments
    from {{ ref('stg_hesa__f07_provider_enrolments') }}
    where not is_grand_total_row
      and level_label = 'All' and mode_of_study = 'All'
      and permanent_address = 'Total'
      and country <> 'All' and region <> 'All'
),
ranked as (
    select *,
           row_number() over (partition by ukprn order by enrolments desc, country, region) as rn,
           count(*) over (partition by ukprn) as n_views
    from views
)
select
    ukprn,
    provider_name,
    country as home_country,
    region  as home_region,
    n_views > 1 as reports_in_several_nations
from ranked
where rn = 1

-- Figure 9 detail grain: academic year x domicile group (UK, Non-UK, Not known).
select
    academic_year,
    case permanent_address
        when 'Total UK'     then 'UK'
        when 'Total Non-UK' then 'Non-UK'
        when 'Not known'    then 'Not known'
    end as domicile_group,
    enrolments
from {{ ref('stg_hesa__f09_domicile') }}
where permanent_address in ('Total UK', 'Total Non-UK', 'Not known')
  and entrant_marker = 'All' and level_label = 'All' and mode_of_study = 'All' and country = 'All'

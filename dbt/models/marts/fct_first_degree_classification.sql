-- Figure 16 detail grain: academic year x degree classification, UK, all modes and sexes.
select
    academic_year,
    classification,
    qualifiers
from {{ ref('stg_hesa__f16_classification') }}
where mode_of_study = 'All' and sex = 'All' and country = 'All'
  and classification in ('First class honours', 'Upper second class honours',
                         'Lower second class honours', 'Third class honours/Pass')

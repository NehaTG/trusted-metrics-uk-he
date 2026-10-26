-- The five governed metrics, one long table. Every number here is computed from detail rows
-- in the fact tables, never read from a published total, so any slice adds up.
with enrol_slices as (
    select academic_year, country as geography, level_group, mode, enrolments
    from {{ ref('fct_he_enrolments') }}
    union all
    select academic_year, 'UK' as geography, level_group, mode, enrolments
    from {{ ref('fct_he_enrolments') }}
),
enrol as (
    select
        academic_year,
        geography,
        sum(enrolments)                                         as total,
        sum(enrolments) filter (where mode = 'Full-time')       as full_time,
        sum(enrolments) filter (where level_group = 'Postgraduate') as postgraduate
    from enrol_slices
    group by academic_year, geography
),
dom as (
    select
        academic_year,
        sum(enrolments)                                         as total,
        sum(enrolments) filter (where domicile_group = 'Non-UK') as non_uk
    from {{ ref('fct_domicile') }}
    group by academic_year
),
cls as (
    select
        academic_year,
        sum(qualifiers)                                                          as classified,
        sum(qualifiers) filter (where classification = 'First class honours')    as first_class
    from {{ ref('fct_first_degree_classification') }}
    group by academic_year
)
select 'he_enrolments' as metric_name, academic_year, geography,
       cast(total as double) as value, cast(null as bigint) as numerator, cast(null as bigint) as denominator
from enrol
union all
select 'full_time_share', academic_year, geography,
       full_time * 1.0 / total, full_time, total
from enrol
union all
select 'postgraduate_share', academic_year, geography,
       postgraduate * 1.0 / total, postgraduate, total
from enrol
union all
select 'non_uk_share', academic_year, 'UK',
       non_uk * 1.0 / total, non_uk, total
from dom
union all
select 'first_class_rate', academic_year, 'UK',
       first_class * 1.0 / classified, first_class, classified
from cls

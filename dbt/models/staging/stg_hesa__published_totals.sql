-- Totals each file states in its own header, one row per source table and academic year.
-- Used to compare sources and to reconcile detail rows against what HESA published.
with years as (
    select distinct academic_year from {{ ref('stg_hesa__f04_enrolments') }}
),
meta as (
    select table_name, stated_totals
    from {{ source('hesa_raw', 'file_meta') }}
    where table_name in ('figure_03', 'figure_07', 'figure_09', 'figure_13')
       or table_name like 'table_61_%'
)
select source_table, academic_year, published_total
from (
    select
        m.table_name  as source_table,
        y.academic_year,
        try_cast(nullif(regexp_extract(m.stated_totals, y.academic_year || ' total=(\d+)', 1), '') as bigint)
                      as published_total
    from meta m
    cross join years y
)
where published_total is not null

-- 5 years x 4 countries x 3 levels x 2 modes = 120 rows. Fewer means a mapping or filter dropped data.
select count(*) as n_rows from {{ ref('fct_he_enrolments') }}
having count(*) <> 120

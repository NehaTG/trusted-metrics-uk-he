{# Custom generic tests. Each returns the rows that FAIL. #}

{% test is_trimmed(model, column_name) %}
select * from {{ model }}
where {{ column_name }} is not null and {{ column_name }} <> trim({{ column_name }})
{% endtest %}

{% test non_negative(model, column_name) %}
select * from {{ model }} where {{ column_name }} < 0
{% endtest %}

{% test multiple_of(model, column_name, n) %}
select * from {{ model }}
where {{ column_name }} is not null and {{ column_name }} % {{ n }} <> 0
{% endtest %}

{% test unique_combination(model, columns) %}
select {{ columns | join(', ') }}, count(*) as n_rows
from {{ model }}
group by {{ columns | join(', ') }}
having count(*) > 1
{% endtest %}

{% test matches_pattern(model, column_name, pattern) %}
select * from {{ model }}
where {{ column_name }} is null or not regexp_matches({{ column_name }}, '{{ pattern }}')
{% endtest %}

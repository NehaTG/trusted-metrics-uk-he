"""Export ONLY tested tables for Tableau Public.
Refuses to export unless `dbt build` finishes with zero errors (warnings allowed).
Usage: python3 -I export_for_tableau.py <dbt_dir> <db_path> <out_dir>"""
import subprocess, sys, os, duckdb
dbt_dir, db, out = sys.argv[1:4]
r = subprocess.run(["dbt", "build", "--profiles-dir", ".", "--no-use-colors"], cwd=dbt_dir, capture_output=True, text=True)
last = [l for l in r.stdout.splitlines() if "Done." in l]
print(last[-1] if last else r.stdout[-500:])
if r.returncode != 0:
    sys.exit("dbt build failed: nothing exported. The dashboard only reads tested data.")
os.makedirs(out, exist_ok=True)
con = duckdb.connect(db, read_only=True)
exports = {
 "metrics_long.csv": """with u as (select v.metric_name, v.academic_year, v.value, d.unit
          from metrics.metric_values v join reference.metric_definitions d using (metric_name)
          where v.geography = 'UK'),
      f as (select metric_name, any_value(unit) unit,
              arg_min(value, academic_year) v0, min(academic_year) y0,
              arg_max(value, academic_year) v1, max(academic_year) y1,
              max(value) vmax, arg_max(academic_year, value) ymax from u group by 1),
      ins as (select metric_name,
              case when unit = 'share'
                then printf('UK: %s from %.1f%% in %s to %.1f%% in %s (%+.1f pts). Peak: %.1f%% in %s.',
                     case when v1 >= v0 then 'up' else 'down' end, v0*100, y0, v1*100, y1, (v1-v0)*100, vmax*100, ymax)
                else printf('UK: %s from %,d in %s to %,d in %s (%+.1f%%). Peak: %,d in %s.',
                     case when v1 >= v0 then 'up' else 'down' end, cast(v0 as bigint), y0, cast(v1 as bigint), y1, (v1/v0-1)*100, cast(vmax as bigint), ymax)
              end as insight from f)
        select v.metric_name, d.display_name, d.unit, v.academic_year, v.geography,
        v.value, v.numerator, v.denominator, d.definition, d.formula, d.source_figure, d.caveat, ins.insight
        from metrics.metric_values v join reference.metric_definitions d using (metric_name)
        join ins using (metric_name)
        order by 1,4,5""",
 "enrolments_by_country_level_mode.csv": "select * from marts.fct_he_enrolments order by 1,2,3,5",
 "provider_enrolments_2023_24.csv": """select f.*, p.provider_name, p.home_country, p.home_region, p.reports_in_several_nations
        from marts.fct_provider_enrolments f left join marts.dim_provider p using (ukprn)""",
 "domicile.csv": "select * from marts.fct_domicile order by 1,2",
 "first_degree_classification.csv": "select * from marts.fct_first_degree_classification order by 1,2",
}
for f, q in exports.items():
    n = con.execute(f"copy ({q}) to '{os.path.join(out, f)}' (header, delimiter ',')").fetchone()[0]
    print(f"{f:42s} {n:>7,} rows")

# KPI tiles: derived only from the governed metric_values table (UK, latest vs previous year)
kpi = """
with u as (select v.*, d.display_name, d.unit,
             row_number() over (partition by v.metric_name order by v.academic_year desc) rn
           from metrics.metric_values v join reference.metric_definitions d using (metric_name)
           where v.geography = 'UK'),
l as (select * from u where rn = 1), p as (select * from u where rn = 2)
select l.display_name as metric, l.academic_year as latest_year,
  case when l.unit = 'share' then printf('%.1f%%', l.value*100)
       else printf('%,d', cast(l.value as bigint)) end as latest_value,
  case when l.unit = 'share'
       then printf('%+.1f pts vs %s', (l.value - p.value)*100, p.academic_year)
       else printf('%+.1f%% vs %s', (l.value/p.value - 1)*100, p.academic_year) end as change_vs_prior,
  case l.metric_name when 'he_enrolments' then 1 when 'full_time_share' then 2
       when 'postgraduate_share' then 3 when 'non_uk_share' then 4 else 5 end as sort_order
from l join p using (metric_name) order by sort_order
"""
n = con.execute(f"copy ({kpi}) to '{os.path.join(out, 'kpi_tiles.csv')}' (header, delimiter ',')").fetchone()[0]
print(f"{'kpi_tiles.csv':42s} {n:>7,} rows")

# schema.ini tells Tableau's text connector to keep the tile values as text (no number parsing)
with open(os.path.join(out, "schema.ini"), "w") as fh:
    fh.write("[kpi_tiles.csv]\nFormat=CSVDelimited\nColNameHeader=True\nCol1=metric Text\nCol2=latest_year Text\n"
             "Col3=latest_value Text\nCol4=change_vs_prior Text\nCol5=sort_order Integer\n")
print("schema.ini written")

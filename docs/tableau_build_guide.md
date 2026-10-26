# Tableau Public build guide (about 45 minutes)

Tableau Public is free: https://public.tableau.com/app/discover (Mac download available). It reads CSV files, so every file in `tableau_data/` is an export of a table that passed all dbt tests. `export_for_tableau.py` refuses to export if the tests fail.

## 1. Connect
Open Tableau Public > Connect > **Text file** > `metrics_long.csv`.
Then Data > New Data Source for `enrolments_by_country_level_mode.csv` and `provider_enrolments_2023_24.csv`. Keep them as separate sources; do not join them.

## 2. Set the fields (metrics_long)
- `academic_year`: leave as text (Dimension).
- `value`: Measure. Format per metric with the `unit` column (share = 0.0%).
- Never sum `value` across metrics. Every sheet must filter to ONE `display_name`.

## 3. Dashboard layout (1200 x 800)
| Zone | Sheet | How |
|---|---|---|
| Top strip, 5 tiles | One KPI per metric, latest year 2023/24, UK | Filter display_name and geography=UK and academic_year=2023/24. Text mark, value only. |
| Left, large | Trend of selected metric, 2019/20 to 2023/24 | Columns academic_year, Rows value, Colour geography. Add a parameter "Metric" (list of display_name) and a calculated filter so one selector drives it. |
| Right, top | Nation comparison, 2023/24 | Bar: geography vs value for the chosen metric (not offered for non_uk_share / first_class_rate: UK only, say so in a note). |
| Right, bottom | Level of study x mode, 2023/24 | Stacked bar from `enrolments_by_country_level_mode`, filter country=UK. |
| Bottom | Definition card | Tooltip or text box from `definition`, `formula`, `source_figure`, `caveat` of the chosen metric. |

## 4. Trust footer (this is the point of the project)
Add a text box: "Every number comes from tables that passed 86 automated checks. Rounding to nearest 5 applies. Source: HESA Student Data, CC BY 4.0. Definitions: link to repo `metric_definitions.csv`."

## 5. Things to avoid
- Do not recompute shares in Tableau. Use `value` as published by the governed metric.
- Do not use Table 61 for headline totals (it sits about 0.2% above Figure 4; see quality log).
- Provider sheet: filter out `reports_in_several_nations = true` before ranking by country.

## 6. Publish
File > Save to Tableau Public > name it "UK Higher Education: Trusted Metrics". Send me the public link and I will add it to the README.

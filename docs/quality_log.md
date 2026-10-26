# Data-quality log: HESA open data (stage 1)

Source: HESA Higher Education Student Statistics 2023/24 (Figures 1-4, 6-18) and Table 61 (2017/18 to 2021/22). Licence stated in every file: Creative Commons Attribution 4.0. Attribution: HESA.

Not covered: Figure 5 (not supplied). Severity is my judgement of the effect on a metric, not a HESA rating. 'Planned handling' is what stage 2 will do, not something already done.

| ID | Severity | Area | Finding |
|---|---|---|---|
| DQ-01 | High | Cross-file consistency | The same headline measure, total HE student enrolments, has different values in different files |
| DQ-02 | High | Structure | Totals, sub-totals and 'All' categories sit inside the data rows, so a plain SUM overcounts |
| DQ-04 | High | Structure | One column mixes different levels of detail (grain) |
| DQ-06 | High | Definitions | The 'level of study' vocabulary differs between files |
| DQ-09 | High | Series break | The data-collection record changes between older and newer years |
| DQ-03 | Medium | Rounding | Published counts are rounded to the nearest 5, so parts do not always add up to the whole |
| DQ-05 | Medium | Redundancy | Figure 7 repeats each provider's figure under several country and region combinations |
| DQ-07 | Medium | Formatting | Some category labels carry trailing spaces |
| DQ-08 | Low | Types | Numbers and percentages arrive as text with inconsistent formats |
| DQ-10 | Low | Sparsity | A large share of rows are zeros |
| DQ-11 | Low | File format | File layout varies between files |

## DQ-01 The same headline measure, total HE student enrolments, has different values in different files

**Severity:** High | **Area:** Cross-file consistency

**Evidence**

```
2019/20: Table 61 2,532,165 | Figs 3/9/13 2,529,870 | Fig 4 HE providers 2,528,295 | Fig 4 HE+FE 2,694,490 | Fig 7 n/a | spread among HE-only figures 3,870
2020/21: Table 61 2,751,865 | Figs 3/9/13 2,747,200 | Fig 4 HE providers 2,745,890 | Fig 4 HE+FE 2,907,710 | Fig 7 n/a | spread among HE-only figures 5,975
2021/22: Table 61 2,862,620 | Figs 3/9/13 2,857,855 | Fig 4 HE providers 2,856,715 | Fig 4 HE+FE 3,002,780 | Fig 7 n/a | spread among HE-only figures 5,905
2022/23: Table 61 n/a | Figs 3/9/13 2,937,155 | Fig 4 HE providers 2,936,050 | Fig 4 HE+FE 3,070,875 | Fig 7 n/a | spread among HE-only figures 1,105
2023/24: Table 61 n/a | Figs 3/9/13 2,904,425 | Fig 4 HE providers 2,903,380 | Fig 4 HE+FE 3,034,720 | Fig 7 2,904,425 | spread among HE-only figures 1,045
```

**Why it matters:** A dashboard that reads Table 61 and one that reads Figure 4 would show different totals for the same year.

**Planned handling:** Choose one source of record per metric and document why. Add a dbt test that fails when two published totals for the same year drift apart by more than a stated tolerance.

## DQ-02 Totals, sub-totals and 'All' categories sit inside the data rows, so a plain SUM overcounts

**Severity:** High | **Area:** Structure

**Evidence**

```
figure_03: SUM(number) = 2,238,820,215 vs stated total 13,976,505 -> 160.2x
figure_07: SUM(number) = 418,022,560 vs stated total 2,904,425 -> 143.9x
figure_09: SUM(number) = 1,006,133,360 vs stated total 13,976,505 -> 72.0x
figure_13: SUM(number) = 2,012,615,270 vs stated total 13,976,505 -> 144.0x
figure_12: SUM(number) = 63,664,375 vs stated total 2,652,685 -> 24.0x
figure_15: SUM(number) = 390,286,690 vs stated total 3,821,150 -> 102.1x
figure_17: SUM(number) = 332,711,775 vs stated total 4,621,915 -> 72.0x
table_61_2017_18: SUM(number) = 163,472,755 vs stated total 2,414,745 -> 67.7x
table_61_2018_19: SUM(number) = 166,239,695 vs stated total 2,456,545 -> 67.7x
table_61_2019_20: SUM(number) = 171,339,095 vs stated total 2,532,165 -> 67.7x
table_61_2020_21: SUM(number) = 186,235,510 vs stated total 2,751,865 -> 67.7x
table_61_2021_22: SUM(number) = 193,592,630 vs stated total 2,862,620 -> 67.6x
```

**Why it matters:** HESA's own disclaimer warns about double counting in pivot tables. A naive SUM(number) gives a figure many times the real total.

**Planned handling:** Tag each row as detail or aggregate in staging, keep only detail rows for summing, and test that the sum of detail rows reconciles to the published total.

## DQ-03 Published counts are rounded to the nearest 5, so parts do not always add up to the whole

**Severity:** Medium | **Area:** Rounding

**Evidence**

```
2,531,791 of 2,531,791 numeric values (100.00%) are multiples of 5 across 20 tables.
Figure 7 (2023/24): 78 of 303 providers have four level-of-study counts that do not add to their own 'All' count. Sum of 'All' = 2,904,405, sum of the four levels = 2,904,445 (difference -40).
Table 61, four nations vs UK total: 2017/18: 2,414,745 vs 2,414,745 (0); 2018/19: 2,456,545 vs 2,456,545 (0); 2019/20: 2,532,165 vs 2,532,165 (0); 2020/21: 2,751,870 vs 2,751,865 (5); 2021/22: 2,862,615 vs 2,862,620 (-5)
Figure 1 entrants, four levels vs stated total: exact in 8 of 10 years, largest gap 5 (rounding is to the nearest 5)
Figure 2 qualifiers, four levels vs stated total: exact in 9 of 10 years, largest gap 5 (rounding is to the nearest 5)
Figure 4, three levels vs 'Total HE Providers': exact in 4 of 5 years, largest gap 5 (rounding is to the nearest 5)
Figure 4, four countries vs UK HE total: exact in 3 of 5 years, largest gap 5 (rounding is to the nearest 5)
```

**Why it matters:** Reconciliation tests need a tolerance. An exact-equality test would fail on correct data.

**Planned handling:** Test with a documented tolerance (a few multiples of 5 per aggregation level) and report the largest observed drift.

## DQ-04 One column mixes different levels of detail (grain)

**Severity:** High | **Area:** Structure

**Evidence**

```
Table 61 'domicile' holds 376 local-authority names (with a LAUA code), 243 entries with no code (for example China, India, Nigeria, Pakistan, United States) and a 'Total' row, all in one column.
Figure 7 'permanent_address' mixes totals, nations and EU/non-EU groups: England, European Union, Non-European Union, Northern Ireland, Not known, Other UK, Scotland, Total, Total Non-UK, Total UK, Wales.
Table 61 'region_of_he_provider' mixes nations, English regions, 'The Open University in England' and 'Total United Kingdom'.
```

**Why it matters:** Counting 'England' and 'North West' together, or a local authority and a country together, double counts.

**Planned handling:** Split into explicit columns (level type, parent, member) in staging and test that each row has exactly one grain.

## DQ-05 Figure 7 repeats each provider's figure under several country and region combinations

**Severity:** Medium | **Area:** Redundancy

**Evidence**

```
166,254 of 219,351 rows are repeat views of a base row (country = All, region = All). 158,481 rows (72% of the file) carry exactly the same number as their base row.
```

**Why it matters:** About this share of the file adds no new information and inflates any total that includes it.

**Planned handling:** Keep one row per provider, level, mode and address in the staging model and drop the duplicate views.

## DQ-06 The 'level of study' vocabulary differs between files

**Severity:** High | **Area:** Definitions

**Evidence**

```
Figure 1 (entrants): First degree | Other undergraduate | Postgraduate (research) | Postgraduate (taught) | Total
Figure 2 (qualifiers): First degree | Other undergraduate | Postgraduate (research) | Postgraduate (taught) | Total
Figure 3: Doctorate research | First degree | Foundation degree | HNC/HND | Institutional credit at postgraduate research | Institutional credit at postgraduate taught | Institutional credit at undergraduate | Master's taught | Other postgraduate research | Other postgraduate taught | Other undergraduate | Postgraduate Certificate in Education | Professional Graduate Certificate in Education | Total | Total other undergraduate | Total postgraduate | Total postgraduate research | Total postgraduate taught | Total undergraduate
Figure 4: First degree | Other undergraduate | Postgraduate | Total | Total FE Providers | Total HE Providers
Figure 7: All | All postgraduate | All undergraduate | First degree | Other undergraduate | Postgraduate (research) | Postgraduate (taught)
Figure 8: All student enrolments | PG Full-time | PG Part-time | UG Full-time | UG Part-time
Table 61: All | All postgraduate | All undergraduate | First degree | Other undergraduate | Postgraduate (research) | Postgraduate (taught)
```

**Why it matters:** Joining or comparing files on this column without a mapping silently drops or mismatches rows.

**Planned handling:** Build one governed level-of-study dimension with a mapping table and a test that every raw label maps to exactly one standard label.

## DQ-07 Some category labels carry trailing spaces

**Severity:** Medium | **Area:** Formatting

**Evidence**

```
figure_10.country_of_he_provider: 80 values with leading or trailing spaces
```

**Why it matters:** 'England ' and 'England' are different strings, so a join on the country column loses rows.

**Planned handling:** Trim every text column in staging and add a not-equal-to-trimmed test.

## DQ-08 Numbers and percentages arrive as text with inconsistent formats

**Severity:** Low | **Area:** Types

**Evidence**

```
Percentages arrive as text with a % sign; blank percentages are common: figure_03: 15,871 blank of 151,345; figure_06: 7,470 blank of 25,795; figure_14: 1,184 blank of 18,470; figure_15: 10,992 blank of 50,130; figure_16: 283 blank of 1,215; figure_18: 475 blank of 4,740.
Counts stored with a decimal point ('10.0'): figure_11 (1,505 rows); figure_12 (2,942 rows); figure_17 (53,688 rows).
```

**Why it matters:** Type inference differs by file, so the same column can load as integer in one table and decimal in another.

**Planned handling:** Cast explicitly in staging (percent text to a 0-1 decimal, counts to integer) and test for null after cast.

## DQ-09 The data-collection record changes between older and newer years

**Severity:** High | **Area:** Series break

**Evidence**

```
collection 051,054,056 | years 2014/15 to 2023/24 | last updated Mar-25: figure_01, figure_02
collection 051,054,056 | years 2019/20 to 2023/24 | last updated Mar-25: figure_03, figure_04, figure_06, figure_09, figure_10, figure_11, figure_13, figure_14, figure_15, figure_16, figure_17, figure_18
collection 056 | years 2023/24 | last updated Mar-25: figure_07, figure_08
collection 052 | years 2019/20 to 2023/24 | last updated Mar-25: figure_12
collection 051, 054 | years 2017/18 | last updated Feb-23: table_61_2017_18
collection 051, 054 | years 2018/19 | last updated Feb-23: table_61_2018_19
collection 051, 054 | years 2019/20 | last updated Feb-23: table_61_2019_20
collection 051, 054 | years 2020/21 | last updated Feb-23: table_61_2020_21
collection 051, 054 | years 2021/22 | last updated Feb-23: table_61_2021_22
HESA's 2023/24 release page describes 2023/24 as the second year of the revised Data Futures data model. The size of any break in the figures is not measured here.
```

**Why it matters:** Trends that cross the change may reflect a change in collection, not a change in students.

**Planned handling:** Mark each year with its collection record, show the break on every trend chart, and avoid year-on-year claims across it without a caveat.

## DQ-10 A large share of rows are zeros

**Severity:** Low | **Area:** Sparsity

**Evidence**

```
figure_07: 76,575 of 219,351 rows (34.9%) are zero
figure_03: 30,798 of 151,345 rows (20.3%) are zero
figure_13: 20,480 of 154,940 rows (13.2%) are zero
table_61_2021_22: 118,846 of 367,845 rows (32.3%) are zero
```

**Why it matters:** The files list every combination, so zero means 'no students in this cell' or 'not applicable'. The files do not say which.

**Planned handling:** Keep zeros in staging, flag them, and exclude them from averages and ranks.

## DQ-11 File layout varies between files

**Severity:** Low | **Area:** File format

**Evidence**

```
22 of 22 files start with a byte-order mark. The first blank separator row sits at line 12 in some files and line 22 in others, so the real header row moves. Table 61 downloads as a zip of five yearly files. Some files pad rows with empty quoted columns.
```

**Why it matters:** A fixed 'skip N rows' reader would misread some files.

**Planned handling:** Detect the header row dynamically (done in the loader) and keep the raw file name and header text in a metadata table.

## Checks that passed

- Figure 7: unique key (ukprn, level, mode, country, region, address): 219,351 distinct keys in 219,351 rows
- Figure 7: 303 UKPRNs map to 303 provider names
- Licence: 22 of 22 files state Creative Commons Attribution 4.0

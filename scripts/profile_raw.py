"""Profile the raw HESA tables and write the data-quality log.

Every number in the log is computed here from the loaded raw tables.
Causes are not asserted unless a source document says so; where a cause is
unknown the log says "unexplained".

Usage: python3 -I profile_raw.py <db_path> <raw_dir> <t61_dir> <docs_dir>
"""
import csv
import glob
import os
import re
import sys

import duckdb

YEARS = ["2019/20", "2020/21", "2021/22", "2022/23", "2023/24"]
db_path, raw_dir, t61_dir, docs_dir = sys.argv[1:5]
con = duckdb.connect(db_path)
con.execute("create schema if not exists profile")


def q(sql, *args):
    return con.execute(sql, list(args)).fetchall()


def stated(table):
    """Parse 'YYYY/YY total=N' items from raw.file_meta into {year: int}."""
    s = q("select stated_totals from raw.file_meta where table_name=?", table)[0][0]
    out = {}
    for m in re.finditer(r"(\d{4}/\d{2}) total=(\d+)", s):
        out[m.group(1)] = int(m.group(2))
    return out


def fmt(n):
    return f"{int(round(n)):,}"


findings = []


def add(fid, severity, area, title, evidence, why, handling):
    findings.append(dict(id=fid, severity=severity, area=area, title=title,
                         evidence=evidence, why=why, handling=handling))


# ---------------------------------------------------------------- F-01
t61_stated = {}
for y in ["2017/18", "2018/19", "2019/20", "2020/21", "2021/22"]:
    tbl = "table_61_" + y.replace("/", "_")
    t61_stated[y] = stated(tbl)[y]
f3 = stated("figure_03")
f7 = stated("figure_07")
f4_he = dict(q("""select academic_year, try_cast(number as bigint) from raw.figure_04
                  where level_of_study='Total HE Providers' and provider_type='Total HE'
                  and mode_of_study='All' and country_of_provider='All'"""))
f4_all = dict(q("""select academic_year, try_cast(number as bigint) from raw.figure_04
                   where level_of_study='Total' and provider_type='Total'
                   and mode_of_study='All' and country_of_provider='All'"""))
rows = []
for y in YEARS:
    rows.append((y, t61_stated.get(y), f3.get(y), f4_he.get(y), f4_all.get(y), f7.get(y)))
os.makedirs(docs_dir, exist_ok=True)
with open(os.path.join(docs_dir, "cross_file_totals.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["academic_year", "table61_stated_total", "figures_3_9_13_stated_total",
                "figure4_total_HE_providers", "figure4_total_HE_plus_FE", "figure7_stated_total"])
    w.writerows(rows)
lines = []
spreads = []
for y, a, b, c, d, e in rows:
    comparable = [v for v in (a, b, c, e) if v is not None]
    spread = max(comparable) - min(comparable)
    spreads.append(spread)
    lines.append(f"{y}: Table 61 {fmt(a) if a else 'n/a'} | Figs 3/9/13 {fmt(b)} | "
                 f"Fig 4 HE providers {fmt(c)} | Fig 4 HE+FE {fmt(d)} | Fig 7 {fmt(e) if e else 'n/a'} "
                 f"| spread among HE-only figures {fmt(spread)}")
add("DQ-01", "High", "Cross-file consistency",
    "The same headline measure, total HE student enrolments, has different values in different files",
    "\n".join(lines),
    "A dashboard that reads Table 61 and one that reads Figure 4 would show different totals for the same year.",
    "Choose one source of record per metric and document why. Add a dbt test that fails when two "
    "published totals for the same year drift apart by more than a stated tolerance.")

# ---------------------------------------------------------------- F-02
ratios = []
for t in ["figure_03", "figure_07", "figure_09", "figure_13", "figure_12", "figure_15", "figure_17"]:
    st = stated(t)
    naive = q(f"select sum(try_cast(number as double)) from raw.{t}")[0][0]
    ratios.append((t, naive, sum(st.values()), naive / sum(st.values())))
for y in ["2017/18", "2018/19", "2019/20", "2020/21", "2021/22"]:
    t = "table_61_" + y.replace("/", "_")
    naive = q(f"select sum(try_cast(number as double)) from raw.{t}")[0][0]
    ratios.append((t, naive, t61_stated[y], naive / t61_stated[y]))
ev = "\n".join(f"{t}: SUM(number) = {fmt(n)} vs stated total {fmt(s)} -> {r:,.1f}x" for t, n, s, r in ratios)
add("DQ-02", "High", "Structure",
    "Totals, sub-totals and 'All' categories sit inside the data rows, so a plain SUM overcounts",
    ev,
    "HESA's own disclaimer warns about double counting in pivot tables. A naive SUM(number) gives a figure "
    "many times the real total.",
    "Tag each row as detail or aggregate in staging, keep only detail rows for summing, and test that "
    "the sum of detail rows reconciles to the published total.")

# ---------------------------------------------------------------- F-03
tables = [r[0] for r in q("select table_name from raw.file_meta order by 1")]
rnd = []
for t in tables:
    cols = [r[0] for r in q("select column_name from information_schema.columns where table_schema='raw' and table_name=?", t)]
    if "number" not in cols:
        continue
    n, m5 = q(f"""select count(*) filter (where try_cast(number as double) is not null),
                         count(*) filter (where try_cast(number as double) % 5 = 0) from raw.{t}""")[0]
    rnd.append((t, n, m5))
tot_n = sum(r[1] for r in rnd)
tot_m = sum(r[2] for r in rnd)
not_m = [(t, n - m) for t, n, m in rnd if n != m]
ev = f"{fmt(tot_m)} of {fmt(tot_n)} numeric values ({tot_m / tot_n:.2%}) are multiples of 5 across {len(rnd)} tables."
if not_m:
    ev += " Tables with values not divisible by 5: " + ", ".join(f"{t} ({fmt(k)})" for t, k in not_m)
parts = q("""
with p as (select ukprn, level_of_study l, try_cast(number as bigint) n from raw.figure_07
           where ukprn<>'' and mode_of_study='All' and country_of_he_provider='All'
             and region_of_he_provider='All' and permanent_address='Total')
select count(*), count(*) filter (where a.n <> coalesce(fd.n,0)+coalesce(ou.n,0)+coalesce(pt.n,0)+coalesce(pr.n,0)),
       sum(a.n), sum(coalesce(fd.n,0)+coalesce(ou.n,0)+coalesce(pt.n,0)+coalesce(pr.n,0))
from p a left join p fd on fd.ukprn=a.ukprn and fd.l='First degree'
 left join p ou on ou.ukprn=a.ukprn and ou.l='Other undergraduate'
 left join p pt on pt.ukprn=a.ukprn and pt.l='Postgraduate (taught)'
 left join p pr on pr.ukprn=a.ukprn and pr.l='Postgraduate (research)'
where a.l='All'""")[0]
ev += (f"\nFigure 7 (2023/24): {parts[1]} of {parts[0]} providers have four level-of-study counts that do not add "
       f"to their own 'All' count. Sum of 'All' = {fmt(parts[2])}, sum of the four levels = {fmt(parts[3])} "
       f"(difference {fmt(parts[2] - parts[3])}).")
nat = []
for y in ["2017/18", "2018/19", "2019/20", "2020/21", "2021/22"]:
    t = "table_61_" + y.replace("/", "_")
    r = q(f"""select
        sum(try_cast(number as bigint)) filter (where region_of_he_provider in ('England','Wales','Scotland','Northern Ireland')),
        max(try_cast(number as bigint)) filter (where region_of_he_provider='Total United Kingdom')
        from raw.{t} where "4_way_domicile"='All' and level_of_study='All' and mode_of_study='All' and domicile='Total'""")[0]
    nat.append((y, r[0], r[1]))
ev += "\nTable 61, four nations vs UK total: " + "; ".join(
    f"{y}: {fmt(a)} vs {fmt(b)} ({fmt(a - b)})" for y, a, b in nat)
add("DQ-03", "Medium", "Rounding",
    "Published counts are rounded to the nearest 5, so parts do not always add up to the whole",
    ev,
    "Reconciliation tests need a tolerance. An exact-equality test would fail on correct data.",
    "Test with a documented tolerance (a few multiples of 5 per aggregation level) and report the "
    "largest observed drift.")

# ---------------------------------------------------------------- F-04
lau, nonlau = q("""select count(distinct domicile) filter (where laua_code<>''),
                          count(distinct domicile) filter (where laua_code='' and domicile<>'Total')
                   from raw.table_61_2021_22""")[0]
sample_non = [r[0] for r in q("""select domicile from raw.table_61_2021_22 where laua_code='' and domicile<>'Total'
                                  group by 1 order by sum(try_cast(number as bigint)) desc limit 5""")]
f7_addr = [r[0] for r in q("select distinct permanent_address from raw.figure_07 order by 1")]
f7_reg = [r[0] for r in q("select distinct region_of_he_provider from raw.figure_07 order by 1")]
ev = (f"Table 61 'domicile' holds {lau} local-authority names (with a LAUA code), {nonlau} entries with no code "
      f"(for example {', '.join(sample_non)}) and a 'Total' row, all in one column.\n"
      f"Figure 7 'permanent_address' mixes totals, nations and EU/non-EU groups: {', '.join(f7_addr)}.\n"
      f"Table 61 'region_of_he_provider' mixes nations, English regions, 'The Open University in England' "
      f"and 'Total United Kingdom'.")
add("DQ-04", "High", "Structure",
    "One column mixes different levels of detail (grain)",
    ev,
    "Counting 'England' and 'North West' together, or a local authority and a country together, double counts.",
    "Split into explicit columns (level type, parent, member) in staging and test that each row has exactly "
    "one grain.")

# ---------------------------------------------------------------- F-05
dup = q("""
with base as (select ukprn, level_of_study, mode_of_study, permanent_address, number n
              from raw.figure_07 where country_of_he_provider='All' and region_of_he_provider='All')
select count(*) filter (where not (f.country_of_he_provider='All' and f.region_of_he_provider='All')),
       count(*) filter (where not (f.country_of_he_provider='All' and f.region_of_he_provider='All') and f.number=b.n),
       count(*)
from raw.figure_07 f join base b using (ukprn, level_of_study, mode_of_study, permanent_address)""")[0]
add("DQ-05", "Medium", "Redundancy",
    "Figure 7 repeats each provider's figure under several country and region combinations",
    f"{fmt(dup[0])} of {fmt(dup[2])} rows are repeat views of a base row (country = All, region = All). "
    f"{fmt(dup[1])} rows ({dup[1] / dup[2]:.0%} of the file) carry exactly the same number as their base row.",
    "About this share of the file adds no new information and inflates any total that includes it.",
    "Keep one row per provider, level, mode and address in the staging model and drop the duplicate views.")

# ---------------------------------------------------------------- F-06
def vals(t, c):
    return sorted(r[0] for r in q(f"select distinct {c} from raw.{t} where {c} is not null"))
vocab = {
    "Figure 1 (entrants)": vals("figure_01", "level_of_study"),
    "Figure 2 (qualifiers)": vals("figure_02", "level_of_qualification"),
    "Figure 3": vals("figure_03", "level_of_study"),
    "Figure 4": vals("figure_04", "level_of_study"),
    "Figure 7": vals("figure_07", "level_of_study"),
    "Figure 8": vals("figure_08", "level_and_mode_of_study"),
    "Table 61": vals("table_61_2021_22", "level_of_study"),
}
ev = "\n".join(f"{k}: {' | '.join(v)}" for k, v in vocab.items())
add("DQ-06", "High", "Definitions",
    "The 'level of study' vocabulary differs between files",
    ev,
    "Joining or comparing files on this column without a mapping silently drops or mismatches rows.",
    "Build one governed level-of-study dimension with a mapping table and a test that every raw label maps "
    "to exactly one standard label.")

# ---------------------------------------------------------------- F-07
ws = []
for t in tables:
    for (c,) in q("select column_name from information_schema.columns where table_schema='raw' and table_name=?", t):
        k = q(f'select count(*) from raw."{t}" where "{c}" is not null and "{c}" <> trim("{c}")')[0][0]
        if k:
            ws.append((t, c, k))
ev = "\n".join(f"{t}.{c}: {fmt(k)} values with leading or trailing spaces" for t, c, k in ws) or "None found."
add("DQ-07", "Medium", "Formatting",
    "Some category labels carry trailing spaces",
    ev,
    "'England ' and 'England' are different strings, so a join on the country column loses rows.",
    "Trim every text column in staging and add a not-equal-to-trimmed test.")

# ---------------------------------------------------------------- F-08
pct = []
for t in tables:
    cols = [r[0] for r in q("select column_name from information_schema.columns where table_schema='raw' and table_name=?", t)]
    if "percentage" in cols:
        n, withp, blank = q(f"""select count(*), count(*) filter (where percentage like '%\\%%' escape '\\'),
                                       count(*) filter (where trim(percentage)='') from raw.{t}""")[0]
        pct.append((t, n, withp, blank))
dec = []
for t in tables:
    cols = [r[0] for r in q("select column_name from information_schema.columns where table_schema='raw' and table_name=?", t)]
    if "number" in cols:
        k = q(f"select count(*) from raw.{t} where number like '%.%'")[0][0]
        if k:
            dec.append((t, k))
ev = ("Percentages arrive as text with a % sign; blank percentages are common: "
      + "; ".join(f"{t}: {fmt(b)} blank of {fmt(n)}" for t, n, w, b in pct if b)
      + ".\nCounts stored with a decimal point ('10.0'): " + ("; ".join(f"{t} ({fmt(k)} rows)" for t, k in dec) or "none")
      + ".")
add("DQ-08", "Low", "Types",
    "Numbers and percentages arrive as text with inconsistent formats",
    ev,
    "Type inference differs by file, so the same column can load as integer in one table and decimal in another.",
    "Cast explicitly in staging (percent text to a 0-1 decimal, counts to integer) and test for null after cast.")

# ---------------------------------------------------------------- F-09
coll = q("select table_name, data_collection, academic_years, last_updated from raw.file_meta order by 1")
by = {}
for t, c, a, l in coll:
    by.setdefault((c, a, l), []).append(t)
ev = "\n".join(f"collection {c or 'n/a'} | years {a} | last updated {l}: {', '.join(v)}" for (c, a, l), v in by.items())
add("DQ-09", "High", "Series break",
    "The data-collection record changes between older and newer years",
    ev + "\nHESA's 2023/24 release page describes 2023/24 as the second year of the revised Data Futures data model. "
         "The size of any break in the figures is not measured here.",
    "Trends that cross the change may reflect a change in collection, not a change in students.",
    "Mark each year with its collection record, show the break on every trend chart, and avoid year-on-year "
    "claims across it without a caveat.")

# ---------------------------------------------------------------- F-10
z = []
for t in ["figure_07", "figure_03", "figure_13", "table_61_2021_22"]:
    n, k = q(f"select count(*), count(*) filter (where try_cast(number as double)=0) from raw.{t}")[0]
    z.append((t, n, k))
add("DQ-10", "Low", "Sparsity",
    "A large share of rows are zeros",
    "\n".join(f"{t}: {fmt(k)} of {fmt(n)} rows ({k / n:.1%}) are zero" for t, n, k in z),
    "The files list every combination, so zero means 'no students in this cell' or 'not applicable'. "
    "The files do not say which.",
    "Keep zeros in staging, flag them, and exclude them from averages and ranks.")

# ---------------------------------------------------------------- F-11
bom = 0
files = sorted(glob.glob(os.path.join(raw_dir, "hesa_figure-*.csv")) + glob.glob(os.path.join(t61_dir, "table-61-*.csv")))
offsets = []
for p in files:
    with open(p, "rb") as fh:
        if fh.read(3) == b"\xef\xbb\xbf":
            bom += 1
    with open(p, newline="", encoding="utf-8-sig") as fh:
        for i, r in enumerate(csv.reader(fh)):
            if i > 5 and all((c or "").strip() == "" for c in r):
                offsets.append(i + 1)
                break
add("DQ-11", "Low", "File format",
    "File layout varies between files",
    f"{bom} of {len(files)} files start with a byte-order mark. The first blank separator row sits at line "
    f"{min(offsets)} in some files and line {max(offsets)} in others, so the real header row moves. "
    "Table 61 downloads as a zip of five yearly files. Some files pad rows with empty quoted columns.",
    "A fixed 'skip N rows' reader would misread some files.",
    "Detect the header row dynamically (done in the loader) and keep the raw file name and header text in "
    "a metadata table.")

# ---------------------------------------------------------------- Passed checks
passes = []


def recon(label, pairs):
    """pairs: list of (parts, total). Report exact matches and the largest gap."""
    exact = sum(1 for p, t in pairs if p == t)
    gap = max(abs(p - t) for p, t in pairs)
    return (f"{label}: exact in {exact} of {len(pairs)} years, "
            f"largest gap {fmt(gap)} (rounding is to the nearest 5)")


recs = []
for t, col, lab in [("figure_01", "level_of_study", "Figure 1 entrants, four levels vs stated total"),
                    ("figure_02", "level_of_qualification", "Figure 2 qualifiers, four levels vs stated total")]:
    st = stated(t)
    pairs = []
    for y, tot in st.items():
        s = q(f"""select sum(try_cast(number as bigint)) from raw.{t}
                  where academic_year=? and {col} <> 'Total'""", y)[0][0]
        pairs.append((int(s), tot))
    recs.append(recon(lab, pairs))
pairs = []
for y in YEARS:
    s = q("""select sum(try_cast(number as bigint)) from raw.figure_04
             where academic_year=? and provider_type='HE providers' and mode_of_study='All'
               and country_of_provider='All' and level_of_study in ('Postgraduate','First degree','Other undergraduate')""", y)[0][0]
    pairs.append((int(s), f4_he[y]))
recs.append(recon("Figure 4, three levels vs 'Total HE Providers'", pairs))
pairs = []
for y in YEARS:
    s = q("""select sum(try_cast(number as bigint)) from raw.figure_04
             where academic_year=? and level_of_study='Total HE Providers' and provider_type='Total HE'
               and mode_of_study='All' and country_of_provider<>'All'""", y)[0][0]
    pairs.append((int(s), f4_he[y]))
recs.append(recon("Figure 4, four countries vs UK HE total", pairs))
# fold the reconciliation results into DQ-03
for f in findings:
    if f["id"] == "DQ-03":
        f["evidence"] += "\n" + "\n".join(recs)
for t, nm in [("figure_07", "Figure 7: unique key (ukprn, level, mode, country, region, address)")]:
    n, d = q("""select count(*), count(distinct (ukprn, level_of_study, mode_of_study, country_of_he_provider,
                region_of_he_provider, permanent_address)) from raw.figure_07""")[0]
    passes.append(f"{nm}: {fmt(d)} distinct keys in {fmt(n)} rows")
n, k = q("select count(*), count(distinct ukprn) from raw.figure_07 where ukprn<>''")[0]
names = q("select count(distinct he_provider) from raw.figure_07 where ukprn<>''")[0][0]
passes.append(f"Figure 7: {fmt(k)} UKPRNs map to {fmt(names)} provider names")
for t in tables:
    if t.startswith("table_61") or t.startswith("figure"):
        pass
lic = q("select count(*), count(*) filter (where licence like 'Creative Commons Attribution 4.0%') from raw.file_meta")[0]
passes.append(f"Licence: {lic[1]} of {lic[0]} files state Creative Commons Attribution 4.0")

# ---------------------------------------------------------------- write outputs
con.execute("drop table if exists profile.findings")
con.execute("create table profile.findings(id varchar, severity varchar, area varchar, title varchar, "
            "evidence varchar, why_it_matters varchar, planned_handling varchar)")
for f in findings:
    con.execute("insert into profile.findings values (?,?,?,?,?,?,?)",
                [f["id"], f["severity"], f["area"], f["title"], f["evidence"], f["why"], f["handling"]])
con.close()

order = {"High": 0, "Medium": 1, "Low": 2}
with open(os.path.join(docs_dir, "quality_log.md"), "w") as out:
    out.write("# Data-quality log: HESA open data (stage 1)\n\n")
    out.write("Source: HESA Higher Education Student Statistics 2023/24 (Figures 1-4, 6-18) and Table 61 "
              "(2017/18 to 2021/22). Licence stated in every file: Creative Commons Attribution 4.0. "
              "Attribution: HESA.\n\n")
    out.write("Not covered: Figure 5 (not supplied). Severity is my judgement of the effect on a metric, "
              "not a HESA rating. 'Planned handling' is what stage 2 will do, not something already done.\n\n")
    out.write("| ID | Severity | Area | Finding |\n|---|---|---|---|\n")
    for f in sorted(findings, key=lambda x: (order[x["severity"]], x["id"])):
        out.write(f"| {f['id']} | {f['severity']} | {f['area']} | {f['title']} |\n")
    out.write("\n")
    for f in sorted(findings, key=lambda x: x["id"]):
        out.write(f"## {f['id']} {f['title']}\n\n**Severity:** {f['severity']} | **Area:** {f['area']}\n\n")
        out.write("**Evidence**\n\n```\n" + f["evidence"] + "\n```\n\n")
        out.write(f"**Why it matters:** {f['why']}\n\n**Planned handling:** {f['handling']}\n\n")
    out.write("## Checks that passed\n\n")
    for p in passes:
        out.write(f"- {p}\n")
print(f"{len(findings)} findings written")
for f in sorted(findings, key=lambda x: x["id"]):
    print("\n==", f["id"], f["severity"], f["title"])
    print(f["evidence"])
print("\n== PASSED")
for p in passes:
    print("-", p)

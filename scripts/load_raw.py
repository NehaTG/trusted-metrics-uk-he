"""Load raw HESA CSVs into DuckDB without changing any values.

Every data column is stored as VARCHAR in schema `raw`, so rounding markers,
percent strings and odd decimals survive exactly as published. Cleaning
happens later, in dbt. File-level facts (title, years, licence, stated
totals, last-updated) go to raw.file_meta.

Usage: python3 -I load_raw.py <raw_dir> <t61_dir> <db_path>
"""
import csv
import glob
import os
import re
import sys

import duckdb
import pandas as pd


def read_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.reader(fh))


def is_blank(row):
    return all((c or "").strip() == "" for c in row)


def split_file(rows):
    """Return (metadata dict, header list, data rows) for a HESA csv."""
    meta, i = {}, 0
    while i < len(rows) and not is_blank(rows[i]):
        k = rows[i][0].strip()
        v = rows[i][1].strip() if len(rows[i]) > 1 else ""
        meta[k] = v
        i += 1
    # HESA puts "Last updated" before OR after the first blank row, so
    # keep reading metadata until we reach a real header row.
    while i < len(rows) and (is_blank(rows[i]) or rows[i][0].strip() in
                             ("Last updated",) or rows[i][0].strip().endswith("total")):
        if not is_blank(rows[i]):
            meta[rows[i][0].strip()] = rows[i][1].strip() if len(rows[i]) > 1 else ""
        i += 1
    header = [h.strip() for h in rows[i]]
    width = len([h for h in header if h != ""])
    header = header[:width]
    data = []
    for r in rows[i + 1:]:
        if is_blank(r):
            continue
        r = (r + [""] * width)[:width]
        data.append(r)
    return meta, header, data


def slug(s):
    s = re.sub(r"[^0-9a-zA-Z]+", "_", s.strip().lower()).strip("_")
    return s or "col"


def main(raw_dir, t61_dir, db_path):
    if os.path.exists(db_path):
        os.remove(db_path)
    con = duckdb.connect(db_path)
    con.execute("create schema raw")
    con.execute("""create table raw.file_meta(
        table_name varchar, source_file varchar, title varchar, academic_years varchar,
        data_collection varchar, licence varchar, last_updated varchar,
        stated_totals varchar, data_rows bigint)""")

    jobs = []
    for p in sorted(glob.glob(os.path.join(raw_dir, "hesa_figure-*.csv"))):
        n = re.search(r"figure-(\d+)", p).group(1)
        jobs.append((f"figure_{int(n):02d}", p))
    for p in sorted(glob.glob(os.path.join(t61_dir, "table-61-*.csv"))):
        yr = re.search(r"\((\d{4})-(\d{2})\)", p)
        jobs.append((f"table_61_{yr.group(1)}_{yr.group(2)}", p))

    for name, path in jobs:
        meta, header, data = split_file(read_rows(path))
        cols = []
        seen = {}
        for h in header:
            s = slug(h)
            seen[s] = seen.get(s, 0) + 1
            cols.append(s if seen[s] == 1 else f"{s}_{seen[s]}")
        con.execute(f'create table raw."{name}" (' + ", ".join(f'"{c}" varchar' for c in cols) + ")")
        if data:
            df = pd.DataFrame(data, columns=cols, dtype=str)
            con.register("df_in", df)
            con.execute(f'insert into raw."{name}" select * from df_in')
            con.unregister("df_in")
        totals = "; ".join(f"{k}={v}" for k, v in meta.items() if k.endswith("total"))
        con.execute("insert into raw.file_meta values (?,?,?,?,?,?,?,?,?)", [
            name, os.path.basename(path), meta.get("Title", ""), meta.get("Academic years", ""),
            meta.get("Data collection", ""), meta.get("Licence", ""), meta.get("Last updated", ""),
            totals, len(data)])
        print(f"{name:22s} rows={len(data):>9,}  cols={len(cols)}")
    con.close()


if __name__ == "__main__":
    main(*sys.argv[1:4])

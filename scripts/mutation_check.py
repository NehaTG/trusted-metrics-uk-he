"""Break a COPY of the database in four known ways, to prove the dbt tests catch each one.
Usage: python3 -I mutation_check.py <source_db> <mutated_db>"""
import shutil, sys, duckdb
src, dst = sys.argv[1:3]
shutil.copy(src, dst)
con = duckdb.connect(dst)
# 1. inflate one detail count by 50 (still a multiple of 5, so only reconciliation can catch it)
con.execute("""update raw.figure_04 set number = '1428880'
  where academic_year='2023/24' and level_of_study='First degree' and provider_type='HE providers'
    and mode_of_study='Full-time' and country_of_provider='England'""")
# 2. a level label that is not in the governed mapping
con.execute("""update raw.figure_07 set level_of_study = 'First Degree'
  where ukprn = '10007160' and level_of_study = 'First degree'""")
# 3. a duplicated row
con.execute("""insert into raw.figure_09 select * from raw.figure_09
  where academic_year='2023/24' and permanent_address='Total UK' and entrant_marker='All'
    and level_of_study='All' and mode_of_study='All' and country_of_he_provider='All'""")
# 4. a count that is not rounded to 5
con.execute("""update raw.figure_16 set number = '123457'
  where academic_year='2023/24' and classification_of_first_degree='First class honours'
    and mode_of_study='All' and sex='All' and country_of_he_provider='All'""")
con.close()
print("mutated copy written")

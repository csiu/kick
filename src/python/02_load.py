import pandas as pd
import glob
import os
import argparse
import psycopg2
from sqlalchemy import create_engine


usage = """
"""

#def getargs():
#    parser = argparse.ArgumentParser(description=usage)
#    parser.add_argument('datadir', help="/dir/path to store downloaded files")
#    args = parser.parse_args()
#    return args
#
#if __name__ == '__main__':
#    args = getargs()


dbname="kick"
tblname="info"
verbose=True
data_dir = "/Users/csiu/repo/kick/data/01_data_set"

engine = create_engine(
        'postgresql://localhost:5432/{dbname}'.format(dbname=dbname))

# Connect to database
conn = psycopg2.connect(dbname=dbname)
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS {table};".format(table=tblname))
conn.commit()

# My files
data_files = glob.glob(os.path.join(data_dir, "Kick*csv"))
num_files = len(data_files)

df = pd.read_csv(data_files[0])

# Define table
sql = """CREATE TABLE {table} (
    index INTEGER,
%s);""".format(table=tblname)

sql_details = ""
for col_name,col_type in zip(df.columns, df.dtypes):
    if col_name in ["friends", "is_starred", "is_backing", "permissions"] or col_type == object:
        data_type = "VARCHAR"
    elif col_type == float:
        data_type = "FLOAT"
    elif col_type == bool:
        data_type = "BOOLEAN"
    elif col_type == int:
        data_type = "INTEGER"
    sql_details += "    {name} {type},".format(name=col_name, type=data_type) + "\n"
sql_details = sql_details.strip(",\n")

sql = sql % sql_details

cur.execute(sql)
conn.commit()


for i,data_file in enumerate(data_files):
    fname = os.path.basename(data_file)
    df = pd.read_csv(data_file)
    try:
        msg = "Processing {i} of {num_files}: {fname}".format(
                i=i+1, num_files=num_files, fname=fname)
        print(msg)
        df.to_sql(tblname, engine, if_exists="append")
    except:
        msg = "ERROR {i} of {num_files}: {fname}".format(
                i=i+1, num_files=num_files, fname=fname)
        print(msg)
        df.to_sql(tblname + str(i+1), engine, if_exists="append")

# Close communication with the database
cur.close()
conn.close()

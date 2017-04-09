import pandas as pd
import glob
import os
import argparse
import psycopg2
from sqlalchemy import create_engine

usage = """
"""

def getargs():
    parser = argparse.ArgumentParser(description=usage)
    parser.add_argument('datadir', help="/dir/path to store downloaded files")
    parser.add_argument('-v', '--verbose', default=True)
    parser.add_argument('-r', '--remake', default=True, help="Remake table")
    args = parser.parse_args()
    return args

def load_data(data_files, dbname="kick", tblname="info",
              remake_table=True, verbose=True):
    # Initialization
    engine = create_engine(
            'postgresql://localhost:5432/{dbname}'.format(dbname=dbname))
    create_table = False

    # Connect to database
    conn = psycopg2.connect(dbname=dbname)
    cur = conn.cursor()

    if remake_table:
        # Remove table before it gets created
        cur.execute("DROP TABLE IF EXISTS {table};".format(table=tblname))
        conn.commit()
        create_table = True

    if create_table:
        sql = """CREATE TABLE {table} (
            index INTEGER,
        %s);""".format(table=tblname)
        sql_details = ""
        df = pd.read_csv(data_files[0])
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

        cur.execute(sql % sql_details)
        conn.commit()

    # Insert data
    num_files = len(data_files)
    for i,data_file in enumerate(data_files):
        fname = os.path.basename(data_file)
        df = pd.read_csv(data_file)
        try:
            msg = "Processing {i} of {num_files}: {fname}".format(
                    i=i+1, num_files=num_files, fname=fname)
            if verbose: print(msg)
            df.to_sql(tblname, engine, if_exists="append")
        except:
            msg = "ERROR {i} of {num_files}: {fname}".format(
                    i=i+1, num_files=num_files, fname=fname)
            if verbose: print(msg)
            df.to_sql(tblname + str(i+1), engine, if_exists="append")

    # Close communication with the database
    cur.close()
    conn.close()

if __name__ == '__main__':
    args = getargs()

    data_dir = args.datadir
    verbose = args.verbose
    remake_table = args.remake

    data_files = glob.glob(os.path.join(data_dir, "Kick*csv"))
    load_data(data_files, dbname="kick", tblname="info",
              remake_table=remake_table, verbose=verbose)

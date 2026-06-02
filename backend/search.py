import sqlite3
import pandas as pd

DB_PATH = "data/agroconnect.db"

def search_product(product, district=""):

    conn = sqlite3.connect(DB_PATH)

    query = f"""
    SELECT * FROM inventory
    WHERE Product LIKE '%{product}%'
    """

    if district:
        query += f" AND District LIKE '%{district}%'"

    df = pd.read_sql(query, conn)

    conn.close()

    return df.to_dict(orient="records")
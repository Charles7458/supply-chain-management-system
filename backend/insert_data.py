import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

def load_csv(file, table):
    df = pd.read_csv(file)
    df.to_sql(table, engine, if_exists="append", index=False)
    print(f"{table} loaded")

load_csv("products.csv", "products")
load_csv("warehouses.csv", "warehouses")
load_csv("inventory.csv", "inventory")
load_csv("sales_history.csv", "sales_history")


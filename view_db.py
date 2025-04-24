from sqlalchemy import create_engine, inspect
import pandas as pd

engine = create_engine('sqlite:///./restaurant_monitoring.db')

inspector = inspect(engine)
tables = inspector.get_table_names()

for table in tables:
    print(f"\nContents of {table} table:")
    query = f"SELECT * FROM {table} LIMIT 5"
    df = pd.read_sql_query(query, engine)
    print(df)
    print(f"Total rows: {len(df)}") 
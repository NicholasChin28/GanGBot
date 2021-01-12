import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

engine = psycopg2.connect(
    database=os.getenv('RDS_DB_NAME'),
    user=os.getenv('RDS_USERNAME'),
    password=os.getenv('RDS_PASSWORD'),
    host=os.getenv('RDS_HOSTNAME'),
    port=os.getenv('RDS_PORT'),
)

cur = engine.cursor()
# List all the tables in the database


# List the fields of a table (vote table)
# cur.execute("drop table vote, guild")
# engine.commit()
# result = cur.fetchone()
# print('Result of drop query: ', result)
# colnames = [desc[0] for desc in cur.description]
# print('Column names: ', colnames)

cur.execute("""SELECT table_name FROM information_schema.tables
       WHERE table_schema = 'public'""")
rows = cur.fetchall()

for row in rows:
    print('Table name: ', row)
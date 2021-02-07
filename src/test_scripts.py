import psycopg2
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

engine = psycopg2.connect(
    database=os.getenv('RDS_DB'),
    user=os.getenv('RDS_USER'),
    password=os.getenv('RDS_PASSWORD'),
    host=os.getenv('RDS_HOST'),
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

'''
cur.execute("""SELECT table_name FROM information_schema.tables
       WHERE table_schema = 'public'""")
rows = cur.fetchall()

for row in rows:
    print("Table name: ", row)
'''

# Select all rows from the 'vote' table
'''
cur.execute(""" SELECT * FROM vote""")
rows = cur.fetchall()

for row in rows:
    print("Row value: ", row)
'''

some_queue = asyncio.Queue()
some_queue.insert(0, 'test')

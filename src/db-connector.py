# To connect with PostgreSQL
# For bot voting feature
import psycopg2
from dotenv import load_dotenv
import os
from tortoise import Tortoise, run_async
# from src.Data.db_context import Models

# Load environment variables
load_dotenv()

# Initialise models and database
"""
async def init():
    await Tortoise.init(
        db_url=f'postgres://{os.getenv("RDS_USERNAME")}:{os.getenv("RDS_PASSWORD")}@{os.getenv("RDS_HOSTNAME")}:{os.getenv("RDS_PORT")}/{os.getenv("RDS_DB_NAME")}',
        modules={'models': ['src.data.db_context', 'aerich.models']}
    )
    # Generate the schema
    await Tortoise.generate_schemas(safe=True)
    
    # Close connection after complete
    await Tortoise.close_connections()

run_async(init())
"""









"""
engine = psycopg2.connect(
    database=os.getenv('RDS_DB_NAME'),
    user=os.getenv('RDS_USERNAME'),
    password=os.getenv('RDS_PASSWORD'),
    host=os.getenv('RDS_HOSTNAME'),
    port=os.getenv('RDS_PORT'),
)
"""
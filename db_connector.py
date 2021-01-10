# To connect with PostgreSQL
# For bot voting feature
import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

engine = psycopg2.connect(
    database=os.getenv('RDS_DB_NAME'),
    user=os.getenv('RDS_USERNAME'),
    password='0G4qnNaBMVUQaF7CRnou',
    host='django-cdn.ciltalo9wqxl.ap-southeast-1.rds.amazonaws.com',
    port='5432'
)
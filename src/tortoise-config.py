# Configuration file for Tortoise-ORM
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

'''
TORTOISE_ORM = {
    "connections": {"default": f'postgres://{os.getenv("RDS_USERNAME")}:{os.getenv("RDS_PASSWORD")}@{os.getenv("RDS_HOSTNAME")}:{os.getenv("RDS_PORT")}/{os.getenv("RDS_DB_NAME")}'},
    "apps": {
        "models": {
            "models": ["src.data.db_context", "aerich.models"],
            "default_connection": "default",
        },
    },
}
'''

TORTOISE_ORM = {
    'connections': {
        # Dict format for connection
        'default': {
            'engine': 'tortoise.backends.asyncpg',
            'credentials': {
                'host': os.getenv('RDS_HOST'),
                'port': os.getenv('RDS_PORT'),
                'user': os.getenv('RDS_USER'),
                'password': os.getenv('RDS_PASSWORD'),
                'database': os.getenv('RDS_DB'),
            }
        },
    },
    'apps': {
        'models': {
            'models': ['data.db_context', 'aerich.models'],
            'default_connection': 'default',
        }
    },
}
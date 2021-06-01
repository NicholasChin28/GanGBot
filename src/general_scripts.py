from botocore.exceptions import ClientError
import psycopg2
from dotenv import load_dotenv
import os
import asyncio
import time
import pathlib
import boto3
import botocore

load_dotenv()

'''
engine = psycopg2.connect(
    database=os.getenv('RDS_DB'),
    user=os.getenv('RDS_USER'),
    password=os.getenv('RDS_PASSWORD'),
    host=os.getenv('RDS_HOST'),
    port=os.getenv('RDS_PORT'),
)

cur = engine.cursor()
'''
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
class VideoRange:
    _start_time = None
    _end_time = None

    @property
    def start_time(self):
        return self._start_time

    @property
    def end_time(self):
        return self._end_time

    def __init__(self, start_time=0, end_time=None) -> None:
        self._start_time = start_time
        self._end_time = end_time

# Checks if string is a valid time format
# Returns None if timestamp is not a valid time format
def validate_time(timestamp):
    time_formats = ['%M:%S', '%H:%M:%S']
    for format in time_formats:
        try:
            print('validate_time called')
            valid_timestamp = time.strptime(timestamp, format)
            return valid_timestamp
        except ValueError:
            pass

def test_parse_time(timestamp):
    # Check if the timestamp is a timestamp range or a single starting timestamp
    time_ranges = None
    if '-' in timestamp:
        time_ranges = timestamp.split('-')

    """
    if len(time_ranges) != 2:
        pass
    """

    time_formats = ['%M:%S', '%H:%M:%S']
    time_range = None
    for format in time_formats:
        try:
            print('parse_time called')
            time_range = time.strptime(timestamp, format)
            break
        except ValueError:
            pass

    return time_range

def parse_time(timestamp):
    time_ranges = timestamp.split('-')  # Split time range
    struct_time_range = []

    if len(time_ranges) == 1:   # Invalid time range length sent
        for i in time_ranges:
            if validate_time(i) is not None:
                struct_time_range.append(validate_time(i))
        
        return VideoRange(start_time=struct_time_range[0])
    elif len(time_ranges) == 2:
        for i in time_ranges:
            if validate_time(i) is not None:
                struct_time_range.append(validate_time(i))

        if len(struct_time_range) != 2: # One of the range format is invalid
            return VideoRange()

        # Compare the first and second time ranges
        # The second range which is the end time must be greater than the first range
        if not struct_time_range[-1] > struct_time_range[0]:    # End time is before the start time
            return VideoRange() 

        return VideoRange(start_time=struct_time_range[0], end_time=struct_time_range[-1])
    else:
        return VideoRange()
    
    
    
    """
    time_formats = ['%M:%S', '%H:%M:%S']
    struct_time_range = []
    # Check if each time ranges are valid time formats
    for format in time_formats:
        for range in time_ranges:
            try:
                print('parse_time called')
                struct_time_range = time.strptime(range, format)
                break
            except ValueError:
                pass
    """
    
    # return VideoRange()


            
    
# Test S3 connection
def create_s3_connection():
    print('Creating AWS S3 connection...')
    s3 = boto3.resource(
        service_name='s3',
        region_name='ap-southeast-1',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )

    # Check if credentials and permissions are correct
    try:
        for _ in s3.buckets.all():
            pass
    except ClientError as e:
        print(f'Client error: {e}')
        return None

    print('AWS S3 connection established')

    # Test code here
    bucket_name = os.getenv('AWS_BUCKET')
    playsound_bucket = s3.Bucket(bucket_name)
    exists = True

    # Check if bucket exist. V2
    try:
        s3.meta.client.head_bucket(Bucket=bucket_name)
    except ClientError as e:
        # If a client error is thrown, then check that it was a 404 error.
        # If it was a 404 error, then the bucket does not exist.
        error_code = e.response['Error']['Code']
        if error_code == '403':
            print('Private bucket. Forbidden Access!')
        elif error_code == '404':
            exists = False
            print('Bucket does not exist')

    

    # Check if bucket exists. V1
    """
    if playsound_bucket.creation_date:
        print("The bucket exists")
    else:
        print('Bucket does not exist. Creating bucket...')
        # Create the bucket
        s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={
            'LocationConstraint': 'ap-southeast-1'
        })
        print('Bucket created...')
    """

    return s3

# Check if bucket exists
def check_bucket():
    bucket_name = os.getenv('AWS_BUCKET')
    playsound_bucket = s3.Bucket(bucket_name)
    exists = True

    # Check if bucket exist. V2
    try:
        s3.meta.client.head_bucket(Bucket=bucket_name)
    except ClientError as e:
        # If a client error is thrown, then check that it was a 404 error.
        # If it was a 404 error, then the bucket does not exist.
        error_code = e.response['Error']['Code']
        if error_code == '403':
            print('Private bucket. Forbidden Access!')
        elif error_code == '404':
            exists = False
            print('Bucket does not exist')

# Create the bucket if it does not exist
def create_bucket():
    s3 = create_s3_connection()
    if s3 is not None:
        return 

class S3Connection:
    def __init__(self):
        s3 = self.create_s3_connection2()

    def create_s3_connection2(self):
        print('Creating AWS S3 connection...')
        s3 = boto3.resource(
            service_name='s3',
            region_name='ap-southeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )

        # Check if credentials and permissions are correct
        try:
            for _ in s3.buckets.all():
                pass
        except ClientError as e:
            print(f'Client error: {e}')
            return None

        print('AWS S3 connection established')

        return s3

    # Check if bucket exists
    def check_bucket(self):
        bucket_name = os.getenv('AWS_BUCKET')
        playsound_bucket = self.s3.Bucket(bucket_name)
        exists = True

        # Check if bucket exist. V2
        try:
            self.s3.meta.client.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            # If a client error is thrown, then check that it was a 404 error.
            # If it was a 404 error, then the bucket does not exist.
            error_code = e.response['Error']['Code']
            if error_code == '403':
                print('Private bucket. Forbidden Access!')
            elif error_code == '404':
                exists = False
                print('Bucket does not exist')


create_s3_connection()

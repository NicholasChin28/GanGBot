from botocore.exceptions import ClientError
import psycopg2
from dotenv import load_dotenv
import os
import asyncio
import time
import pathlib
import boto3
import botocore
import re
import json
from pydub import AudioSegment

load_dotenv()
    
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

# Class that is in use
class S3Connection:

    def __init__(self):
        self.s3 = self.create_s3_connection2()
        self.playsounds_bucket = os.getenv('AWS_BUCKET')
        self.s3_bucket = self.get_bucket()

    async def create_s3_connection2(self):
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

    # Get playsound bucket
    async def get_bucket(self):
        exists = True

        # Check if bucket exist. V2
        try:
            self.s3.meta.client.head_bucket(Bucket=self.playsounds_bucket)
            return self.s3.Bucket(self.playsounds_bucket)
        except ClientError as e:
            # If a client error is thrown, then check that it was a 404 error.
            # If it was a 404 error, then the bucket does not exist.
            error_code = e.response['Error']['Code']
            if error_code == '403':
                print('Private bucket. Forbidden Access!')
            elif error_code == '404':
                exists = False
                print('Bucket does not exist')
                print('Creating bucket...')
                await create_bucket()
                return self.s3.Bucket(self.playsounds_bucket)

        return None

    # Check if file exists in bucket
    async def check_file(self, filename):
        try:
            self.s3.Object(self.playsounds_bucket, filename).load()
        except ClientError as e:
            return int(e.response['Error']['Code']) != 404
        return True

    # Downloads file from bucket
    async def download_file(self, filename, exists):
        try:
            self.s3_bucket.download_file(filename, filename)
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                print("The object does not exist")

    # Uploads file to bucket
    async def upload_files(self, files):
        file_uploads = []
        for file in files:
            try:
                self.s3_bucket.upload_file(file, file)
                file_uploads.add(S3File(file, '200'))
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    print("Bucket does not exist. Called from upload_file")
                elif e.response['Error']['Code'] == '403':
                    print("Insufficient permissions to upload file")
                file_uploads.add(S3File(file, e.response['Code']))
            
        return file_uploads # Returns status of each file upload

    
        
    # Create bucket
    async def create_bucket(self):
        await self.s3.create_bucket(Bucket=self.playsounds_bucket, CreateBucketConfiguration={
            'LocationConstraint': 'ap-southeast-1'
        })
        print('Bucket created...')
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
# Represents a file from AWS S3 bucket
class S3File:
    def __init__(self, name, status) -> None:
        self._name = name
        self._status = status

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        self._status = status


# create_s3_connection()

# Test re.search()
"""
to_search = ["<Attachment id=852447641166020618 filename='sample-15s.mp3' url='https://cdn.discordapp.com/attachments/694753759091359825/852447641166020618/sample-15s.mp3'>"]
temp_val = json.dumps(to_search)
print(f'temp_val: {temp_val}')
"""



# Test slicing audio file with pydub
song = AudioSegment.from_mp3("random.mp3")

ten_seconds = 10 * 1000
first_10_seconds = song[:ten_seconds]

# song.export("edited_mashup.mp3", format="mp3")
first_10_seconds.export("edited_mashup.mp3", format="mp3")
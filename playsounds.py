# Storing and retrieving playsounds from AWS S3 bucket
# Reference material: https://www.gormanalysis.com/blog/connecting-to-aws-s3-with-python/   
import boto3
from dotenv import load_dotenv
import os

load_dotenv()

s3_resource = boto3.resource(
    service_name = 's3',
    region_name = 'ap-southeast-1',
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
)

for bucket in s3_resource.buckets.all():
    print(bucket.name)

# Upload sample file
# s3_resource.Bucket('discord-playsounds').upload_file(Filename='sqlite_db.py', Key='to_download.txt')

for obj in s3_resource.Bucket('discord-playsounds').objects.all():
    print(obj)

# Download file
# s3_resource.Bucket('discord-playsounds').download_file(Key='to_download.txt', Filename='to_download.txt')

'''
playsound_bucket = s3_resource.Bucket(name='discord-playsounds')

# Uploading file
s3_resource.Object(playsound_bucket, 'bot2.py').upload_file(
    Filename='bot2.py'
)
'''
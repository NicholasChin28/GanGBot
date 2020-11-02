# Storing and retrieving playsounds from AWS S3 bucket
# Reference material: https://www.gormanalysis.com/blog/connecting-to-aws-s3-with-python/   
import boto3
from dotenv import load_dotenv
import os
from pathlib import Path
from mutagen.mp3 import MP3

load_dotenv()

# TODO: Compare local files with AWS S3 Bucket. Only upload files that are different / new

# Checks if the file is a valid playsound
def get_valid_playsounds(filenames):
    '''
    Valid playsound criteria:
    Duration: <= 15 seconds
    File type: .mp3
    '''
    playsounds = []
    for item in filenames:
        print('Item value: ', item)
        playsound = MP3(item)
        if playsound.info.length <= 15:
            playsounds.append(item.name)

    return playsounds

def create_s3_connection():
    s3_resource = boto3.resource(
        service_name = 's3',
        region_name = 'ap-southeast-1',
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    return s3_resource

# Alternate method
def is_valid_playsound(filename):
    playsound = MP3(filename)
    if playsound.info.length <= 15:
        return filename

'''
for item in s3_resource.Bucket('discord-playsounds').objects.all():
    print(item.key)
'''

# Upload playsound files from ~/playsounds
def upload_playsounds():
    # Check if valid playsound
    p = Path('playsounds')
    valid_playsounds = [x for x in p.glob('*.mp3') if is_valid_playsound(x) is not None]
    # valid_playsounds = get_valid_playsounds(file_sounds)

    for valid in valid_playsounds:
        print('valid values: ', valid)
        # print('valid values name: ', valid.name)

    s3 = create_s3_connection()

    for item in valid_playsounds:
        s3.Bucket('discord-playsounds').upload_file(Filename=str(item), Key=item.name)

upload_playsounds()

    

# playsounds_storage = s3_resource.Bucket('discord-playsounds')



'''
obj = s3_resource.Object(bucket_name='discord-playsounds', key='bot2.py')
print(obj.bucket_name)
print(obj.key)
'''




'''
for bucket in s3_resource.buckets.all():
    print(bucket.name)

# Upload sample file
# s3_resource.Bucket('discord-playsounds').upload_file(Filename='sqlite_db.py', Key='to_download.txt')

for obj in s3_resource.Bucket('discord-playsounds').objects.all():
    print(obj)

# Download file
# s3_resource.Bucket('discord-playsounds').download_file(Key='to_download.txt', Filename='to_download.txt')

def s3_connection():
    try:
        s3_resource

def get_playsounds():
'''

'''
playsound_bucket = s3_resource.Bucket(name='discord-playsounds')

# Uploading file
s3_resource.Object(playsound_bucket, 'bot2.py').upload_file(
    Filename='bot2.py'
)
'''
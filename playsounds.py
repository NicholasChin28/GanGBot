# Storing and retrieving playsounds from AWS S3 bucket
# Reference material: https://www.gormanalysis.com/blog/connecting-to-aws-s3-with-python/   
import boto3
from dotenv import load_dotenv
import os
from pathlib import Path
from mutagen.mp3 import MP3

load_dotenv()

# TODO: Compare local files with AWS S3 Bucket. Only upload files that are different / new
# May be possible to use e_tag to compare local files and S3 files
# Possible reference: https://stackoverflow.com/questions/1775816/how-to-get-the-md5sum-of-a-file-on-amazons-s3
# Possible reference: https://stackoverflow.com/questions/14591926/how-to-compare-local-file-with-amazon-s3-file

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
    print('Creating AWS S3 connection...')
    s3_resource = boto3.resource(
        service_name = 's3',
        region_name = 'ap-southeast-1',
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    print('AWS S3 connection established')
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

# TODO: Refactor function to store all the downloaded playsounds as the "Master" list
def store_playsounds():
    # Check if valid playsound
    p = Path('playsounds')
    valid_playsounds = [x for x in p.glob('*.mp3') if is_valid_playsound(x) is not None]
    print('valid_playsounds: ', valid_playsounds)
    # valid_playsounds = get_valid_playsounds(file_sounds)

    for valid in valid_playsounds:
        print('valid values: ', valid)
        # print('valid values name: ', valid.name)

    print('Creating AWS S3 connection')
    s3 = create_s3_connection()

    for item in valid_playsounds:
        print('Uploading file...')
        s3.Bucket('discord-playsounds').upload_file(Filename=str(item), Key=item.name)
        print('File uploaded...')

# Downloads playsounds from AWS S3 bucket
# Version 1.0: Downloads playsounds based on S3 Object key
# TODO: Compare checksum of files and download only differing files
def download_playsounds():
    # Creating download folder
    p = Path('download_sounds')
    p.mkdir(parents=True, exist_ok=True)

    s3 = create_s3_connection()
    playsound_bucket = s3.Bucket('discord-playsounds')
 
    for obj in playsound_bucket.objects.all():
        print('Getting S3 file...')
        playsound_bucket.download_file(Key=obj.key, Filename=(p / obj.key).__str__())
        print('S3 file downloaded')

# Upload playsound files from ~/upload_sounds
def upload_playsounds2():
    # Check if valid playsound
    p = Path('upload_sounds')

    valid_playsounds = [x for x in p.glob('*.mp3') if is_valid_playsound(x) is not None]
    print('valid_playsounds: ', valid_playsounds)
    # valid_playsounds = get_valid_playsounds(file_sounds)

    for valid in valid_playsounds:
        print('valid values: ', valid)
        # print('valid values name: ', valid.name)

    print('Creating AWS S3 connection')
    s3 = create_s3_connection()

    for item in valid_playsounds:
        print('Uploading file...')
        s3.Bucket('discord-playsounds').upload_file(Filename=str(item), Key=item.name)
        print('File uploaded...')
    

upload_playsounds2()
# download_playsounds()
# upload_playsounds()

    

# playsounds_storage = s3_resource.Bucket('discord-playsounds')








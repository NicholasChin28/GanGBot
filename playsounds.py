# Storing and retrieving playsounds from AWS S3 bucket
# Reference material: https://www.gormanalysis.com/blog/connecting-to-aws-s3-with-python/   
import boto3
from dotenv import load_dotenv
import os
from pathlib import Path
from mutagen.mp3 import MP3
import hashlib

load_dotenv()

# TODO: Getting the MD5 from Etag of AWS S3 objects will not be the same if the files are multi part uploaded
# Find a way of possibly getting MD5 checksum regardless of multipart uploaded or individually uploaded
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
def upload_playsounds():
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

    # TODO: Compare hash
    s3_objects = s3.Bucket('discord-playsounds').objects.all()
    


    for item in valid_playsounds:
        print('Uploading file...')
        s3.Bucket('discord-playsounds').upload_file(Filename=str(item), Key=item.name)
        print('File uploaded...')

# Downloads playsounds from AWS S3 bucket
def download_playsounds():
    # Creating download folder
    p = Path('download_sounds')
    p.mkdir(parents=True, exist_ok=True)

    local_file_checksum = get_files_hash()

    print('local_file_checksum: ', local_file_checksum[0][0])

    s3 = create_s3_connection()
    playsound_bucket = s3.Bucket(os.getenv('AWS_BUCKET'))
    
    for obj in playsound_bucket.objects.all():
        print('Getting S3 file...')
        print('Filename of file', obj.key)
        print(f'MD5 checksum of file: {obj.e_tag}, type: {type(obj.e_tag)}, char at index 0: {obj.e_tag[0]}')

        if obj.e_tag.replace('"', '') not in local_file_checksum:                   # Remove " character from obj.e_tag
            playsound_bucket.download_file(Key=obj.key, Filename=(p / obj.key).__str__())
            print('S3 file downloaded')
        else:
            print('File already exists... skipping file')

# Get all the hashes of the files in local folder
def get_files_hash():
    hashes = []
    p = Path('playsounds').glob('**/*')
    files = [x for x in p if x.is_file()]
    for x in files:
        hash_md5 = hashlib.md5()
        with open(x, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_md5.update(chunk)
        hashes.append(hash_md5.hexdigest())

    return hashes

# TODO: Helper function
# Get all objects in a bucket
def get_bucket_objects():
    print('Creating AWS S3 connection')
    s3 = create_s3_connection()

    playsound_bucket = s3.Bucket(os.getenv('AWS_BUCKET'))


# get_files_hash()
# upload_playsounds2()
download_playsounds()
# upload_playsounds()

    










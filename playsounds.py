# Storing and retrieving playsounds from AWS S3 bucket
# Reference material: https://www.gormanalysis.com/blog/connecting-to-aws-s3-with-python/   
import boto3
from dotenv import load_dotenv
import os
from pathlib import Path
from mutagen.mp3 import MP3
import hashlib

load_dotenv()

# TODO: Allow for audio file formats other than .mp3
# TODO: Getting the MD5 from Etag of AWS S3 objects will not be the same if the files are multi part uploaded
# Find a way of possibly getting MD5 checksum regardless of multipart uploaded or individually uploaded
# Possible reference: https://stackoverflow.com/questions/1775816/how-to-get-the-md5sum-of-a-file-on-amazons-s3
# Possible reference: https://stackoverflow.com/questions/14591926/how-to-compare-local-file-with-amazon-s3-file

import discord
from discord.ext import commands
from discord.utils import get

# TODO: Create Playsound Cog
class Playsound(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def _addsound(self, ctx):
        await ctx.send('addsound function')

# Testing cog
'''
class Greetings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._last_member = None

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.system_channel
        if channel is not None:
            await channel.send('Welcome {0.mention}.'.format(member))

    @commands.command()
    async def hello(self, ctx, *, member: discord.Member = None):
        """ Says hello """
        member = member or ctx.author
        if self._last_member is None or self._last_member.id != member.id:
            await ctx.send('Hello {0.name}~'.format(member))
        else:
            await ctx.send('Hello {0.name}... This feels familiar'.format(member))
        self._last_member = member
'''



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

def upload_playsounds():
    # Check if valid playsound
    valid_playsounds = get_valid_playsounds()
    print('valid_playsounds: ', valid_playsounds)

    for valid in valid_playsounds:
        print('valid values: ', valid)

    s3_bucket = get_bucket()
    s3_objects = s3_bucket.objects.all()
    s3_hashes = [obj.e_tag.replace('"', '') for obj in s3_objects]

    for d in valid_playsounds:
        local_hash = d['hexdigest']
        if local_hash not in s3_hashes:
            print('local_name: ', d['name'])
            print('filename: ', d['name'].name)
            print('Uploading file...')
            s3_bucket.upload_file(Filename=str(d['name']), Key=d['name'].name)
            print('File uploaded') 
        else:
            print('File exists.. skipping')


# Downloads playsounds from AWS S3 bucket
def download_playsounds():
    # Creating download folder
    p = Path('playsounds')
    p.mkdir(parents=True, exist_ok=True)

    local_file_checksum = get_valid_playsounds()

    if local_file_checksum:
        print('local_file_checksum: ', local_file_checksum)

    s3_bucket = get_bucket()
    s3_objects = s3_bucket.objects.all()
    
    for obj in s3_objects:
        print('Getting S3 file...')
        print('Filename of file', obj.key)
        print(f'MD5 checksum of file: {obj.e_tag}, type: {type(obj.e_tag)}, char at index 0: {obj.e_tag[0]}')
        if obj.e_tag.replace('"', '') not in [d['hexdigest'] for d in local_file_checksum]: # Remove " character from obj.e_tag
            s3_bucket.download_file(Key=obj.key, Filename=(p / obj.key).__str__())
            print('S3 file downloaded')
        else:
            print('File already exists... skipping file')

def get_valid_playsounds():
    '''
    Valid playsound criteria:
    Duration: <= 15 seconds
    File type: .mp3
    '''
    hashes = []
    p = Path('playsounds').glob('**/*.mp3')

    files = [x for x in p if MP3(x).info.length <= 15]

    for x in files:
        hash_md5 = hashlib.md5()
        with open(x, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_md5.update(chunk)
        hashes.append({"name": x, "hexdigest": hash_md5.hexdigest()})

    return hashes
    # print(hashes)

# Get all objects in a bucket
def get_bucket():
    print('Creating AWS S3 connection')
    s3 = create_s3_connection()

    playsound_bucket = s3.Bucket(os.getenv('AWS_BUCKET'))
    return playsound_bucket

# get_valid_playsounds()
# upload_playsounds2()
# download_playsounds()
# upload_playsounds()

    










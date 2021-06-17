# Storing and retrieving playsounds from AWS S3 bucket
# Reference material: https://www.gormanalysis.com/blog/connecting-to-aws-s3-with-python/   
# TODO: Add file watcher
import typing
import boto3
from dotenv import load_dotenv
import os
from pathlib import Path
import mutagen
import hashlib
import asyncio
import functools
import discord
from discord.ext import commands
from botocore.exceptions import ClientError
from aiohttp import ClientSession
import aiofiles
import humanfriendly
from mutagen.apev2 import delete
from pydub import AudioSegment

load_dotenv()

# TODO: Getting the MD5 from Etag of AWS S3 objects will not be the same if the files are multi part uploaded
# Find a way of possibly getting MD5 checksum regardless of multipart uploaded or individually uploaded
# Possible reference: https://stackoverflow.com/questions/1775816/how-to-get-the-md5sum-of-a-file-on-amazons-s3
# Possible reference: https://stackoverflow.com/questions/14591926/how-to-compare-local-file-with-amazon-s3-file

# Non existent playsound file error
class SoundError(Exception):
    pass


class PlaysoundSource(discord.PCMVolumeTransformer):
    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.duration = self.parse_duration(data.get('duration'))
        self.title = data.get('title')
        
    def __str__(self):
        return 'PlaysoundSource class __str__ function'

    @classmethod
    async def get_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()

        # partial = functools.partial(cls.extract_info, search)
        partial = functools.partial(PlaysoundSource.extract_info, search)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise SoundError('Playsound does not exist')

        location = Path(f"{os.getenv('APP_PATH')}/playsounds/{search}.mp3")
        return cls(ctx, discord.FFmpegPCMAudio(location), data = data)

    # TODO: Get metadata of local sound files to display in queue function
    @staticmethod
    def extract_info(search: str):
        location = Path(f"{os.getenv('APP_PATH')}/playsounds/{search}.mp3")
        if location.is_file():
            details = {}
            playsound = mutagen.File(location)

            details['duration'] = int(playsound.info.length)
            details['title'] = search
            
            return details
        else:
            return details

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append('{} days'.format(days))
        if hours > 0:
            duration.append('{} hours'.format(hours))
        if minutes > 0:
            duration.append('{} minutes'.format(minutes))
        if seconds > 0:
            duration.append('{} seconds'.format(seconds))

        return ', '.join(duration)

# Custom added class to play local .mp3 files as a soundboard
class Sound:
    __slots__ = ('source', 'requester')

    def __init__(self, source: PlaysoundSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        embed = (discord.Embed(title='Now playing',
                                description='```css\n{0.source.title}\n```'.format(self),
                                color=discord.Color.blurple())
                .add_field(name='Duration', value=self.source.duration)
                .add_field(name='Requested by', value=self.requester.mention))

        return embed

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

class Playsound(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        """
        self.s3 = self.create_s3_connection()
        self.playsound_bucket = os.getenv('AWS_BUCKET')
        self.s3_bucket = self.get_bucket()
        self.bucket_objects = self.get_bucket_objects()
        """
        self.s3 = None
        self.playsound_bucket = None
        self.s3_bucket = None
        self.bucket_objects = None

        # self.playsound_folder = Path(__file__).parent.absolute() / 'random2.mp3'
        self.playsound_folder = Path(__file__).parents[1].absolute() / 'playsounds'

    @commands.Cog.listener()
    async def on_ready(self):
        print('Playsound cog loaded!')

        """
        self.s3 = await self.create_s3_connection()
        self.playsound_bucket = os.getenv('AWS_BUCKET')
        self.s3_bucket = await self.get_bucket()
        self.bucket_objects = await self.get_bucket_objects()
        print('Initialized variables')

        print(f'Val of: {self.s3}')
        print(f'Val of: {self.playsound_bucket}')
        print(f'Val of: {self.s3_bucket}')
        print(f'Val of: {self.bucket_objects}')
        await self.download_playsounds()
        """

    async def create_s3_connection(self):
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

    @commands.command(name='listsounds')
    async def _listsounds(self, ctx: commands.Context, *, page: int = 1):
        """ Get list of playsounds """
        p = Path(f"{os.getenv('APP_PATH')}/playsounds")
        file_sounds = [os.path.splitext(x.name)[0] for x in p.glob('*.mp3')]

        # If no playsounds
        if len(file_sounds) == 0:
            return await ctx.send("No playsounds found")
        else:
            limit = 10      # Playsounds per page
            embeds = []
            playsounds = ''
            
            # Create an embeds from the file_sounds and store in a dictionary.
            # Each item will contain {limit} playsounds.
            for i, sounds in enumerate(file_sounds[0:], start=1):
                
                if i % limit == 0:
                    playsounds += '`{0}.` `{1}`\n'.format(i, sounds)
                    embeds.append(playsounds)
                    playsounds = ''
                else:
                    playsounds += '`{0}.` `{1}`\n'.format(i, sounds)
                    if i == len(file_sounds):
                        embeds.append(playsounds)
                
            pages = len(embeds)  # Total pages

            embed = (discord.Embed(description='**{} sounds:**\n\n{}'.format(len(file_sounds), embeds[page - 1]))
                    .set_footer(text='Viewing page {}/{}'.format(page, pages)))
            message = await ctx.send(embed=embed)

            # Create reactions based on the number of pages
            async def add_page_reactions():
                if page == pages:
                    pass    # Only 1 page. No reactions required
                if page > 1:
                    await message.add_reaction('\u25c0')
                if pages > page:
                    await message.add_reaction('\u25b6')
            
            await add_page_reactions()

            # Recreates the embed
            async def refresh_embed():
                await message.clear_reactions()
                embed = (discord.Embed(description='**{} sounds:**\n\n{}'.format(len(file_sounds), embeds[page - 1]))
                    .set_footer(text='Viewing page {}/{}'.format(page, pages)))

                await message.edit(embed=embed)
                await add_page_reactions()

            # Check for reaction
            def check(reaction, user):
                return not user.bot and reaction.message.id == message.id and (reaction.emoji in ['\u25c0', '\u25b6'])

            while True:
                try:
                    # reaction, _ = await bot.wait_for('reaction_add', timeout=60, check=check)
                    reaction, _ = await ctx.bot.wait_for('reaction_add', timeout=60, check=check)
                except asyncio.TimeoutError:
                    await message.delete()
                    break
                else:
                    if reaction.emoji == '\u25c0':
                        page -= 1
                        await refresh_embed()
                    elif reaction.emoji == '\u25b6':
                        page += 1
                        await refresh_embed()

    # Additional command to play local .mp3 files for soundboard
    @commands.command(name='ps')
    async def _playsound(self, ctx: commands.Context, *, search: str):
        """Plays a custom playsound"""
        parent_cog = ctx.bot.get_cog('Music')
        cur_voice_state = parent_cog.get_voice_state(ctx)
        ctx.voice_state = cur_voice_state
        if not cur_voice_state.voice:
            await ctx.bot.get_command('join').callback(self, ctx)

        async with ctx.typing():
            try:
                source = await PlaysoundSource.get_source(ctx, search, loop=self.bot.loop)
            except SoundError as e:
                await ctx.send(e)
            else:
                sound = Sound(source)

                await cur_voice_state.songs.put(sound)
                await ctx.send('Enqueued a playsound')

    # Request playsound to be added 
    # TODO: Add this feature
    """
    @commands.command(name='addsound')
    async def _addsound(self, ctx: commands.Context):
        if ctx.message.reference is not None and not ctx.message.is_system:
            return await ctx.send('Called from a message reply')
        return await ctx.send('Addsound returned false')

    async def create_s3_connection(self):
        print('Creating AWS S3 connection...')
        s3_resource = boto3.resource(
            service_name='s3',
            region_name='ap-southeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        print('AWS S3 connection established')
        return s3_resource
    """

    # Downloads playsounds from AWS S3 bucket
    async def download_playsounds(self):
        # Creating download folder
        p = Path('playsounds')
        p.mkdir(parents=True, exist_ok=True)

        local_file_checksum = await self.get_valid_playsounds()

        if local_file_checksum:
            print('local_file_checksum: ', local_file_checksum)

        s3_bucket = await self.get_bucket()
        # s3_objects = s3_bucket.objects.all()
        
        for obj in self.bucket_objects:
            print('Getting S3 file...')
            # print('Filename of file', obj.key)
            # print(f'MD5 checksum of file: {obj.e_tag}, type: {type(obj.e_tag)}, char at index 0: {obj.e_tag[0]}')
            if obj.e_tag.replace('"', '') not in [d['hexdigest'] for d in local_file_checksum]: # Remove " character from obj.e_tag
                await s3_bucket.download_file(Key=obj.key, Filename=(p / obj.key).__str__())
                print('S3 file downloaded')
            else:
                print('File already exists... skipping file')

    # Gets playsound bucket
    async def get_bucket(self):
        exists = True

        # Check if bucket exist. V2
        try:
            self.s3.meta.client.head_bucket(Bucket=self.playsound_bucket)
            return self.s3.Bucket(self.playsound_bucket)
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
                await self.create_bucket()
                return self.s3.Bucket(self.playsound_bucket)

        return None

    # Gets all objects in playsound bucket
    # This is more of a helper method to reduce queries sent to AWS S3 endpoint
    async def get_bucket_objects(self):
        s3_objects = self.s3_bucket.objects.all()
        return s3_objects

    async def get_valid_playsounds(self):
        '''
        Valid playsound criteria:
        Duration: <= 15 seconds
        File type: Valid file format supported by mutagen
        '''
        hashes = []
        p = Path('playsounds').glob('**/*')

        files = [x for x in p if mutagen.File(x) is not None and mutagen.File(x).info.length <= 15 ]

        for x in files:
            hash_md5 = hashlib.md5()
            with open(x, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_md5.update(chunk)
            hashes.append({"name": x, "hexdigest": hash_md5.hexdigest()})

        return hashes
        # print(hashes)

    # Get playsound bucket
    async def get_bucket(self):
        exists = True

        # Check if bucket exist. V2
        try:
            self.s3.meta.client.head_bucket(Bucket=self.playsound_bucket)
            return self.s3.Bucket(self.playsound_bucket)
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
                await self.create_bucket()
                return self.s3.Bucket(self.playsound_bucket)

        return None

    # Create bucket
    async def create_bucket(self):
        self.s3.create_bucket(Bucket=self.playsound_bucket, CreateBucketConfiguration={
            'LocationConstraint': 'ap-southeast-1'
        })
        print('Bucket created...')
        
    # Upload command test
    @commands.command(name='upload')
    async def _upload(self, ctx: commands.Context):
        file_to_upload = Path('')   # Insert hardcoded path of .mp3 file to test
        to_send = []
        to_send.append(file_to_upload)
        temp_val = await self.upload_files(to_send)
        print(f'Value of file_uploads: {temp_val}')

    # Upload command test 2
    @commands.command(name='upload2')
    async def _upload2(self, ctx: commands.Context, name: typing.Optional[str]):
        max_size = '10MB'   # Max size allowed for playsound
        '''
        TODO: Things to do for upload
        1. Upload audio file
            - Check when command is called, does it have an attachment.
                If not, check if the second argument is a Youtube link
        '''
        message_attachments = ctx.message.attachments
        if len(message_attachments) == 0:
            # TODO: Handle if user gives Youtube link
            return await ctx.send("No attachment provided")
        else:
            # Handling for user file attachment
            filename = message_attachments[0].filename
            file_url = message_attachments[0].url
            print(f'Value of message_attachments: {message_attachments}')
            # Only need to check first item as Discord only allows one file per message
            
            async with ClientSession() as session:
                async with session.get(file_url) as response:
                    if not response.status == 200:
                        return await ctx.send("Invalid attachment URL")

                    content_type = response.headers['content-type']
                    if not content_type.startswith('audio/'):
                        return await ctx.send("Invalid file type")

                    max_length = humanfriendly.parse_size(max_size, binary=True)
                    content_length = response.headers['content-length']
                    
                    if int(content_length) > max_length:
                        return await ctx.send('File size is too large. Send a file 10MB or less')

                    # All criteria passed. Download file to temporary file
                    async with aiofiles.tempfile.NamedTemporaryFile('wb+', delete=False, suffix='.mp3') as f:
                        await f.write(await response.read()) 
                        await f.seek(0)
                        
                        type_file_f2 = mutagen.File(f.name)
                        print(f"type_file_f2: {type_file_f2}, {type_file_f2.info.length}")

                        # Working code segment to crop audio
                        """ 
                        song = AudioSegment.from_mp3(f.name)    # Accessing file from temp folder

                        ten_seconds = 10 * 1000
                        first_10_seconds = song[:ten_seconds]

                        first_10_seconds.export("edited_mashup2.mp3", format="mp3") # This saves the exported file to src/

                        print("File slicing completed!")
                        """

                        
                        f2 = await aiofiles.open(f.name)
                        print(f"f2: {f2}")
                        
                        # await f.close()


                        # TODO: Save temp file with suffix based on uploaded file.
                        # TODO: Temp file successfully create. Re-open it and crop audio
                        """
                        async with aiofiles.open(f.name, mode='r+b') as the_tempfile:
                            content = await the_tempfile.read()
                            print(f'content: {content}')
                            type_file = mutagen.File(the_tempfile)
                            print(F"type_file: {type_file}")
                        """

                        
                        """
                        type_file = await aiofiles.open(f.name, mode='rb+')
                        print(f'type_file: {mutagen.File(type_file)}')
                        os.unlink(f.name)
                        print(f"exists: {os.path.exists(f.name)}")
                        """
                        # TODO: Read the temporary audio file and trim the audio
                        """
                        async for data in f:
                            print(f'Data: {data}')
                        """

            # TODO: Implement loop below 
            """
            loop = asyncio.get_event_loop()
            loop.run_until_complete('function name for getting url and downloading file')
            """
            
            

    # Uploads file to bucket
    async def upload_files(self, files):
        file_uploads = []
        for file in files:
            try:
                self.s3_bucket.upload_file(file.__str__(), 'sample15s.mp3')
                file_uploads.append(S3File(file.__str__(), '200'))
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    print("Bucket does not exist. Called from upload_file")
                elif e.response['Error']['Code'] == '403':
                    print("Insufficient permissions to upload file")
                file_uploads.append(S3File(file.__str__(), e.response['Code']))
            
        return file_uploads     # Returns status of each file upload

    # Define playsound criteria
    async def check_audiofile(self, file):
        '''
        1. Is a mutagen file
        2. File is less than 30 seconds
        '''
        valid_file = mutagen.File(file) is not None and mutagen.File(file).info.length <= 30
        return valid_file

def setup(bot):
    bot.add_cog(Playsound(bot))

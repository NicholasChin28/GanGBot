# Storing and retrieving playsounds from AWS S3 bucket
# Reference material: https://www.gormanalysis.com/blog/connecting-to-aws-s3-with-python/   
# TODO: Add file watcher
from helper.helper import validate_upload_arguments
import pathlib
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
import shutil
from pydub import AudioSegment
from Models.s3file import S3File
import validators
from urllib.parse import urlparse
from helper import helper
from Models.ytdl_source import YTDLSource
from Models.playsound_source import PlaysoundSource

load_dotenv()

# TODO: Getting the MD5 from Etag of AWS S3 objects will not be the same if the files are multi part uploaded
# Find a way of possibly getting MD5 checksum regardless of multipart uploaded or individually uploaded
# Possible reference: https://stackoverflow.com/questions/1775816/how-to-get-the-md5sum-of-a-file-on-amazons-s3
# Possible reference: https://stackoverflow.com/questions/14591926/how-to-compare-local-file-with-amazon-s3-file

# Non existent playsound file error
class SoundError(Exception):
    pass


class PlaysoundSource_old(discord.PCMVolumeTransformer):
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
        self.playsound_folder = Path(__file__).parents[1].absolute() / 'playsounds' # Playsounds
        self.preview_playsounds_folder = Path(__file__).parents[1].absolute()   / 'preview_playsounds'  # Cropped playsounds to be previewed

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
            region_name=os.getenv('AWS_REGION'),
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
                source = await PlaysoundSource_old.get_source(ctx, search, loop=self.bot.loop)
            except SoundError as e:
                await ctx.send(e)
            else:
                sound = Sound(source)

                await cur_voice_state.songs.put(sound)
                await ctx.send('Enqueued a playsound')

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
        file_to_upload = Path('')   
        to_send = []
        to_send.append(file_to_upload)
        temp_val = await self.upload_files(to_send)
        print(f'Value of file_uploads: {temp_val}')

    # Add reactions for upload playsounds
    async def add_playsound_reactions(self, message):
        x_emoji = '❌'
        tick_emoji = '✅'

        await message.add_reaction(tick_emoji)
        await message.add_reaction(x_emoji)
        

    # Upload command test 2
    @commands.command(name='upload2')
    async def _upload2(self, ctx: commands.Context, *args):
        # Prevent user from uploading attachment together and url argument
        # Use *args method instead so that user can do with file attachment, etc:
        # .upload2 00:30-1:00
        # print(type(args))
        if len(args) == 0:
            return await ctx.send("Invalid use of upload command")

        message_attachments = ctx.message.attachments
        url = args[0]
        if len(message_attachments) > 0:
            if len(args) != 1:
                return await ctx.send("Please specify the timestamp")

            timestamp = helper.parse_time(args[0])
            if timestamp is None:
                return await ctx.send("Invalid timestamp provided")
            # Only allow one argument. Which is timestamp
            
        # Handle Youtube
        else:
            # Temporarily make it a must to provide start time and end time
            # TODO: Calculate end time as the end duration of Youtube video
            if len(args) != 2:
                return await ctx.send("Please provide Youtube link together with start time and end time")
            if not validators.url(url) and 'youtube.com' in urlparse(url).netloc:
                return await ctx.send("Invalid Youtube link")
            timestamp = helper.parse_time(args[1])
            if timestamp is None:
                return await ctx.send("Invalid timestamp")
            
            youtube_source = await YTDLSource.create_source(url)
            print(f'Value of youtube_source: {youtube_source.duration}')    # Returns seconds

            try:
                helper.validate_range(timestamp, youtube_source)
            except Exception as e:
                return await ctx.send(e)

            '''
            TODO: Continue from here <<
            Before creating the playsound,
            calculate the estimated size of the file
            '''


            # Process playsound from Youtube url
            loop = asyncio.get_event_loop()
            partial = functools.partial(helper.create_playsound, url, "most random name", timestamp)

            async_result = await loop.run_in_executor(None, partial)

            if async_result is None:
                return await ctx.send("Should not happen from async_result")

            return await ctx.send(f"Processing complete. Check local file: {async_result}")


        # CODE BELOW IS NOT IN USE. 15 JULY 2021
        if (not url and len(message_attachments) == 0) or (url and len(message_attachments) != 0):
            return await ctx.send("Try uploading a file OR sending a Youtube link")
        

        max_size = '10MB'   # Max size allowed for playsound

        # Handle Youtube links
        if len(message_attachments) == 0 and url:
            # Check if url is a valid Youtube URL
            if not validators.url(url) and 'youtube.com' in urlparse(url).netloc:
                return await ctx.send("Invalid Youtube link")
            # TODO: Check if user put timestamp arguments as well
            if timestamp is not None:
                # Validate timestamp
                # TODO: Now accepting time_range as seconds. Refactor it to use similar style as .play command
                # Extract info from youtube url
                await ctx.send(f"Value of timestamp: {timestamp}")
                timerange = helper.parse_time(timestamp)
        # Handle file attachments
        else:
            # Handling for user file attachment
            filename = message_attachments[0].filename
            file_ext = pathlib.Path(filename).suffix
            file_url = message_attachments[0].url

            print(f'Value of message_attachments: {message_attachments}')
            print(f'Value of extension: {file_ext}')
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
                    async with aiofiles.tempfile.NamedTemporaryFile('wb+', delete=False, suffix=file_ext) as f:
                        await f.write(await response.read()) 
                        await f.seek(0)
                        
                        type_file_f2 = mutagen.File(f.name)
                        print(f"type_file_f2: {type_file_f2}, {type_file_f2.info.length}")

                        # Working code segment to crop audio
                        song = AudioSegment.from_mp3(f.name)    # Accessing file from temp folder

                        ten_seconds = 10 * 1000
                        first_10_seconds = song[:ten_seconds]

                        
                        # Save the cropped file to a temporary file name
                        
                        print(f'The parent folder: {pathlib.Path(f.name).parent}')

                        # temp_filename = f'{pathlib.Path(f.name).parent}/({pathlib.Path(filename).stem}_playsound{file_ext})'
                        temp_filename = pathlib.Path(f.name).parent / f'{pathlib.Path(filename).stem}_playsound{file_ext}' 
                        print(f'Value of temp_filename: {temp_filename}')

                        # Save the cropped file to a temporary file name
                        first_10_seconds.export(temp_filename, format=file_ext[1:])

                        print("File slicing completed!")

                        preview_playsound = discord.File(temp_filename)
                        message = await ctx.send(file=preview_playsound)

                        # Add reactions to confirm if the cropped playsound is as wanted
                        await self.add_playsound_reactions(message)

                        # Check for reaction
                        def check(reaction, user):
                            return not user.bot and reaction.message.id == message.id and (reaction.emoji in ['✅', '❌'])

                        while True:
                            try:
                                reaction, _ = await self.bot.wait_for('reaction_add', timeout=120, check=check)
                            except asyncio.TimeoutError:
                                await message.delete()
                                break
                            else:
                                if reaction.emoji == '✅':
                                    # TODO: Approved playsound
                                    # TODO: Check if a similar named playsound already exists
                                    # Place the playsound into the '~/playsounds' folder
                                    # TODO: self.playsound_folder variable is not correct value. Creating file instead of saving into directory
                                    shutil.move(temp_filename, self.playsound_folder)

                                    print(f'Cur value of temp_filename: {temp_filename}')
                                    print(f'Cur value of self.playsound_folder: {self.playsound_folder}')
                                    print('File moved successfully')
                                elif reaction.emoji == '❌':
                                    # TODO: Rejected playsound
                                    # Delete the playsound from the preview_playsounds_folder
                                    try:
                                        os.unlink(temp_filename)
                                        print(f'File deleted at {temp_filename} successful')
                                    except Exception:
                                        print(f'File deletion at temp_filename: {temp_filename} failed')

            # TODO: Implement loop below 
            """
            loop = asyncio.get_event_loop()
            loop.run_until_complete('function name for getting url and downloading file')
            """
    
    # Upload command test 3
    @commands.command(name='upload3')
    async def _upload3(self, ctx: commands.Context, *args):
        message_attachments = ctx.message.attachments

        use_help = discord.Embed(
                title="How to use:",
                description=f"{ctx.command.name}")
        use_help.add_field(name='With file attachment', value=f'.{ctx.command.name} 00:20-00:30', inline=False)
        use_help.add_field(name='With link', value=f'.{ctx.command.name} https://www.youtube.com/watch?v=dQw4w9WgXcQ 00:20-00:30', inline=False)

        if len(message_attachments) > 1:
            return await ctx.send('File upload only supports one file attachment')
        
        # File upload
        if len(message_attachments) == 1:
            if len(args) > 1:
                return await ctx.send(use_help)

            first_attachment = message_attachments[0]
                    
            filename = first_attachment.filename
            file_ext = pathlib.Path(filename).suffix
            file_url = first_attachment.url

            if not first_attachment.content_type.startswith('audio/'):
                return await ctx.send('Only audio files supported')

            if file_ext != ".mp3":
                return await ctx.send('Only mp3 uploads supported')

            try:
                pass
                # Handling for user file attachment
                # self.handle_playsound_upload(url=file_url, timestamp=args[0])
                playsound_source = await PlaysoundSource.create_source(ctx, args[0], file_upload=True)

                print(f'Value of playsound_source: {playsound_source.start_time.datetime}')
            except Exception as e:
                return await ctx.send(e)
        # From Url
        else:
            print('test here')
            playsound_source = await PlaysoundSource.create_source(ctx, args[-1], url=args[0])
        
    @_upload3.error
    async def upload3_error(self, ctx: commands.Context, error):
        # Check if arguments passed
        if isinstance(error, commands.MissingRequiredArgument):
            use_help = discord.Embed(
                title="How to use:",
                description=f"{ctx.command.name}")
            use_help.add_field(name='With file attachment', value=f'.{ctx.command.name} 00:20-00:30', inline=False)
            use_help.add_field(name='With link', value=f'.{ctx.command.name} https://www.youtube.com/watch?v=dQw4w9WgXcQ 00:20-00:30', inline=False)

            await ctx.send(embed=use_help)

    async def handle_playsound_upload(self, url: str, timestamp: str):
        # Validate url
        if not validators.url(url):
            raise Exception("Not a valid url")

        # Validate timestamp
        # playsound_source = 
    # Handle upload commmand with file attachment
    # async def handle_file_upload()
    # async def handle_file_upload(self, url, timestamp)
    # async def handle_url_upload(self, url, timestamp)
    # TODO: Calculate the file size from the timestamp
            
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

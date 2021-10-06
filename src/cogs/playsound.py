# Storing and retrieving playsounds from AWS S3 bucket
# Reference material: https://www.gormanalysis.com/blog/connecting-to-aws-s3-with-python/   
# TODO: Add file watcher
import pathlib
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
import validators
from urllib.parse import urlparse
from helper import helper
from helper.s3_bucket import S3Bucket
from Models.ytdl_source import YTDLSource
from Models.playsound_source import PlaysoundSource, PlaysoundSource_supernew

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
        """
        partial = functools.partial(PlaysoundSource.extract_info, search)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise SoundError('Playsound does not exist')

        location = Path(f"{os.getenv('APP_PATH')}/playsounds/{search}.mp3")
        return cls(ctx, discord.FFmpegPCMAudio(location), data=data)
        """
                

    # TODO: Get metadata of local sound files to display in queue function
    @staticmethod
    def extract_info(search: str):
        location = Path(f"{os.getenv('APP_PATH')}/playsounds/{search}.mp3")
        details = {}
        if location.is_file():
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

    def __init__(self, source: PlaysoundSource_supernew):
        self.source = source
        # self.requester = source.requester

    def create_embed(self):
        embed = discord.Embed(title="Now playing playsound")

        return embed

    """
    def create_embed(self):
        embed = (discord.Embed(title='Now playing',
                                description='```css\n{0.source.title}\n```'.format(self),
                                color=discord.Color.blurple())
                .add_field(name='Duration', value=self.source.duration)
                .add_field(name='Requested by', value=self.requester.mention))

        return embed
    """

class Playsound(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # self.playsound_folder = Path(__file__).parent.absolute() / 'random2.mp3'
        self.playsound_folder = Path(__file__).parents[1].absolute() / 'playsounds' # Playsounds
        self.preview_playsounds_folder = Path(__file__).parents[1].absolute()   / 'preview_playsounds'  # Cropped playsounds to be previewed

    @commands.Cog.listener()
    async def on_ready(self):
        print('Playsound cog loaded!')

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
    # TODO: New listsounds command
    # @commands.command(name='')

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

    # Command to play sound file from AWS S3 bucket
    @commands.command(name='ps2')
    async def _playsound2(self, ctx: commands.Context, *, search: str):
        """Plays a custom playsound"""
        parent_cog = ctx.bot.get_cog('Music')
        cur_voice_state = parent_cog.get_voice_state(ctx)
        ctx.voice_state = cur_voice_state
        if not cur_voice_state.voice:
            await ctx.bot.get_command('join').callback(self, ctx)

        # TODO: Search playsound from AWS S3
        async with ctx.typing():
            try:
                source = await PlaysoundSource_supernew.get_source(ctx, search, loop=self.bot.loop)
                print('source: ', source)
                print('type of source: ', type(source))
            except Exception as e:
                await ctx.send(f"Source does not exist: {e}")
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
        
    # Add reactions for upload playsounds
    async def add_playsound_reactions(self, message):
        x_emoji = '❌'
        tick_emoji = '✅'

        await message.add_reaction(tick_emoji)
        await message.add_reaction(x_emoji)
    
    # Upload command
    @commands.command(name='upload')
    async def _upload(self, ctx: commands.Context, *args):
        message_attachments = ctx.message.attachments

        use_help = discord.Embed(
                title="How to use:",
                description=f"{ctx.command.name}")
        use_help.add_field(name='With file attachment', value=f'.{ctx.command.name} 00:20-00:30', inline=False)
        use_help.add_field(name='With link', value=f'.{ctx.command.name} https://www.youtube.com/watch?v=dQw4w9WgXcQ 00:20-00:30', inline=False)

        if len(args) == 0:
            return await ctx.send(embed=use_help, delete_after=20)

        if len(message_attachments) > 1:
            return await ctx.send('File upload only supports one file attachment', delete_after=20)
        
        uploader = ctx.message.author

        # File upload
        if len(message_attachments) == 1:
            if len(args) > 1:
                return await ctx.send(use_help, delete_after=20)

            first_attachment = message_attachments[0]
                    
            filename = first_attachment.filename
            file_ext = pathlib.Path(filename).suffix
            file_url = first_attachment.url

            if not first_attachment.content_type.startswith('audio/'):
                return await ctx.send('Only audio files supported')

            if file_ext != ".mp3":
                return await ctx.send('Only mp3 uploads supported')

            # TODO: Standardize into one call
            try:
                # Handling for user file attachment
                playsound_source = await PlaysoundSource.create_source(ctx, args[0], file_upload=True)
                playsound = discord.File(playsound_source.filename)
                message = await ctx.send(file=playsound)
            except Exception as e:
                return await ctx.send(e)
        # From Url
        else:
            url = args[0]

            if not validators.url(url) and 'youtube.com' in urlparse(url).netloc:
                return await ctx.send("Only valid Youtube links supported")

            try:
                playsound_source = await PlaysoundSource.create_source(ctx, args[-1], url=url)
                playsound = discord.File(playsound_source.filename)
                message = await ctx.send(file=playsound)
            except Exception as e:
                return await ctx.send(e)

        # Check with user if the playsound generated is correct
        def check(reaction, user):
            return not user.bot and reaction.message.id == message.id and (reaction.emoji in ['❌', '✅']) 

        def name_check(message):
            print("name_check called")
            return message.author == uploader
        
        # Add reactions to message
        await message.add_reaction('❌')
        await message.add_reaction('✅')

        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=10, check=check)
        except asyncio.TimeoutError:
            # TODO: Delete the playsound and delete the message
            await ctx.send("Reaction timeout exceeded. Deleting playsound")
            Path(playsound_source.filename).unlink(missing_ok=True)

        if reaction.emoji == '✅':
            await ctx.send("Give a cool name for the playsound!")
            try:
                name = await self.bot.wait_for('message', timeout=10, check=name_check)
            except asyncio.TimeoutError:
                Path(playsound_source.filename).unlink(missing_ok=True)
                print("Timeout exceeded from message wait")
                return await ctx.send('Message timeout exceeded. Removing playsound.')

            if name:
                # Approved playsound. Upload it to AWS S3
                print('Approving playsound')

                loop = asyncio.get_running_loop()
                
                # Rename the file before uploading
                playsound_local = Path(playsound_source.filename)
                # print(playsound_local)
                new_name = Path(name.content + playsound_local.suffix)
                # print(new_name)
                playsound_local.rename(new_name)

                test_con = S3Bucket()
                partial = functools.partial(test_con.upload_files, ctx, [new_name.__str__()])
                try:
                    upload_results = await loop.run_in_executor(None, partial)
                    # After upload_results returns, there will be an exception. Probably due to the connection closing.
                    print('upload_results: ', upload_results)   
                    return await ctx.send("Playsound added!")
                except Exception as e:
                    return await ctx.send(e)
        elif reaction.emoji == '❌':
            # Rejected playsound. Delete it from temp folder
            print('Rejecting playsound')
            Path(playsound_source.filename).unlink(missing_ok=True)
            await message.delete()
            await ctx.send("Rejected playsound. Removing...")

    @_upload.error
    async def upload_error(self, ctx: commands.Context, error):
        # Check if arguments passed
        if isinstance(error, commands.MissingRequiredArgument):
            use_help = discord.Embed(
                title="How to use:",
                description=f"{ctx.command.name}")
            use_help.add_field(name='With file attachment', value=f'.{ctx.command.name} 00:20-00:30', inline=False)
            use_help.add_field(name='With link', value=f'.{ctx.command.name} https://www.youtube.com/watch?v=dQw4w9WgXcQ 00:20-00:30', inline=False)

            await ctx.send(embed=use_help)

def setup(bot):
    bot.add_cog(Playsound(bot))

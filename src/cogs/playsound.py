import pathlib
import aiohttp
from discord.ext.commands.context import Context
from dotenv import load_dotenv
import os
from pathlib import Path
import mutagen
import hashlib
import typing
import asyncio
import functools
import discord
from discord import ButtonStyle
from discord.ui import Button
from discord.ext import commands
from botocore.exceptions import ClientError
from aiohttp import ClientSession
from pyaml_env import parse_config
from tortoise import Tortoise, run_async
import wavelink
from wavelink.player import Player
from models.playsound import Playsound as PsObject
import validators
from urllib.parse import urlparse
from models.emojis import Emojis
from helper import helper
from helper.s3_bucket import S3Bucket
from models.ytdl_source import YTDLSource
from models.playsound_source import PlaysoundAudio, PlaysoundSource
from views.confirm import Confirm

load_dotenv()


# Non existent playsound file error
class SoundError(Exception):
    pass


# Custom added class to play local .mp3 files as a soundboard
class Sound:
    __slots__ = ('source', 'requester')

    def __init__(self, source: PlaysoundSource):
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

    @commands.Cog.listener()
    async def on_ready(self):
        print('Playsound cog loaded!')

    @commands.command(name='listsounds', aliases=['ls'])
    async def _listsounds2(self, ctx: commands.Context, *, page: int = 1):
        """ Get list of playsounds from bucket """
        loop = asyncio.get_running_loop()

        test_con = S3Bucket()
        partial = functools.partial(test_con.get_files, ctx)

        the_list = await loop.run_in_executor(None, partial)
        print(the_list)

        if len(the_list) == 0:
            return await ctx.send("No playsounds found")
        else:
            limit = 10      # Playsounds per peage
            embeds = []
            playsounds = ''

            for i, playsound in enumerate(the_list[0:], start=1):
                if i % limit == 0:
                    playsounds += '`{0}.` `{1}`\n'.format(i, playsound)
                    embeds.append(playsounds)
                    playsounds = ''
                else:
                    playsounds += '`{0}.` `{1}`\n'.format(i, playsound)
                    if i == len(the_list):
                        embeds.append(playsounds)

            pages = len(embeds) # Total pages

            embed = (discord.Embed(description='**{} sounds:**\n\n{}'.format(len(the_list), embeds[page - 1]))
                    .set_footer(text='Viewing page {}/{}'.format(page, pages)))
            message = await ctx.send(embed=embed)

            # Page reactions
            async def add_page_reactions():
                if page == pages:
                    pass    # Only 1 page. No reactions required
                if page > 1:
                    await message.add_reaction(Emojis.reverse_button)
                if pages > page:
                    await message.add_reaction(Emojis.play_button)

            await add_page_reactions()

            # Recreates the embed
            async def refresh_embed():
                await message.clear_reactions()
                embed = (discord.Embed(description='**{} sounds:**\n\n{}'.format(len(the_list), embeds[page - 1]))
                    .set_footer(text='Viewing page {}/{}'.format(page, pages)))

                await message.edit(embed=embed)
                await add_page_reactions()

            # Check for reaction
            def check(reaction, user):
                return not user.bot and reaction.message.id == message.id and (reaction.emoji in [Emojis.reverse_button, Emojis.play_button])

            while True:
                try:
                    reaction, _ = await ctx.bot.wait_for('reaction_add', timeout=60, check=check)
                except asyncio.TimeoutError:
                    await message.delete()
                    break
                else:
                    if reaction.emoji == Emojis.reverse_button:
                        page -= 1
                        await refresh_embed()
                    elif reaction.emoji == Emojis.play_button:
                        page += 1
                        await refresh_embed()
    
    @commands.command(name='ps2')
    async def _playsound_new(self, ctx: commands.Context, *, search: str):
        """Plays a playsound"""
        async with ctx.typing():
            node = wavelink.NodePool.get_node()
            if not ctx.voice_client:
                if ctx.author.voice is None:
                    return await ctx.send('Please connect to a voice channel')
                vc: Player = await ctx.author.voice.channel.connect(cls=Player)
            else:
                vc: Player = ctx.voice_client
            # Check cache if playsound exists
            playsound_folder = Path(f'./playsounds/{ctx.guild.id}/')

            if not playsound_folder.exists():
                print(f'Creating folder for guild {ctx.guild.id}')
                playsound_folder.mkdir(parents=True, exist_ok=False)
            
            playsound_path = playsound_folder / f'{search}.mp3'

            if playsound_path.exists():
                track = await node.get_tracks(cls=wavelink.LocalTrack, query=f'{playsound_path.resolve().__str__()}')
                # await vc.queue.put_wait(track[0])
                # await ctx.send('Added playsound')
            else:
                # Get file from AWS S3 bucket
                bucket = S3Bucket()
                playsound = await bucket.download_playsound(ctx, playsound_path, f'{ctx.guild.id}/{search}.mp3')

                track = await node.get_tracks(cls=wavelink.LocalTrack, query=f'{playsound_path.resolve().__str__()}')
                # await vc.queue.put_wait(track[0])
                # await ctx.send('Added playsound')

            if vc.queue.is_empty and not vc.is_playing():
                await vc.queue.put_wait(track[0])
                self.bot.tqueuenew.update({track[0].id: ctx})
                await ctx.send('Added playsound')
                await vc.play(await vc.queue.get_wait())
            else:
                await vc.queue.put_wait(track[0])
                self.bot.tqueuenew.update({track[0].id: ctx})
                await ctx.send('Added playsound')

            """
            playsound_folder = Path('./playsounds')
            playsound_temp = Path('./playsounds/mald.mp3')
            playsound_path = f'{ctx.guild.id}/{search}.mp3'
            """

            """
            full_path = playsound_folder / playsound_path
            # playsound = playsound_folder / f'{search}.mp3'

            s3bucket = S3Bucket()
            playsound = await s3bucket.get_fileplaysound(ctx=ctx, query=search)
            # track = await node.get_tracks(cls=wavelink.LocalTrack, query=f'{playsound.name}')
            track = await node.get_tracks(cls=wavelink.LocalTrack, query=f'{playsound_temp.resolve().__str__()}')
            await vc.queue.put_wait(track[0])
            await ctx.send('Added playsound')
            """

            """
            if Path(f'./{search}.mp3').exists():
                # track = await node.get_tracks(cls=wavelink.Track, query=f'{playsound.__str__()}')
                # track = await node.get_tracks(cls=wavelink.LocalTrack, query=f'./mald.mp3')
                track = await node.get_tracks(cls=wavelink.LocalTrack, query='mald.mp3')
                await vc.queue.put_wait(track[0])
            else:
                # Download from AWS S3
                bucket = S3Bucket()
                playsound = await bucket.download_playsound(ctx, playsound_folder, playsound_path)
            """


    # DEPRECATED: DONT USE
    # Command to play sound file from AWS S3 bucket
    @commands.command(name='ps')
    async def _playsound2(self, ctx: commands.Context, *, search: str):
        """Plays a playsound"""
        async with ctx.typing():
            try:
                source = await PlaysoundAudio.get_source(ctx, search, loop=self.bot.loop)
                print('source: ', source)
                print('type of source: ', type(source))

                # Join VC only if playsound exists
                parent_cog = ctx.bot.get_cog('Music')
                cur_voice_state = parent_cog.get_voice_state(ctx)
                ctx.voice_state = cur_voice_state
                if not cur_voice_state.voice:
                    await ctx.bot.get_command('join').callback(self, ctx)
            except Exception as e:
                await ctx.send("Playsound not found")
            else:
                sound = Sound(source)

                await cur_voice_state.songs.put(sound)
                await ctx.send('Enqueued a playsound')

    # Delete playsound
    # TODO: Delete playsound from s3 and remove database record
    @commands.command(name='delps', aliases=['psdelete', 'dps', 'psdel'])
    async def _delete(self, ctx: commands.Context, ps_name):
        """Deletes a playsound"""
        view = Confirm()
        await ctx.send('Are you sure you want to delete the playsound?', view=view)

        await view.wait()
        if view.value is None:
            print('Timed out...')
        elif view.value:
            print('Confirmed...')
            # Delete playsound here
            loop = asyncio.get_running_loop()

            s3_con = S3Bucket()
            partial = functools.partial(s3_con.delete_playsound, ctx, name=ps_name)
            result = await loop.run_in_executor(None, partial)

            if result:
                # Delete from database
                tortoise_config = parse_config('./tortoise-config.yaml')
                await Tortoise.init(config=tortoise_config)

                record = await PsObject.filter(
                    name=f'{ps_name}.mp3'
                ).first()

                if record:
                    await record.delete()
                await ctx.send('Playsound deleted')
        else:
            print('Cancelled...')

    # Upload playsounds command
    @commands.command(name='addps2', aliases=['psadd2', 'aps2', 'uploadps2'])
    async def addps2(self, ctx: commands.Context, link: str, *, timestamp: typing.Optional[str] = None):
        """Add a playsound v2"""
        def uploader_check(message):
            return message.author == ctx.message.author

        video_unavailable = '"playabilityStatus:":{"status":"ERROR","reason":"Video unavailable"}'
        
        print(f'link: {link}')
        print(f'timestamp: {timestamp}')

        # Verify link provided
        if not validators.url(link) and 'youtube.com' in urlparse(link).netloc:
            return await ctx.send('Only Youtube links supported')

        async with ClientSession() as session:
            async with session.get(link) as resp:
                print(await resp.text())
                if video_unavailable in await resp.text():
                    return await ctx.send('Invalid Youtube link')
                
                loop = asyncio.get_event_loop()
                # duration = await loop.run_in_executor(None, helper.extract_duration, [link])
                try:
                    duration = await loop.run_in_executor(None, helper.extract_duration, link)
                except Exception as e:
                    return await ctx.send('Uh oh. An unexpected error occurred')

                # Construct the timestamp
                if timestamp:
                    try:
                        playsound_source_new = await loop.run_in_executor(None, helper.parse_time_new, timestamp, duration)
                        download_playsound = await loop.run_in_executor(None, helper.download_playsound_new, link, playsound_source_new.start_time, playsound_source_new.end_time, playsound_source_new.duration)
                    except Exception as e:
                        print(e)
                        return await ctx.send(e)
                else:
                    if duration > 20:
                        return await ctx.send('Only playsounds 20 seconds or less can be added')
                    
                    download_playsound = await loop.run_in_executor(None, helper.download_playsound_new, link)

                if download_playsound.get('download_result'):
                    playsound = discord.File(download_playsound.get('filename'))
                    await ctx.send(file=playsound)

                    confirm_view = Confirm()
                    await ctx.send('Is this the correct playsound?', view=confirm_view)

                    await confirm_view.wait()

                    playsound_name = download_playsound.get('filename')
                    playsound_path = Path(playsound_name)

                    if confirm_view.value is None:
                        print('Timed out')
                        playsound_path.unlink()
                        await ctx.send('Timeout exceeded. Removing playsound')
                    elif confirm_view.value:
                        # Set playsound name
                        await ctx.send('Give a cool name for the playsound!')
                        try:
                            name = await self.bot.wait_for('message', timeout=15, check=uploader_check)
                        except asyncio.TimeoutError:
                            playsound_path.unlink()
                            return await ctx.send('Timeout exceeded. Removing playsound')

                        # Approve the playsound
                        try:
                            # playsound_path = playsound_path.rename(f'{name.content}')     # Throwing error here
                            playsound_path = playsound_path.rename(f'{name.content}.mp3')
                            print('Approving the playsound')
                            await ctx.send('Approving playsound')
                            test_con = S3Bucket()
                            upload_results = await loop.run_in_executor(None, test_con.upload_files, ctx, playsound_path.name)
                            print(f'upload_results: {upload_results}')

                            # Save playsound details in database
                            tortoise_config = parse_config('./tortoise-config.yaml')
                            await Tortoise.init(config=tortoise_config)

                            await PsObject.create(
                                name=download_playsound.get('filename'),
                                duration=10,
                                uploader=ctx.author.id,
                                played=0,
                                guild=ctx.author.guild.id,
                            )

                            await ctx.send('Playsound added!')
                            playsound_path.unlink()
                            
                            await Tortoise.close_connections()
                        except Exception as e:
                            print(e)
                            playsound_path.unlink()
                            return await ctx.send('Error when approving playsound. Check the logs')
                    else:
                        # Reject the playsound
                        await ctx.send('Rejecting playsound')
                        print('Rejecting the playsound')
                        playsound_path.unlink()
                        await ctx.send('Playsound rejected')
                else:
                    return await ctx.send('Unexpected error occurred. Please check logs')

    @addps2.error
    async def addps2_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please provide a valid Youtube link')
            
            help_link = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
            help_timestamp = '00:20-00:30'
            help_start = '00:20'
            
            use_help = discord.Embed(title='How to use:', description=f'{ctx.command.name}')
            use_help.add_field(name='Whole video', value=f'.{ctx.command.name} {help_link}', inline=False)
            use_help.add_field(name='Start timestamp to video end', value=f'.{ctx.command.name} {help_link} {help_start}', inline=False)
            use_help.add_field(name='Start and end timestamp', value=f'.{ctx.command.name} {help_link} {help_timestamp}', inline=False)

            await ctx.send(embed=use_help)
            

    # Upload command
    @commands.command(name='addps', aliases=['psadd', 'aps', 'uploadps'])
    async def _upload(self, ctx: commands.Context, link: str, timestamp: typing.Optional[str] = None):
        """Add a playsound"""
        video_unavailable = '"playabilityStatus:":{"status":"ERROR","reason":"Video unavailable"}'
        message_attachments = ctx.message.attachments

        use_help = discord.Embed(
                title="How to use:",
                description=f"{ctx.command.name}")
        use_help.add_field(name='With file attachment', value=f'.{ctx.command.name} 00:20-00:30', inline=False)
        use_help.add_field(name='With link', value=f'.{ctx.command.name} https://www.youtube.com/watch?v=dQw4w9WgXcQ 00:20-00:30', inline=False)


        '''
        if len(args) == 0:
            return await ctx.send(embed=use_help, delete_after=20)
        '''

        if len(message_attachments) > 1:
            return await ctx.send('File upload only supports one file attachment', delete_after=20)
        
        uploader = ctx.message.author

        # File upload
        if len(message_attachments) == 1:
            if len(link) > 1:
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
            if not validators.url(link) and 'youtube.com' in urlparse(link).netloc:
                return await ctx.send("Only Youtube links supported")

            async with ClientSession() as session:
                async with session.get(link) as resp:
                    print(await resp.text())
                    if video_unavailable in await resp.text():
                        return await ctx.send('Invalid Youtube link')
            try:
                playsound_source = await PlaysoundSource.create_source(ctx, url=link, timestamp=timestamp)
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
        await message.add_reaction(Emojis.x_emoji)
        await message.add_reaction(Emojis.tick_emoji)

        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=20, check=check)
        except asyncio.TimeoutError:
            # TODO: Delete the playsound and delete the message
            await ctx.send("Reaction timeout exceeded. Deleting playsound")
            Path(playsound_source.filename).unlink(missing_ok=True)

        if reaction.emoji == Emojis.tick_emoji:
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
                    
                    # TODO: Save the playsound details in db
                    tortoise_config = parse_config('./tortoise-config.yaml')
                    await Tortoise.init(config=tortoise_config)
                    
                    await PsObject.create(
                        name=new_name,
                        duration=playsound_source.duration,
                        uploader=playsound_source.uploader.id,
                        played=0,
                        guild=playsound_source.guild.id,
                    )

                    await ctx.send("Playsound added!")
                    # Delete the playsound after successful upload
                    Path(new_name).unlink(missing_ok=True)

                    await Tortoise.close_connections()
                except Exception as e:
                    return await ctx.send(e)
        elif reaction.emoji == Emojis.x_emoji:
            # Rejected playsound. Delete it
            print('Rejecting playsound')
            Path(playsound_source.filename).unlink(missing_ok=True)
            await message.delete()
            await ctx.send("Rejected playsound. Removing...")

    @_upload.error
    async def upload_error(self, ctx: commands.Context, error):
        # Check if arguments passed
        if isinstance(error, commands.MissingRequiredArgument):
            print('Missing required argument')
            use_help = discord.Embed(
                title="How to use:",
                description=f"{ctx.command.name}")
            use_help.add_field(name='With file attachment', value=f'.{ctx.command.name} 00:20-00:30', inline=False)
            use_help.add_field(name='With link', value=f'.{ctx.command.name} https://www.youtube.com/watch?v=dQw4w9WgXcQ 00:20-00:30', inline=False)

            await ctx.send(embed=use_help)


# Example how to use Buttons, discordpy 2.0
# https://github.com/Rapptz/discord.py/blob/master/examples/views/confirm.py
class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None
        self.timeout = 20

    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message('Confirming', ephemeral=True)
        self.value = True
        self.stop()

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.grey)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message('Cancelling', ephemeral=True)
        self.value = False
        self.stop()

def setup(bot):
    bot.add_cog(Playsound(bot))

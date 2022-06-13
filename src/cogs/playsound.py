import pathlib
import aiohttp
from mutagen.id3 import ID3, TIT2, TPE1
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
from tortoise.expressions import F
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
from views.multipage import MultiPage, PreviousButton, NextButton
from datetime import datetime

load_dotenv()

class Playsound(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self) -> None:
        print("Playsound cog loaded! from 2.0")

    async def cog_unload(self) -> None:
        print("Playsound cog unloaded! from 2.0")

    @commands.command(name='listsounds', aliases=['ls'])
    async def _listsounds(self, ctx: commands.Context):
        """Lists all available playsounds"""
        page = 1
        loop = asyncio.get_event_loop()
        tortoise_config = parse_config('./tortoise-config.yaml')
        await Tortoise.init(config=tortoise_config)

        # Get all playsounds
        playsounds = await PsObject.all()
        if len(playsounds) == 0:
            return await ctx.send('No playsounds found')
        
        embeds = await loop.run_in_executor(None, self.playsound_embeds, playsounds)

        embed = discord.Embed(description=f'**{len(playsounds)} sounds:**\n\n{embeds[page - 1]}')
        embed.set_footer(text=f'Viewing page {page}/{len(embeds)}')

        message = await ctx.send(embed=embed)
        await message.edit(embed=embed, view=MultiPage(message, embeds, len(playsounds)))
    
    @commands.command(name='ps')
    async def _playsound(self, ctx: commands.Context, *, search: str):
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
            else:
                # Get file from AWS S3 bucket
                bucket = S3Bucket()
                playsound = await bucket.download_playsound(ctx, playsound_path, f'{ctx.guild.id}/{search}.mp3')

                track = await node.get_tracks(cls=wavelink.LocalTrack, query=f'{playsound_path.resolve().__str__()}')

            # Temp update the track details
            if track[0].title == 'Unknown title':
                track[0].title = 'Playsound'
                track[0].info.update({'title': 'Playsound'})

            # track[0].title = 'test'
            # track[0].info.update({'title': 'test'})

            if vc.queue.is_empty and not vc.is_playing():
                print(track[0].title)
                await vc.queue.put_wait(track[0])
                self.bot.tqueuenew.update({track[0].id: ctx})
                await ctx.send('Added playsound')
                await vc.play(await vc.queue.get_wait())
            else:
                await vc.queue.put_wait(track[0])
                self.bot.tqueuenew.update({track[0].id: ctx})
                await ctx.send('Added playsound')

            tortoise_config = parse_config('./tortoise-config.yaml')
            await Tortoise.init(config=tortoise_config)
            
            # Update the database record
            await PsObject.filter(
                name=search,
                guild=ctx.author.guild.id
            ).update(
                played=F('played') + 1
            )

            await Tortoise.close_connections()

    # Delete playsound
    # TODO: Delete playsound from s3 and remove database record
    @commands.command(name='delps', aliases=['psdelete', 'dps', 'psdel'])
    @commands.is_owner()
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
                    name=f'{ps_name}'
                ).first()

                if record:
                    await record.delete()
                await ctx.send('Playsound deleted')
        else:
            print('Cancelled...')

    # Upload playsounds command
    @commands.command(name='addps', aliases=['psadd', 'aps', 'uploadps'])
    async def _addps(self, ctx: commands.Context, link: str, *, timestamp: typing.Optional[str] = None):
        """Add a playsound"""
        # Get all playsounds
        loop = asyncio.get_event_loop()
        s3_con = S3Bucket()
        playsound_names = await loop.run_in_executor(None, s3_con.get_files, ctx)

        """Add a playsound"""
        def uploader_check(message):
            # Check if playsound name already exists
            test = not message.content in playsound_names
            return message.author == ctx.message.author and not message.content in playsound_names

        video_unavailable = '"playabilityStatus:":{"status":"ERROR","reason":"Video unavailable"}'
        
        print(f'link: {link}')
        print(f'timestamp: {timestamp}')

        # Verify link provided
        if not validators.url(link) and 'youtube.com' in urlparse(link).netloc:
            return await ctx.send('Only Youtube links supported')

        async with ClientSession() as session:
            async with session.get(link) as resp:
                if video_unavailable in await resp.text():
                    return await ctx.send('Invalid Youtube link')
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
                    
                    download_playsound = await loop.run_in_executor(None, helper.download_playsound_new, link, None, None, duration)

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
                        await ctx.send('Give a cool name for the playsound!')
                        
                        while True:
                            try:
                                name = await self.bot.wait_for('message', timeout=20)
                            except asyncio.TimeoutError:
                                playsound_path.unlink()
                                return await ctx.send('Timeout exceeded. Removing playsound')
                            if name.content not in playsound_names:
                                break
                            else:
                                await ctx.send('A playsound with that name already exists. Try something else')
                                continue
                                """
                                test_some = name
                                if name.content in playsound_names:
                                    await ctx.send('A playsound with that name already exists. Try something else')
                                    continue
                                """
                                
                        """
                        try:
                            name = await self.bot.wait_for('message', timeout=20, check=uploader_check)
                            print(f'value of name: {name}')
                        except asyncio.TimeoutError:
                            playsound_path.unlink()
                            return await ctx.send('Timeout exceeded. Removing playsound')
                        """

                        print(f'value of name v2: {name}')
                        # Approve the playsound
                        try:
                            # Check if there is a similar named playsound
                            playsound_path = playsound_path.rename(f'{name.content}.mp3')

                            # Update the metadata
                            # https://en.wikipedia.org/wiki/ID3
                            # TPE1 = Artist
                            # TIT2 = Title
                            file = mutagen.id3.ID3(Path(f'{playsound_path.name}'))
                            file.add(TIT2(encoding=3, text=playsound_path.stem))
                            file.add(TPE1(encoding=3, text='Playsound'))
                            file.save()

                            print('Approving the playsound')
                            await ctx.send('Approving playsound')
                            test_con = S3Bucket()
                            upload_results = await loop.run_in_executor(None, test_con.upload_files, ctx.message.guild.id, playsound_path.name)
                            print(f'upload_results: {upload_results}')

                            # Save playsound details in database
                            tortoise_config = parse_config('./tortoise-config.yaml')
                            await Tortoise.init(config=tortoise_config)

                            await PsObject.create(
                                name=playsound_path.stem,
                                extension=playsound_path.suffix,
                                duration=download_playsound.get('file').info.length,
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

    @_addps.error
    async def addps_error(self, ctx: commands.Context, error):
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

    def playsound_embeds(self, playsounds: typing.List[PsObject]):
        limit = 10
        embeds = []
        embed_text = ''

        for idx, playsound in enumerate(playsounds[0:], start=1):
            if idx % limit == 0:
                embed_text += f'{idx}. {playsound.name}\n'
                embeds.append(embed_text)
                embed_text = ''
            else:
                embed_text += f'{idx}. {playsound.name}\n'
                if idx == len(playsounds):
                    embeds.append(embed_text)

        return embeds
                


async def setup(bot):
    await bot.add_cog(Playsound(bot))

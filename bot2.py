# TODO: In the future, add cogs to organize the functions more neatly
import os
import random
from dotenv import load_dotenv

# For the discord.Embed 2048 character limit
import textwrap

from os import listdir
from os.path import isfile, join

import asyncio
import itertools
import functools
import math

import ctypes
import ctypes.util

import discord
from discord.ext import commands
from discord.utils import get

from async_timeout import timeout

# Logging errors to the console
import logging

import youtube_dl

# Wrap text
import lorem

# Relative path
from pathlib import Path

# Import Spotify source custom class
# import spotify_source

# For getting mp3 metadata
import mutagen

# Inspiration code from: https://gist.github.com/vbe0201/ade9b80f2d3b64643d854938d40a0a2d

# Silence useless bug reports messages
youtube_dl.utils.bug_reports_message = lambda: ''

# Set the logging command line messages
logging.basicConfig(level=logging.INFO)

class VoiceError(Exception):
    pass

class YTDLError(Exception):
    pass

# Non existent playsound file error
class SoundError(Exception):
    pass

# Youtube-dl class
class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmp1': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.id = data.get('id')
        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_id')        # May not exist anymore. Changed from 'uploader_url' to 'uploader_id' Check youtube-dl docs.
        date = data.get('upload_date')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')              # May not exist anymore.
        self.description = data.get('description')  
        self.duration = self.parse_duration(int(data.get('duration')))
        self.tags = data.get('tags')
        self.url = data.get('url')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.dislikes = data.get('dislike_count')
        self.stream_url = data.get('url')

    def __str__(self):
        return '**{0.title}** by **{0.uploader}**'.format(self)

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(cls.ytdl.extract_info, search, download = False, process = False)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError("Couldn't find anything that matches `{}`".format(search))

        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError("Couldn't find anything that matches `{}`".format(search))

        webpage_url = process_info['webpage_url']
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download = False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError("Couldn't fetch `{}`".format(webpage_url))

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError("Couldn't retrieve any matches for `{}`".format(webpage_url))
        
        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data = info)

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

class LocalSource(discord.PCMVolumeTransformer):
    # TODO: Get metadata of local sound files to display in queue function

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, volume: float = 0.5):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
    
    def __str__(self):
        return f'LocalSource class __str__ function'

    @classmethod
    async def get_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(cls.parse_availability, search)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise SoundError("Specified playsound could not be found")

        location = f"./playsounds/{search}.mp3"
        print(f"Location of get_source: {location}")
        return cls(ctx, discord.FFmpegPCMAudio(f'./playsounds/{search}.mp3'))

    @staticmethod
    def parse_availability(search: str):
        if os.path.isfile(f'./playsounds/{search}.mp3'):
            print('File exists')
            return "Yes"
        else:
            print("File does not exist")

class Song:
    __slots__ = ('source', 'requester')

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        embed = (discord.Embed(title='Now playing',
                                description='```css\n{0.source.title}\n```'.format(self),
                                color=discord.Color.blurple())
                .add_field(name='Duration', value=self.source.duration)
                .add_field(name='Requested by', value=self.requester.mention)
                .add_field(name='Uploader', value='[{0.source.uploader}]({0.source.uploader_url})'.format(self))
                .add_field(name='URL', value='[Click]({0.source.url})'.format(self))
                .set_thumbnail(url=self.source.thumbnail))

        return embed

# Custom added class to play local .mp3 files as a soundboard
class Sound:
    __slots__ = ('source', 'requester')

    def __init__(self, source: LocalSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        '''
        embed = (discord.Embed(title='Now playing',
                                description='```css\n{0.source.title}\n```'.format(self),
                                color=discord.Color.blurple())
                .add_field(name='Duration', value=self.source.duration)
                .add_field(name='Requested by', value=self.requester.mention)
                .add_field(name='Uploader', value='[{0.source.uploader}]({0.source.uploader_url})'.format(self))
                .add_field(name='URL', value='[Click]({0.source.url})'.format(self))
                .set_thumbnail(url=self.source.thumbnail))
        '''
        
        embed = discord.Embed(title="Playing a local sound file")
        return embed

class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]

class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self._ctx = ctx

        # Added to allow bot to play another song when it timeout
        # Credit to "LegendBegins" : https://gist.github.com/vbe0201/ade9b80f2d3b64643d854938d40a0a2d
        self.exists = True

        self.current = None
        self.voice = None
        self.next = asyncio.Event()     # Based on Python documentation, deprecated since version 3.8 . Look for possible alternatives
        self.songs = SongQueue()

        self._loop = False
        self._volume = 0.5
        self.skip_votes = set()

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property       # What is the @property decorator for?
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()
            print(f'audio_player_task called')
            print(f'Value of self.loop: {self.loop}')
            if not self.loop:
                # Try to get the next song within 3 minutes.
                # If no song will be added to the queue in time,
                # the player will disconnect due to performance
                # reasons.
                try:
                    async with timeout(180):    # 3 minutes
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    self.exists = False
                    self.bot.loop.create_task(self.stop())
                    return

                print('Init source details')
                self.current.source.volume = self._volume
                print(f'Type of current source {type(self.current.source)}')
                self.voice.play(self.current.source, after=self.play_next_song)
                await self.current.source.channel.send(embed=self.current.create_embed())
            else:
                self.now = discord.FFmpegPCMAudio(self.current.source.stream_url, **YTDLSource.FFMPEG_OPTIONS)
                self.voice.play(self.now, after=self.play_next_song)

            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))
        
        self.next.set()

    def skip(self):
        self.skip_votes.clear()
        # self._loop = False  
        if self.is_playing:
            self.voice.stop()
            # Remove skipped song from the queuelist

    async def stop(self):
        self.songs.clear()
        # self._loop = False
        # Manually added
        self.current = None
        if self.voice:
            await self.voice.disconnect()
            self.voice = None
            
class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state or not state.exists:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage("This command can't be used in DM channels.")

        return True
    
    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send('An error occurred: {}'.format(str(error)))

    @commands.command(name='join', invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context):
        """Joins a voice channel."""

        destination = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name='summon')
    @commands.has_permissions(manage_guild=True)
    async def _summon(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        """Summons the bot to a voice channel.

        If no channel was specified, it joins your channel.
        """

        if not channel and not ctx.author.voice:
            raise VoiceError('You are neither connected to a voice channel nor specified a channel to join.')

        destination = channel or ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name='leave', aliases=['disconnect'])
    @commands.has_permissions(manage_guild=True)
    async def _leave(self, ctx: commands.Context):
        """Clears the queue and leaves the voice channel."""

        if not ctx.voice_state.voice:
            return await ctx.send('Not connected to any voice channel')

        await ctx.voice_state.stop()
        del self.voice_states[ctx.guild.id]

    @commands.command(name='now', aliases=['current', 'playing'])
    async def _now(self, ctx: commands.Context):
        """Displays the currently playing song."""

        # If current is None, means that there is no song being played
        if ctx.voice_state.current is None:
            await ctx.send('Not playing any song right now.')
        else:
            # await ctx.send(f'The current item in queue is: {ctx.songs.__getitem__(0)}')
            await ctx.send(embed=ctx.voice_state.current.create_embed())

    @commands.command(name='queue')
    async def _queue(self, ctx: commands.Context, *, page: int = 1):
        """ Displays items in the queue """
        async def generate_embed_msg():
            queue = ''
            upper_limit = page * items_per_page 
            lower_limit = (page - 1) * items_per_page
            for i, song in enumerate(queue_list[lower_limit:upper_limit], start=lower_limit):
                queue += queue_list[i]
            return queue

        if len(ctx.voice_state.songs) == 0 and ctx.voice_state.current is None:
            return await ctx.send('Empty queue')
        else:
            items_per_page = 5
            queue_list = []

            # Youtube link format
            yt_link = 'https://www.youtube.com/watch?v='

            queue_list.append(f'`1.` [{ctx.voice_state.current.source.title}]({yt_link}{ctx.voice_state.current.source.id})- NOW PLAYING\n')

            for i, song in enumerate(ctx.voice_state.songs[0:], start=1):
                queue_list.append(f'`{i + 1}.` [{song.source.title}]({yt_link}{song.source.id})\n')

            pages = math.ceil(len(queue_list) / items_per_page)
            
            embed = (discord.Embed(description='**{} tracks:**\n\n{}'.format(len(queue_list), await generate_embed_msg()))
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
                # embed_msg = await generate_embed_msg()
                embed = (discord.Embed(description='**{} tracks:**\n\n{}'.format(len(queue_list), await generate_embed_msg()))
                    .set_footer(text='Viewing page {}/{}'.format(page, pages)))

                await message.edit(embed = embed)
                await add_page_reactions()

            # Check for reaction
            def check(reaction, user):
                return not user.bot and reaction.message.id == message.id and (reaction.emoji in ['\u25c0', '\u25b6'])

            while True:
                try:
                    reaction, user = await bot.wait_for('reaction_add', timeout=5, check=check)
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

    # Not in use
    '''
    @commands.command(name='voicestate')
    async def _voicestate(self, ctx: commands.Context):
        print(f"Current voice state: {ctx.voice_state.current}")
    '''

    @commands.command(name='volume')
    async def _volume(self, ctx: commands.Context, *, volume: int):
        """ Sets the volume of the player """
        if not ctx.voice_state.is_playing:
            return await ctx.send('Nothing being played at the moment.')

        if volume not in range(0, 101):
            return await ctx.send('Volume must be between 0 and 100')
            
        ctx.voice_state.current.source.volume = volume / 100
        return await ctx.send('Volume of the player set to {}%'.format(volume))
        
    @_volume.error
    async def volume_error(self, ctx: commands.Context, error):
        # Checks if volume argument is of int data type
        if isinstance(error, commands.BadArgument):
            raise commands.BadArgument(await ctx.send('Volume must be a number'))
        
    @commands.command(name='pause')
    @commands.has_permissions(manage_guild=True)
    async def _pause(self, ctx: commands.Context):
        """Pauses the currently playing song."""
        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            await ctx.message.add_reaction('⏯')            
        
    @commands.command(name='resume')
    @commands.has_permissions(manage_guild=True)
    async def _resume(self, ctx: commands.Context):
        """Resumes a currently paused song."""
        if ctx.voice_state.current and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction('⏯')
        else:
            await ctx.send('There is no song to resume')

    @commands.command(name='stop')
    @commands.has_permissions(manage_guild=True)
    async def _stop(self, ctx: commands.Context):
        """Stops playing song and clears the queue."""
        ctx.voice_state.songs.clear()
        
        if ctx.voice_state.is_playing:
            ctx.voice_state.voice.stop()
            # Sets the current song to be None
            ctx.voice_state.current = None
            await ctx.message.add_reaction('⏹')
        elif not ctx.voice_state.is_playing:
            emoji = get(ctx.guild.emojis, name='Pepehands')
            await ctx.send(f"No music is being played {emoji} . Use me please sirs.")
        else:
            await ctx.send(f'This message should never happen. Message called from stop.')
        
    @commands.command(name='skip')
    async def _skip(self, ctx: commands.Context):
        """ Skips current track. """
        if not ctx.voice_state.is_playing:
            return await ctx.send('Not playing any music right now...')

        await ctx.message.add_reaction('⏭')
        ctx.voice_state.skip()

    @commands.command(name='shuffle')
    async def _shuffle(self, ctx: commands.Context):
        """Shuffles the queue."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        ctx.voice_state.songs.shuffle()
        await ctx.message.add_reaction('✅')

    @commands.command(name='remove')
    async def _remove(self, ctx: commands.Context, index: int):
        """Removes a track from the queue at a given index."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        ctx.voice_state.songs.remove(index - 1)
        await ctx.message.add_reaction('✅')

    @commands.command(name='loop')
    async def _loop(self, ctx: commands.Context):
        """Loops the currently playing track.

        Invoke this command again to unloop the track.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send('Nothing being played at the moment')

        # Inverse boolean value to loop and unloop
        print('Before change loop status: ', ctx.voice_state.loop)
        ctx.voice_state.loop = not ctx.voice_state.loop
        print('After change loop status: ', ctx.voice_state.loop)
        await ctx.message.add_reaction('✅')

        # Replay the song

    @commands.command(name='play')
    async def _play(self, ctx: commands.Context, *, search: str):
        """Plays a song.

        This command automatically searches from various sites if no URL is provided.
        A list of these sites can be found found at: https://rg3.github.io/youtube-dl/supportedsites.html
        """

        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)

        async with ctx.typing():
            try:
                source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
            except YTDLError as e:
                await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
            else:
                song = Song(source)

                await ctx.voice_state.songs.put(song)
                await ctx.send('Enqueued {}'.format(str(source)))

    # TODO: Implement {0}, {1} placeholders to allow choose options with white spaces
    @commands.command(name='choose')
    async def _choose(self, ctx: commands.Context, *argv):
        """ Chooses a random item from options. """
        if len(argv) < 2:
            return await ctx.send("Two or more choices should be given")

        items = [str(i) for i in argv]
        return await ctx.send("Maldbot chose: " + random.choice(items))

    # TODO: Add multiple choices picker
    @commands.command(name='choosemany')
    async def _choosemany(self, ctx: commands.Context, *argv, choices: int):
        """ Chooses {choices} number of items from options. """
        '''
        if len(argv) < 2:
            return await ctx.send("Two or more choices should be given")

        if (choices >= len(argv)):
            return await ctx.send("Choices should be more than options given")
        '''
        
        # Prepares a Discord embed 
        '''
        embed = (discord.Embed(title='Choices'),
                                    description='List of choices...'))
                        .add_field()
        '''

    # TODO: Create poll function
    # Reference code: https://stackoverflow.com/questions/62248341/poll-command-discord-py
    async def _poll(self, ctx: commands.Context, question: str, *options: str):
        """ Creates a poll with choices. """
        author = ctx.author
        
        if len(options) <= 1:
            return await ctx.send("Error! A poll must have more than one option.")
        
        if len(options) >= 2:
            reactions = ['👍', '👎']

        description = []
        for x, option in enumerate(options):
            description += '\n {} {}'.format(reactions[x], option)

        embed = discord.Embed(title = question, color = 3553599, description = ''.join(description))

        react_message = await ctx.send(embed)

        for reaction in reactions[:len(options)]:
            await ctx.message.add_reaction(react_message, reaction)

        embed.set_footer(text='Poll ID: {}'.format(react_message.id))

        
        
    # Additional command to play local .mp3 files for soundboard
    @commands.command(name='playsound')
    async def _playsound(self, ctx: commands.Context, *, search: str):
        """ Plays sound. """
        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)

        async with ctx.typing():
            try:
                # async def get_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
                source = await LocalSource.get_source(ctx, search, loop=self.bot.loop)
                # source = await LocalSource.get_source(ctx, search)
            except YTDLError as e:
                await ctx.send('An error occurred while processing this request: playsound does not exist')
            else:
                sound = Sound(source)

                await ctx.voice_state.songs.put(sound)
                await ctx.send(f'Enqueued a playsound')
    
    @commands.command(name='listsounds')
    async def _listsounds(self, ctx: commands.Context, *, page: int = 1):
        """ Get list of playsounds """
        p = Path('playsounds')
        file_sounds = [x.name for x in p.glob('*.mp3')]
        print('Length of file_sounds variable: ', len(file_sounds))

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
                
            pages = len(embeds) # Total pages

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

                await message.edit(embed = embed)
                await add_page_reactions()

            # Check for reaction
            def check(reaction, user):
                return not user.bot and reaction.message.id == message.id and (reaction.emoji in ['\u25c0', '\u25b6'])

            while True:
                try:
                    reaction, user = await bot.wait_for('reaction_add', timeout=5, check=check)
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

    # Command to play songs from spotify
    @commands.command(name='playspotify')
    async def _playspotify(self, ctx: commands.Context):
        """ Plays songs from spotify. """
        # temp = spotify_source.SpotifySource()
        
    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('You are not connected to any voice channel.')

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError('Bot is already in a voice channel.')
    
bot = commands.Bot('.', description='GanG スター Bot')
bot.add_cog(Music(bot))

'''
@bot.event
async def on_connect():
    # Set avatar of bot
    with open('gravel.jpg', 'rb') as f:
        image = f.read()
    await bot.user.edit(avatar = image)
'''

@bot.event
async def on_ready():
    print('Logged in as \n{0.user.name}\n{0.user.id}'.format(bot))
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='yumans'))

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot.run(TOKEN)
        






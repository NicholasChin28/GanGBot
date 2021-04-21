# TODO: Pass context between different cogs
# TODO: Add an emoji to cancel votes
# TODO: Generate a helper decorator function to calculate the execution time of a function
# Reference link for helper decorator function: https://dev.to/s9k96/calculating-run-time-of-a-function-using-python-decorators-148o
# https://stackoverflow.com/questions/56796991/discord-py-changing-prefix-with-command
# For editing / removing help command: https://stackoverflow.com/questions/45951224/how-to-remove-default-help-command-or-change-the-format-of-it-in-discord-py

# TODO: Generate custom help command for the bot
# TODO: Use the current volume settings for future songs and playsounds
from playsounds import Playsound
from custom_help import CustomHelp
# from spotify_player import SpotifyCog, SpotTrack, SpotifyRealSource, SpotError
# from spotify_player import SpotifyCog
# from custom_poll import MyMenu
import os
import random
from dotenv import load_dotenv

import asyncio
import itertools
import functools
import math
from datetime import datetime

import discord
from discord.ext import commands
from discord.utils import get

from async_timeout import timeout

# Logging errors to the console
import logging

import youtube_dl

# Import Spotify source custom class
# import spotify_source

# For voting
import re
import string
import emoji

# Inspiration code from: https://gist.github.com/vbe0201/ade9b80f2d3b64643d854938d40a0a2d
# Lookup command grouping in the future: https://stackoverflow.com/questions/62460182/discord-py-how-to-invoke-another-command-inside-another-one
# Use tasks, etc. @task.loop for automating timed tasks

# Silence useless bug reports messages
youtube_dl.utils.bug_reports_message = lambda: ''

# Set the logging command line messages
logging.basicConfig(level=logging.INFO)


class VoiceError(Exception):
    pass


class YTDLError(Exception):
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

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 1.0):
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

        partial = functools.partial(cls.ytdl.extract_info, search, download=False, process=False)
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
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
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
        
        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)

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

# TODO: Populate the data with the details from YTDLSource
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

    def addtest(self, index: int, elem):
        self._queue.insert(index, elem)
    # Gets a single item / index


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
        self._volume = 1.0
        # self.skip_votes = set()
        self.votes = set()

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
            print('audio_player_task called')
            print(f'Value of self.loop: {self.loop}')
            if not self.loop:
                # Try to get the next song within 3 minutes.
                # If no song will be added to the queue in time,
                # the player will disconnect due to performance
                # reasons.
                try:
                    async with timeout(180):    # 3 minutes
                        self.current = None
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
            # If loop is true
            # Credit to "guac420": https://gist.github.com/vbe0201/ade9b80f2d3b64643d854938d40a0a2d
            else:
                # Works only for yt-dlc
                self.now = discord.FFmpegPCMAudio(self.current.source.stream_url, **YTDLSource.FFMPEG_OPTIONS)
                self.voice.play(self.now, after=self.play_next_song)

            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            print('play_next_song function')
            raise VoiceError(str(error))
        self.next.set()

    def skip(self):
        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()
        # Manually added
        if self.voice:
            await self.voice.disconnect()
            # self.current = None
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
        if ctx.voice_state.current is None:
            await ctx.send('Not playing any song right now.')
        else:
            await ctx.send(embed=ctx.voice_state.current.create_embed())

    # TODO: Update queue generate_embed_msg after removing an item
    @commands.command(name='queue')
    async def _queue(self, ctx: commands.Context, *, page: int = 1):
        """ Displays items in the queue """
        async def generate_embed_msg():
            queue = ''
            upper_limit = page * items_per_page
            lower_limit = (page - 1) * items_per_page
            for i, _ in enumerate(queue_list[lower_limit:upper_limit], start=lower_limit):
                queue += queue_list[i]
            return queue

        if len(ctx.voice_state.songs) == 0 and ctx.voice_state.current is None:
            return await ctx.send('Empty queue')
        else:
            items_per_page = 5
            queue_list = []

            # Youtube link format
            yt_link = 'https://www.youtube.com/watch?v='

            try:
                queue_list.append(f'`1.` [{ctx.voice_state.current.source.title}]({yt_link}{ctx.voice_state.current.source.id})- NOW PLAYING\n')
            except AttributeError:
                queue_list.append(f'`1.` {ctx.voice_state.current.source.title} (Playsound) - NOW PLAYING\n')

            for i, song in enumerate(ctx.voice_state.songs[0:], start=1):
                try:
                    queue_list.append(f'`{i + 1}.` [{song.source.title}]({yt_link}{song.source.id})\n')
                except AttributeError:
                    queue_list.append(f'`{i + 1}.` {song.source.title} (Playsound)\n')

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

                await message.edit(embed=embed)
                await add_page_reactions()

            # Check for reaction
            def check(reaction, user):
                return not user.bot and reaction.message.id == message.id and (reaction.emoji in ['\u25c0', '\u25b6'])

            while True:
                try:
                    reaction, _ = await bot.wait_for('reaction_add', timeout=60, check=check)
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
        # if ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
        if not ctx.voice_state.is_playing:
            return await ctx.send('Nothing being played at the moment.')

        if volume not in range(0, 101):
            return await ctx.send('Volume must be between 0 and 100')

        # ctx.voice_state.current.source.volume = volume / 100
        ctx.voice_state.current.source.volume = volume / 100
        ctx.voice_state.volume = volume / 100
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
        ctx.voice_state.loop = False    # Unloops the queue
        ctx.voice_state.songs.clear()

        if ctx.voice_state.is_playing:
            # ctx.voice_state.loop = False
            ctx.voice_state.voice.stop()
            # Sets the current song to be None
            ctx.voice_state.current = None
            await ctx.message.add_reaction('⏹')
        elif not ctx.voice_state.is_playing:
            emoji = get(ctx.guild.emojis, name='Pepehands')
            await ctx.send(f"No music is being played {emoji} . Use me please sirs.")
        else:
            await ctx.send('This message should never happen. Message called from stop.')

    @commands.command(name='skip')
    async def _skip(self, ctx: commands.Context):
        """ Skips current track. """
        if not ctx.voice_state.is_playing:
            return await ctx.send('Not playing any music right now...')

        ctx.voice_state.loop = False    # Unloops the queue
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
        # If index 1, remove / skip current playing song
        if not ctx.voice_state.is_playing:
            return await ctx.send('Empty queue.')

        if index == 1:
            ctx.voice_state.skip()
            await ctx.message.add_reaction('✅')
            return

        try:
            ctx.voice_state.songs.remove(index - 2)
            await ctx.message.add_reaction('✅')
        except IndexError:
            return await ctx.send('Invalid queue index')

    @commands.command(name='loop')
    async def _loop(self, ctx: commands.Context):
        """Loops the currently playing track.

        Invoke this command again to unloop the track.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send('Nothing being played at the moment')

        # Inverse boolean value to loop and unloop
        ctx.voice_state.loop = not ctx.voice_state.loop
        await ctx.message.add_reaction('✅')

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

    @commands.command(name='choose')
    async def _choose(self, ctx: commands.Context, *, choose: str):
        """ Chooses a random item """
        options = [x.strip() for x in choose.split(',') if len(x.strip()) > 0]
        print('options: ', options)
        if len(options) < 2:
            return await ctx.send('Two or more choices should be given')

        return await ctx.send('Maldbot chose: ' + random.choice(options))

    # TODO: Add multiple choices picker
    '''
    @commands.command(name='choosemany')
    async def _choosemany(self, ctx: commands.Context):
        """ Chooses {choices} number of items from options. """
        m = MyMenu()
        await m.start(ctx)
    '''

    # Voting feature using embeds and reactions
    @commands.command(name='vote')
    async def _vote(self, ctx: commands.Context, *args):
        print('Prefix of command: ', ctx.prefix)
        print('Starting of args: ')
        # Help details for vote command
        # TODO: Refactor help command to be in another location
        if ctx.prefix == '?':
            return await ctx.send("""To use the vote command, refer to this example: 
.vote {title} [option] [option] (duration)\n  
title: Insert your title here 
option: List as many options you want. Number of options can be up to 20 
duration: How long the vote should last. Currently the duration allowed is between 30 seconds - 5 minutes
The duration must be in seconds (eg. 300 for 5 minutes)""")

        arg_string = ' '.join(args)

        # Emojis for embed
        option_emoji = [''.join((':regional_indicator_', x, ':')) for x in list(string.ascii_lowercase)]

        # Actual emojis for reaction
        option_emoji2 = [emoji.emojize(x, use_aliases=True) for x in option_emoji]

        # Finds the title
        title = re.findall("^{.*}", arg_string)

        # Finds the options
        options = re.findall(r'\[.*?\]', arg_string)

        # Finds the voting duration
        vote_time = re.findall(r"\(\d*?\)", arg_string)

        # Allow voting duration between 30 seconds - 5 minutes
        try:
            vote_time = int(vote_time[0][1:-1])
        except ValueError:
            await ctx.send('Vote time must be a number')
            return

        if vote_time < 30 or vote_time > 300:
            await ctx.send('Vote time must be between 30 seconds - 5 minutes')        
            return

        formatted_options = []
        for x, option in enumerate(options):
            formatted_options += '\n {} {}'.format(option_emoji2[x], option[1:-1])

        # Create embed from title and options
        embed = discord.Embed(title=title[0][1:-1], color=3553599, description=''.join(formatted_options))

        react_message = await ctx.send(embed=embed)

        # For tracking the voters
        voter = ctx.message.author
        if voter.id not in ctx.voice_state.votes:
            ctx.voice_state.votes.add(voter.id)

        for option in option_emoji2[:len(options)]:
            print('Value of options: ', option)
            await react_message.add_reaction(option)

        await react_message.edit(embed=embed)

        # Check for reaction
        def check(reaction, user):
            return not user.bot and reaction.message.id == react_message.id

        try:
            # async with timeout(int(vote_time[0][1:-1])):
            async with timeout(vote_time):
                while True:
                    try:
                        reaction, _ = await bot.wait_for('reaction_add', check=check)
                    except Exception:
                        await ctx.send('Normal exception occurred. Should not happen')
        except asyncio.TimeoutError:
            # Display results here
            the_list = await ctx.channel.fetch_message(react_message.id)
            await ctx.send('Voting ended. Calculating results...')

            vote_counts = [x.count - 1 for x in the_list.reactions]
            print('vote_counts: ', vote_counts)
            highest_count = max(vote_counts)    # Highest vote count

            if sum(vote_counts) == 0:
                pepehands = get(ctx.guild.emojis, name='Pepehands')
                await ctx.send(f'No votes casted.. {pepehands} no one voted')    
            elif vote_counts.count(highest_count) > 1:
                await ctx.send('More than one vote has the highest votes. No winner :(')
            else:
                await ctx.send(f'The winning vote is "{(options[vote_counts.index(highest_count)])[1:-1]}" with a vote count of {highest_count}!')

    @commands.command(name='skipto')
    async def _skipto(self, ctx: commands.Context, index: int):
        """Skips to song number in queue"""
        if not ctx.voice_state.is_playing:
            return await ctx.send('Empty queue.')

        ctx.voice_state.loop = False    # Unloops the queue
        
        if index == 1:
            return await ctx.send("Can't skip to current track")

        # Get the song to skip to
        temp_song = ctx.voice_state.songs.__getitem__(index - 2)

        # Remove it from the queue
        ctx.voice_state.songs.remove(index - 2)

        # Add the song to skip to the first item of the queue
        ctx.voice_state.songs.addtest(0, temp_song)

        # Skip the current playing song, so that it plays the song to be skipped to immediately
        ctx.voice_state.skip()

    @commands.command(name='chelp')
    async def _chelp(self, ctx: commands.Context):
        """ Custom help command """
        embed = discord.Embed()
        embed.description = "[Test]()"
        await ctx.send(embed=embed)
        
    # Try creating splay command here
    '''
    @commands.command(name='splay')
    async def _splay(self, ctx: commands.Context, search: str):
        spotify_cog = self.bot.get_cog('SpotifyCog')
        if spotify_cog is not None:
            print('Cog exists')
            track = await SpotifyCog.splay2(ctx, search)
            print('Track has value: ', track)
            await ctx.voice_state.songs.put(track)

            return await ctx.send(f'Enqueued a spotify track')

        await ctx.send('Cannot add track spot track')
    '''

    '''
    @commands.command(name='splay_temp')
    async def _splay(self, ctx: commands.Context, search: str):
        track = await SpotifyCog.splay2(ctx, search)
        await ctx.voice_state.songs.put(track)

        return await ctx.send(f'Enqueued a spotify track')
    '''

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

    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('You are not connected to any voice channel.')

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError('Bot is already in a voice channel.')


bot = commands.Bot(command_prefix=['.', '?'], description='GanG スター Bot')
# Custom help embed


bot.add_cog(Music(bot))
bot.add_cog(Playsound(bot))
bot.add_cog(CustomHelp(bot))

# Temporary cog for SpotifyCog
# bot.add_cog(SpotifyCog(bot))

# bot.add_cog(Greetings(bot))

'''
@bot.event
async def on_connect():
    # Set avatar of bot
    with open('Maldbot-01.jpg', 'rb') as f:
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



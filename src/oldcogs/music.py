# Cogs to store music commands for bot
from os import pipe
import random
import asyncio
import itertools
import functools
import math

import discord
from discord.ext import commands
from discord.utils import get
import typing

from async_timeout import timeout

# Logging errors to the console
import logging

import youtube_dl

from helper import helper
import validators
from models.emojis import Emojis

# Inspiration code from: https://gist.github.com/vbe0201/ade9b80f2d3b64643d854938d40a0a2d

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
        'options': f'-vn -re',
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
    async def create_source(cls, ctx: commands.Context, search: str, timestamp: int = 0, *, loop: asyncio.BaseEventLoop = None):
        print('create_source function called')
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

        # Duration of the video
        # print(f'Total duration of the video: {info.get("duration")}')
        
        # Set the value of FFMPEG_OPTIONS options
        if not isinstance(timestamp, int):  # Means that timestamp is a VideoRange class
            if timestamp.end_time is not None:
                cls.FFMPEG_OPTIONS['options'] = (f'-vn -ss {timestamp.start_time.tm_hour}:{timestamp.start_time.tm_min}:{timestamp.start_time.tm_sec}'
                                                f' -to {timestamp.end_time.tm_hour}:{timestamp.end_time.tm_min}:{timestamp.end_time.tm_sec}')
            else:
                # Debug here
                print(f'Value of start hour: {timestamp.start_time.tm_hour}')
                print(f'Value of start minute: {timestamp.start_time.tm_min}')
                print(f'Value of start second: {timestamp.start_time.tm_sec}')
                cls.FFMPEG_OPTIONS['options'] = f'-vn -ss {timestamp.start_time.tm_hour}:{timestamp.start_time.tm_min}:{timestamp.start_time.tm_sec}'
        else:
            cls.FFMPEG_OPTIONS['options'] = f'-vn'

        print('Finish setting up options attribute for FFMPEG_OPTIONS')
        

        # Refer to: https://stackoverflow.com/questions/62354887/is-it-possible-to-seek-through-streamed-youtube-audio-with-discord-py-play-from
        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)

        # TODO: Try saving the ffmpeg seeked source to local file, then play from it, instead of 
        # TODO: Search in discord.py Discord group, "audio seek"
        # return cls(ctx, discord.FFmpegPCMAudio("./testing.mp3"), data=info)

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

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property       
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
                print('Else block in audio_player_task method')
                print(f'Value of YTDLSource ffmpeg options: {YTDLSource.FFMPEG_OPTIONS}')
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

    @commands.Cog.listener()
    async def on_ready(self):
        print('Music cog loaded')

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

    @commands.command(name='leave', aliases=['disconnect'])
    @commands.has_permissions(manage_guild=True)
    async def _leave(self, ctx: commands.Context):
        """Clears the queue and leaves the voice channel."""

        if not ctx.voice_state.voice:
            return await ctx.send('Not connected to any voice channel')

        await ctx.voice_state.stop()
        del self.voice_states[ctx.guild.id]

    # TODO: Add more error checking for invalid track number
    @commands.command(name='track')
    async def _now(self, ctx: commands.Context, track: typing.Optional[int] = 1):
        """Gets the track info"""
        if ctx.voice_state.current is None:
            return await ctx.send('Not playing any song right now.')

        print(f'Length of songs: {len(ctx.voice_state.songs)}')
        print(f'Variable type of ctx.voice_state.songs: {type(ctx.voice_state.songs)}')

        if track < 1:
            return await ctx.send('Invalid track number')
        elif track == 1:
            return await ctx.send(embed=ctx.voice_state.current.create_embed())
        else:
            try:
                print(f'Type of current source: {type(ctx.voice_state.current)}')
                print(f'Type of songs voice state: {type(ctx.voice_state.songs[0])}')
                print(f'Value of track - 2: {track - 2}')
                await ctx.send(embed=ctx.voice_state.songs[track - 2].create_embed())
            except IndexError:
                await ctx.send("Uh-oh, that track number is not valid")
                await ctx.send("Try checking the queue again.")
                queue_cmd = self.bot.get_command("queue")
                await queue_cmd(ctx)

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
                    await message.add_reaction(Emojis.reverse_button)
                if pages > page:
                    await message.add_reaction(Emojis.play_button)

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
                return not user.bot and reaction.message.id == message.id and (reaction.emoji in [Emojis.reverse_button, Emojis.play_button])

            while True:
                try:
                    reaction, _ = await self.bot.wait_for('reaction_add', timeout=60, check=check)
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

    @commands.command(name='volume')
    async def _volume(self, ctx: commands.Context, *, volume: typing.Optional[int]):
        """ Sets the volume of the player """
        if not volume: 
            await ctx.send(f'Current volume: {int(ctx.voice_state.volume * 100)}%')
        else:
            if volume not in range(0, 101):
                return await ctx.send('Volume must be between 0 and 100')

            if ctx.voice_state.is_playing:
                ctx.voice_state.current.source.volume = volume / 100

            ctx.voice_state.volume = volume / 100
            return await ctx.send(f'Volume of the player set to {volume}%')

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
            await ctx.message.add_reaction(Emojis.play_pause)            

    @commands.command(name='resume')
    @commands.has_permissions(manage_guild=True)
    async def _resume(self, ctx: commands.Context):
        """Resumes a currently paused song."""
        if ctx.voice_state.current and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction(Emojis.play_pause)
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
            await ctx.message.add_reaction(Emojis.stop_button)
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
        await ctx.message.add_reaction(Emojis.next_button)

        ctx.voice_state.skip()

    @commands.command(name='shuffle')
    async def _shuffle(self, ctx: commands.Context):
        """Shuffles the queue."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        ctx.voice_state.songs.shuffle()
        await ctx.message.add_reaction(Emojis.tick_emoji)

    @commands.command(name='remove')
    async def _remove(self, ctx: commands.Context, index: int):
        """Removes a track from the queue at a given index."""
        # If index 1, remove / skip current playing song
        if not ctx.voice_state.is_playing:
            return await ctx.send('Empty queue.')

        if index == 1:
            ctx.voice_state.skip()
            await ctx.message.add_reaction(Emojis.tick_emoji)
            return

        try:
            ctx.voice_state.songs.remove(index - 2)
            await ctx.message.add_reaction(Emojis.tick_emoji)
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
        await ctx.message.add_reaction(Emojis.tick_emoji)

    @commands.command(name='play')
    async def _play(self, ctx: commands.Context, *search):
        """Plays a song.

        This command automatically searches from various sites if no URL is provided.
        A list of these sites can be found found at: https://rg3.github.io/youtube-dl/supportedsites.html
        """

        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)

        async with ctx.typing():
            try:
                # Check if the last argument is a timestamp / timestamp range
                # TODO: Check if it is not a URL
                timestamp = None
                if not validators.url(search[-1]):
                    timestamp = helper.parse_time(search[-1])
                
                # If timestamp is None, means that the last argument is not a timestamp / timestamp range
                if timestamp is not None:
                    print(f'Search query with timestamp: {" ".join(search[0:-1])}')
                    source = await YTDLSource.create_source(ctx, ' '.join(search[0:-1]), timestamp=timestamp, loop=self.bot.loop)
                else:
                    print(f'Search query without timestamp: {" ".join(search)}')
                    source = await YTDLSource.create_source(ctx, ' '.join(search), loop=self.bot.loop)

            except YTDLError as e:
                await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
            else:
                song = Song(source)

                await ctx.voice_state.songs.put(song)
                await ctx.send('Enqueued {}'.format(str(source)))

    # TODO: Add multiple choices picker
    '''
    @commands.command(name='choosemany')
    async def _choosemany(self, ctx: commands.Context):
        """ Chooses {choices} number of items from options. """
        m = MyMenu()
        await m.start(ctx)
    '''


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

def setup(bot):
    bot.add_cog(Music(bot))
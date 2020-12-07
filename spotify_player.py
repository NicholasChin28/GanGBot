# Player for Discord Spotify Bot
import os
import sys
import asyncio

import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth

from pprint import pprint
from time import sleep

import spotdl
import subprocess

# Discord
import discord
from discord.ext import commands

import functools
from pathlib import Path

# Add discord.PCMVolumeTransformer 
# TODO: Add listener to detect when the current track has finished playing
# TODO: Use SpotDl instead to get .mp3 files of Spotify tracks and to download
# TODO: Store some of the downloaded .mp3 files in the file system. For faster access
# TODO: Store references to the file in a database
# https://towardsdatascience.com/sql-on-the-cloud-with-python-c08a30807661
class SpotError(Exception):
    pass

class SpotifyRealSource(discord.PCMVolumeTransformer):
    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        # self.duration = YTDLSource.parse_duration(data.get('duration'))
        # self.title = data.get('title')

    def __str__(self):
        return f'PlaysoundSource class __str__ function'

    @classmethod
    async def get_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(SpotifyRealSource.extract_info, search)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise SpotError('Spotify track does not exist')

        location = Path(f"{os.getenv('APP_PATH')}/{search}.mp3")
        return cls(ctx, discord.FFmpegPCMAudio(location), data = data)

    @staticmethod
    def extract_info(search: str):
        location = Path(f"{os.getenv('APP_PATH')}/{search}.mp3")
        if location.is_file():
            return True

class SpotTrack():
    __slots__ = ('source', 'requester')

    def __init__(self, source: SpotifyRealSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        embed = discord.Embed(title='Spotify embed')

        return embed

class SpotifyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Spotify cog loaded!')
        
    @commands.command(name='spsearch')
    async def _spsearch(self, ctx: commands.Context, *, search: str):
        """ Searches Spotify for the track. """
        results = await SpotifySource.search_track(search)

        # Generate Spotify search embed message
        base_embed = discord.Embed(title='Spotify Search',
                                    description='Spotify search results',
                                    color=discord.Color.blurple())
                            
        temp_embed = discord.Embed().add_field(name='Test', value='test')
                        
        
        for num, i in enumerate(results, start=1):
            base_embed.add_field(name=f'```Track {num}```',
                                    value=f'```Title: {i["title"]}\n Artist: {i["artist"]}\n {i["duration"]}\n URL: {i["url"]}```')
            # base_embed.add_field(name=chr(173), value=chr(173))   # Causes very weird orientation
            # base_embed += (discord.Embed) 
        
        # base_embed.add_field(name='Track', value=f'Name: Something\n Duration: 3ms 4s\n URL: Something/something')

        await ctx.send(embed=base_embed)

    # TODO: Download and play track
    @commands.command(name='splay')
    async def _splay(self, ctx: commands.Context, *, search: str):
        """ Plays downloaded Spotify track. """
        # if not ctx.voice_state.voice:
        #     await ctx.invoke(self._join)

        async with ctx.typing():
            try:
                source = await SpotifyRealSource.get_source(ctx, search, loop=self.bot.loop)
            except SpotError as e:
                await ctx.send(e)
            else:
                sound = SpotTrack(source)

                await ctx.voice_state.songs.put(sound)
                await ctx.send(f'Enqueued a spotify track')



class SpotifySource:

    search_results = []

    # TODO: Implement SpotifySource(link)
    # def __init__(self, uri: str):
    def __init__(self):
        '''
        metadata = self.get_metadata(uri)
        self.title = metadata.get('title')
        self.duration = metadata.get('duration')
        self.artist = metadata.get('artist')
        self.url = metadata.get('url')
        '''

        '''
        self.title = metadata['title']
        self.duration = metadata['duration']
        self.artist = metadata['artist']
        self.uri = metadata['uri']
        '''

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)

        duration = []
        if hours > 0:
            duration.append(f'{hours} h')
        if minutes > 0:
            duration.append(f'{minutes} m')
        if seconds > 0:
            duration.append(f'{seconds} s')

        return ' '.join(duration)
            
    def play_song(self, link: str):
        scope = 'user-read-playback-state, user-modify-playback-state'
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

        # Shows playing devices
        res = sp.devices()
        pprint(res)

        # Set volume 
        sp.volume(100)

        # Change track
        sp.start_playback(uris=[link])

    # Temporary function to print results of search_results variable
    def search_results_list(self):
        pprint(self.search_results)

    # Use bot2.py queue. (Currently will have YTDLSource, LocalSource, SpotifySource)
    # May need to manually monitor queue. Spotipy does not seem to monitor queue
    def add_to_queue(self, uri: str):
        scope = 'user-read-playback-state, user-modify-playback-state'
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

        sp.add_to_queue(uri)

    # Get spotify track metadata
    @staticmethod
    async def search_track(uri: str):
        # Refer to https://developer.spotify.com/documentation/web-api/reference/search/search/
        """
        1. Title
        2. Duration
        3. URI
        4. Artist
        """
        search_results = []
        scope = 'user-library-read'
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, cache_path='.cache'))

        res = sp.search(q=uri)

        tracks = res['tracks']
        print('Number of items: ', len(tracks['items']))
        for item in tracks['items']:
            title = f"{item['name']}"
            duration = f"Duration: {SpotifySource.parse_duration(item['duration_ms'] // 1000)}"
            url = f"{item['external_urls']['spotify']}"
            artist = f"{item['artists'][0]['name']}"

            print("Track name: ", title)
            print("Track duration: ", duration)
            print("Track url: ", url)
            print("Track artist: ", artist)
            
            track_details = {"title": title, "duration": duration, "url": url, "artist": artist}
            search_results.append(track_details)
            # self.search_results.append(track_details)
            
        pprint(search_results)
        return search_results

    def pause(self):
        scope = 'user-library-read, user-modify-playback-state'
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
        sp.start_playback()

    

    # In development functions
    def get_current_playback(self):
        scope = 'user-library-read, user-read-playback-state'
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
        details = sp.currently_playing()
        print('Details: ', details)

    # Downloads Spotify track using SpotDl
    def download_track(self, url: str):
        subprocess.call(f'spotdl {url}',
            creationflags=subprocess.CREATE_NEW_CONSOLE)    


# spot = SpotifySource()
# spot.search_track('abba')



# spot = SpotifySource()
# spot.download_track('https://open.spotify.com/track/6Ftb6ULdD3PBAdgi5atz3h')
# spot.get_current_playback()
# asyncio.run(spot.spotify_player_task())
# loop = asyncio.get_event_loop()
# asyncio.get_running_loop()
'''
spot = SpotifySource('Daddy daddy do amalee')
spot.pause()
'''

'''
spot = SpotifySource()
spot.search_results_list()
spot.play_song('spotify:track:2TVUmfNirOmgg9anvXJmZY')
spot.add_to_queue('spotify:track:3MnmutTVHSZ5g2Ybl1P6JT') # Violet Evergarden
SpotifySource.play_song('spotify:track:6gdLoMygLsgktydTQ71b15')
'''










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

# Add discord.PCMVolumeTransformer 
# TODO: Add listener to detect when the current track has finished playing
# TODO: Use SpotDl instead to get .mp3 files of Spotify tracks and to download
# TODO: Store some of the downloaded .mp3 files in the file system. For faster access
# TODO: Store references to the file in a database
# https://towardsdatascience.com/sql-on-the-cloud-with-python-c08a30807661
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
    def search_track(self, uri: str):
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
            duration = f"Duration: {self.parse_duration(item['duration_ms'] // 1000)}"
            url = f"{item['external_urls']['spotify']}"
            artist = f"{item['artists'][0]['name']}"

            print("Track name: ", title)
            print("Track duration: ", duration)
            print("Track url: ", url)
            print("Track artist: ", artist)
            
            track_details = {"title": title, "duration": duration, "url": url, "artist": artist}
            search_results.append(track_details)
            self.search_results.append(track_details)
            
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


spot = SpotifySource()
spot.search_track('abba')
spot.download_track('https://open.spotify.com/track/2245x0g1ft0HC7sf79zbYN')
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










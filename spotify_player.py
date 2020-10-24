# Player for Discord Spotify Bot
import os
import sys

import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth

from pprint import pprint
from time import sleep

# Add discord.PCMVolumeTransformer 
# TODO: Add listener to detect when the current track has finished playing
class SpotifySource:

    # TODO: Implement SpotifySource(link)
    def __init__(self, uri: str):
        metadata = self.get_metadata(uri)
        self.title = metadata.get('title')
        self.duration = metadata.get('duration')
        self.artist = metadata.get('artist')
        self.uri = metadata.get('uri')
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

    def search_song(self, query: str):
        # Refer to https://developer.spotify.com/documentation/web-api/reference/search/search/
        scope = 'user-library-read'
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

        res = sp.search(q=query)

        tracks = res['tracks']
        for item in tracks['items']:
            '''
            Gets track values:
            1. Track name - Track Artist
            2. Track duration
            3. Track URI
            '''
            name = f"{item['name']} - {item['artists'][0]['name']}"
            duration = f"Duration: {self.parse_duration(item['duration_ms'] // 1000)}"
            uri = f"{item['uri']}"

            print("Track name: ", name)
            print("Track duration: ", duration)
            print("Track uri: ", uri)
            
            track_details = {"name": name, "duration": duration, "uri": uri}
            self.search_results.append(track_details)
            
            
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
    def get_metadata(self, uri: str):
        """
        1. Title
        2. Duration
        3. URI
        4. Artist
        """
        search_results = []
        scope = 'user-library-read'
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

        res = sp.search(q=uri)

        tracks = res['tracks']
        for item in tracks['items']:
            title = f"{item['name']}"
            duration = f"Duration: {self.parse_duration(item['duration_ms'] // 1000)}"
            uri = f"{item['uri']}"
            artist = f"{item['artists'][0]['name']}"

            print("Track name: ", title)
            print("Track duration: ", duration)
            print("Track uri: ", uri)
            print("Track artist: ", artist)
            
            track_details = {"title": title, "duration": duration, "uri": uri, "artist": artist}
            # search_results.append(track_details)
            # self.search_results.append(track_details)
            return track_details

    def pause(self):
        scope = 'user-library-read, user-modify-playback-state'
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
        sp.start_playback()


spot = SpotifySource('Daddy daddy do amalee')
spot.pause()
'''
spot = SpotifySource()
spot.search_song('Daddy daddy do')
spot.search_results_list()
spot.play_song('spotify:track:2TVUmfNirOmgg9anvXJmZY')
spot.add_to_queue('spotify:track:3MnmutTVHSZ5g2Ybl1P6JT') # Violet Evergarden
SpotifySource.play_song('spotify:track:6gdLoMygLsgktydTQ71b15')
'''










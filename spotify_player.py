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
# Add listener to detect when the current track has finished playing
class SpotifySource:

    search_results = []
    # Duration is in seconds
    # Not calculating days. Assuming spotify track would never exceed 24 hours
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

    # TODO: Add to playlist queue
    # May need to manually monitor queue. Spotipy does not seem to monitor queue
    def add_to_queue(self, link: str):
        scope = 'user-read-playback-state, user-modify-playback-state'
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

        sp.add_to_queue(link)



spot = SpotifySource()
spot.search_song('Daddy daddy do')
spot.search_results_list()
spot.play_song('spotify:track:2TVUmfNirOmgg9anvXJmZY')
spot.add_to_queue('spotify:track:6gdLoMygLsgktydTQ71b15')
# SpotifySource.play_song('spotify:track:6gdLoMygLsgktydTQ71b15')
'''
scope = "user-library-read"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

results = sp.current_user_saved_tracks()
for idx, item in enumerate(results['items']):
    track = item['track']
    print(idx, track['artists'][0]['name'], " – ", track['name'])
'''

# player.py from https://github.com/plamere/spotipy/blob/master/examples/player.py
'''
scope = 'user-read-playback-state,user-modify-playback-state'
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))


# Shows playing devices
res = sp.devices()
pprint(res)

# Change track
sp.start_playback(uris=['spotify:track:6gdLoMygLsgktydTQ71b15'])

# Change volume
sp.volume(100)
sleep(2)
sp.volume(50)
sleep(2)
sp.volume(100)
'''




# Read a user's saved tracks
'''
scope = 'user-library-read'

if len(sys.argv) > 1:
    username =  sys.argv[1]
else:
    print("Usage: %s username" % (sys.argv[0],))
    sys.exit()

token = util.prompt_for_user_token(username, scope)
print(f'Value of token: {token}')

if token:
    sp = spotipy.Spotify(auth=token)
    results = sp.current_user_saved_tracks()
    for item in results['items']:
        track = item['track']
        print(track['name'] + ' - ' + track['artists'][0]['name'])
else:
    print("Can't get token for", username)
'''

# Uses Spotify Premium
'''
scope = 'user-read-playback-state,user-modify-playback-state'

if len(sys.argv) > 1:
    username = sys.argv[1]
else:
    print("Usage: %s username" % (sys.argv[0],))
    sys.exit()

token = util.prompt_for_user_token(username, scope)
print(f'Value of token: {token}')

if token:
    sp = spotipy.Spotify(auth=token)
    # Shows playing devices
    res = sp.devices()
    pprint(res)

    # Change track
    sp.start_playback(uris=['spotify:track:6gdLoMygLsgktydTQ71b15'])

    # Change volume
    sp.volume(100)
    sleep(2)
    sp.volume(50)
    sleep(2)
    sp.volume(100)
else:
    print("Can't get token for", username)
'''



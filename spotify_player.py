# Player for Discord Spotify Bot
import os
import sys

import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth

from pprint import pprint
from time import sleep

class SpotifySource:
    def search_song(query: str):
        # Refer to https://developer.spotify.com/documentation/web-api/reference/search/search/
        scope = 'user-library-read'
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

        res = sp.search(q=query)

        tracks = res['tracks']
        for item in tracks['items']:
            print(f"{item['name']} - {item['artists'][0]['name']}")
        
SpotifySource.search_song('Toxic')
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



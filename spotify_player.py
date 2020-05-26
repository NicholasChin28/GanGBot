# Player for Discord Spotify Bot
import os
import sys

import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth

from pprint import pprint
from time import sleep

# Set environment variables for Windows platform
# set SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
# set SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

# Example from official Spotipy documentation 
# Albums by artist 'Birdy'
''' 
birdy_uri = 'spotify:artist:2WX2uTcsvV5OnS0inACecP'
spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

results = spotify.artist_albums(birdy_uri, album_type='album')
albums = results['items']
while results['next']:
    results = spotify.next(results)
    albums.extend(results['items'])

for album in albums:
    print(album['name'])
'''

# Example 2
'''
lz_uri = 'spotify:artist:36QJpDe2go2KgaRleHCDTp'

spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
results = spotify.artist_top_tracks(lz_uri)

for track in results['tracks'][:10]:
    print(f'track : {track["name"]}')
    print(f'audio : {track["preview_url"]}')
    print(f'track : {track["album"]["images"][0]["url"]}')
    print()
'''

# Example 3
'''
spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

if len(sys.argv) > 1:
    name = ' '.join(sys.argv[1:])
else:
    name = 'Radiohead'

results = spotify.search(q='artist:' + name, type='artist')
items = results['artists']['items']
if len(items) > 0:
    artist = items[0]
    print(artist['name'], artist['images'][0]['url'])
'''

# player.py from https://github.com/plamere/spotipy/blob/master/examples/player.py
'''
scope = 'user-read-playback-state,user-modify-playback-state'
sp = spotipy.Spotify(client_credentials_manager=SpotifyOAuth(scope=scope))


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

# player.py version 2
# Error suggests that Spotify Premum is required.
# TODO: Buy from Shopee once I get back my phone.
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



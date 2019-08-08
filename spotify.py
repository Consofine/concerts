import sys
import spotipy
import spotipy.util as util
import pandas as pd
import keys



def get_artists(arr, tracks):
    for i, item in enumerate(tracks['items']):
        if (item['track']['artists'][0]['name'] not in arr):
            arr.append(item['track']['artists'][0]['name'])

def print_artists(arr):
    for i in range(len(arr)):
        print('{}: {}'.format(i, arr[i]))

def main():
    # import keys/info
    clientId = keys.spotifyClientId
    clientSecret = keys.spotifyClientSecret
    redirectUrl = keys.spotifyRedirectUrl
    scope = 'playlist-read-private'
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        print('Missing argument: username')
        sys.exit()
    token = util.prompt_for_user_token(
        username, scope, clientId, clientSecret, redirectUrl)
    if token:
        artists = []
        sp = spotipy.Spotify(auth=token)
        playlists = sp.user_playlists(username)
        for playlist in playlists['items']:
            print(playlist['name'])
        playlists = sp.current_user_playlists()
        for playlist in playlists['items']:
            print('Working: {}'.format(playlist['name']))
            results = sp.user_playlist(username, playlist['id'],
                                       fields="tracks,next")
            tracks = results['tracks']
            get_artists(artists, tracks)
            while tracks['next']:
                tracks = sp.next(tracks)
                get_artists(artists, tracks)
        print_artists(artists)
        newDict = pd.DataFrame(artists, columns=['artist'])
        with open('artists.csv', 'w') as f:
            newDict.to_csv(f)
    else:
        print("Can't get token for", username)

main()

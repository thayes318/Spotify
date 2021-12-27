"""
Get Spotify playlist data.

quick script to pull data from a Spotify playlist
and track it in a local Excel file

"""
import requests
import pandas as pd
from openpyxl import load_workbook
import datetime as dt
import spotify_config  # separate file on local machine with acct credentials

get_token = requests.post('https://accounts.spotify.com/api/token',
                          params=spotify_config.token_params,
                          headers=spotify_config.token_headers).json()
auth = {'Authorization': 'Bearer ' + get_token['access_token']}

# pull the full list of playlists & get track data for the designated playlist
playlists = requests.get('https://api.spotify.com/v1/me/playlists',
                         headers=auth).json()
for playlist in playlists['items']:
    if playlist['name'] == 'Release Radar':
        tracks = requests.get(
            'https://api.spotify.com/v1/playlists/' + playlist['id'] + '/tracks',
            headers=auth,
            params={'fields': 'items'}
            ).json()
tracks = tracks['items']

# separately, build a list of track ids from above and use it to get features
# from a separate API endpoint
track_ids = [track['track']['id'] for track in tracks]
id_list = {'ids': ','.join(track_ids)}
track_features = requests.get(
    'https://api.spotify.com/v1/audio-features',
    headers=auth,
    params=id_list
    ).json()

# pull the two data sources together into one line
track_columns = []
for x, y in enumerate(tracks):  # use enumerate here
    track_line = [y['track']['name'],
                  y['added_at'],
                  y['track']['artists'][0]['name'],
                  y['track']['popularity'],
                  y['track']['id'],
                  track_features['audio_features'][x]['acousticness'],
                  track_features['audio_features'][x]['danceability'],
                  track_features['audio_features'][x]['energy'],
                  track_features['audio_features'][x]['instrumentalness'],
                  track_features['audio_features'][x]['key'],
                  track_features['audio_features'][x]['liveness'],
                  track_features['audio_features'][x]['loudness'],
                  track_features['audio_features'][x]['mode'],
                  track_features['audio_features'][x]['speechiness'],
                  track_features['audio_features'][x]['tempo'],
                  track_features['audio_features'][x]['time_signature'],
                  track_features['audio_features'][x]['valence']
                  # track_features['audio_features'][x]['url']
                  ]

    track_columns.append(track_line)

# build a dataframe with the nested list to prep for transfer to Excel
df = pd.DataFrame(track_columns, columns=['track_name', 'week', 'artist_name',
                                          'popularity', 'id', 'acousticness',
                                          'danceability', 'energy',
                                          'instrumentalness', 'key',
                                          'liveness', 'loudness',
                                          'mode (1 = major key)',
                                          'speechiness', 'tempo (bpm)',
                                          'time_signature',
                                          'happiness (valence)'])

# transfer to Excel with a new tab for today's date
book = load_workbook(spotify_config.file_location)
thismonth = str(dt.date.today().month)
thisday = str(dt.date.today().day)
today = str(dt.date.today().year)+'-'+thismonth+'-'+thisday

with pd.ExcelWriter(spotify_config.file_location,
                    engine='openpyxl') as writer:
    writer.book = book
    writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
    df.to_excel(writer, sheet_name=str(today))
    writer.save()

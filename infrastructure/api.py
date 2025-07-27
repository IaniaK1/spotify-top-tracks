import os
import requests
from domain.models import Token, Artist, Track
from dotenv import load_dotenv
load_dotenv()


class SpotifyAPI:
    """
    Class for Spotify API interaction.
    """
    def __init__(self, spotify_client_id=None, spotify_client_secret=None):
        self.url = 'https://api.spotify.com/v1'
        self.spotify_client_id = spotify_client_id or os.environ.get('spotify_client_id')
        self.spotify_client_secret = spotify_client_secret or os.environ.get('spotify_client_secret')
        self._token_spotify = None
        self._token_spotify = self._request_token()

    @property
    def token(self):
        """
        Returns a valid access token for the Spotify API.

        If the current token is expired or doesn't exist, automatically requests a new one.

        Returns:
            str: Valid access token.
        """
        if not self._token_spotify or not self._token_spotify.valid:
            self._token_spotify = self._request_token()
        return self._token_spotify.token

    def _request_token(self):
        """
        Requests and returns a new access token for the Spotify API using client credentials flow.

        Returns:
            Token: Valid access token for authentication in Spotify API requests.
        """
        try:
            token_url = 'https://accounts.spotify.com/api/token'

            headers = {'Content-Type': 'application/x-www-form-urlencoded'}

            body = {
                'grant_type': 'client_credentials',
                'client_id': f'{self.spotify_client_id}',
                'client_secret': f'{self.spotify_client_secret}'
            }
            
            request = requests.post(token_url, headers=headers, data=body)
            request.raise_for_status()

            token = request.json()['access_token']
            expires_in = request.json()['expires_in']
            return Token(token, expires_in)
        except Exception as e:
            print(f'Error requesting token: {e}')
            return None

    def search_artist(self, artist):
        """
        Searches for an artist ID by name using the Spotify API.

        Args: 
            artist (str): Artist name.

        Returns:
            Artist: Found Artist object.
        """
        try:
            url = self.url + f'/search'
            
            headers = {
                'Authorization': f'Bearer {self.token}'
            }

            request = requests.get(url, headers=headers, params={'q': artist, 'type': 'artist', 'limit': 1})

            request.raise_for_status()
            result = request.json()

            artist_data = result['artists']['items'][0]
        except Exception as e:
            print(f'Error searching for artist {artist}: {e}')
            return

        return Artist(name=artist_data['name'], artist_id=artist_data['id'])
    
    def search_top_tracks(self, artist: Artist):
        """
        Searches for an artist's most popular tracks using the Spotify API.

        Args:
            artist (Artist): Artist object.

        Returns:
            dict: Dictionary containing the artist and a list of their top tracks (Track objects).
        """
        try:
            url = self.url + f'/artists/{artist.artist_id}/top-tracks'

            headers = {
                'Authorization': f'Bearer {self.token}'
            }

            request = requests.get(url, headers=headers)
            request.raise_for_status()
            response = request.json()

            tracks = []
            for track in response['tracks']:
                tracks.append(Track(
                    track_name=track['name'],
                    track_id=track['id'],
                    popularity=track['popularity'],
                    album=track['album']['name']
                ))
        except Exception as e:
            print(f'Error searching tracks for artist {artist}: {e}')
            return

        return {'artist': artist, 'top_tracks': tracks}

import unittest
from unittest.mock import patch, mock_open
import json
import os
import csv
from infrastructure.api import SpotifyAPI
from infrastructure.database import Database, session, Artists, TopTracks
from domain.models import Artist, Track, Token
from datetime import date
from io import StringIO
from contextlib import redirect_stdout

class TestsSpotifyAPI(unittest.TestCase):
    @patch('requests.post')
    def test_request_token(self, mock_post):
        """
        Tests if the _request_token method returns a valid Token object when receiving API response.
        """
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'access_token': 'ABCD1234',
            'expires_in': 3600
        }

        client_id = 'my_client_id'
        client_secret = 'my_client_secret'

        api = SpotifyAPI(client_id, client_secret)
        token_obj = api._request_token()
        
        mock_post.assert_called_with(
            'https://accounts.spotify.com/api/token',
            headers = {'Content-Type': 'application/x-www-form-urlencoded'},
            data = {'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret}
        )

        self.assertEqual(token_obj.token, 'ABCD1234')
        self.assertEqual(token_obj._expires_in, 3600)
        self.assertTrue(token_obj.valid)

    @patch('requests.post')
    @patch('requests.get')
    def test_search_artist(self, mock_get, mock_post):
        """
        Tests if search_artist correctly returns the Artist object when querying the Spotify API.
        """
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'access_token': 'ABCD1234',
            'expires_in': 3600
            }

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'artists': {
                'items': [
                    {'id': '123', 'name': 'Linkin Park'}
                ]
            }
        }

        api = SpotifyAPI('my_client_id', 'my_client_secret')
        artist = api.search_artist('Linkin Park')

        self.assertEqual(artist.name, 'Linkin Park')
        self.assertEqual(artist.artist_id, '123')

        mock_get.assert_called_with(
            'https://api.spotify.com/v1/search',
            headers = {'Authorization': f'Bearer {api.token}'},
            params={'q': 'Linkin Park', 'type': 'artist', 'limit': 1}
        )

    @patch('requests.get')
    @patch('requests.post')
    def test_search_top_tracks(self, mock_post, mock_get):
        """
        Tests if search_top_tracks correctly returns the information of the artist's most popular tracks.
        """
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'access_token': 'ABCD1234',
            'expires_in': 3600
            }

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'tracks': [
                {
                    'name': 'In the End',
                    'popularity': 91,
                    'album': {'name': 'Hybrid Theory'},
                    'id': '123456abcde'
                },
                {
                    'name': 'Numb',
                    'popularity': 90,
                    'album': {'name': 'Meteora'},
                    'id': '654321ebca'
                }
            ]
        }

        api = SpotifyAPI('my_client_id', 'my_client_secret')
        artist = Artist(name = 'Linkin Park', artist_id= 'artist_id')
        result = api.search_top_tracks(artist)

        mock_get.assert_called_with(
            'https://api.spotify.com/v1/artists/artist_id/top-tracks',
            headers = {'Authorization': f'Bearer {api.token}'}
        )

        self.assertEqual(result['artist'].name, 'Linkin Park')
        self.assertEqual(result['artist'].artist_id, 'artist_id')
        self.assertEqual(len(result['top_tracks']), 2)

        track1 = result['top_tracks'][0]
        self.assertIsInstance(track1, Track)
        self.assertEqual(track1.track_name, 'In the End')
        self.assertEqual(track1.popularity, 91)
        self.assertEqual(track1.album, 'Hybrid Theory')
        self.assertEqual(track1.track_id, '123456abcde')

        track2 = result['top_tracks'][1]
        self.assertIsInstance(track2, Track)
        self.assertEqual(track2.track_name, 'Numb')
        self.assertEqual(track2.popularity, 90)
        self.assertEqual(track2.album, 'Meteora')
        self.assertEqual(track2.track_id, '654321ebca')
 

class TestsDatabase(unittest.TestCase):
    def setUp(self):
        self.database = Database()

    def test_check_data_date(self):
        """
        Tests the check_data_date function.
        Clears the database before test (still has csv), creates artists in database,
        creates temporary JSON, inserts Linkin Park data today, removes temporary JSON and clears database.
        
        """
        session.query(TopTracks).delete()
        session.query(Artists).delete()
        session.commit()

        artist1 = Artists(artist_id = '1', artist_name = 'Linkin Park')
        artist2 = Artists(artist_id = '2', artist_name = 'Disturbed')
        session.add_all([artist1, artist2])
        session.commit()

        self.json_path = 'artists_test.json'
        with open(self.json_path, 'w', encoding='utf-8') as f:
                  json.dump(['Linkin Park', 'Disturbed'], f)

        today = str(date.today())
        track = TopTracks(
             song_name = 'In the End',
             song_id = 'abc',
             popularity = 90,
             album = 'Hybrid Theory',
             artist_id = '1',
             insertion_date = today
        )
        session.add(track)
        session.commit()

        result = self.database.check_data_date(self.json_path)
        self.assertEqual(result, ['Disturbed'])

        if os.path.exists(self.json_path):
            os.remove(self.json_path)
        session.query(TopTracks).delete()
        session.query(Artists).delete()
        session.commit()

    def test_create_csv(self):
        """
        Tests if create_csv generates the CSV file correctly from the results.
        """
        artist = Artist(name = 'Linkin Park', artist_id = '1')
        track1 = Track(track_name = 'In The End', track_id = 'abc', popularity = 91, album='Hybrid Theory')
        track2 = Track(track_name='Numb', track_id='def', popularity=90, album='Meteora')
        results = [{'artist': artist, 'top_tracks': [track1, track2]}]

        m = mock_open()
        with patch('builtins.open', m):
             with patch('csv.DictWriter') as mock_writer_class:
                  mock_writer = mock_writer_class.return_value
                  mock_writer.writeheader = lambda: None
                  mock_writer.writerow = lambda row: None

                  self.database.create_csv(results)

                  mock_writer_class.assert_called()

                  assert mock_writer.writeheader is not None
                  assert mock_writer.writerow is not None

    def test_insert_csv_data_to_database(self):
        """
        Tests if insert_csv_data_to_database correctly inserts CSV data into the database.
        """
        with patch('os.listdir', return_value = ['test.csv']):
             csv_content = (
            "artist_name;artist_id;song_name;song_id;popularity;album;insertion_date\n"
            "Linkin Park;1;In the End;abc;91;Hybrid Theory;2024-07-22\n"
            "Linkin Park;1;Numb;def;90;Meteora;2024-07-22\n"
             )

             m = mock_open(read_data=csv_content)
             with patch('builtins.open', m):
                  with patch('csv.DictReader', wraps = csv.DictReader) as mock_reader:
                    session.query(TopTracks).delete()
                    session.query(Artists).delete()
                    session.commit()

                    self.database.insert_csv_data_to_database('data')

                    artists = session.query(Artists).filter_by(artist_id = '1').all()
                    tracks = session.query(TopTracks).filter_by(artist_id = '1').all()

                    self.assertEqual(len(artists), 1)
                    self.assertEqual(artists[0].artist_name, 'Linkin Park')
                    self.assertEqual(len(tracks), 2)
                    song_names = [t.song_name for t in tracks]
                    self.assertIn('In the End', song_names)
                    self.assertIn('Numb', song_names)

                    session.query(TopTracks).delete()
                    session.query(Artists).delete()
                    session.commit()

    def test_query_artists_data(self):
        """
        Tests if query_artists_data returns the correct artists for different filters.
        """
        session.query(Artists).delete()
        session.commit()

        artist1 = Artists(artist_id = '1', artist_name = 'Linkin Park')
        artist2 = Artists(artist_id = '2', artist_name = 'Disturbed')
        artist3 = Artists(artist_id = '3', artist_name = 'Metallica')
        session.add_all([artist1, artist2, artist3])
        session.commit()

        result = self.database.query_artists_data(['linkin park'])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].artist_id, '1')
        self.assertEqual(result[0].artist_name, 'Linkin Park')

        result = self.database.query_artists_data(['2'])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].artist_name, 'Disturbed')

        result = self.database.query_artists_data(['metallica', 'LINKIN PARK'])
        ids = [a.artist_id for a in result]
        self.assertIn('1', ids)
        self.assertIn('3', ids)

        session.query(Artists).delete()
        session.commit()

    def test_query_top_tracks_data(self):
        """
        Tests if query_top_tracks_data returns the most popular tracks from the most recent date.
        """
        session.query(TopTracks).delete()
        session.query(Artists).delete()
        session.commit()

        artist = Artists(artist_id = '1', artist_name = 'Linkin Park')
        session.add(artist)
        session.commit()

        track1 = TopTracks(
            song_name = 'In The End',
            song_id = 'abc',
            popularity = 91,
            album = 'Hybrid Theory',
            artist_id = '1',
            insertion_date = '2024-07-22'
        )
        track2 = TopTracks(
            song_name = 'Numb',
            song_id = 'def',
            popularity = 90,
            album = 'Meteora',
            artist_id = '1',
            insertion_date = '2024-07-22'
        )
        track3 = TopTracks(
            song_name = 'Papercut',
            song_id = 'ghi',
            popularity = 80,
            album = 'Hybrid Theory',
            artist_id = '1',
            insertion_date = '2024-07-21'
        )
        session.add_all([track1, track2, track3])
        session.commit()

        result = self.database.query_top_tracks_data('1')

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].song_name, 'In The End')
        self.assertEqual(result[1].song_name, 'Numb')

        session.query(TopTracks).delete()
        session.query(Artists).delete()
        session.commit()

    def test_display_artists(self):
        """
        Tests if display_artists correctly prints all registered artists in the database.
        """
        session.query(TopTracks).delete()
        session.query(Artists).delete()
        session.commit()

        artist1 = Artists(artist_id = '1', artist_name = 'Linkin Park')
        artist2 = Artists(artist_id = '2', artist_name = 'Disturbed')
        session.add_all([artist1, artist2])
        session.commit()

        f = StringIO()
        with redirect_stdout(f):
            self.database.display_artists()
        output = f.getvalue()

        self.assertIn('Linkin Park', output)
        self.assertIn('Disturbed', output)
        self.assertIn('All artists in database', output)

        session.query(TopTracks).delete()
        session.query(Artists).delete()
        session.commit()

if __name__ == '__main__':
    unittest.main()

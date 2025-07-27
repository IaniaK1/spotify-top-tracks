from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, PrimaryKeyConstraint, func, Date, cast
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import csv
from datetime import date, timedelta, datetime
import json

os.makedirs('data', exist_ok=True)
db = create_engine("sqlite:///data/spotify_data.db")
Session = sessionmaker(bind=db)
session = Session()

Base = declarative_base()

class Artists(Base):
    __tablename__ = 'artists'
    artist_id = Column(String, primary_key=True)
    artist_name = Column(String)

    def __repr__(self):
        return f'<Artist(artist_id="{self.artist_id}", artist_name="{self.artist_name}")>'

class TopTracks(Base):
    __tablename__ = 'top_tracks'
    song_name = Column(String)
    song_id = Column(String)
    popularity = Column(Integer)
    album = Column(String)
    artist_id = Column(String, ForeignKey('artists.artist_id'))
    insertion_date = Column(String)
    __table_args__ = (PrimaryKeyConstraint('song_id', 'insertion_date'),)

    def __repr__(self):
        return (f'<TopTracks(song_name="{self.song_name}", song_id="{self.song_id}", '
                f'popularity={self.popularity}, album="{self.album}", '
                f'artist_id="{self.artist_id}", insertion_date="{self.insertion_date}")>')

Base.metadata.create_all(bind=db)

class Database:
    def check_data_date(self, artists_json):
        """
        Checks if data exists for each artist in the JSON for the current date.

        Returns:
            list: List of artists without updated data for the current day.
        """
        try:
            with open(artists_json, 'r', encoding='utf-8') as f:
                artists = json.load(f)
        except Exception as e:
            raise Exception(f'Error processing or reading file {artists_json}: {e}')

        try:
            today = str(date.today().strftime('%Y-%m-%d'))
            artists_without_data = list()

            for artist in artists:
                exists = session.query(TopTracks).join(Artists).filter(
                    func.lower(Artists.artist_name) == artist.lower(),
                    TopTracks.insertion_date.like(f'{today}%')
                ).first()
                if not exists:
                    artists_without_data.append(artist)


        except Exception as e:
            raise Exception(f'Error querying database: {e}')
        
        return artists_without_data

    def create_csv(self, results):
        """
        Creates a CSV file with the results of artists' tracks.

        Args:
            results (list): List of dictionaries containing artist and track information.
        """
        try:
            subfolder = 'data'
            full_path = os.path.join(subfolder, f'search_results_{date.today()}.csv')
            file_exists = os.path.exists(full_path)
            write_header = not file_exists or os.path.getsize(full_path) == 0

            current_insertion_date = datetime.now()

            with open(full_path, 'a', newline='', encoding='utf-8') as f:
                columns = ['artist_name', 'artist_id', 'song_name', 'song_id', 'popularity', 'album', 'insertion_date']

                writer = csv.DictWriter(f, fieldnames=columns, delimiter=';')

                if write_header:
                    writer.writeheader()

                for artist_info in results:
                    artist = artist_info['artist']
                    for track in artist_info['top_tracks']:
                        writer.writerow({
                            'artist_name': artist.name,
                            'artist_id': artist.artist_id,
                            'song_name': track.track_name,
                            'song_id': track.track_id,
                            'popularity': track.popularity,
                            'album': track.album,
                            'insertion_date': current_insertion_date
                        })
        except Exception as e:
            print(e)
            return

    def insert_csv_data_to_database(self, csv_folder='data'):
        """
        Reads all CSV files from the specified folder and inserts data into the database.

        Args:
            csv_folder (str): Path to the folder containing CSV files. Default is 'data'.
        """
        try:
            for file in os.listdir(csv_folder):
                if file.endswith('.csv'):
                    full_path = os.path.join(csv_folder, file)
                    with open(full_path, encoding='utf-8') as f:
                        reader = csv.DictReader(f, delimiter=';')
                        if reader.fieldnames is None:
                            raise RuntimeError(f'CSV file {file} is empty or has no header.')
                        rows = list(reader)
                        if not rows:
                            raise RuntimeError(f'CSV file {file} is empty.')
                        for row in rows:
                            artist_obj = Artists(
                                artist_id=row['artist_id'],
                                artist_name=row['artist_name']
                            )
                            session.merge(artist_obj)

                            track_obj = TopTracks(
                                song_name=row['song_name'],
                                song_id=row['song_id'],
                                popularity=int(row['popularity']),
                                album=row['album'],
                                artist_id=row['artist_id'],
                                insertion_date=row['insertion_date']
                            )
                            session.merge(track_obj)
                        session.commit()
        except Exception as e:
            raise RuntimeError(f'Error inserting CSV data from {file}: {e}')

    def query_artists_data(self, filter_list):
        """
        Search for artists and their top tracks in the database by name (case-insensitive) or exact ID.

        Args:
            filter_list (list): List of artist names or IDs.

        Return:
            list: List of found Artist objects.
        """
        if not filter_list:
            return session.query(Artists).all()
        
        filter_lower = [name.lower() for name in filter_list]

        artists_info = session.query(Artists).filter(
            (func.lower(Artists.artist_name).in_(filter_lower)) |
            (Artists.artist_id.in_(filter_list))
        ).all()

        return artists_info

    def query_top_tracks_data(self, artist_id):
        """
        Search for top tracks and their information by ID.

        Args:
            artist_id (str): Artist ID.

        Returns:
            list: List of TopTracks objects for the artist, ordered by popularity (descending).
        """
        most_recent_date = session.query(func.max(TopTracks.insertion_date)).filter(
            TopTracks.artist_id == artist_id
        ).scalar()

        tracks = session.query(TopTracks).filter(
            TopTracks.artist_id == artist_id,
            TopTracks.insertion_date == most_recent_date
        ).order_by(TopTracks.popularity.desc()).all()

        return tracks

    def display_artists(self):
        """
        Displays all registered artists in the database, sorted alphabetically.
        Returns True if there are artists, False if there are none.
        """
        all_artists = self.query_artists_data([])
        if not all_artists:
            raise RuntimeError('No artists found in database. Run with --artists_json to update data.')
        print('\nAll artists in database:\n')
        for artist in sorted(all_artists, key=lambda a: a.artist_name.lower()):
            print(f'{artist.artist_id} - {artist.artist_name}')

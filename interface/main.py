import argparse
from infrastructure.api import SpotifyAPI
from infrastructure.database import Database
from application.update_data import UpdateDataUseCase
from application.query_data import QueryDataUseCase


def main(spotify_client_id, spotify_client_secret, artists_json, filter):
    try:   
        api = SpotifyAPI(spotify_client_id, spotify_client_secret)
        database = Database()

        if artists_json is not None:
            usecase = UpdateDataUseCase(api, database.check_data_date, database.create_csv, database.insert_csv_data_to_database)
            usecase.execute(artists_json)
        else:
            print('Direct query: existing data from database will be used.')

        database.display_artists()

        usecase = QueryDataUseCase(database.query_artists_data, database.query_top_tracks_data, filter)
        result = usecase.execute()

        print(result)
            
    except Exception as e:
        print(e)
        return


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', type=str, required=False)
    parser.add_argument('--secret', type=str, required=False)
    parser.add_argument('--artists_json', type=str, required=False)
    parser.add_argument('--filter', type=str, required=False, help='Names or IDs separated by comma')
    args = parser.parse_args()
    main(args.id,
         args.secret,
         args.artists_json,
         args.filter)

class UpdateDataUseCase:
    def __init__(self, spotify_api, check_data_date, create_csv, insert_csv_data_to_database):
        self.spotify_api = spotify_api
        self.check_data_date = check_data_date
        self.create_csv = create_csv
        self.insert_csv_data_to_database = insert_csv_data_to_database

    def execute(self, artists_json):
        artists = self.check_data_date(artists_json)
        if not artists:
            print('Data already updated. No new search will be executed.')
            return
    
        results = []
        print('Searching...')
        for artist in artists:
            print(f'Searching for {artist}')
            artist_obj = self.spotify_api.search_artist(artist)
            print(f'Searching tracks for artist {artist}')
            artist_info = self.spotify_api.search_top_tracks(artist_obj)
            results.append(artist_info)

        self.create_csv(results)
        print(f'Search completed. File saved at /data/search_results.csv.')

        self.insert_csv_data_to_database()
        print(f'Database created successfully. File saved at /data/spotify_data.db.')

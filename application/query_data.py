class QueryDataUseCase:
    def __init__(self, query_artists, query_tracks, filter=None):
        self.query_artists = query_artists
        self.query_tracks = query_tracks
        self.filter = filter

    def execute(self):
        if self.filter == None:
            user_input = input('\nFor more information, enter artist names or IDs separated by comma: ')
            filter_list = [f.strip() for f in user_input.split(',')]
        else:
            filter_list = [f.strip() for f in self.filter.split(',')]

        artists = self.query_artists(filter_list)

        result = {}
        for artist in artists:
            tracks = self.query_tracks(artist.artist_id)
            result[artist.artist_name] = {
                'id': artist.artist_id,
                'top_tracks': [
                    {
                        'song_name': t.song_name,
                        'song_id': t.song_id,
                        'popularity': t.popularity,
                        'album': t.album,
                        'insertion_date': t.insertion_date
                    } for t in tracks
                ]
            }
        return result

class ConsultarDadosUseCase:
    def __init__(self, consultar_artistas, consultar_tracks, filtro=None):
        self.consultar_artistas = consultar_artistas
        self.consultar_tracks = consultar_tracks
        self.filtro = filtro

    def executar(self):
        if self.filtro == None:
            filtro = input('\nPara mais informações, digite nomes ou IDs dos artistas separados por vírgula: ')
            filtro_lista = [f.strip() for f in filtro.split(',')]
        else:
            filtro_lista = [f.strip() for f in self.filtro.split(',')]

        artistas = self.consultar_artistas(filtro_lista)

        resultado = {}
        for artista in artistas:
            tracks = self.consultar_tracks(artista.id_artista)
            resultado[artista.nome_artista] = {
                'id': artista.id_artista,
                'top_tracks': [
                    {
                        'nome_musica': t.nome_musica,
                        'id_musica': t.id_musica,
                        'popularidade': t.popularidade,
                        'album': t.album,
                        'data_insercao': t.data_insercao
                    } for t in tracks
                ]
            }
        return resultado

class UpdateDataUseCase:
    def __init__(self, spotify_api, checagem_data_dados, criar_csv, inserir_dados_csv_no_banco):
        self.spotify_api = spotify_api
        self.checagem_data_dados = checagem_data_dados
        self.criar_csv = criar_csv
        self.inserir_dados_csv_no_banco = inserir_dados_csv_no_banco

    def execute(self, artistas_json):
        artistas = self.checagem_data_dados(artistas_json)
        if not artistas:
            print('Dados já atualizados. Nenhuma nova pesquisa será executada.')
            return
    
        resultados = []
        print('Pesquisando...')
        for artista in artistas:
            print(f'Pesquisando {artista}')
            artista_obj = self.spotify_api.buscar_artista(artista)
            print(f'Pesquisando tracks do artista {artista}')
            artista_info = self.spotify_api.buscar_top_tracks(artista_obj)
            resultados.append(artista_info)

        self.criar_csv(resultados)
        print(f'Pesquisa concluida. Arquivo salvo em /dados/resultado_pesquisas.csv.')

        self.inserir_dados_csv_no_banco()
        print(f'Banco de dados criado com sucesso. Arquivo salvo em /dados/spotify_data.db.')

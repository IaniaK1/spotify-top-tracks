import argparse
from infrastructure.api import SpotifyAPI
from infrastructure.database import Database
from application.update_data import UpdateDataUseCase
from application.query_data import QueryDataUseCase


def main(spotify_client_id, spotify_client_secret, artistas_json, filtro):
    try:   
        api = SpotifyAPI(spotify_client_id, spotify_client_secret)
        banco = BancoDeDados()

        if artistas_json is not None:
            usecase = AtualizarDadosUseCase(api, banco.checagem_data_dados, banco.criar_csv, banco.inserir_dados_csv_no_banco)
            usecase.executar(artistas_json)
        else:
            print('Consulta direta: serão usados os dados já existentes no banco.')

        banco.exibir_artistas()

        usecase = ConsultarDadosUseCase(banco.consultar_dados_artistas, banco.consultar_dados_top_tracks, filtro)
        resultado = usecase.executar()

        print(resultado)
            
    except Exception as e:
        print(e)
        return


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', type=str, required=False)
    parser.add_argument('--secret', type=str, required=False)
    parser.add_argument('--artistas_json', type=str, required=False)
    parser.add_argument('--filtro', type=str, required=False, help='Nomes ou ids separados por virgula')
    args = parser.parse_args()
    main(args.id,
         args.secret,
         args.artistas_json,
         args.filtro)

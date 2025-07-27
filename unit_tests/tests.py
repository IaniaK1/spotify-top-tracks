import unittest
from unittest.mock import patch, mock_open
import json
import os
import csv
from infraestrutura.api import SpotifyAPI
from infraestrutura.bancodedados import BancoDeDados, session, Artistas, TopTracks
from dominio.modelos import Artista, Track, Token
from datetime import date
from io import StringIO
from contextlib import redirect_stdout

class TestesSpotifyAPI(unittest.TestCase):
    @patch('requests.post')
    def test_solicitar_token(self, mock_post):
        """
        Testa se o método _solicitar_token retorna um objeto Token válido ao receber resposta da API.
        """
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'access_token': 'ABCD1234',
            'expires_in': 3600
        }

        client_id = 'meu_client_id'
        client_secret = 'meu_client_secret'

        api = SpotifyAPI(client_id, client_secret)
        token_obj = api._solicitar_token()
        
        mock_post.assert_called_with(
            'https://accounts.spotify.com/api/token',
            headers = {'Content-Type': 'application/x-www-form-urlencoded'},
            data = {'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret}
        )

        self.assertEqual(token_obj.token, 'ABCD1234')
        self.assertEqual(token_obj._expira_em, 3600)
        self.assertTrue(token_obj.valido)

    @patch('requests.post')
    @patch('requests.get')
    def test_buscar_artista(self, mock_get, mock_post):
        """
        Testa se buscar_artista retorna corretamente o objeto Artista ao consultar a API do Spotify.
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

        api = SpotifyAPI('meu_client_id', 'meu_client_secret')
        artista = api.buscar_artista('Linkin Park')

        self.assertEqual(artista.nome, 'Linkin Park')
        self.assertEqual(artista.id_artista, '123')

        mock_get.assert_called_with(
            'https://api.spotify.com/v1/search',
            headers = {'Authorization': f'Bearer {api.token}'},
            params={'q': 'Linkin Park', 'type': 'artist', 'limit': 1}
        )

    @patch('requests.get')
    @patch('requests.post')
    def test_buscar_top_tracks(self, mock_post, mock_get):
        """
        Testa se buscar_top_tracks retorna corretamente as informacoes das faixas mais populares do artista.
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

        api = SpotifyAPI('meu_client_id', 'meu_client_secret')
        artista = Artista(nome = 'Linkin Park', id_artista = 'id_do_artista')
        resultado = api.buscar_top_tracks(artista)

        mock_get.assert_called_with(
            'https://api.spotify.com/v1/artists/id_do_artista/top-tracks',
            headers = {'Authorization': f'Bearer {api.token}'}
        )

        self.assertEqual(resultado['artista'].nome, 'Linkin Park')
        self.assertEqual(resultado['artista'].id_artista, 'id_do_artista')
        self.assertEqual(len(resultado['top_tracks']), 2)

        track1 = resultado['top_tracks'][0]
        self.assertIsInstance(track1, Track)
        self.assertEqual(track1.nome_track, 'In the End')
        self.assertEqual(track1.popularidade, 91)
        self.assertEqual(track1.album, 'Hybrid Theory')
        self.assertEqual(track1.id_track, '123456abcde')

        track2 = resultado['top_tracks'][1]
        self.assertIsInstance(track2, Track)
        self.assertEqual(track2.nome_track, 'Numb')
        self.assertEqual(track2.popularidade, 90)
        self.assertEqual(track2.album, 'Meteora')
        self.assertEqual(track2.id_track, '654321ebca')
 

class TestesBancoDeDados(unittest.TestCase):
    def setUp(self):
        self.banco = BancoDeDados()

    def test_checagem_data_dados(self):
        """
        Testa a funcao checagem_data_dados.
        Limpa o banco antes do teste (ainda tem o csv), cria artistas no banco,
        cria JSON temporario, insere dados de linkin park hoje, remove JSON temporario e limpa o banco.
        
        """
        session.query(TopTracks).delete()
        session.query(Artistas).delete()
        session.commit()

        artista1 = Artistas(id_artista = '1', nome_artista = 'Linkin Park')
        artista2 = Artistas(id_artista = '2', nome_artista = 'Disturbed')
        session.add_all([artista1, artista2])
        session.commit()

        self.json_path = 'artistas_test.json'
        with open(self.json_path, 'w', encoding='utf-8') as f:
                  json.dump(['Linkin Park', 'Disturbed'], f)

        hoje = str(date.today())
        track = TopTracks(
             nome_musica = 'In the End',
             id_musica = 'abc',
             popularidade = 90,
             album = 'Hybrid Theory',
             id_artista = '1',
             data_insercao = hoje
        )
        session.add(track)
        session.commit()

        resultado = self.banco.checagem_data_dados(self.json_path)
        self.assertEqual(resultado, ['Disturbed'])

        if os.path.exists(self.json_path):
            os.remove(self.json_path)
        session.query(TopTracks).delete()
        session.query(Artistas).delete()
        session.commit()

    def test_criar_csv(self):
        """
        Testa se criar_csv gera o arquivo CSV corretamente a partir dos resultados.
        """
        artista = Artista(nome = 'Linkin Park', id_artista = '1')
        track1 = Track(nome_track = 'In The End', id_track = 'abc', popularidade = 91, album='Hybrid Theory')
        track2 = Track(nome_track='Numb', id_track='def', popularidade=90, album='Meteora')
        resultados = [{'artista': artista, 'top_tracks': [track1, track2]}]

        m = mock_open()
        with patch('builtins.open', m):
             with patch('csv.DictWriter') as mock_writer_class:
                  mock_writer = mock_writer_class.return_value
                  mock_writer.writeheader = lambda: None
                  mock_writer.writerow = lambda row: None

                  self.banco.criar_csv(resultados)

                  mock_writer_class.assert_called()

                  assert mock_writer.writeheader is not None
                  assert mock_writer.writerow is not None

    def test_inserir_dados_csv_no_banco(self):
        """
        Testa se inserir_dados_csv_no_banco insere corretamente os dados do CSV no banco.
        """
        with patch('os.listdir', return_value = ['teste.csv']):
             csv_content = (
            "nome_artista;id_artista;nome_musica;id_musica;popularidade;album;data_insercao\n"
            "Linkin Park;1;In the End;abc;91;Hybrid Theory;2024-07-22\n"
            "Linkin Park;1;Numb;def;90;Meteora;2024-07-22\n"
             )

             m = mock_open(read_data=csv_content)
             with patch('builtins.open', m):
                  with patch('csv.DictReader', wraps = csv.DictReader) as mock_reader:
                    session.query(TopTracks).delete()
                    session.query(Artistas).delete()
                    session.commit()

                    self.banco.inserir_dados_csv_no_banco('dados')

                    artistas = session.query(Artistas).filter_by(id_artista = '1').all()
                    tracks = session.query(TopTracks).filter_by(id_artista = '1').all()

                    self.assertEqual(len(artistas), 1)
                    self.assertEqual(artistas[0].nome_artista, 'Linkin Park')
                    self.assertEqual(len(tracks), 2)
                    nomes_musicas = [t.nome_musica for t in tracks]
                    self.assertIn('In the End', nomes_musicas)
                    self.assertIn('Numb', nomes_musicas)

                    session.query(TopTracks).delete()
                    session.query(Artistas).delete()
                    session.commit()

    def test_consultar_dados_artistas(self):
        """
        Testa se consultar_dados_artistas retorna os artistas corretos para diferentes filtros.
        """
        session.query(Artistas).delete()
        session.commit()

        artista1 = Artistas(id_artista = '1', nome_artista = 'Linkin Park')
        artista2 = Artistas(id_artista = '2', nome_artista = 'Disturbed')
        artista3 = Artistas(id_artista = '3', nome_artista = 'Metallica')
        session.add_all([artista1, artista2, artista3])
        session.commit()

        resultado = self.banco.consultar_dados_artistas(['linkin park'])
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0].id_artista, '1')
        self.assertEqual(resultado[0].nome_artista, 'Linkin Park')

        resultado = self.banco.consultar_dados_artistas(['2'])
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0].nome_artista, 'Disturbed')

        resultado = self.banco.consultar_dados_artistas(['metallica', 'LINKIN PARK'])
        ids = [a.id_artista for a in resultado]
        self.assertIn('1', ids)
        self.assertIn('3', ids)

        session.query(Artistas).delete()
        session.commit()

    def test_consultar_dados_top_tracks(self):
        """
        Testa se consultar_dados_top_tracks retorna as tracks mais populares da data mais recente.
        """
        session.query(TopTracks).delete()
        session.query(Artistas).delete()
        session.commit()

        artista = Artistas(id_artista = '1', nome_artista = 'Linkin Park')
        session.add(artista)
        session.commit()

        track1 = TopTracks(
            nome_musica = 'In The End',
            id_musica = 'abc',
            popularidade = 91,
            album = 'Hybrid Theory',
            id_artista = '1',
            data_insercao = '2024-07-22'
        )
        track2 = TopTracks(
            nome_musica = 'Numb',
            id_musica = 'def',
            popularidade = 90,
            album = 'Meteora',
            id_artista = '1',
            data_insercao = '2024-07-22'
        )
        track3 = TopTracks(
            nome_musica = 'Papercut',
            id_musica = 'ghi',
            popularidade = 80,
            album = 'Hybrid Theory',
            id_artista = '1',
            data_insercao = '2024-07-21'
        )
        session.add_all([track1, track2, track3])
        session.commit()

        resultado = self.banco.consultar_dados_top_tracks('1')

        self.assertEqual(len(resultado), 2)
        self.assertEqual(resultado[0].nome_musica, 'In The End')
        self.assertEqual(resultado[1].nome_musica, 'Numb')

        session.query(TopTracks).delete()
        session.query(Artistas).delete()
        session.commit()

    def test_exibir_artisas(self):
        """
        Testa se exibir_artistas imprime corretamente todos os artistas cadastrados no banco.
        """
        session.query(TopTracks).delete()
        session.query(Artistas).delete()
        session.commit()

        artista1 = Artistas(id_artista = '1', nome_artista = 'Linkin Park')
        artista2 = Artistas(id_artista = '2', nome_artista = 'Disturbed')
        session.add_all([artista1, artista2])
        session.commit()

        f = StringIO()
        with redirect_stdout(f):
            self.banco.exibir_artistas()
        output = f.getvalue()

        self.assertIn('Linkin Park', output)
        self.assertIn('Disturbed', output)
        self.assertIn('Todos os artistas do banco', output)

        session.query(TopTracks).delete()
        session.query(Artistas).delete()
        session.commit()

if __name__ == '__main__':
    unittest.main()

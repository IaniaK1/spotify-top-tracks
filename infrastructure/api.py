import os
import requests
from dominio.modelos import Token, Artista, Track
from dotenv import load_dotenv
load_dotenv()


class SpotifyAPI:
    """
    Classe para a interação com a API do Spotify.
    """
    def __init__(self, spotify_client_id=None, spotify_client_secret=None):
        self.url = 'https://api.spotify.com/v1'
        self.spotify_client_id = spotify_client_id or os.environ.get('spotify_client_id')
        self.spotify_client_secret = spotify_client_secret or os.environ.get('spotify_client_secret')
        self._token_spotify = None
        self._token_spotify = self._solicitar_token()

    @property
    def token(self):
        """
        Retorna um token de acesso válido para a API do Spotify.

        Se o token atual estiver expirado ou não existir, solicita um novo automaticamente.

        Returns:
            str: Token de acesso valido.
        """
        if not self._token_spotify or not self._token_spotify.valido:
            self._token_spotify = self._solicitar_token()
        return self._token_spotify.token

    def _solicitar_token(self):
        """
        Solicita e retorna um novo token de acesso a API do Spotify o fluxo client credentials.

        Returns:
            str: Token de acesso valido para autenticacao nas requisicoes a API do Spotify.
        """
        try:
            url_token = 'https://accounts.spotify.com/api/token'

            headers = {'Content-Type': 'application/x-www-form-urlencoded'}

            body = {
                'grant_type': 'client_credentials',
                'client_id': f'{self.spotify_client_id}',
                'client_secret': f'{self.spotify_client_secret}'
            }
            
            requisicao = requests.post(url_token, headers=headers, data=body)
            requisicao.raise_for_status()

            token = requisicao.json()['access_token']
            expira_em = requisicao.json()['expires_in']
            return Token(token, expira_em)
        except Exception as e:
            print(f'Erro ao solicitar token: {e}')
            return None

    def buscar_artista(self, artista):
        """
        Busca o ID de um artista pelo nome usando a API do Spotify.

        Args: 
            artista (str): Nome do artista.

        Returns:
            Artista: Objeto Artista encontrado.
        """
        try:
            url = self.url + f'/search'
            
            headers = {
                'Authorization': f'Bearer {self.token}'
            }

            requisicao = requests.get(url, headers=headers, params={'q':artista,'type': 'artist','limit': 1})

            requisicao.raise_for_status()
            resultado = requisicao.json()

            dados_artista = resultado['artists']['items'][0]
        except Exception as e:
            print(f'Erro ao buscar artista {artista}: {e}')
            return

        return Artista(nome=dados_artista['name'], id_artista=dados_artista['id'])
    
    def buscar_top_tracks(self, artista: Artista):
        """
        Busca as faixas mais populares de um artista usando a API do Spotify.

        Args:
            artista (Artista): Objeto Artista.

        Returns:
            dict: Dicionário contendo o artista e uma lista de suas top tracks (objetos Track).
        """
        try:
            url = self.url + f'/artists/{artista.id_artista}/top-tracks'

            headers = {
                'Authorization': f'Bearer {self.token}'
            }

            requisicao = requests.get(url, headers=headers)
            requisicao.raise_for_status()
            resposta = requisicao.json()

            tracks = []
            for track in resposta['tracks']:
                tracks.append(Track(
                    nome_track=track['name'],
                    id_track=track['id'],
                    popularidade=track['popularity'],
                    album=track['album']['name']
                ))
        except Exception as e:
            print(f'Erro ao buscar tracks do artista {artista}: {e}')
            return

        return {'artista': artista, 'top_tracks': tracks}

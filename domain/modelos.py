from dataclasses import dataclass, field
from datetime import timedelta, datetime
import time


@dataclass
class Artista:
   """
   Classe para armazenar as informações do artista que resultam da busca na API do Spotify.
   """
   nome: str
   id_artista: str

@dataclass
class Track:
    """
    Classe para armazenar as informações da track do artista que resultam da busca na API do Spotify.
    """
    nome_track: str
    id_track: str
    popularidade: int
    album: str

@dataclass
class Token:
    """
    Classe para armazenar o token de acesso a sua respectiva API.
    """
    token: str
    _expira_em: int
    _momento_criacao: float = field(default_factory=time.time)

    @property
    def valido(self) -> bool:
        """
        Retorna True se o token ainda está válido, False caso contrário.
        """
        return (time.time() - self._momento_criacao) < self._expira_em

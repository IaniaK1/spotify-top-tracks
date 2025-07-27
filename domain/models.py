from dataclasses import dataclass, field
from datetime import timedelta, datetime
import time


@dataclass
class Artist:
   """
   Classe para armazenar as informações do artista que resultam da busca na API do Spotify.
   """
   name: str
   artist_id: str

@dataclass
class Track:
    """
    Classe para armazenar as informações da track do artista que resultam da busca na API do Spotify.
    """
    track_name: str
    track_id: str
    popularity: int
    album: str

@dataclass
class Token:
    """
    Classe para armazenar o token de acesso a sua respectiva API.
    """
    token: str
    _expires_in: int
    _creation_time: float = field(default_factory=time.time)

    @property
    def valid(self) -> bool:
        """
        Retorna True se o token ainda está válido, False caso contrário.
        """
        return (time.time() - self._creation_time) < self._expires_in

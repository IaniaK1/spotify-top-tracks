from dataclasses import dataclass, field
from datetime import timedelta, datetime
import time


@dataclass
class Artist:
   """
   Class to store artist information resulting from Spotify API search.
   """
   name: str
   artist_id: str

@dataclass
class Track:
    """
    Class to store track information from the artist resulting from Spotify API search.
    """
    track_name: str
    track_id: str
    popularity: int
    album: str

@dataclass
class Token:
    """
    Class to store the access token for its respective API.
    """
    token: str
    _expires_in: int
    _creation_time: float = field(default_factory=time.time)

    @property
    def valid(self) -> bool:
        """
        Returns True if the token is still valid, False otherwise.
        """
        return (time.time() - self._creation_time) < self._expires_in

from dataclasses import dataclass
from .thumbnail import Thumbnail
@dataclass(frozen=True)
class MusicMetadata:
    title:str
    orientation:str
    sizingRule:str
    subtitle:str
    secondary_subtitle:str
    thumbnail:Thumbnail
    all_info:str
    owner_id:str
    def __repr__(self)->str:
        return f"<MusicMetadata {self.title}/>"
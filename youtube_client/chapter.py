from .query import ThumbnailQuery
class ChapterBase:
    def __init__(self):
        self.title:str = None
        self.thumbnails:ThumbnailQuery = None
        self.time_description:str = None
    def __repr__(self)->str:
        return f"<Chapter {self.time} \"{self.title}\" />"
class Chapter(ChapterBase):
    def __init__(self):
        self.start_range_ms:int = None
        self.time:str = None
        super().__init__()
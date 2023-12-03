from .extract import video_id
from .base_youtube_player import BaseYoutubePlayer
from . import video
from functools import cached_property
from . import request
from . import extract
def get_url_by_id(id:str)->str:
    return f"https://youtube.com/shorts/{id}"

class Short(video.Video):
    def __init__(self,url:str=None,id:str=None):
        """
        Args:
            id (str, optional): id of video. Defaults to None.
            url (str, optional): url of video. Defaults to None.

        Raises:
            Exception: Exception, when id and url is None
        """
        if id == None and url == None:
            raise Exception("id and url is None")
        rid:str = video_id(url) if url else id 
        rurl:str = video.get_url(rid)
        self.short_url = get_url_by_id(rid)
        super().__init__(id=rid,url=rurl)
    def __repr__(self)->str:
        return f"<Short id=\"{self.id}\" />"
    @property
    def short_html(self)->str:
        return request.default_obj.get(self.short_url)
    @cached_property
    def short_initial_data(self)->dict:
        return extract.initial_data(self.short_html)

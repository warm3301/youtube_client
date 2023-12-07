from typing import Callable,Any,Optional
from urllib.request import urlretrieve
from .base_downloader import VideoDownloader
from ..streams import Stream
class UrllibDownloader(VideoDownloader):
    def __init__(self,
        stream:Stream,
        output_path:str=None,
        ext_in_path:bool=False,
        skip_existing: bool = True,
        on_complete:Optional[Callable[[Any,str],None]]=None,
        default_title:str = "Unknown youtube video"
        ):
        super().__init__(stream=stream,on_complete=on_complete,default_title=default_title,output_path=output_path,ext_in_path=ext_in_path,skip_existing=skip_existing)
    def download(self)->str:
        if self.skip:
            self._on_complete(self.file_path)
            return self.file_path
        urlretrieve(self.stream.url,self.file_path)
        return self.file_path
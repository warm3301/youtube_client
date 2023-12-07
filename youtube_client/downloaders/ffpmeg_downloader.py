from typing import Optional,Callable,Any
from ffmpeg import FFmpeg, Progress
from .base_downloader import VideoDownloader
from ..streams import Stream
class FFMpegDownloader(VideoDownloader):
    def __init__(self,
    stream:Stream,
    output_path:str=None,
    ext_in_path:bool=False,
    skip_existing: bool = True,
    on_complete:Optional[Callable[[Any,str],None]]=None,
    on_progress:Optional[Callable[[Any,"Progress"],None]]=None,
    default_title:str = "Unknown youtube video",
    ):
        self.on_progress = on_progress
        super().__init__(stream=stream,on_complete=on_complete,default_title=default_title,output_path=output_path,ext_in_path=ext_in_path,skip_existing=skip_existing)
        self.ffdownloader = (FFmpeg().option("y").input(self.stream.url).output(self.file_path,vcodec="copy",acodec="copy"))
    
    def download(self):
        if self.skip:
            self._on_complete(self.file_path)
            return self.file_path
        
        @self.ffdownloader.on("progress")
        def _on_progress(progress:"Progress"):
            if self.on_progress:
                self.on_progress(self,progress)
        self.ffdownloader.execute()
        self._on_complete(self.file_path)
        return self.file_path
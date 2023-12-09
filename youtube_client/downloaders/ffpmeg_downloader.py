# https://github.com/jonghwanhyeon/python-ffmpeg
from typing import Optional,Callable,Any,Union,Tuple
from ffmpeg import FFmpeg, Progress
from .base_downloader import VideoDownloader
from ..streams import Stream

class FFMpegDownloader(VideoDownloader):
    def __init__(self,
    streams:Union[Stream,Tuple[Stream]],
    output_path:str=None,
    ext_in_path:bool=False,
    skip_existing: bool = True,
    time_from:str = None,
    time_to:str = None,
    lenght:str = None,
    on_complete:Optional[Callable[[Any,str],None]]=None,
    on_progress:Optional[Callable[[Any,"Progress"],None]]=None,
    default_title:str = "Unknown youtube video",
    ):
        self.on_progress = on_progress
        super().__init__(stream=streams,on_complete=on_complete,default_title=default_title,output_path=output_path,ext_in_path=ext_in_path,skip_existing=skip_existing)
        self.ffdownloader = FFmpeg().option("y").option("threads",2)#TODO other concatenator. add metadata,subtitles
        params = {}
        if time_from:
            params["ss"]=time_from
        if time_to:
            params["to"]=time_to
        if lenght:
            params["t"]=lenght
        if isinstance(streams,Stream):
            self.ffdownloader.input(self.stream.url,params)
        elif isinstance(streams,tuple):
            if len(streams) == 1:
                self.ffdownloader.input(self.stream[0].url,params)
            elif len(streams) == 2:
                self.ffdownloader.input(self.stream[0].url,params)
                self.ffdownloader.input(self.stream[1].url,params)
            else:
                raise Exception("streams is not Stream or tuple of streams contains 2 or 1 Stream")
        else:
            raise Exception("streams is not Stream or tuple of streams contains 2 or 1 Stream")
        self.ffdownloader.output(self.file_path,vcodec="copy",acodec="copy")
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
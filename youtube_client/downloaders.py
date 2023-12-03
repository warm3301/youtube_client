from . import request
from .base_youtube_player import BaseYoutubePlayer
from .streams import Stream
from typing import Optional,Callable,Any,BinaryIO,Dict,Tuple,Union
from urllib.error import HTTPError
import os

from .helpers import safe_filename,generate_filename
from .thumbnail import Thumbnail
from urllib.request import urlretrieve

import io
#TODO raw for video, buffer for thumbnail
#TODO request for thumbnail!!!!
import requests
#!!!!!
#TODO caption downloader
from .captions import Caption
from .query import CaptionQueryFirst

class VideoDownloader:
    def __init__(
        self,stream:Stream,
        on_complete:Optional[Callable[[Any,str],None]]=None,
        default_title:str = "Unknown youtube video",
        output_path:str=None,
        ext_in_path:bool=False,
        skip_existing: bool = True
        ):
        self.stream = stream
        self.default_title = default_title
        self.on_complete = on_complete
        self.file_path = self.get_file_path(output_path,ext_in_path)
        self.skip = skip_existing and self.exists_at_path(self.file_path)



    @property
    def default_filename(self) -> str:#TODO update helpers.generate_filename for base includig directory and del param directory 
        #TODO and add param postfix
        #TODO separator if not added symbols to base
        name=self.default_title
        if self.stream.title:
            name= self.stream.title
        filename = safe_filename(name)
        return f"{filename}.{self.stream.ext}"
    def get_file_path(self,file_path:Optional[str],ext_contain:bool=False)->str:
        path = file_path
        if path == None:
            return self.default_filename
        if not ext_contain:
            path += f".{self.stream.ext}"
        return path
    def exists_at_path(self, file_path: str) -> bool:
        return os.path.isfile(file_path) and os.path.getsize(file_path) == self.stream.filesize
    def _on_complete(self,file_path):
        if self.on_complete:
            self.on_complete(self,file_path)

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

        from ffmpeg import FFmpeg, Progress
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

class SingleDownlower(VideoDownloader):
    def __init__(self,
    stream:Stream,
    output_path:str=None,
    ext_in_path:bool=False,
    skip_existing: bool = True,
    on_progress:Optional[Callable[[Any, bytes, int],None]]=None,
    on_complete:Optional[Callable[[Any, Optional[str]],None]]=None,
    default_title:str = "Unknown youtube video"
    ):#stream_getter also save title and lenght in cashe(and other if possible)
        self.on_progress:Optional[Callable[[Any, bytes, int],None]] = on_progress
        super().__init__(stream=stream,on_complete=on_complete,default_title=default_title,output_path=output_path,ext_in_path=ext_in_path,skip_existing=skip_existing)

    def _on_progress(self, chunk: bytes, file_handler: BinaryIO, bytes_remaining: int):
        file_handler.write(chunk)
        if self.on_progress:
            self.on_progress(self,chunk,bytes_remaining)

    def stream_to_buffer(self, buffer: BinaryIO) -> None:
        """Write the media stream to buffer

        :rtype: io.BytesIO buffer
        """
        bytes_remaining = self.stream.filesize
        for chunk in request.stream(self.stream.url):
            # reduce the (bytes) remainder by the length of the chunk.
            bytes_remaining -= len(chunk)
            # send to the on_progress callback.
            self._on_progress(chunk, buffer, bytes_remaining)
        self._on_complete(None)
    def download(
        self,
        timeout: int = None,
        max_retries:int = 0
    ) -> str:
        if self.skip:
            self._on_complete(self.file_path)
            return self.file_path

        bytes_remaining = self.stream.filesize

        with open(self.file_path, "wb") as fh:
            try:
                for chunk in request.stream(
                    self.stream.url,
                    timeout=timeout,
                    max_retries=max_retries
                ):
                    # reduce the (bytes) remainder by the length of the chunk.
                    bytes_remaining -= len(chunk)
                    # send to the on_progress callback.
                    self._on_progress(chunk, fh, bytes_remaining)
            except HTTPError as e:
                if e.code != 404:
                    raise
                # Some adaptive streams need to be requested with sequence numbers
                for chunk in request.seq_stream(
                    self.stream.url,
                    timeout=timeout,
                    max_retries=max_retries
                ):
                    # reduce the (bytes) remainder by the length of the chunk.
                    bytes_remaining -= len(chunk)
                    # send to the on_progress callback.
                    self._on_progress(chunk, fh, bytes_remaining)
        self._on_complete(self.file_path)
        return self.file_path


class ThumbnailDownloader:
    def __init__(self,img:Thumbnail, output_path:str=None, ext_in_path:bool=True,skip_if_exist:bool=True,on_process=None,on_complete=None):
        from PIL import Image
        self.img = img
        self.ext_in_path = ext_in_path
        self.on_process = on_process
        self.on_complete = on_complete
        self.file_path = self.get_file_path(output_path,ext_in_path)
        self.skip = skip_if_exist and self.exists_at_path(output_path)
    @property
    def default_filename(self)->str:
        return generate_filename(ext="jpeg",base=f"thumbnail_{self.img.width}*{self.img.height}px_")
    def exists_at_path(self, file_path: str) -> bool:
        return os.path.isfile(file_path) #and os.path.getsize(file_path) == self.stream.filesize
    def get_file_path(self,file_path:Optional[str],ext_contain:bool=False)->str:
        path = file_path
        if path == None:
            return self.default_filename
        if not ext_contain:
            path += f".jpeg"
        return path
    def get_image(self)->"Image.Image":
        return Image.open(self.get_raw())
    def get_raw(self)->io.BytesIO:
        return io.BytesIO(requests.get(s["url"]).content)
    def download(self):
        if skip:
            return self.file_path
        with open(self.file_path,"wb") as file:
            file.write(self.get_raw())
        return self.file_path


#TODO add CaptionQueryFirst in caption:Union[Caption,CaptionQueryFirst]
class CaptionDownloader:
    def __init__(self,
    caption:Union[Caption,CaptionQueryFirst],
    lang:str=None,
    fmt:str="srt",
    prefer_user_created_cap:bool=True,
    translatable:bool=True,
    delete_nl:bool = False,
    output_path:str=None,
    ext_in_path:bool=False,
    skip_if_exist:bool=True,
    on_process=None,
    on_complete=None):
        """param delete_nl in xml2crt xml2text change some new line symbols to space"""
        self.caption_obj = caption
        self.ext_in_path = ext_in_path
        self.on_process = on_process
        self.on_complete = on_complete
        self.fmt = fmt#TODO ext from fmt, list format and extension matching
        self.delete_nl = delete_nl
        self.lang = lang
        self.prefer_user_created_cap = prefer_user_created_cap
        self.translatable = translatable


        if lang != None and not lang in self.caption_obj.translation_languages:
            raise Exception(f"{lang} is not in translation_languages")

        if isinstance(self.caption_obj,CaptionQueryFirst):
            if lang == None and self.caption_obj.caption_base_generated == None:
                raise Exception("lang is None and not find default")
            self.caption_obj,self.lang = self._get_caption()

        if self.caption_obj == None or (self.caption_obj.is_translatable == False and self.lang != None and self.lang != self.caption_obj.l_code):
            raise Exception("not translatable or not found")



        self.file_path = self.get_file_path(output_path,ext_in_path)
        self.skip = skip_if_exist and self.exists_at_path(self.file_path)

    def _get_caption(self)->Optional[Tuple[Caption,str]]:
        if len(self.caption_obj) == 0:
            return None
        lang = self.lang
        if lang == None:
            lang = self.caption_obj.caption_base_generated.l_code
        val = self.caption_obj.filter(is_generated=not self.prefer_user_created_cap,l_code=lang)
        if len(val) > 0:
            return (val.first,None)
        val = self.caption_obj.filter(is_generated=self.prefer_user_created_cap,l_code=lang)
        if len(val) > 0:
            return (val.first,None)

        if not self.translatable:
            return None

        if self.prefer_user_created_cap and self.caption_obj.caption_base_generated.is_translatable:
            val = self.caption_obj.filter(l_code=self.caption_obj.caption_base_generated.l_code, is_translatable=True,is_generated=False)
        if len(val) > 0:
            return (val.first,lang)
        if self.prefer_user_created_cap:
            val = self.caption_obj.filter(is_translatable=True,is_generated=False)
        if len(val) > 0:
            return (val.first,lang)
        
        if self.caption_obj.caption_base_generated != None:
            return (self.caption_obj.caption_base_generated,lang)
        val = self.caption_obj.filter(is_translatable=True)
        if len(val)>0:
            return (val.first,lang)
        return None
    @property
    def default_filename(self):#TODO caption' lang
        return generate_filename(ext=self.fmt,base=f"caption_{self.caption_obj.vss_id}_")
    def exists_at_path(self, file_path: str) -> bool:
        return os.path.isfile(file_path)
    def get_file_path(self,file_path:Optional[str],ext_contain:bool=False)->str:
        path = file_path
        if path == None:
            return self.default_filename
        if not ext_contain:
            path += f".{self.fmt}"
        return path
    def get(self):
        return self.caption_obj.get(self.fmt,self.lang,self.delete_nl)
    #TODO ext from path
    def download(self):
        if skip:
            return self.file_path
        with open(self.file_path,"w") as file:
            file.write(self.get())
        return self.file_path



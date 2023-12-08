from typing import Callable,Any,Optional
from ..helpers import safe_filename
from ..streams import Stream
import os
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
        self.def_stream = self.stream[0] if isinstance(self.stream,tuple) else self.stream
        self.default_title = default_title
        self.on_complete = on_complete
        self.file_path = self.get_file_path(output_path,ext_in_path)
        self.skip = skip_existing and self.exists_at_path(self.file_path)


    @property
    def default_filename(self) -> str:#TODO update helpers.generate_filename for base includig directory and del param directory 
        #TODO and add param postfix
        #TODO separator if not added symbols to base

        name=self.default_title
        if self.def_stream.title:
            name= self.def_stream.title
        filename = safe_filename(name)
        return f"{filename}.{self.def_stream.ext}"
    def get_file_path(self,file_path:Optional[str],ext_contain:bool=False)->str:
        path = file_path
        if path == None:
            return self.default_filename
        if not ext_contain:
            path += f".{self.def_stream.ext}"
        return path
    def exists_at_path(self, file_path: str) -> bool:
        return os.path.isfile(file_path) #and os.path.getsize(file_path) == self.stream.filesize
    def _on_complete(self,file_path):
        if self.on_complete:
            self.on_complete(self,file_path)
from typing import Optional
from PIL import Image
import io
import os
import requests
import urllib
from ..helpers import generate_filename
from ..thumbnail import Thumbnail
class ThumbnailDownloader:
    def __init__(self,img:Thumbnail, output_path:str=None, ext_in_path:bool=False,skip_if_exist:bool=True):#on_process=None,on_complete=None
        self.img = img
        self.ext_in_path = ext_in_path
        # self.on_process = on_process
        # self.on_complete = on_complete
        self.file_path = self.get_file_path(output_path,ext_in_path)
        self.skip = skip_if_exist and self.exists_at_path(output_path)

    @property
    def default_filename(self)->str:
        return generate_filename(ext=self.file_extention,base=f"thumbnail_{self.img.width}*{self.img.height}px_")
    def exists_at_path(self, file_path: str) -> bool:
        return os.path.isfile(file_path) #and os.path.getsize(file_path) == self.stream.filesize
    def get_file_path(self,file_path:Optional[str],ext_contain:bool=False)->str:
        path = file_path
        if path == None:
            return self.default_filename
        if not ext_contain:
            query = urllib.parse.urlparse(self.img.url)
            ext = query.path.split('.')[-1]
            print(ext)
            path += '.' + ext
        return path
    def get_image(self)->"Image.Image":
        return Image.open(self.get_raw())
    def get_raw(self)->io.BytesIO:
        rr = requests.get(self.img.url)
        if rr.status_code != 200:
            raise Exception(f"status code {rr.status_code}")
        return io.BytesIO(rr.content)
    def download(self):
        if self.skip:
            return self.file_path
        with open(self.file_path,"wb") as file:
            file.write(self.get_raw().getvalue())
        return self.file_path
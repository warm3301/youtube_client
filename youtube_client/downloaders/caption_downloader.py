from typing import Union,Optional,Tuple
import os
from ..captions import Caption
from ..query import CaptionQueryFirst
from ..helpers import generate_filename
class CaptionDownloader:
    def __init__(self,
    caption:Union[Caption,CaptionQueryFirst],
    output_path:str=None,
    fmt:str="srt",
    lang:str=None,
    prefer_user_created_cap:bool=True,
    translatable:bool=True,
    delete_nl:bool = False,
    # ext_in_path:bool=False,
    skip_if_exist:bool=True,
    #on_process=None,
    #on_complete=None
    ):
        """param delete_nl in xml2crt xml2text change some new line symbols to space"""
        self.caption_obj = caption
        self.ext_in_path = None#ext_in_path#Dont use
        # self.on_process = on_process
        # self.on_complete = on_complete
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



        self.file_path = self.get_file_path(output_path,self.ext_in_path)
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
        if self.skip:
            return self.file_path
        with open(self.file_path,"w") as file:
            file.write(self.get())
        return self.file_path



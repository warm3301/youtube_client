import math
import os
import time
import json
import xml.etree.ElementTree as ElementTree
from html import unescape
from typing import Dict, Optional

from . import request
from .helpers import safe_filename, target_directory

class Caption:
    def __init__(self,raw:dict,translation_languages:[(str,str)]):
        self.translation_languages:[(str,str)] = translation_languages
        self.raw:dict = raw
        self.url:str = raw["baseUrl"]
        self.name:str = raw["name"]["simpleText"]
        self.vss_id:str = raw["vssId"]
        self.l_code:str = raw["languageCode"]
        self.is_translatable:bool = raw["isTranslatable"]
        vid =self.vss_id.split('.')
        self.is_generated:bool = vid[0] == "a"
        self.kind:str = raw.get("kind")
        self.rtl:bool = raw.get("rtl",False) #.ar True
    def __repr__(self)->str:
        return f"<Caption vss=\"{self.vss_id}\"/>"


   
    @staticmethod
    def _float_to_srt_time_format(d: float) -> str:
        fraction, whole = math.modf(d)
        time_fmt = time.strftime("%H:%M:%S,", time.gmtime(whole))
        ms = f"{fraction:.3f}".replace("0.", "")
        return time_fmt + ms
    @staticmethod
    def _xml_caption_to_srt(xml_captions: str,replace_nl:bool=False) -> str:
        segments = []
        root = ElementTree.fromstring(xml_captions)
        count_line = 0
        for i, child in enumerate(list(root.findall("text"))):
        
            text = ''.join(child.itertext()).strip()
            if not text:
                continue
            count_line += 1
            tttx = text.replace("  ", " ")
            if replace_nl:
                tttx.replace("\n"," ")
            caption = unescape(tttx,)
            try:
                duration = float(child.attrib["dur"])
            except KeyError:
                duration = 0.0
            start = float(child.attrib["start"])
            end = start + duration
            #end2
            try:
                end2 = float(root.findall("text")[i+2].attrib['start'])
            except:
                end2 = float(root.findall("text")[i].attrib['start']) + duration
            sequence_number = i + 1  # convert from 0-indexed to 1.
            line = "{seq}\n{start} --> {end}\n{text}\n".format(
                seq=count_line,
                start=Caption._float_to_srt_time_format(start),
                end=Caption._float_to_srt_time_format(end),
                text=caption,
            )
            segments.append(line)

        return "\n".join(segments).strip()
    @staticmethod
    def _xml_caption_to_text(xml_captions:str,replace_nl:bool=False)-> str:
        segments = []
        root = ElementTree.fromstring(xml_captions)
        for i, child in enumerate(list(root.findall("text"))):
            text = ''.join(child.itertext()).strip()
            if not text:
                continue
            tttx = text.replace("  ", " ")
            if replace_nl:
                tttx.replace("\n"," ")
            caption = unescape(tttx,)
            segments.append(caption)

        return "\n".join(segments).strip()


    def get(self,fmt:str="srt",t_lang:str=None,delete_nl:bool=False):
        """replace_nl in xml2crt xml2text change some new line symbols to space"""
        if self.is_translatable == False and t_lang != None and t_lang != self.l_code:
            raise Exception("not translatable")
        if t_lang != None and not t_lang in self.translation_languages:
            raise Exception(f"translation_langs does not contains {t_lang}")
        fmt = fmt.lower()
        lq = ""
        if t_lang != None:
            lq = f"&tlang={t_lang}"
        if fmt in ["json","json3"]:
            return request.default_obj.get(self.url + "&fmt=json3"+lq)
        elif fmt == "xml":
            return request.default_obj.get(self.url+lq)
        elif fmt == "srv1":#is xml? by default
            return request.default_obj.get(self.url+"&fmt=srv1"+lq)
        elif fmt == "srv2":
            return request.default_obj.get(self.url+"&fmt=srv2"+lq)
        elif fmt == "srv3":
            return request.default_obj.get(self.url+"&fmt=srv3"+lq)
        elif fmt == "ttml":
            return request.default_obj.get(self.url+"&fmt=ttml"+lq)
        elif fmt in ["vtt","webvtt"]:
            return request.default_obj.get(self.url+"&fmt=vtt"+lq)
        elif fmt in ["txt","text"]:
            return self._xml_caption_to_text(request.default_obj.get(self.url+lq),delete_nl)
        elif fmt == "srt":
            return self._xml_caption_to_srt(request.default_obj.get(self.url+lq),delete_nl)
        else:
            raise Exception("fmt is not supported")

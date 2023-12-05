import socket
import urllib
from functools import cached_property
from . import request
from . import extract
from . import innertube
class BaseYoutube:
    def __init__(self,url):
        self.url:str = url
        self._loaded_base_html:bool = False
        self._loaded_base_initial_data:bool = False
        self._loaded_base_ytcfg:bool = False
    @cached_property
    def parsed_url(self)->urllib.parse.ParseResult:
        return urllib.parse.urlparse(value)
    @cached_property
    def html(self)->str:
        self._loaded_base_html = True
        return request.default_obj.get(url=self.url)
    @cached_property
    def initial_data(self)->dict:
        self._loaded_base_initial_data = True
        ip = extract.initial_data(self.html)
        return ip
    @cached_property
    def ytcfg(self)->dict:
        self._loaded_base_ytcfg = True
        val = extract.get_ytcfg(self.html)
        innertube.update_default_headers(val)
        return val
    @cached_property
    def logged_in(self)->bool:
        return not self.initial_data["responseContext"]["mainAppWebResponseContext"]["loggedOut"]
    @cached_property
    def res_lang(self)->str:
        return self.initial_data["topbar"]["desktopTopbarRenderer"]["searchbox"]["fusionSearchboxRenderer"]["config"]["webSearchboxConfig"]["requestLanguage"]

        



from typing import BinaryIO,Optional,Dict,Tuple
import logging
from math import ceil
from .itags import get_format_profile
from . import request
from datetime import datetime
from urllib.parse import parse_qs
import os
from . import extract, request
from .helpers import safe_filename, target_directory
from .itags import get_format_profile
from urllib.error import HTTPError
import urllib.request
from .cipher import Cipher

logger = logging.getLogger(__name__)

class AudioTrackInfo:
    def __init__(self,raw):
        self.id:str = raw["id"]
        self.name:str = raw["displayName"]
        self.is_default:bool = raw["audioIsDefault"]
    def __repr__(self)->str:
        return f"<AudioTrack {self.name}/>"
class Stream:
    def __init__(self,raw,duration,title):
        self.duration = duration
        self.title = title
        self.raw = raw
        self.itag = raw["itag"]
        self.url:str = raw["url"]
        self._content_lenght:str = int(raw.get("contentLength",0))
        self.average_bitrate:int = raw.get("averageBitrate",None)
        self.mime_type_sourse:str = raw["mimeType"]
        self.bitrate:int = raw["bitrate"]
        self.last_modified:str = raw.get("lastModified")
        self.quality:str = raw["quality"]
        self.projection_type:str = raw["projectionType"]
        self.approx_duration:str = raw.get("approxDurationMs") 
        
        self.color_info_matrix_coefficients:str = None
        self.color_info_primaries:str = None
        self.color_info_transfer_characteristics:str = None
        _color_info = raw.get("colorInfo")
        if _color_info:
            self.color_info_primaries=_color_info.get("primaries")
            self.color_info_transfer_characteristics=_color_info.get("transferCharacteristics")
            self.color_info_matrix_coefficients = _color_info.get("matrixCoefficients")
        
        self.fps:float = raw.get("fps",None)
        self.width:int = raw.get("width",None)
        self.height:int = raw.get("height",None)
        self.video_quality_lable = raw.get("qualityLabel")

        self.audio_quality:str =raw.get("audioQuality")
        self.audio_channels:int = raw.get("audioChannels")
        self.audio_sample_rate:str = raw.get("audioSampleRate")
        self.loudness_db:float = raw.get("loudnessDb")

        # 'video/webm; codecs="vp8, vorbis"' -> 'video/webm', ['vp8', 'vorbis']
        self.mime_type, self.codecs = extract.mime_type_codec(self.mime_type_sourse)
        # 'video/webm' -> 'video', 'webm'
        self.type, self.ext = self.mime_type.split("/")

        # ['vp8', 'vorbis'] -> video_codec: vp8, audio_codec: vorbis. DASH
        # streams return NoneType for audio/video depending.
        self.video_codec, self.audio_codec = self.parse_codecs()
        

        
        self._filesize_kb: Optional[float] = float(ceil(float(self._content_lenght) / 1024 * 1000) / 1000)
        self._filesize_mb: Optional[float] = float(ceil(float(self._content_lenght) / 1024 / 1024 * 1000) / 1000)
        self._filesize_gb: Optional[float] = float(ceil(float(self._content_lenght) / 1024 / 1024 / 1024 * 1000) / 1000)

        # Additional information about the stream format, such as resolution,
        # frame rate, and whether the stream is live (HLS) or 3D.
        itag_profile = get_format_profile(self.itag)
        self.is_dash = itag_profile["is_dash"]
        self.abr = itag_profile["abr"]  # average bitrate (audio streams only)
        self.resolution = itag_profile[
            "resolution"
        ]  # resolution (e.g.: "480p")
        self.is_3d:bool = itag_profile["is_3d"]
        self.is_hdr:bool = itag_profile["is_hdr"]
        # self.is_live:bool = itag_profile["is_live"] # not true
        self.is_otf:bool = raw.get("is_otf",None)
        self._lparsed_url = None

        self.contains_audio_track_info:bool =  "audioTrack" in raw
        self.audio_track_info:Optional[AudioTrackInfo] = AudioTrackInfo(raw["audioTrack"]) if self.contains_audio_track_info else None
        

    #From url
    @property
    def _parsed_url(self):#expire = parse_qs(self.url.split("?")[1])["expire"][0]
        if self._lparsed_url:
            return self._lparsed_url
        self._lparsed_url = parse_qs(self.url.split("?")[1])#urllib.parse.urlparse(url)
        return self._lparsed_url
    @property
    def expiration(self) -> datetime:
        expire = self._parsed_url["expire"][0]
        return datetime.utcfromtimestamp(int(expire))
    @property
    def current_ip(self)->str:
        return self._parsed_url['ip'][0]
    @property
    def aitags(self)->[int]:#TODO for test:
        return [int(x) for x in self._parsed_url.get("aitags",[""])[0].split(',') if x.isdigit()]
    @property
    def require_ssl(self)->Optional[bool]:#TODO move to extract.py
        val = self._parsed_url["requiressl"][0]
        if val == "yes":
            return True
        elif val == "no":
            return False
        else:
            return None
    @property
    def url_duration(self)->float:
        return float(self._parsed_url.get('dur',[0])[0])
    @property
    def lmt(self)->Optional[str]:
        return self._parsed_url.get('lmt',[None])[0]
    @property
    def keep_alive(self)->Optional[bool]:
        val = self._parsed_url.get('keepalive',[None])[0]
        if val == "yes":
            return True
        elif val == "no":
            return False
        else:
            return None
    @property
    def ratebypass(self)->Optional[bool]:
        val = self._parsed_url.get('ratebypass',[None])[0]
        if val == "yes":
            return True
        elif val == "no":
            return False
        else:
            return None
    @property
    def pcm2cms(self)->Optional[bool]:
        val = self._parsed_url.get("pcm2cms",[None])[0]
        if val == "yes":
            return True
        elif val == "no":
            return False
        else:
            return None
    @property
    def sm_host(self)->Optional[str]:
        """For live stream"""
        return self._parsed_url.get("smhost",[None])[0]
    @property
    def sourse(self)->str:
        return self._parsed_url.get("source",[None])[0]
    @property
    def is_live(self)->bool:
        return self._parsed_url.get("live",[0])[0] == "1"
    @property
    def current_device(self)->str:
        return self._parsed_url.get("c",[None])[0]
    @property
    def filesize(self) -> int:
        """File size of the media stream in bytes.

        :rtype: int
        :returns:
            Filesize (in bytes) of the stream.
        """
        if self._content_lenght == 0:
            try:
                self._content_lenght = request.filesize(self.url)
            except HTTPError as e:
                if e.code != 404:
                    raise
                self._content_lenght = request.seq_filesize(self.url)
        return self._content_lenght
    @property
    def filesize_kb(self) -> float:
        """File size of the media stream in kilobytes.

        :rtype: float
        :returns:
            Rounded filesize (in kilobytes) of the stream.
        """
        if self._filesize_kb == 0:
            try:
                self._filesize_kb = float(ceil(request.filesize(self.url)/1024 * 1000) / 1000)
            except HTTPError as e:
                if e.code != 404:
                    raise
                self._filesize_kb = float(ceil(request.seq_filesize(self.url)/1024 * 1000) / 1000)
        return self._filesize_kb
    
    @property
    def filesize_mb(self) -> float:
        """File size of the media stream in megabytes.

        :rtype: float
        :returns:
            Rounded filesize (in megabytes) of the stream.
        """
        if self._filesize_mb == 0:
            try:
                self._filesize_mb = float(ceil(request.filesize(self.url)/1024/1024 * 1000) / 1000)
            except HTTPError as e:
                if e.code != 404:
                    raise
                self._filesize_mb = float(ceil(request.seq_filesize(self.url)/1024/1024 * 1000) / 1000)
        return self._filesize_mb

    @property
    def filesize_gb(self) -> float:
        """File size of the media stream in gigabytes.

        :rtype: float
        :returns:
            Rounded filesize (in gigabytes) of the stream.
        """
        if self._filesize_gb == 0:
            try:
                self._filesize_gb = float(ceil(request.filesize(self.url)/1024/1024/1024 * 1000) / 1000)
            except HTTPError as e:
                if e.code != 404:
                    raise
                self._filesize_gb = float(ceil(request.seq_filesize(self.url)/1024/1024/1024 * 1000) / 1000)
        return self._filesize_gb
    #TODO ?
    @property
    def filesize_approx(self) -> int:
        """Get approximate filesize of the video

        Falls back to HTTP call if there is not sufficient information to approximate

        :rtype: int
        :returns: size of video in bytes
        """
        if self.duration and self.bitrate:
            return int(
                (int(self.duration) * self.bitrate) / 8
            )

        return self.filesize
    @property
    def filesize_approx_kb(self)->float:
        return float(ceil(self.filesize_approx / 1024 * 1000)/1000)
    @property
    def filesize_approx_mb(self)->float:
        return float(ceil(self.filesize_approx/1024/1024 * 1000)/1000)
    @property
    def filesize_approx_gb(self)->float:
        return float(ceil(self.filesize_approx/1024/1024/1024 * 1000)/1000)
    
    @property
    def is_adaptive(self) -> bool:
        """Whether the stream is DASH.

        :rtype: bool
        """
        # if codecs has two elements (e.g.: ['vp8', 'vorbis']): 2 % 2 = 0
        # if codecs has one element (e.g.: ['vp8']) 1 % 2 = 1
        #return bool(len(self.codecs) % 2)
        return self.raw["is_adaptive"]

    @property
    def is_progressive(self) -> bool:
        """Whether the stream is progressive.

        :rtype: bool
        """
        return not self.is_adaptive

    @property
    def includes_audio(self) -> bool:
        """Whether the stream only contains audio.

        :rtype: bool
        """
        return self.is_progressive or self.type == "audio"

    @property
    def includes_video(self) -> bool:
        """Whether the stream only contains video.

        :rtype: bool
        """
        return self.is_progressive or self.type == "video"
    @property
    def only_video(self)->bool:
        return self.includes_video and (not self.includes_audio)
    @property
    def only_audio(self)->bool:
        return self.includes_audio and (not self.includes_video)
    
    def parse_codecs(self) -> (str, str):
        """Get the video/audio codecs from list of codecs.

        Parse a variable length sized list of codecs and returns a
        constant two element tuple, with the video codec as the first element
        and audio as the second. Returns None if one is not available
        (adaptive only).

        :rtype: tuple
        :returns:
            A two element tuple with audio and video codecs.

        """
        video = None
        audio = None
        if not self.is_adaptive:
            video, audio = self.codecs
        elif self.includes_video:
            video = self.codecs[0]
        elif self.includes_audio:
            audio = self.codecs[0]
        return video, audio
   
    def __repr__(self)->str:
        parts = ['itag="{s.itag}"', 'mime_type="{s.mime_type}"']
        if self.includes_video:
            parts.extend(['res="{s.resolution}"', 'fps="{s.fps}fps"'])
            if not self.is_adaptive:
                parts.extend(
                    ['vcodec="{s.video_codec}"', 'acodec="{s.audio_codec}"',]
                )
            else:
                parts.extend(['vcodec="{s.video_codec}"'])
        else:
            parts.extend(['abr="{s.abr}"', 'acodec="{s.audio_codec}"'])
        parts.extend(['progressive="{s.is_progressive}"', 'type="{s.type}"'])
        return f"<Stream: {' '.join(parts).format(s=self)}>"





from datetime import date, datetime
from .base_youtube import BaseYoutube
from . import extract
from . import video
from . import thumbnail
from .query import ThumbnailQuery,get_thumbnails_from_raw
from functools import cached_property
from . import request
from . import innertube
from typing import Iterable,List,Optional

class VideoPlaylistResult:
    def __init__(self,raw:dict):
        self.raw =raw
        self.video_id:str = raw["videoId"]
        self.url:str = "https://youtube.com" + raw["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
        self.title:str = "".join(x["text"] for x in raw["title"]["runs"])
        self.lenght_sec:str = raw["lengthSeconds"]
        self.lenght:str = raw["lengthText"]["simpleText"]

        vid_info = raw["videoInfo"]
        self.view_count:Optional[str] =None
        self.publish_date:str = None
        #TODO "badges" in raw and raw["badges"][0]["metadataBadgeRenderer"]["style"] == "BADGE_STYLE_TYPE_MEMBERS_ONLY"
        if "simpleText" in vid_info:
            self.publish_date = vid_info["simpleText"]
            self.view_count = None
        else:
            self.view_count = vid_info["runs"][0]["text"]
            self.publish_date = vid_info["runs"][-1]["text"]

        self.owner_name:str = raw["shortBylineText"]["runs"][0]["text"]
        self.owner_id:str = raw["shortBylineText"]["runs"][0]["navigationEndpoint"]["browseEndpoint"]["browseId"]
        self.owner_url:str = "https://youtube.com" + raw["shortBylineText"]["runs"][0]["navigationEndpoint"]["browseEndpoint"]["canonicalBaseUrl"]

        self.index:str = raw["index"]["simpleText"] if "index" in raw else None
        self.is_playable:bool = raw['isPlayable']

        

    @property
    def thumbnails(self)->ThumbnailQuery:
        return get_thumbnails_from_raw(self.raw["thumbnail"]["thumbnails"])
    def get_full_obj(self)->video.Video:
        return video.Video(url=self.url)
    def __repr__(self)->str:
        return f"<VideoPlaylistItem {self.video_id} {self.title=}/>"
#TODO continuation
class Playlist(BaseYoutube):
    def __init__(self,url:str):#TODO pl id
        super().__init__(url)
        self.playlist_id:str = extract.playlist_id(url)
        self.playlist_url:str = f"https://www.youtube.com/playlist?list={self.playlist_id}"
        self.current_video_id:str = None
        self.current_video_url:str = None
        try:
            self.current_video_id = extract.video_id(url)
            self.current_video_url = video.get_url(self.current_video_id)
        except KeyError: pass
        self.contains_video:bool = self.current_video_id != None
    def __repr__(self)->str:
        return f"<Playlist id=\"{self.playlist_id}\"/>"
    @cached_property
    def playlist_initial_data(self)->dict:
        return extract.initial_data(request.get(self.playlist_url))
    @cached_property
    def playable_playlist_info(self)->dict:
        return self.initial_data["contents"]["twoColumnWatchNextResults"]["playlist"]["playlist"]
    @property
    def _metadata(self)->dict:
        return self.playlist_initial_data["metadata"]["playlistMetadataRenderer"]
    @property
    def _microformat(self)->dict:
        return self.playlist_initial_data["microformat"]["microformatDataRenderer"]
    @property
    def _sidebar_primary_info(self)->dict:
        return self.playlist_initial_data["sidebar"]["playlistSidebarRenderer"]["items"][0]["playlistSidebarPrimaryInfoRenderer"]
    @property
    def _sidebar_secondary_info(self)->dict:
        return self.playlist_initial_data["sidebar"]["playlistSidebarRenderer"]["items"][1]["playlistSidebarSecondaryInfoRenderer"]["videoOwner"]["videoOwnerRenderer"]
    @property
    def _contents(self)->List[dict]:
        return self.playlist_initial_data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"]
    @property
    def title(self)->str:
        return self._sidebar_primary_info["title"]["runs"][0]["text"]
    @property
    def thumbnails(self)->ThumbnailQuery:
        return get_thumbnails_from_raw(self._sidebar_primary_info["thumbnailRenderer"]["playlistVideoThumbnailRenderer"]["thumbnail"]["thumbnails"])
    @property
    def video_count(self)->str:
        return self._sidebar_primary_info["stats"][0]["runs"][0]["text"]
    @property
    def view_count(self)->str:
        return self._sidebar_primary_info["stats"][1]["simpleText"]
    @property
    def updated_date(self)->str:
        return self._sidebar_primary_info["stats"][-1]["runs"][-1]["text"]


    @property
    def first_video_url(self)->str:
        return "https://youtube.com" + self._sidebar_primary_info["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
    @property
    def first_video_id(self)->str:
        return self._sidebar_primary_info["navigationEndpoint"]["watchEndpoint"]["videoId"]
    @property
    def first_video(self)->video.Video:
        return video.Video(url=self.first_video_url)


    @property
    def description(self)->Optional[str]:
        return self._sidebar_primary_info["description"]["simpleText"] if "simpleText" in self._sidebar_primary_info["description"] else None
    @property
    def owner_name(self)->str:
        return self._sidebar_secondary_info["title"]["runs"][0]["text"]
    @property
    def owner_url(self)->str:
        return "https://youtube.com" + self._sidebar_secondary_info["navigationEndpoint"]["browseEndpoint"]["canonicalBaseUrl"]
    @property
    def owner_id(self)->str:
        return self._sidebar_secondary_info["navigationEndpoint"]["browseEndpoint"]["browseId"]
    #TODO is editable can delate public state
    @property
    def is_editable(self)->bool:
        return self._contents[0]["itemSectionRenderer"]["contents"][0]["playlistVideoListRenderer"]["isEditable"]
    @property
    def can_reorder(self)->bool:
        return self._contents[0]["itemSectionRenderer"]["contents"][0]["playlistVideoListRenderer"]["canReorder"]


    def _extract_from_raw(self,raw)->(List[VideoPlaylistResult],Optional[str]):
        videos = []
        continuation = None
        if "continuationItemRenderer" in raw[-1]:
            continuation = raw[-1]["continuationItemRenderer"]["continuationEndpoint"]["continuationCommand"]["token"]
            raw = raw[:-1]
        for x in raw:
            videos.append(VideoPlaylistResult(x["playlistVideoRenderer"]))

        return videos,continuation
    def get_videos(self)->Iterable[List[VideoPlaylistResult]]:
        videos,continuation = self._extract_from_raw(self._contents[0]["itemSectionRenderer"]["contents"][0]["playlistVideoListRenderer"]["contents"])
        yield videos
        if continuation == None:
            return
        while continuation:
            raw = innertube.default_obj.browse(browse_id=None,continuation=continuation)
            raw = raw["onResponseReceivedActions"][0]["appendContinuationItemsAction"]["continuationItems"]
            videos,continuation = self._extract_from_raw(raw)
            yield videos
    @property
    def mobile_url(self)->str:
        return self._microformat["linkAlternates"][0]["hrefUrl"]
    @property
    def android_url(self)->str:
        return self._microformat["linkAlternates"][1]["hrefUrl"]
    @property
    def ios_url(self) ->str:
        return self._microformat["linkAlternates"][2]["hrefUrl"]
    @property
    def noindex(self)->bool:
        return self._microformat["noindex"]
    @property
    def unlisted(self)->bool:
        return self._microformat["noindex"]
    @property
    def message(self)->Optional[str]:
        if "alerts" in self.playlist_initial_data:
            return self.playlist_initial_data["alerts"][0]["alertWithButtonRenderer"]["text"]["simpleText"]
        return None
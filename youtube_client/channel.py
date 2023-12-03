from typing import Iterator,List,Optional,Iterable
from functools import cached_property
from abc import abstractmethod,ABC
import enum

from .base_youtube import BaseYoutube
from . import extract
from . import request
from . import thumbnail
from .playlist import Playlist
from .video import Video
from .live import Live
from .post import PostThread
from . import innertube
from . import short
from .query import get_thumbnails_from_raw,ThumbnailQuery

class GetBy(enum.Enum):
    """Sort type items in channel"""
    new = 0
    top = 1
    old = 2
class Link:
    def __init__(self,raw):
        self.raw = raw
        self.content = raw["title"]["content"]
        self.url_info = raw["link"]["content"]
        self.raw_url = raw["link"]["commandRuns"][0]["onTap"]["innertubeCommand"]["urlEndpoint"]["url"]
        self.url = extract.decode_url(self.raw_url)
    def __repr__(self)->str:
        return f"<Link {self.content} {self.url}/>"
    @property
    def favicon(self)->Optional[ThumbnailQuery]:
        return get_thumbnails_from_raw(raw["favicon"]["sources"])if "favicon" in raw else None
class ResultObject(ABC):
    def __init__(self,raw:str):
        self.raw = raw
    @property
    def url(self)->str:
        return "https:/youtube.com"+self.raw["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
    @property
    def title(self)->str:
        try:
            try:
                return " ".join([x["text"] for x in self.raw["title"]["runs"]])
            except KeyError:
                return self.raw["title"]["simpleText"]
        except KeyError:
            return self.raw["headline"]["simpleText"]
    @abstractmethod
    def get_full_obj(self):NotImplemented
class PlayableBaseObject(ResultObject):
    def __init__(self,raw:str):
        super().__init__(raw)
    @property
    def thumbnails(self)->ThumbnailQuery:
        return get_thumbnails_from_raw(self.raw["thumbnail"]["thumbnails"])
    @abstractmethod
    def get_full_obj(self):
        v = Video(url=self.url)
        v.title = self.title
    @property
    def id(self)->str:
        try:
            return self.raw["videoId"]
        except KeyError:
            return extract.video_id(self.raw)
class VideoResult(PlayableBaseObject):
    def __init__(self,raw):
        super().__init__(raw)
    @property
    def moving_thumbnails(self)->Optional[ThumbnailQuery]:
        return get_thumbnails_from_raw(self.raw["richThumbnail"]["movingThumbnailRenderer"][
                "movingThumbnailDetails"]["thumbnails"])[0] if "richThumbnail" in self.raw else None
    @property
    def published_time_text(self)->str:
        return self.raw["publishedTimeText"]["simpleText"]
    @property
    def lenght(self)->str:
        return self.raw["lengthText"]["simpleText"]
    @property
    def view_count(self)->str:
        return self.raw["viewCountText"]["simpleText"]
    @property
    def description_snippet(self)->str:
        return "".join(x["text"] for x in self.raw["descriptionSnippet"]["runs"])
    @property
    def owner_is_vereficated(self)->bool:
        try:
            return  self.raw["ownerBadges"][0]["metadataBadgeRenderer"]["style"] in ["BADGE_STYLE_TYPE_VERIFIED","BADGE_STYLE_TYPE_VERIFIED_ARTIST"]
        except KeyError:
            return False
    def __repr__(self)->str:
        return f"<VideoChannelResult {self.id} title=\"{self.title[:100]}\"/>"
    def get_full_obj(self)->Video:
        v = Video(url=self.url)
        v.title = self.title
        return v
class LiveResult(VideoResult):
    def __init__(self,raw):
        super().__init__(raw)
    def __repr__(self)->str:
        return f"<LiveChannelResult {self.id} title=\"{self.title[:100]}\"/>"
    def get_full_obj(self)->Video:
        v = Live(url=self.url)
        v.title = self.title
        return v
class ShortResult(PlayableBaseObject):
    def __init__(self,raw:str):
        super().__init__(raw)
    @property
    def video_type(self)->str:
        return self.raw["videoType"]
    @property
    def style(self)->str:
        return self.raw["style"]
    @property
    def other_thumbnails(self)->ThumbnailQuery:
        return get_thumbnails_from_raw(self.raw["navigationEndpoint"]["reelWatchEndpoint"]["thumbnail"]["thumbnails"])
    @property
    def view_count(self)->str:
        return self.raw["viewCountText"]["simpleText"]
    #TODO lenght via accessibility
    def __repr__(self)->str:
        return f"<ShortResult {self.id=} title=\"{self.title[:100]}\"/>"
    def get_full_obj(self)->short.Short:
        v = Short(url=self.url)
        v.title = self.title
        return v
class PlaylistResult(PlayableBaseObject):
    def __init__(self,raw:str):
        super().__init__(raw)
    @property
    def playlist_id(self)->str:
        return self.raw["playlistId"]
    @property
    def video_count(self)->str:
        #return "".join([x["text"] for x in self.raw["videoCountText"]["runs"]])
        return self.raw["videoCountShortText"]["simpleText"]
    @property
    def sidebar_thumbnails(self)->ThumbnailQuery:
        return get_thumbnails_from_raw(self.raw["sidebarThumbnails"][0]["thumbnails"])
    @property
    def renderer_thumbnails(self)->ThumbnailQuery:
        return get_thumbnails_from_raw(self.raw["thumbnailRenderer"]["playlistVideoThumbnailRenderer"]["thumbnail"]["thumbnails"])
    @property
    def owner_is_vereficated(self)->bool:
        try:
            return  self.raw["ownerBadges"][0]["metadataBadgeRenderer"]["style"] in ["BADGE_STYLE_TYPE_VERIFIED","BADGE_STYLE_TYPE_VERIFIED_ARTIST"]
        except KeyError:
            return False

    def __repr__(self)->str:
        return f"<PlaylistResult {self.title=}/>"
    def get_full_obj(self)->Playlist:
        pl = Playlist(url = self.url)
        return pl
class Channel(BaseYoutube):
    def __init__(self,url:str):
        channel_url = url
        try:
            channel_url = "https://youtube.com"+extract.channel_name(url)
        except:
            pass
        self.featured_url = channel_url + "/featured"
        self.videos_url = channel_url + '/videos'
        self.shorts_url = channel_url + "/shorts"
        self.streams_url = channel_url + "/streams"
        self.playlists_url = channel_url + '/playlists'
        self.community_url = channel_url + '/community'
        self.list_channels_url = channel_url + '/channels'
        self.about_url = channel_url + '/about'
        super().__init__(channel_url)
        self._tab_content_by_url:dict = {}
        self._last_initial_data = None

    def __repr__(self)->str:
        return f"<Channel {self.url}/>"
    def _get_tab_content_by_url(self,url:str)->dict:
        if url in self._tab_content_by_url.keys():
            return self._tab_content_by_url[url]
        if url == self.featured_url or url == self.url:
            tab_renders = self.initial_data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"]
            return tab_renders
        html = request.default_obj.get(url)
        ind = extract.initial_data(html)
        if not innertube.updated_headers:
            innertube.update_default_headers(extract.get_ytcfg(html))
        self._last_initial_data = ind
        tab_renders = ind["contents"]["twoColumnBrowseResultsRenderer"]["tabs"]
        self._tab_content_by_url[url] = tab_renders
        return tab_renders
    def _find_tab_by_end_url(self,tabs:List[dict],end:str)->Optional[dict]:
        for tab in tabs:
            try:
                if tab["tabRenderer"]["endpoint"]["commandMetadata"]["webCommandMetadata"]["url"].endswith(end):
                    return tab
            except KeyError:
                continue
        return None
    @property
    def tab_content_main(self)->dict:
        return self._find_tab_by_end_url(self._get_tab_content_by_url(self.featured_url),"featured")["tabRenderer"]
    #Except error if not exist ValueError
    @property
    def tab_content_videos(self)->dict:
        return self._find_tab_by_end_url(self._get_tab_content_by_url(self.videos_url),"videos")["tabRenderer"]
    @property
    def tab_content_shorts(self)->dict:
        return self._find_tab_by_end_url(self._get_tab_content_by_url(self.shorts_url),"shorts")["tabRenderer"]
    @property
    def tab_content_lives(self)->dict:
        return self._find_tab_by_end_url(self._get_tab_content_by_url(self.streams_url),"streams")["tabRenderer"]
    @property
    def tab_content_playlists(self)->dict:
        return self._find_tab_by_end_url(self._get_tab_content_by_url(self.playlists_url),"playlists")["tabRenderer"]
    @property
    def tab_content_community(self)->dict:
        return self._find_tab_by_end_url(self._get_tab_content_by_url(self.community_url),"community")["tabRenderer"]
    
    @property
    def _second_inital_data(self)->dict:
        """provides the ability to use shared data from any tabs, such as home, videos, playlists, etc."""
        idate = None
        if self._last_initial_data:
            idate = self._last_initial_data
        else:
            idate = self.initial_data
            self._last_initial_data = idate
        return idate
    @property
    def _metadata_renderer(self)->dict:
       return self._second_inital_data["metadata"]["channelMetadataRenderer"]
    @property
    def _tabbed_renderer(self)->dict:
        return self._second_inital_data["header"]["c4TabbedHeaderRenderer"]

    @cached_property
    def title(self)->str:
        return self._metadata_renderer["title"]
    @property
    def description(self)->str:
        return self._metadata_renderer["description"]
    @property
    def short_description(self)->str:
        return self._second_inital_data["microformat"]["microformatDataRenderer"]["description"]
    @property
    def keywords(self)->str:#TODO split fgdsf "first_word second_word" sfas asdf
        return self._metadata_renderer["keywords"]

    @property
    def canonical_url(self)->str:
        return self._second_inital_data["microformat"]["microformatDataRenderer"]["urlCanonical"]
    @property
    def channel_id(self)->str:
        return self._tabbed_renderer["channelId"]
    @property
    def owner_urls(self)->List[str]:
        return self._metadata_renderer["ownerUrls"]
    @property
    def vanity_url(self)->str:
        return self._metadata_renderer["vanityChannelUrl"]
    
    @property
    def is_family_safe(self)->bool:
        return self._metadata_renderer["isFamilySafe"]
    @property
    def no_index(self)->bool:
        return self._second_inital_data["microformat"]["microformatDataRenderer"]["noindex"]
    @property
    def unlisted(self)->bool:
        return self._second_inital_data["microformat"]["microformatDataRenderer"]["unlisted"]
    @property
    def tags(self)->List[str]:
        return self._second_inital_data["microformat"]["microformatDataRenderer"]["tags"]
    @property
    def available_country_codes(self) ->List[str]:
        return self._metadata_renderer["availableCountryCodes"]

    @property
    def short_description(self)->str:
        return self._tabbed_renderer["tagline"]["channelTaglineRenderer"]["content"]
    @property
    def one_header_link(self)->str:#TODO object??
        return self._tabbed_renderer["headerLinks"]["channelHeaderLinksViewModel"]["firstLink"]["content"]
    @property
    def is_vereficated(self)->str:
        try:
            return self._tabbed_renderer["badges"][0]["metadataBadgeRenderer"]["style"] in ["BADGE_STYLE_TYPE_VERIFIED_ARTIST","BADGE_STYLE_TYPE_VERIFIED"]
        except Exception as e:
            return False
        
    
    @property
    def avatars(self)->ThumbnailQuery:
        return get_thumbnails_from_raw(self._tabbed_renderer["avatar"]["thumbnails"])
    @property
    def avatars_high(self)->ThumbnailQuery:
        return get_thumbnails_from_raw(self._metadata_renderer["avatar"]["thumbnails"])
    @property
    def thumbnails(self)->ThumbnailQuery:
        return get_thumbnails_from_raw(self._second_inital_data["microformat"]["microformatDataRenderer"]["thumbnail"]["thumbnails"])
    @property
    def banners(self)->ThumbnailQuery:
        return get_thumbnails_from_raw(self._tabbed_renderer["banner"]["thumbnails"])
    @property
    def tv_banners(self)->ThumbnailQuery:
        return get_thumbnails_from_raw(self._tabbed_renderer["tvBanner"]["thumbnails"])
    @property
    def mobile_banners(self)->ThumbnailQuery:
        return get_thumbnails_from_raw(self._tabbed_renderer["mobileBanner"]["thumbnails"])


    @property
    def videos_count(self)->str:
        return self._tabbed_renderer["videosCountText"]["runs"][0]["text"]
    @property
    def subscribers_count(self) -> str:
        return self._tabbed_renderer["subscriberCountText"]["simpleText"]
    

    #TODO other continuation new,top,old
    def _extract_videos_from_raw(self,raw_videos:List[dict])->([Video],str):
        vids = []
        continuation = None
        if "continuationItemRenderer" in raw_videos[-1]:
            continuation = raw_videos[-1]["continuationItemRenderer"][
                "continuationEndpoint"]["continuationCommand"]["token"]
            raw_videos = raw_videos[:-1]
        for x in raw_videos:
            vr = x["richItemRenderer"]["content"]["videoRenderer"]
            vids.append(VideoResult(vr))
        return vids,continuation

    @property
    def _other_video_continuation(self):
        return self.tab_content_videos["content"]["richGridRenderer"]["header"]["feedFilterChipBarRenderer"]["contents"]
    
    def get_videos(self)->Iterator[List[Video]]:
        videos,continuation = self._extract_videos_from_raw(self.tab_content_videos["content"][
                "richGridRenderer"]["contents"])
        yield videos
        if continuation == None:
            return
        it = innertube.default_obj
        while continuation:
            res = it.browse(browse_id=None,continuation=continuation)
            if len(res["onResponseReceivedActions"]) == 1:
                videos,continuation = self._extract_videos_from_raw(res["onResponseReceivedActions"][0][
                    "appendContinuationItemsAction"]["continuationItems"])
            else:
                videos,continuation = self._extract_videos_from_raw(res["onResponseReceivedActions"][1][
                    "reloadContinuationItemsCommand"]["continuationItems"])
            yield videos



    def _extract_posts_from_raw(self,raw:List[dict])->(List[PostThread],Optional[str]): 
        continuation = None
        if "continuationItemRenderer" in raw[-1]:
            continuation = raw[-1]["continuationItemRenderer"]["continuationEndpoint"][
                "continuationCommand"]["token"]
            raw = raw[:-1]
        return [PostThread(x["backstagePostThreadRenderer"]["post"][
            "backstagePostRenderer"]) for x in raw],continuation

    def get_posts(self)->Iterator[List[PostThread]]:
        cont = self.tab_content_community["content"]["sectionListRenderer"]["contents"][0][
            "itemSectionRenderer"]["contents"]
        if "messageRenderer" in cont[0]:
            return
        posts,continuation = self._extract_posts_from_raw(cont)
        it = innertube.default_obj
        while continuation:
            #sometimes browse return result with 0 items and also contains continuation token.
            while True:
                res = it.browse(browse_id=None,continuation=continuation)
                apcia = res["onResponseReceivedEndpoints"][0][
                        "appendContinuationItemsAction"]
                if not "continuationItems" in apcia:
                    return
                posts,continuation = self._extract_posts_from_raw(apcia["continuationItems"])
                if len(posts) > 0:
                    break
            yield posts
        else:
            yield posts
            


    def _extract_shorts_from_raw(self,raw:List[dict]) -> (List[ShortResult],Optional[str]):
        continuation = None
        if "continuationItemRenderer" in raw[-1]:
            continuation = raw[-1]["continuationItemRenderer"]["continuationEndpoint"]["continuationCommand"]["token"]#BROWSE
            raw = raw[:-1]
        shorts = []
        for x in raw:
            renderer = x["richItemRenderer"]["content"]["reelItemRenderer"]
            shorts.append(ShortResult(renderer))
        return shorts,continuation
    def get_shorts(self)->Iterator[short.Short]:
        shorts, continuation = self._extract_shorts_from_raw(self.tab_content_shorts["content"]["richGridRenderer"]["contents"])
        i = 0
        yield shorts
        if continuation == None:
            return
        it = innertube.default_obj
        while continuation:
            res=it.browse(browse_id=None,continuation=continuation)
            if len(res["onResponseReceivedActions"]) == 1:
                shorts,continuation = self._extract_shorts_from_raw(res["onResponseReceivedActions"][0][
                    "appendContinuationItemsAction"]["continuationItems"])
            else:
                shorts,continuation = self._extract_shorts_from_raw(res["onResponseReceivedActions"][1][
                    "reloadContinuationItemsCommand"]["continuationItems"])
            yield shorts

        
    def _extract_lives_from_raw(self,raw:List[dict])->(List[Live],Optional[str]):
        continuation = None
        if "continuationItemRenderer" in raw[-1]:
            continuation = raw[-1]["continuationItemRenderer"]["continuationEndpoint"]["continuationCommand"]["token"]#BROWSE
            raw = raw[:-1]
        lives = []
        for x in raw:
            renderer = x["richItemRenderer"]["content"]["videoRenderer"]
            lives.append(LiveResult(renderer))
        return lives,continuation
    def get_lives(self)->Iterator[List[Live]]:
        lives,continuation = self._extract_lives_from_raw(self.tab_content_lives["content"]["richGridRenderer"]["contents"])
        yield lives
        if continuation == None:
            return
        it = innertube.default_obj
        while continuation:
            res = it.browse(browse_id=None,continuation=continuation)
            if len(res["onResponseReceivedActions"]) == 1:
                lives,continuation = self._extract_lives_from_raw(res["onResponseReceivedActions"][0][
                    "appendContinuationItemsAction"]["continuationItems"])
            else:
                lives,continuation = self._extract_lives_from_raw(res["onResponseReceivedActions"][1][
                    "reloadContinuationItemsCommand"]["continuationItems"])
            yield lives


    #not work -_-
    # @property
    # def channels(self):
    #     ch_objs = []
    #     for x in self.tab_content_list_channels["content"]["sectionListRenderer"]["contents"][0][
    #         "itemSectionRenderer"]["contents"][0]["gridRenderer"]["items"]:
    #         renderer = x["gridChannelRenderer"]
    #         ch_id:str = renderer["channelId"]
    #         th:[thumbnail.Thumbnail] = get_thumbnails_from_raw(renderer["thumbnail"]["thumbnails"])
    #         video_count_text:str = renderer["videoCountText"]["runs"][0]["text"]
    #         subscribers_count_text:str = renderer["subscriberCountText"]["simpleText"]
    #         url:str = renderer["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
    #         title:str = renderer["title"]["simpleText"]
    #         is_vereficated = renderer["ownerBadges"][0][
    #             "metadataBadgeRenderer"]["style"] == "BADGE_STYLE_TYPE_VERIFIED" if "ownerBadges" in renderer else False
    #         ch_obj = Channel(url = f"https://youtube.com{url}")
    #         ch_objs.append(ch_obj)
    #     return ch_objs


    def _extract_playlists_from_raw(self,raw:List[dict])->(List[Playlist],Optional[str]):
        continuation = None
        if "continuationItemRenderer" in raw[-1]:
            continuation = raw[-1]["continuationItemRenderer"]["continuationEndpoint"]["continuationCommand"]["token"]#BROWSE
            raw = raw[:-1]
        pl_objs = []
        for x in raw:
            renderer = x["gridPlaylistRenderer"]
            pl_objs.append(PlaylistResult(renderer))
        return pl_objs,continuation
    def get_playlists(self)->Iterator[List[Playlist]]:
        playlists,continuation = self._extract_playlists_from_raw(self.tab_content_playlists["content"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"][
            "contents"][0]["gridRenderer"]["items"])
        yield playlists
        if continuation == None:
            return
        it = innertube.default_obj
        while continuation:
            res = it.browse(browse_id=None,continuation=continuation)
            if len(res["onResponseReceivedActions"]) == 1:
                playlists,continuation = self._extract_playlists_from_raw(res["onResponseReceivedActions"][0][
                    "appendContinuationItemsAction"]["continuationItems"])
            else:
                playlists,continuation = self._extract_playlists_from_raw(res["onResponseReceivedActions"][1][
                    "reloadContinuationItemsCommand"]["continuationItems"])
            yield playlists


    #TODO iosAppindexingLink androidAppindexingLink androidDeepLink
    @property
    def mobile_link(self)->str:
        return self._second_inital_data["microformat"]["microformatDataRenderer"]["linkAlternates"][0]["hrefUrl"]
    @property
    def android_link(self)->str:
        return self._second_inital_data["microformat"]["microformatDataRenderer"]["linkAlternates"][1]["hrefUrl"]
    @property
    def ios_link(self) ->str:
        return self._second_inital_data["microformat"]["microformatDataRenderer"]["linkAlternates"][2]["hrefUrl"]
    @property
    def channel_source(self)->str:
        """@UserName"""
        return "".join([x["text"] for x in self._tabbed_renderer["channelHandleText"]["runs"]])
    @property
    def rss_url(self)->str:
        return self._metadata_renderer["rssUrl"]
    @property
    def conversion_url(self)->Optional[str]:
        return self._metadata_renderer["channelConversionUrl"] if "channelConversionUrl" in self._metadata_renderer else None
    @property
    def _about_continuation(self)->str:
        return self._tabbed_renderer["headerLinks"]["channelHeaderLinksViewModel"]["more"]["commandRuns"][0]["onTap"]["innertubeCommand"][
            "showEngagementPanelEndpoint"]["engagementPanel"]["engagementPanelSectionListRenderer"]["content"]["sectionListRenderer"][
            "contents"][0]["itemSectionRenderer"]["contents"][0]["continuationItemRenderer"]["continuationEndpoint"]["continuationCommand"]["token"]
    @property
    def tab_content_about(self)->dict:
        return innertube.default_obj.browse(browse_id=None,continuation=self._about_continuation)
    @cached_property
    def tab_content_about_metadata(self)->dict:
        return self.tab_content_about["onResponseReceivedEndpoints"][0]["appendContinuationItemsAction"]["continuationItems"][0][
            "aboutChannelRenderer"]["metadata"]["aboutChannelViewModel"]
    @property
    def country(self)->str:
        return self.tab_content_about_metadata["country"]
    @property
    def view_count(self)->str:
        return self.tab_content_about_metadata["viewCountText"]
    @property
    def joined_date(self)->str:
        return self.tab_content_about_metadata["joinedDateText"]["content"]
    @property
    def links(self)->List[Link]:
        return [Link(raw_link["channelExternalLinkViewModel"]) for raw_link in self.tab_content_about_metadata["links"]]

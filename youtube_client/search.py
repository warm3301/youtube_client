from . import innertube
from typing import Optional,Union,List,Iterable
from functools import cached_property
from .chapter import Chapter
from .query import get_thumbnails_from_raw,ThumbnailQuery
from abc import abstractmethod
import collections
from . import extract
from abc import abstractmethod,ABC
from . chapter import ChapterBase
from .query import get_thumbnails_from_raw,ThumbnailQuery
from typing import Optional,Iterable
from .video import Video
from .playlist import Playlist
from .channel import Channel
from .live import Live
from .short import Short
#TODO lives result search
class ResultObject(ABC):
    def __init__(self,raw:str):
        self.raw = raw
    @property
    def url(self)->str:
        return "https:/youtube.com"+self.raw["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
    @property
    def description_snippet(self)->str:
        try:
            return "".join(x["text"] for x in self.raw["detailedMetadataSnippets"][0]["snippetText"]["runs"])
        except KeyError:
            return "".join(x["text"] for x in self.raw["descriptionSnippet"]["snippetText"]["runs"])
    @abstractmethod
    def get_full_obj(self):NotImplemented
class PlayableBaseObject(ResultObject):
    def __init__(self,raw:str):
        super().__init__(raw)
    @abstractmethod
    def get_full_obj(self):
        v = Video(url=self.url)
        v.title = self.title
    @property
    def title(self)->str:
        try:
            try:
                return " ".join([x["text"] for x in self.raw["title"]["runs"]])
            except KeyError:
                return self.raw["title"]["simpleText"]
        except KeyError:
            return self.raw["headline"]["simpleText"]
    @property
    def id(self)->str:
        try:
            return self.raw["videoId"]
        except KeyError:
            return extract.video_id(self.raw)
class SearchChapter(ChapterBase):
    def __init__(self,raw):
        self.raw = raw
        super().__init__()
        self.title = " ".join(x["text"] for x in self.raw["title"]["runs"])
        self.time_description = self.raw["timeDescription"]["runs"][0]["text"]
        self.thumbnails = get_thumbnails_from_raw(self.raw["thumbnail"]["thumbnails"])
        self.url = "https://youtube.com" + self.raw["onTap"]["commandMetadata"]["webCommandMetadata"]["url"]

class VideoResult(PlayableBaseObject):
    def __init__(self,raw:str):
        super().__init__(raw)
    @property
    def thumbnails(self)->ThumbnailQuery:
        return get_thumbnails_from_raw(self.raw["thumbnail"]["thumbnails"])
    @property
    def author_name(self)->str:
        return self.raw["longBylineText"]["runs"][0]["text"]
    @property
    def author_id(self)->str:
        return self.raw["longBylineText"]["runs"][0]["navigationEndpoint"]["browseEndpoint"]["browseId"]
    @property
    def author_url(self)->str:
        return "https:/youtube.com"+self.raw["longBylineText"]["runs"][0]["navigationEndpoint"]["browseEndpoint"]["browseId"]["canonicalBaseUrl"]
    @property
    def published_time_text(self)->str:
        return self.raw["publishedTimeText"]["simpleText"]
    @property
    def lenght(self)->str:
        return self.raw["lengthText"]["simpleText"]
    @property
    def view_count(self)->str:
        return self.raw["viewCountText"]["simpleText"]
    #raw["badges"][0]["metadataBadgeRenderer"]
    @property
    def owner_is_vereficated(self)->bool:
        try:
            return  self.raw["ownerBadges"][0]["metadataBadgeRenderer"]["style"] in ["BADGE_STYLE_TYPE_VERIFIED","BADGE_STYLE_TYPE_VERIFIED_ARTIST"]
        except KeyError:
            return False
    @property
    def owner_thumbnais(self)->ThumbnailQuery:
        return get_thumbnails_from_raw(self.raw["channelThumbnailSupportedRenderers"]["channelThumbnailWithLinkRenderer"]["thumbnail"]["thumbnails"])
    @property
    def chapters(self)->Optional[Iterable[SearchChapter]]:
        try:
            for x in self.raw["expandableMetadata"]["expandableMetadataRenderer"]["expandedContent"]["horizontalCardListRenderer"]["cards"]:
                yield SearchChapter(raw=x["macroMarkersListItemRenderer"])
        except KeyError:
            return None

    def __repr__(self)->str:
        return f"<VideoSearchResult {self.id} title=\"{self.title[:100]}\"/>"
    def get_full_obj(self)->Video:
        v = Video(url=self.url)
        v.title = self.title
        return v
class ShortResult(PlayableBaseObject):
    def __init__(self,raw:str):
        super().__init__(raw)
    def __repr__(self)->str:
        return f"<ShortSearchResult {self.id=} title=\"{self.title[:100]}\"/>"
    def get_full_obj(self)->Short:
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
    def video_count(self)->int:
        return int(self.raw["videoCount"])
    @property
    def thumbnails(self)->ThumbnailQuery:
        return get_thumbnails_from_raw(x["thumbnails"] for x in self.raw["thumbnails"])
    @property
    def thumbnail_other(self):#TODO rename and see
        return get_thumbnails_from_raw(self.raw["thumbnailRenderer"]["playlistVideoThumbnailRenderer"]["thumbnail"]["thumbnails"])
    @property
    def videos(self)->Iterable[PlayableBaseObject]:
        for x in self.raw["videos"]:
            yield PlayableBaseObject(x["childVideoRenderer"])

    def __repr__(self)->str:
        return f"<PlaylistSearchResult {self.title=}/>"
    def get_full_obj(self)->Playlist:
        pl = Playlist(url = self.url)
        return pl
class ChannelResult(ResultObject):
    def __init__(self,raw:str):
        super().__init__(raw)
    @property
    def id(self)->str:
        return self.raw["channelId"]
    @property
    def name(self)->str:
        return self.raw["title"]["simpleText"]
    @property
    def thumbnails(self)->ThumbnailQuery:
        return get_thumbnails_from_raw(self.raw["thumbnail"]["thumbnails"])
    @property
    def subsciribers_count(self)->str:
        return self.raw["videoCountText"]["simpleText"]
    @property
    def is_subscribed(self)->bool:
        return self.raw["subscriptionButton"]["subscribed"]
    @property
    def is_vereficated(self)->bool:
        try:
            return self.raw["ownerBadges"][0]["metadataBadgeRenderer"]["style"] in ["BADGE_STYLE_TYPE_VERIFIED","BADGE_STYLE_TYPE_VERIFIED_ARTIST"]
        except KeyError:
            return False
    
    def __repr__(self)->str:
        return f"<ChannelSearchResult {self.name=}/>"
    def get_full_obj(self)->Channel:
        c = Channel(url=self.url)
        return c
class DidYouMean:
    def __init__(self,raw):
        self.raw = raw
    @property
    def correct_arr(self)->[(str,bool)]:
        return [(x["text"],x.get("italics",False)) for x in self.raw["correctedQuery"]["runs"]]
    @property
    def corrected_query(self)->str:
        return self.raw["correctedQueryEndpoint"]["searchEndpoint"]["query"]
    @property
    def corrected_words(self)->str:
        return "".join([x[0] for x in self.correct_arr if x[1]])
    @property
    def initial_query(self)->str:
        return self.raw["originalQuery"]["simpleText"]
    def __repr__(self)->str:
        return f"<DidYouMean {self.initial_query=} {self.corrected_query=}>"
def get_obj(x_raw)->Union[DidYouMean,VideoResult,PlaylistResult,ChannelResult,List[ShortResult],List[VideoResult]]:
    obj = None
    if "videoRenderer" in x_raw:
        r = x_raw["videoRenderer"]
        obj = VideoResult(r)
    elif "reelShelfRenderer" in x_raw:# shorts list
        obj = []
        for short in x_raw["reelShelfRenderer"]["items"]:
            r = short["reelItemRenderer"]
            so = ShortResult(r)#url=f"https://youtube.com/shorts/{r['videoId']}"
            obj.append(so)
    elif "radioRenderer" in x_raw:
        r = x_raw["radioRenderer"]
        obj = PlaylistResult(r)#url=f"https://youtube.com/watch?list={r['playlistId']}"
        #obj.title = r["title"]["simpleText"]
    elif "channelRenderer" in x_raw:
        r = x_raw["channelRenderer"]
        obj = ChannelResult(r)#url="https://youtube.com"+r["navigationEndpoint"]["browseEndpoint"]["canonicalBaseUrl"]
        #obj.name = r["title"]["simpleText"]
    elif "shelfRenderer" in x_raw: # people also watched
        r = x_raw["shelfRenderer"]
        obj = []
        for video_raw in r["content"]["verticalListRenderer"]["items"]:
            if "videoRenderer" in video_raw:
                r = video_raw["videoRenderer"]
                video = VideoResult(r)#r["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"] #TODO get url
                # video.title = " ".join([x["text"] for x in r["title"]["runs"]])
                # video.id =r["videoId"]
                obj.append(video)
            else:
                obj.append(None)
    elif "playlistRenderer" in x_raw:
        r = x_raw["playlistRenderer"]
        obj = PlaylistResult(r)#url="https://youtube.com"+r["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
    elif "backgroundPromoRenderer" in x_raw and x_raw["backgroundPromoRenderer"]["icon"]["iconType"] == "EMPTY_SEARCH":
        raise Exception("Empty search")
    elif "didYouMeanRenderer" in x_raw:#TODO move up
        obj = DidYouMean(x_raw["didYouMeanRenderer"])
    elif "showingResultsForRenderer" in x_raw:
        obj = DidYouMean(x_raw["showingResultsForRenderer"])
    else:
        return None
        #raise Exception(f"Not expected \"{list(x_raw.keys())[0]}\"")
    return obj
    
class SearchResponceNext:
    def __init__(self,raw,it_obj,continuation:str=None):
        self._it = it_obj
        self.raw = raw
        self._continuation = continuation
    @property
    def estimated_results(self)->int:
        return self.raw.get("estimatedResults")
    @property
    def _raw_content(self)->Iterable[dict]:
        return self.raw["onResponseReceivedCommands"][0]["appendContinuationItemsAction"]["continuationItems"][0]["itemSectionRenderer"]["contents"]
    @property
    def content(self)->Iterable[Union[DidYouMean,VideoResult,PlaylistResult,ChannelResult,List[ShortResult],List[VideoResult]]]:
        for x in self._raw_content:
            yield get_obj(x)
    def next(self)->"SearchResponceNext":
        if self._continuation == None:
            raise StopIteration()
        res = self._it.search(continuation=self._continuation)
        continuation:str = None
        try:
            continuation = res["onResponseReceivedCommands"][0]["appendContinuationItemsAction"][
                "continuationItems"][-1]["continuationItemRenderer"]["continuationEndpoint"]["continuationCommand"]["token"]
        except KeyError:
            pass
        except IndexError:
            pass
        return SearchResponceNext(res,self._it,continuation=continuation)
class SearchResponce(SearchResponceNext):
    def __init__(self,raw,it_obj):
        self._continuation = None
        self._raw_resp = raw["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]["sectionListRenderer"]["contents"]
        try:
            self._continuation = self._raw_resp[-1]["continuationItemRenderer"]["continuationEndpoint"]["continuationCommand"]["token"]
        except KeyError:
            pass
        except IndexError:
            pass
        super().__init__(raw,it_obj,self._continuation)

    @property
    def refinements(self)->[str]:
        return self.raw.get("refinements")
    
    @property
    def _raw_content(self)->Iterable[dict]:
        for x_raw in self._raw_resp[0]["itemSectionRenderer"]["contents"]:
            yield x_raw


class Search(collections.abc.Iterable):
    def __init__(self,query:str):
        self.query = query
        self._it = innertube.default_obj
        self._val = None
    def search(self)->SearchResponce:
        return SearchResponce(self._it.search(self.query),self._it)
        
    def __iter__(self)->Iterable[Union[SearchResponceNext,SearchResponce]]:
        self._val = self.search()
        yield self._val
        while True:
            self._val = self._val.next()
            yield self._val
    def __next__(self)->Union[SearchResponceNext,SearchResponce]:
        if not self._val:
            self._val = self.search()
        self._val = self._val.next()
        return self._val
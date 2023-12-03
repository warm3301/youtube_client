from typing import List
from . import video
from . import Playlist
from . import innertube
from . base_youtube_player import BaseYoutubePlayer
from . import thumbnail
from .query import get_thumbnails_from_raw,ThumbnailQuery


class AutoplaySet:
    def __init__(self):
        self.mode:str = None
        
        self.has_previous:bool = False
        self.previous_video_id:str = None
        self.previous_video_playlist_id:str = None
        self.previous_video_index:int = None
        self.previous_video_url:str = None

        self.has_next:bool = False
        self.next_video_id:str = None
        self.next_video_playlist_id:str = None
        self.next_video_index:int = None
        self.next_video_url:str = None
    def __repr__(self)->str:
        rs = f"<Autoplayset {self.mode}"
        if self.has_previous:
            rs+= f" previous video index={self.previous_video_index} ID={self.previous_video_id}"
        if self.has_next:
            rs+=f" next video index={self.next_video_index} ID={self.next_video_id}"
        rs+="/>"
        return rs
        

class VideoPaginator():
    def __init__(self,byp:BaseYoutubePlayer):
        self.byp = byp

    @property
    def source(self):
        return self.byp
    @property#TODO if local continuation
    def current_video(self)->video.Video:
        vid_id = self.byp.initial_player["videoDetails"]["videoId"]
        vid = video.Video(id=vid_id)
        return vid


    @property
    def next_video(self)->"Paginator":
        raw_url = self.byp.initial_data["contents"]["twoColumnWatchNextResults"]["autoplay"]["autoplay"]["sets"][0]["autoplayVideo"]

        raw = self.byp.initial_data["playerOverlays"]["playerOverlayRenderer"]["autoplay"]["playerOverlayAutoplayRenderer"]
        vid_id = raw["videoId"]
        vid_url = "https://youtube.com" + raw_url["commandMetadata"]["webCommandMetadata"]["url"]
        #["nextButton"]["buttonRenderer"]["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
        
        res = video.Video(url = vid_url)
        res.title = raw["videoTitle"]["simpleText"]
        owner_name = raw["byline"]["runs"][0]["text"]
        owner_id = raw["byline"]["runs"][0]["navigationEndpoint"]["browseEndpoint"]["browseId"]
        owner_url = "https://youtube.com" + raw["byline"]["runs"][0]["navigationEndpoint"]["browseEndpoint"]["canonicalBaseUrl"]
        background = get_thumbnails_from_raw(raw["background"]["thumbnails"])
        time_len = raw["thumbnailOverlays"][0]["thumbnailOverlayTimeStatusRenderer"]["text"]["simpleText"]
        published_time_text = raw["publishedTimeText"]["simpleText"]
        webShowNewAutonavCountdown:bool = raw["webShowNewAutonavCountdown"]
        webShowBigThumbnailEndscreen:bool = raw["webShowBigThumbnailEndscreen"]
        view_count:str = raw["shortViewCountText"]
        return VideoPaginator(res)
    @property
    def next_end_screen_renderer(self) -> List[video.Video]:
        res = []
        raw = self.byp.initial_data["playerOverlays"]["playerOverlayRenderer"]["endScreen"]["watchNextEndScreenRenderer"]["results"]
        for x in raw:
            if not "endScreenVideoRenderer" in x:
                print("endScreenVideoRenderer not contains in x,"+x.keys())
                continue
            xr = x["endScreenVideoRenderer"]
            vid = video.Video(id=xr["videoId"])
            vid._title = xr["title"]["simpleText"]
            thumbnails = get_thumbnails_from_raw(xr["thumbnail"]["thumbnails"])
            owner_name = xr["shortBylineText"]["runs"][0]["text"]
            owner_id = xr["shortBylineText"]["runs"][0]["navigationEndpoint"]["browseEndpoint"]["browseId"]
            owner_url = "https://youtube.com" + xr["shortBylineText"]["runs"][0]["navigationEndpoint"]["browseEndpoint"]["canonicalBaseUrl"]
            lenght_text = xr.get("lengthText")
            if lenght_text:
                lenght_text = lenght_text["simpleText"]
            lenght_sec:int = xr.get("lengthInSeconds")
            url = "https://youtube.com" + xr["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
            view_count = xr["shortViewCountText"]["simpleText"]
            published_time = xr["publishedTimeText"]["simpleText"]
            res.append(vid)
        return res
    @property
    def second_results(self)->List[video.Video]:
        """you may also like"""
        # rawss = self.byp.initial_data["contents"]["twoColumnWatchNextResults"]["secondaryResults"][
        #     "secondaryResults"]["results"]
        # continuation = None
        # if "continuationItemRenderer" in rawss[-1]:
        #     continuation = rawss[-1]["continuationItemRenderer"]["continuationEndpoint"]["continuationCommand"]["token"]
        #     rawss = rawss[:-1]
        res = []
        raw = self.byp.initial_data["contents"]["twoColumnWatchNextResults"]["secondaryResults"]["secondaryResults"]
        continuation = None
        if "continuations" in raw:
            continuation = raw["continuations"][0]["nextContinuationData"]["continuation"]
        for x in raw["results"]:
            if not "compactVideoRenderer" in x:
                print("not contains compactVideoRenderer,",+x.keys())
                continue
            x_raw = x["compactVideoRenderer"]
            vid_id = x_raw["videoId"]
            vid_url = "https://youtube.com" + x_raw["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
            vid = video.Video(url=vid_url)
            vid._title = x_raw["title"]["simpleText"]
            thubmnails = get_thumbnails_from_raw(x_raw["thumbnail"]["thumbnails"])
            owner_name = x_raw["longBylineText"]["runs"][0]["text"]
            owner_url = x_raw["longBylineText"]["runs"][0]["navigationEndpoint"]["browseEndpoint"]["canonicalBaseUrl"]
            owner_id =  "https://youtube.com" + x_raw["longBylineText"]["runs"][0]["navigationEndpoint"]["browseEndpoint"]["browseId"]
            ownerThumbnail = get_thumbnails_from_raw(x_raw["channelThumbnail"]["thumbnails"])
            publishedTimeText = x_raw["publishedTimeText"]["simpleText"]
            viewCountText = x_raw["viewCountText"]["simpleText"]
            lengthText = x_raw["lengthText"]["simpleText"]
            channel_is_vereficated = x_raw["ownerBadges"][0][
                "metadataBadgeRenderer"]["style"] in ["BADGE_STYLE_TYPE_VERIFIED","BADGE_STYLE_TYPE_VERIFIED_ARTIST"] if "ownerBadges" in x_raw else False 
            #TODO have_owner_badges BADGE_STYLE_TYPE_VERIFIED_ARTIST   BADGE_STYLE_TYPE_VERIFIED
            res.append(vid)
        return res


    #TODO test
    # @property
    # def continuation(self)->str:#TODO test this
    #     return self.initial_data["contents"]["twoColumnWatchNextResults"][
    #         "results"]["results"]["contents"][-1]["itemSectionRenderer"][
    #             "contents"][0]["continuationItemRenderer"]["continuationEndpoint"]["continuationCommand"]["token"]
    @property
    def autoplay_sets(self) -> [AutoplaySet]:
        ap_sets = []
        for ap_set in self.byp.initial_data["contents"]["twoColumnWatchNextResults"]["autoplay"]["autoplay"]["sets"]:
            setobj = AutoplaySet()
            setobj.mode = ap_set["mode"]

            if "previousButtonVideo" in ap_set:
                setobj.has_previous = True
                setobj.previous_video_url = "https://youtube.com"+ap_set["previousButtonVideo"]["commandMetadata"]["webCommandMetadata"]["url"]
                setobj.previous_video_id:str = ap_set["previousButtonVideo"]["watchEndpoint"]["videoId"]

                setobj.previous_video_playlist_id:str = ap_set["previousButtonVideo"]["watchEndpoint"]["playlistId"] #TODO playlist id??
                setobj.previous_video_index:int = ap_set["previousButtonVideo"]["watchEndpoint"]["index"]


            if "nextButtonVideo" in ap_set:
                setobj.has_next = True
                setobj.next_video_url ="https://youtube.com"+ ap_set["nextButtonVideo"]["commandMetadata"]["webCommandMetadata"]["url"]
                setobj.next_video_id = ap_set["nextButtonVideo"]["watchEndpoint"]["videoId"]
                
                setobj.next_video_playlist_id = ap_set["nextButtonVideo"]["watchEndpoint"]["playlistId"] #TODO playlist id??
                setobj.next_video_index = ap_set["nextButtonVideo"]["watchEndpoint"]["index"]
                
            if "autoplayVideo" in ap_set:
                setobj.has_next = True
                setobj.next_video_url = "https://youtube.com"+ap_set["autoplayVideo"]["commandMetadata"]["webCommandMetadata"]["url"]
                setobj.next_video_id = ap_set["autoplayVideo"]["watchEndpoint"]["videoId"]
            ap_sets.append(setobj)
        return ap_sets


class PaginatorPlaylistResult:
    def __init__(self,raw):
        self.raw = raw
        self.playlist_id:str = raw["playlistId"]
        self.url:str = raw["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
        self.playlist_view_url:str =raw["viewPlaylistText"]["runs"][0]["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
        self.title:str = raw["title"]["simpleText"]

        self.owner_id:str = None
        self.owner_name:str = None
        self.owner_url:str = None
        self.owner_name:str =raw["longBylineText"]["runs"][0]["text"]
        self.owner_url:str = "https://youtube.com" + raw["longBylineText"]["runs"][0]["navigationEndpoint"]["browseEndpoint"]["canonicalBaseUrl"]
        self.owner_id:str = raw["longBylineText"]["runs"][0]["navigationEndpoint"]["browseEndpoint"]["browseId"]

        self.video_count:str = raw["videoCountText"]["runs"][0]["text"]
        
    @property
    def thumbnails(self)->ThumbnailQuery:
        return get_thumbnails_from_raw(self.raw["thumbnail"]["thumbnails"])
    @property
    def sidebar_thumbnais(self)->ThumbnailQuery:
        return get_thumbnails_from_raw([x["thumbnails"] for x in self.raw["sidebarThumbnails"]])
    def get_full_obj(self)->Playlist:
        return Playlist(url=self.url)
    def __repr__(self)->str:
        return f"<PaginatorPlaylistResult {self.title}/>"        

class PlaylistsPaginator:
    def __init__(self,bpo:Playlist):
        self.bpo:Playlist = bpo
    def next_playlists(self)->List[PaginatorPlaylistResult]:
        playlists = []
        continuaion = None
        try:
            continuaion = self.bpo._contents[-1]["continuationItemRenderer"]["continuationEndpoint"]["continuationCommand"]["token"]
        except KeyError: pass
        if not continuaion:
            return playlists
        res = innertube.default_obj.browse(browse_id=None,continuation=continuaion)
        try:
            for x in res["onResponseReceivedActions"][0]["appendContinuationItemsAction"]["continuationItems"][0][
                "itemSectionRenderer"]["contents"][0]["shelfRenderer"]["content"]["horizontalListRenderer"]["items"]:
                playlists.append(PaginatorPlaylistResult(x["gridPlaylistRenderer"]))
        except KeyError:pass
        return playlists
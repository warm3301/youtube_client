import os
import re
import json
import socket
import urllib
from typing import Tuple,Optional,Dict,Iterator,List

from .extract import apply_descrambler
from .streams import Stream
from .captions import Caption
from .thumbnail import Thumbnail
from .base_youtube import BaseYoutube
from . import storyboard
from . import request
from . import extract
from .exceptions import ExtractError
from . import innertube
from .query import StreamQuery,ThumbnailQuery,get_thumbnails_from_raw,CaptionQueryFirst

from functools import cached_property
from .music_metadata import MusicMetadata
_js = None
_js_url = None

class AudioTrack:
    def __init__(self,raw,streams:StreamQuery):
        self.raw = raw
        self.visibility:str = raw["visibility"]
        self.captions_state:str = raw["captionsInitialState"]
        self.id:str = raw["audioTrackId"]
        self.has_default:bool = raw["hasDefaultTrack"]
        self.streams:StreamQuery = streams.get_by_audio_track_id(self.id)
        ati = self.streams.first.audio_track_info
        self.name = ati.name
    def __repr__(self)->str:
        return f"<AudioTrack \"{self.id}\" {self.name}/>"
class BaseYoutubePlayer(BaseYoutube):
    def __init__(self,url):
        super().__init__(url)
        self._js_url:str = None
        self._js:str = None
    @cached_property
    def initial_player(self)->dict:
        return extract.get_ytplayer_config(self.html)

    @cached_property
    def time_from_url(self)->int:
        return extract.time_from_url(self.url)
    @cached_property
    def age_restricted(self) -> bool:
        return extract.is_age_restricted(self.html)
    @property
    def js_url(self)->str:
        if self._js_url:
            return self._js_url

        if self.age_restricted:
            self._js_url = extract.js_url(self.embed_html)
        else:
            self._js_url = extract.js_url(self.html)

        return self._js_url
    @property
    def js(self)->str:
        global _js
        global _js_url
        if self._js:
            return self._js

        # If the js_url doesn't match the cached url, fetch the new js and update
        #  the cache; otherwise, load the cache.
        if _js_url != self.js_url:
            self._js = request.default_obj.get(self.js_url)
            _js = self._js
            _js_url = self.js_url
        else:
            self._js = _js

        return self._js

    @cached_property
    def is_owner_viewing(self)->bool:
        return self.initial_player["videoDetails"]["isOwnerViewing"]

    @cached_property
    def title(self) -> str:
        return self.initial_player["videoDetails"]["title"]
    @cached_property
    def description(self)->str:
        return self.initial_player["videoDetails"]["shortDescription"]
    @cached_property
    def view_count(self)->str:
        return self.initial_player["microformat"]["playerMicroformatRenderer"]["viewCount"]
    @cached_property
    def lenght(self) -> int:
        """Lenght of video in seconds"""
        return int(self.initial_player["videoDetails"]["lengthSeconds"])
    @property
    def allow_rating(self)->bool:
        return self.initial_player["videoDetails"]["allowRatings"]
    @property
    def category(self)->str:
        return self.initial_player["microformat"]["playerMicroformatRenderer"]["category"]

    @property
    def keywords(self)->[str]:
        try:
            return self.initial_player["videoDetails"]["keywords"]
        except KeyError:
            return None

    @property
    def is_family_safe(self)->bool:
        return self.initial_player["microformat"]["playerMicroformatRenderer"]["isFamilySafe"]
    @property
    def available_countries(self)->[str]:
        return self.initial_player["microformat"]["playerMicroformatRenderer"]["availableCountries"]

    @property
    def is_unplugged_corpus(self)->bool:
        return self.initial_player["videoDetails"]["isUnpluggedCorpus"]
    @property
    def is_crawlable(self)->bool:
        return self.initial_player["videoDetails"]["isCrawlable"]
    @property
    def is_unlisted(self)->bool:
        return self.initial_player["microformat"]["playerMicroformatRenderer"]["isUnlisted"]
    @property
    def has_ypc_metadata(self)->bool:
        return self.initial_player["microformat"]["playerMicroformatRenderer"]["hasYpcMetadata"]
    

    @cached_property
    def owner_name(self)->str:
        return self.initial_player["videoDetails"]["author"]
    @cached_property
    def owner_url(self)->str:
        return self.initial_player["microformat"]["playerMicroformatRenderer"]["ownerProfileUrl"]
    @cached_property
    def owner_id(self)->str:
        return self.initial_player["microformat"]["playerMicroformatRenderer"]["externalChannelId"]
    


    @cached_property
    def publish_date(self)->str:
        return self.initial_player["microformat"]["playerMicroformatRenderer"]["publishDate"]
    @cached_property
    def upload_date(self)->str:
        return self.initial_player["microformat"]["playerMicroformatRenderer"]["uploadDate"]
    @cached_property
    def date_from_data(self)->str:
        return self._primary_renderer["dateText"]["simpleText"]
    @cached_property
    def relative_date_from_data(self)->str:
        try:
            return self._primary_renderer["relativeDateText"]["simpleText"]
        except:
            return None
    
    @property
    def thumbnails(self)->ThumbnailQuery:
        return get_thumbnails_from_raw(self.initial_player["videoDetails"]["thumbnail"]["thumbnails"])



    @cached_property
    def translation_languages(self)->Dict[str,str]:
        translationLanguages = {}
        cap = self.initial_player.get("captions")
        if cap == None:
            return {}
        for x in cap["playerCaptionsTracklistRenderer"]["translationLanguages"]:
            translationLanguages[x["languageCode"]] = x["languageName"]["simpleText"]
        return translationLanguages
    @property
    def has_captions(self)->bool:
        return "captions" in self.initial_player
    @cached_property
    def captions(self)->Optional[CaptionQueryFirst]:
        cap = self.initial_player.get("captions")
        captions = []
        if cap == None:
            return None
        for x in cap["playerCaptionsTracklistRenderer"]["captionTracks"]:
            captions.append(Caption(x,self.translation_languages))
        if len(captions) == 0:
            return None
        return CaptionQueryFirst(captions,self.translation_languages)
    

    
    @cached_property
    def storyboards_array(self)->[storyboard.Storyboard]:
        sb = self.initial_player["storyboards"]
        if "playerStoryboardSpecRenderer" in sb:
            sb = sb["playerStoryboardSpecRenderer"]
        elif "playerLiveStoryboardSpecRenderer" in sb:
            sb = sb["playerLiveStoryboardSpecRenderer"]
        return storyboard.get_groups(sb,int(self.lenght))
        
   

    def _get_streams_from_raw(self,raw,lenght,title)->StreamQuery:
        raw = apply_descrambler(raw)
        try:
            extract.apply_signature(raw, self.initial_player, self.js)
        except ExtractError:
            # To force an update to the js file, we clear the cache and retry
            _js = None
            _js_url = None
            extract.apply_signature(raw, self.initial_player, self.js)
        streams = []
        for x in raw:
            streams.append(Stream(x,lenght,title))
        return StreamQuery(streams)
    @property
    def _streaming_data(self)->(dict,str,str):
        vid = self.id
        if not vid:
            vid = self.initial_player["videoDetails"]["videoId"]
        val= innertube.streams_it_obj.player(vid)
        return val["streamingData"],val["videoDetails"]["lengthSeconds"],val["videoDetails"]["title"]#ANDROID #TV_EMBED
        # return self.initial_player["streamingData"]
    @cached_property
    def streams(self)->StreamQuery:
        return self._get_streams_from_raw(*self._streaming_data)


    @property
    def playback_mode(self)->str:
        return self.initial_player["playabilityStatus"]["miniplayer"]["miniplayerRenderer"]["playbackMode"]


    #TODO vsdf
    @property
    def playability_status(self)->str:#TODO for live?
        return self.initial_player["playabilityStatus"]["status"]
    @property
    def error_reason(self)->str:
        return self.initial_player['playabilityStatus'].get("reason")
    @cached_property#TODO test
    def is_private(self)->bool:
        return self.initial_player["videoDetails"]["isPrivate"]


    @property
    def playable_in_embed(self)->str:
        return self.initial_player["playabilityStatus"]["playableInEmbed"]
    @property
    def autoplay_enabled(self)->bool:
        return self.initial_data["playerOverlays"]["playerOverlayRenderer"]["autonavToggle"]["autoplaySwitchButtonRenderer"]["enabled"]

    def _find_engagement_panel(self,panel_id):
        for x in self.initial_data["engagementPanels"][1:]:
            if x["engagementPanelSectionListRenderer"]["panelIdentifier"] == panel_id:
                return x
        return None
    @cached_property
    def music_metadata(self):
        hcvr = None
        for x in self._find_engagement_panel("engagement-panel-structured-description")["engagementPanelSectionListRenderer"][
            "content"]["structuredDescriptionContentRenderer"]["items"]:
            if "horizontalCardListRenderer" in x:
                hcvr = x["horizontalCardListRenderer"]
                break
        if hcvr == None or len(hcvr["cards"])==0 or "macroMarkersListItemRenderer" in hcvr["cards"][0]:
            return None
        _ = hcvr["header"]["richListHeaderRenderer"]["title"]["simpleText"] #music? #epi
        count = None
        try:
            count = hcvr["header"]["richListHeaderRenderer"]["subtitle"]["simpleText"]
        except KeyError:
            pass
        card  =hcvr["cards"][0]["videoAttributeViewModel"]
        
        orientation = card["orientation"]
        sizingRule = card["sizingRule"]
        title = card["title"]
        subtitle = card["subtitle"]
        secondary_subtitle = card["secondarySubtitle"]["content"]
        thumbnail = Thumbnail(card["image"]["sources"][0]["url"])
        all_info = " ".join([x["text"] for x in card["overflowMenuOnTap"]["innertubeCommand"]["confirmDialogEndpoint"]["content"][
            "confirmDialogRenderer"]["dialogMessages"][0]['runs']])
        owner_id = hcvr["footerButton"]["buttonViewModel"]["onTap"]["innertubeCommand"]["browseEndpoint"]["browseId"]          
        #footerButton.buttonViewModel.titleFormatted.content 'music'
        owner_url = hcvr["footerButton"]["buttonViewModel"]["onTap"]["innertubeCommand"]["commandMetadata"]["webCommandMetadata"]["url"]
        return MusicMetadata(title,orientation,sizingRule,subtitle,secondary_subtitle,thumbnail,all_info,owner_id)
    
    @cached_property
    def other_audio_tracks_count(self)->int:
        return len(self.initial_player["captions"]["playerCaptionsTracklistRenderer"]["audioTracks"]) if self.captions else 0
    @property
    def default_track_index(self)->int:
        cap = self.initial_player.get("captions")
        if cap == None:
            return None
        return cap["playerCaptionsTracklistRenderer"]["defaultAudioTrackIndex"]
    @property
    def default_track(self)->Optional[AudioTrack]:
        if self.other_audio_tracks_count < 2: return None
        return AudioTrack(self.initial_player["captions"]["playerCaptionsTracklistRenderer"]["audioTracks"][self.default_track_index],self.streams)
    @property
    def audio_tracks(self)->Optional[Iterator[List[AudioTrack]]]:
        if self.other_audio_tracks_count < 2: return None
        return (AudioTrack(x,self.streams) for x in self.initial_player["captions"]["playerCaptionsTracklistRenderer"]["audioTracks"])
    @property
    def audio_tracks_ids(self)->[str]:
        if self.other_audio_tracks_count < 2: return None
        return [x["audioTrackId"] for x in self.initial_player["captions"]["playerCaptionsTracklistRenderer"]["audioTracks"]]
    
    
    
    
    
    @property
    def was_live(self)->bool:
        return "liveBroadcastDetails" in self.initial_player["microformat"]["playerMicroformatRenderer"]
    @property
    def is_live_now(self)->bool:
        if self.was_live:
            return self.initial_player["microformat"]["playerMicroformatRenderer"].get("isLiveNow",False)
        return False

    @property
    def is_live_content(self)->bool:
        # is live? any case
        return self.initial_player["videoDetails"]["isLiveContent"]
    @property
    def is_live(self)->bool:#TODO test
        return self.initial_player["videoDetails"].get("isLive",False)

    @cached_property
    def start_live(self)->str:
        if self.was_live:
            return self.initial_player["microformat"]["playerMicroformatRenderer"].get("startTimestamp")
        return None
    @cached_property
    def end_live(self)->str:
        if self.was_live:
            return self.initial_player["microformat"]["playerMicroformatRenderer"].get("endTimestamp")
        return None
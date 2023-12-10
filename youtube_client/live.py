from dataclasses import dataclass
from typing import Iterable,List,Tuple,Any,Union,Dict
from . import request
from .video import Video
from . import innertube
from .query import get_thumbnails_from_raw,ThumbnailQuery
@dataclass
class LiveMetadata:
    title:str=None
    description:str=None
    date:str=None
    view_count:str=None
    is_live:bool=None
    def update(self, new:Dict):
        for key, value in new.items():
            if hasattr(self, key):
                setattr(self, key, value)
class LiveMetadataUpdater:
    def __init__(self,vid_id:str):
        self._vid_id:str = vid_id
        self._continuation:str = None
    def _get_updated_info_with_token(self,continuation:str=None)->(List[Dict[str,Union[str,bool]]],str):
        """in [0] list of updated options in first name in second value. in [1] continuation."""
        params = dict()
        if continuation:
            params["continuation"] = continuation
        else:
            params["video_id"] = self._vid_id
        raw = innertube.default_obj.update_metadata(**params)
        res = dict()
        for prop in raw["actions"]:
            if "updateViewershipAction" in prop:
                res["view_count"] = prop["updateViewershipAction"]["viewCount"]["videoViewCountRenderer"]["originalViewCount"]
                res["is_live"] = prop["updateViewershipAction"]["viewCount"]["videoViewCountRenderer"].get("isLive",False)
            elif "updateDateTextAction" in prop:
                res["date"] = prop["updateDateTextAction"]["dateText"]["simpleText"]
            elif "updateTitleAction" in prop:
                res["title"] = "".join(x["text"] for x in prop["updateTitleAction"]["title"]["runs"])
            elif "updateDescriptionAction" in prop:
                res["description"] = "".join(x["text"] for x in prop["updateDescriptionAction"]["description"]["runs"])
        continuation = raw["continuation"]["timedContinuationData"]["continuation"]
        return res,continuation
    def update(self,updated_data_class:LiveMetadata)->List[Dict[str,Union[str,bool]]]:
        """update UPdatedLiveMetadata"""
        res, self._continuation, *_ = self._get_updated_info_with_token(self._continuation)
        if updated_data_class:
            updated_data_class.update(res)
        return res

class LiveChatMessage:
    def __init__(self,raw):
        self.raw = raw
    @property
    def id(self)->str:
        return self.raw["id"]
    @property
    def timestep_usec(self)->str:
        return self.raw["timestampUsec"]
    @property
    def message(self)->str:
        try:
            return "".join(x["text"] if "text" in x else x["emoji"]["emojiId"] for x in self.raw["message"]["runs"])
        except KeyError:
            return self.raw["message"]
    @property
    def author_name(self)->str:
        return self.raw["authorName"]["simpleText"]
    @property
    def author_id(self)->str:
        return self.raw["authorExternalChannelId"]
    @property
    def thumbnails(self)->ThumbnailQuery:
        return get_thumbnails_from_raw(self.raw["authorPhoto"]["thumbnails"])
    def __repr__(self)->str:
        return f"<LiveChatMessage \"{self.message}\" />"
class LiveChatResponce:
    def __init__(self,raw):
        self.raw =raw 
        self._continuation_token:str = raw["continuationContents"]["liveChatContinuation"]["continuations"][0]["invalidationContinuationData"][
            "continuation"]
    @property
    def messages(self)->List[LiveChatMessage]:
        res = []
        actions = self.raw["continuationContents"]["liveChatContinuation"]
        if not "actions" in actions:
            return res
        actions = actions["actions"]
        for message_raw in actions:
            if "addChatItemAction" in message_raw:
                message_raw = message_raw["addChatItemAction"]["item"]
                if "liveChatTextMessageRenderer" in message_raw:
                    message_raw = message_raw["liveChatTextMessageRenderer"] #liveChatViewerEngagementMessageRenderer
                    res.append(LiveChatMessage(message_raw))
        return res
class LiveChat:
    def __init__(self,continuation:str):
        self._continuation = continuation
    def get_responce(self)->LiveChatResponce:
        res = LiveChatResponce(innertube.default_obj.live_chat(self._continuation))
        import json
        with open("jsons/live_chat_continuation.json","w") as file:
            file.write(json.dumps(res.raw))
        self._continuation = res._continuation_token
        return res
class Live(Video):
    def __init__(self,url:str=None,id:str=None):
        """
        Args:
            id (str, optional): id of video. Defaults to None.
            url (str, optional): url of video. Defaults to None.

        Raises:
            Exception: Exception, when id and url is None
        """
        super().__init__(id=id,url=url)
    @property
    def broadcast_id(self)->str:
        return self.initial_player["playabilityStatus"]["liveStreamability"]["liveStreamabilityRenderer"]["broadcastId"]
    @property
    def poll_delay_ms(self)->str:
        return self.initial_player["playabilityStatus"]["liveStreamability"]["liveStreamabilityRenderer"]["pollDelayMs"]
    @property
    def dash_manifest_url(self)->str:
        return self._streaming_data[0]["dashManifestUrl"]
    @property
    def hls_manifest_url(self)->str:
        return self._streaming_data[0]["hlsManifestUrl"]
    @property
    def dash_manifest(self)->str:
        """xml"""
        return request.default_obj.get(self.dash_manifest_url)
    @property
    def hls_manifest(self)->str:
        return request.default_obj.get(self.hls_manifest_url)
    @property
    def is_live_dvr_enabled(self)->bool:
        return self.initial_player["videoDetails"]["isLiveDvrEnabled"]
    @property
    def live_chunk_readahead(self)->int:
        return self.initial_player["videoDetails"]["liveChunkReadahead"]
    @property
    def is_low_latency_live(self)->bool:
        return self.initial_player["videoDetails"]["isLowLatencyLiveStream"]
    @property
    def latency_class(self)->str:
        return self.initial_player["videoDetails"]["latencyClass"]
    @property
    def is_live_content(self)->bool:
        return self.initial_player["videoDetails"]["isLiveContent"]
    @property
    def is_live(self)->bool:
        return self.initial_player["videoDetails"]["isLive"]

    @property
    def live_now(self)->bool:
        if not self.was_live:
            return False 
        return self.initial_player["microformat"]["playerMicroformatRenderer"]["liveBroadcastDetails"]["isLiveNow"]
    @property
    def live_start_timestamp(self)->str:
        return self.initial_player["microformat"]["playerMicroformatRenderer"]["liveBroadcastDetails"]["startTimestamp"]
    @property
    def live_end_timestamp(self)->str:
        return self.initial_player["microformat"]["playerMicroformatRenderer"]["liveBroadcastDetails"]["startTimestamp"]
    def _current_live_chat_contnuation(self)->str:
        return self.initial_data["contents"]["twoColumnWatchNextResults"]["conversationBar"]["liveChatRenderer"][
            "continuations"][0]["reloadContinuationData"]["continuation"]
    def _get_live_chat_continuation(self,index=0)->str:
        """index=0 - top chat
        index=1 - live chat"""
        return self.initial_data["contents"]["twoColumnWatchNextResults"]["conversationBar"]["liveChatRenderer"][
            "header"]["liveChatHeaderRenderer"]["viewSelector"]["sortFilterSubMenuRenderer"]["subMenuItems"][index][
            "continuation"]["reloadContinuationData"]["continuation"]
    
    @property
    def metadata_updater(self)->LiveMetadataUpdater:
        return LiveMetadataUpdater(self.id)
    def get_live_chat(self,index=0)->LiveChat:
        """index=0 - top chat
        index=1 - live chat"""
        return LiveChat(self._get_live_chat_continuation(0))
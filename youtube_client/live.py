from . import request
from .video import Video

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
    
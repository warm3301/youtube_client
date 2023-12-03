from . import extract
from .query import get_thumbnails_from_raw,ThumbnailQuery
class EndscreenPanel:
    def __init__(self,raw):
        self.raw = raw
        self.id:str = raw["id"]
        self.type:str = raw["style"]

        
        self.start_ms:str = raw["startMs"]
        self.end_ms:str = raw["endMs"]
        self.left:float = raw["left"]
        self.width:float = raw["width"]
        self.top:float = raw["top"]
        self.aspect_ratio:float = raw.get("aspectRatio")


        self.title:str =raw["title"]["simpleText"]
        self.thumbnails:ThumbnailQuery = get_thumbnails_from_raw(raw["image"]["thumbnails"])
        self.metadata:str = raw["metadata"]["simpleText"]
        self.url:str = raw["endpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
        if self.type != "WEBSITE":
            self.url:str = "https://youtube.com" + self.url
        else:
            self.url = extract.decode_url(self.url)
    def __repr__(self)->str:
        return f"<EndscreenPanel type={self.type} \"{self.title}\"/>"
class EndscreenPanel_Video(EndscreenPanel):
    def __init__(self,raw):
        super().__init__(raw)
        self.view_count:str = self.metadata
        self.video_id:str = raw["endpoint"]["watchEndpoint"]["videoId"]
        self.lenght:str = raw["thumbnailOverlays"][0]["thumbnailOverlayTimeStatusRenderer"]["text"]["simpleText"]
class EndscreenPanel_Channel(EndscreenPanel):
    def __init__(self,raw):
        super().__init__(raw)
        self.channel_description:str = self.metadata
        self.is_subscribed:bool = raw.get("isSubscribe")#TODO witout hovercardButton in jsons
        # sub_raw = raw["hovercardButton"]["subscribeButtonRenderer"]
        # self.subscribe_button_is_enable:bool = sub_raw.get("enabled")
        # self.subscribe_type:str = sub_raw.get("type")
        # self.channel_id:str = sub_raw.get("channelId")
        # self.show_preferences:bool = sub_raw.get("showPreferences")
        
class EndscreenPanel_Website(EndscreenPanel):
    def __init__(self,raw):
        super().__init__(raw)
        self.domain:str = self.metadata
class Endscreen:
    def __init__(self,raw):
        self.raw = raw
    def start_endscreen_ms(self)->str:
        return self.raw["startMs"]
    def get_panels(self)->[EndscreenPanel]:
        for x in (x["endscreenElementRenderer"] for x in self.raw["elements"]):
            pt = x["style"]
            if pt == "WEBSITE": yield EndscreenPanel_Website(x)
            elif pt == "VIDEO": yield EndscreenPanel_Video(x)
            elif pt == "CHANNEL": yield EndscreenPanel_Channel(x)
            else: yield EndscreenPanel(x)
    def __repr__(self)->str:
        return f"<Enscreen {list(self.get_panels())}/>"

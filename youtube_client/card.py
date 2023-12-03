from .query import ThumbnailQuery,get_thumbnails_from_raw
class Card:
    def __init__(self,raw,raw_ep):
        self.raw = raw
        self.raw_ep = raw_ep
        self.cue_ranges_len:int = len(raw["cueRanges"])#TODO for test
        self.start_min_ms:str = raw["cueRanges"][0]["startCardActiveMs"]
        self.start_max_delay_ms:str = raw["cueRanges"][0]["endCardActiveMs"]
        self.duration:str = raw["cueRanges"][0]["teaserDurationMs"]
        teaser = raw["teaser"]["simpleCardTeaserRenderer"]
        self.message:str = teaser["message"]["simpleText"]


        self.thumbnails:ThumbnailQuery = get_thumbnails_from_raw(raw_ep["thumbnail"]["thumbnails"])
        self.author_text:str = raw_ep["shortBylineText"]["simpleText"]
        self.thumbnail_width:int = raw_ep["thumbnailWidth"]
        self.aspect_ratio:float =raw_ep["aspectRatio"]
        self.title:str = raw_ep["title"]["simpleText"]
        self.video_id:str = raw_ep["navigationEndpoint"]["watchEndpoint"]["videoId"] #TODO channel card
        self.url:str = "https://youtube.com"+raw_ep["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
    def __repr__(self)->str:
        return f"<Card {self.message} {self.author_text}/>"

class Card_Video(Card):
    def __init__(self,raw,raw_ep):
        super().__init__(raw,raw_ep)
        self.metadata:str = raw_ep["metadataDetails"]["simpleText"]
        self.lenght:str = raw_ep["lengthText"]["simpleText"]
        self.is_live:bool = raw_ep["isLiveVideo"]

class Card_Playlist(Card):
    def __init__(self,raw,raw_ep):
        super().__init__(raw,raw_ep)
        # self.channel_avatar:Optional[Thumbnail] =  get_thumbnails_from_raw(raw["teaser"]["channelAvatar"]["thumbnails"]).first
        self.playlist_id:str = raw_ep["navigationEndpoint"]["watchEndpoint"]["playlistId"]
        self.video_count:str = raw_ep["videoCountShortText"]["simpleText"]
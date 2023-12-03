from typing import Union,Optional
from .base_youtube import BaseYoutube
from . import innertube
from .comments import CommentGetter
from .query import get_thumbnails_from_raw,ThumbnailQuery
class PoolAttachment:
    def __init__(self,raw,poll_status):
        self.raw = raw
        self.poll_status = poll_status
        self.choices = ["".join([y["text"] for y in x["text"]["runs"]]) for x in self.raw["choices"]]
        self.total_votes = self.raw["totalVotes"]["simpleText"]
        self.type = self.raw["type"]
    def __repr__(self)->str:
        return f"<PoolPostAttachment {self.choices=}/>"
class VideoAttachment:
    def __init__(self,raw):
        self.raw = raw
        self.video_id:str = raw["videoId"]
        self.url:str = "https://youtube.com" + raw["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
        self.title:str = "".join([x["text"] for x in raw["title"]["runs"]])
        self.description_snippet:str = "".join([x["text"] for x in raw["descriptionSnippet"]["runs"]]) if "descriptionSnippet" in raw else None
        #.ownerText.runs.0...
        self.owner_name:str = raw["longBylineText"]["runs"][0]["text"]
        self.owner_url:str = "https//youtube.com" + raw["longBylineText"]["runs"][0]["navigationEndpoint"]["browseEndpoint"]["canonicalBaseUrl"]
        self.owner_id:str = "https//youtube.com" + raw["longBylineText"]["runs"][0]["navigationEndpoint"]["browseEndpoint"]["browseId"]
        self.owner_is_vereficated:bool = raw["ownerBadges"][0][
            "metadataBadgeRenderer"]["style"] in ["BADGE_STYLE_TYPE_VERIFIED","BADGE_STYLE_TYPE_VERIFIED_ARTIST"] if "ownerBadges" in raw and len(raw["ownerBadges"])!=0 else False
        self.published_time:str = raw["publishedTimeText"]["simpleText"]
        self.lenght:str = raw["lengthText"]["simpleText"]
        self.view_count:str = raw["viewCountText"]["simpleText"]
    @property
    def thumbnails(self)->ThumbnailQuery:
        return get_thumbnails_from_raw(self.raw["thumbnail"]["thumbnails"])
    @property
    def owner_thumbnails(self)->ThumbnailQuery:
        return get_thumbnails_from_raw(self.raw["channelThumbnailSupportedRenderers"]["channelThumbnailWithLinkRenderer"]["thumbnail"]["thumbnails"])
        
    def __repr__(self)->str:
        return f"<VideoPostAttachment {self.video_id} {self.title=}/>"
class PostThread(BaseYoutube):
    @property
    def attachment(self) ->Optional[Union[VideoAttachment,PoolAttachment]]:
        if not "backstageAttachment" in self.post_raw:
            return None
        at = self.post_raw["backstageAttachment"]
        if "backstageImageRenderer" in at:
            return get_thumbnails_from_raw(at["backstageImageRenderer"]["image"]["thumbnails"])
        elif "videoRenderer" in at:
            return VideoAttachment(at["videoRenderer"])
        elif "pollRenderer" in at:
            return PoolAttachment(at["pollRenderer"],self.post_raw["pollStatus"])
        else:
            NotImplemented
        return None
    def __init__(self,raw):
        self.post_raw = raw
        #TODO from url
        #contents.twoColumnBrowseResultsRenderer.tabs.0.tabRenderer.content.sectionListRenderer.contents.0.itemSectionRenderer.contents.0.backstagePostThreadRenderer
        #contents.twoColumnBrowseResultsRenderer.tabs.0.tabRenderer.content.sectionListRenderer.contents.1.itemSectionRenderer.contents.0.
        #continuationItemRenderer.continuationEndpoint.continuationCommand.token

        self.id:str = raw["postId"]
        self.content:str = " ".join([x["text"] for x in (raw["contentText"]["runs"] if "runs" in raw["contentText"] else raw["contentText"]) ])
        self.author_name:str = "".join([x["text"] for x in raw["authorText"]['runs']])
        self.author_id:str = raw["authorEndpoint"]["browseEndpoint"]["browseId"]
        self.author_url:str = "https://youtube.com"+raw["authorEndpoint"]["browseEndpoint"]["canonicalBaseUrl"]
        self.author_thumbnails:ThumbnailQuery = get_thumbnails_from_raw(raw["authorThumbnail"]["thumbnails"])
        self.vote_status:str = raw["voteStatus"]
        self.published_time:str = raw["publishedTimeText"]["runs"][0]["text"]
        self.vote_count:str = raw["voteCount"]["simpleText"]
        self.surface:str = raw["surface"]

        blinfo = raw["actionButtons"]["commentActionButtonsRenderer"][
            "likeButton"]["toggleButtonRenderer"]
        self.likes_count:str = blinfo["accessibility"]["label"]
        self.like_is_toggled:bool = blinfo["isToggled"]
        self.like_is_disabled:bool = blinfo["isDisabled"]
        bdinfo = raw["actionButtons"]["commentActionButtonsRenderer"][
            "dislikeButton"]["toggleButtonRenderer"]
        self.dislike_is_toggled:bool = bdinfo["isToggled"]
        self.dislike_is_disabled:bool = bdinfo["isDisabled"]
        brinfo = raw["actionButtons"]["commentActionButtonsRenderer"][
            "replyButton"]["buttonRenderer"]
        self.replies_count:str =  brinfo["text"]["simpleText"] #text.accessibility.accessibilityData.label
    
        super().__init__(f"https://youtube.com/post/{self.id}")
    def get_comments_getter(self):
        return CommentGetter(self.initial_data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][0][
            "tabRenderer"]["content"]["sectionListRenderer"]["contents"][1]["itemSectionRenderer"][
                "contents"][0]["continuationItemRenderer"]["continuationEndpoint"]["continuationCommand"]["token"],browse=True)
    def __repr__(self)->str:
        return f"<Post {self.published_time} content=\"{self.content[:125]}...\"/>"
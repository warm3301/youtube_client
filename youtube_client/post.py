from typing import Union,Optional,List
from functools import cached_property
from .base_youtube import BaseYoutube
from . import innertube
from . import extract
from .comments import CommentGetter
from .query import get_thumbnails_from_raw,ThumbnailQuery
def get_post_url(id:str)->str:
    return f"https://www.youtube.com/post/{id}"
class PoolAttachmentChoice:
    def __init__(self,raw):
        self.raw = raw
    @property
    def content(self)->str:
        return " ".join(x["text"] for x in self.raw["text"]["runs"])
    @property
    def image(self)->Optional[ThumbnailQuery]:
        return get_thumbnails_from_raw(self.raw["image"]["thumbnails"]) if "image" in self.raw else None
    def __repr__(self)->str:
        return f"<PoolAttachmentChoice \"{self.content}\"/>"
class PoolAttachment:
    def __init__(self,raw,poll_status):
        self.raw = raw
        self.poll_status:str = poll_status
        self.choices:List[PoolAttachmentChoice] = [PoolAttachmentChoice(x) for x in self.raw["choices"]]
        self.total_votes:str = self.raw["totalVotes"]["simpleText"]
        self.type:str = self.raw["type"]
    def __repr__(self)->str:
        return f"<PoolPostAttachment {self.total_votes} {self.choices=}/>"
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
    def __init__(self,url:str=None,id:str=None,raw:dict=None):
        if url == None and id and raw ==None:
            raise Exception("url and id is None")
        self._post_raw = raw
        #TODO from url
        #contents.twoColumnBrowseResultsRenderer.tabs.0.tabRenderer.content.sectionListRenderer.contents.0.itemSectionRenderer.contents.0.backstagePostThreadRenderer
        #contents.twoColumnBrowseResultsRenderer.tabs.0.tabRenderer.content.sectionListRenderer.contents.1.itemSectionRenderer.contents.0.
        #continuationItemRenderer.continuationEndpoint.continuationCommand.token

        self.id:str = raw["postId"] if raw else extract.post_id(url) if url else id
        self.url:str = get_post_url(self.id)
        super().__init__(get_post_url(self.id))
    @property
    def raw(self)->dict:
        if self._post_raw:
            return self._post_raw
        self._post_raw = self.initial_data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][0][
            "tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"][
                "contents"][0]["backstagePostThreadRenderer"]["post"]["backstagePostRenderer"]
        return self._post_raw
    @property
    def content(self)->str:
        return " ".join([x["text"] for x in (self.raw["contentText"]["runs"] if "runs" in self.raw["contentText"] else self.raw["contentText"]) ])
    @property
    def author_name(self)->str:
        return "".join([x["text"] for x in self.raw["authorText"]["runs"]])
    @property
    def author_id(self)->str:
        return self.raw["authorEndpoint"]["browseEndpoint"]["browseId"]
    @property
    def author_url(self)->str:
        return "https://youtube.com"+self.raw["authorEndpoint"]["browseEndpoint"]["canonicalBaseUrl"]
    @property
    def author_thumbnails(self)->ThumbnailQuery:
        return get_thumbnails_from_raw(self.raw["authorThumbnail"]["thumbnails"])
    @property
    def vote_status(self)->str:
        return self.raw["voteStatus"]
    @property
    def vote_count(self)->str:
        return self.raw["voteCount"]["simpleText"]
    @property
    def published_time(self)->str:
        return self.raw["publishedTimeText"]["runs"][0]["text"]
    @property
    def surface(self)->str:
        return self.raw["surface"]
    @property
    def _like_info(self)->dict:
        return self.raw["actionButtons"]["commentActionButtonsRenderer"]["likeButton"]["toggleButtonRenderer"]
    @property
    def _dislike_info(self)->dict:
        return self.raw["actionButtons"]["commentActionButtonsRenderer"]["dislikeButton"]["toggleButtonRenderer"]

    @property
    def likes_count(self)->int:
        return self._like_info["accessibility"]["label"]
    @property
    def like_is_toggled(self)->bool:
        return self._like_info["isToggled"]
    @property
    def like_is_disabled(self)->bool:
        return self._like_info["isDisabled"]
    @property
    def dislike_is_toggled(self)->bool:
        return self._dislike_info["isToggled"]
    @property
    def dislike_is_disabled(self)->bool:
        return self._dislike_info["isDisabled"]
    # @property
    # def _replies_info(self)->Optional[dict]:
    #     btns = self.raw["actionButtons"]["commentActionButtonsRenderer"]
    #     return btns["replyButton"]["buttonRenderer"] if "replyButton" in btns else None
    # @property
    # def replies_count(self)->str:
    #     return self._replies_info["text"]["simpleText"]#text.accessibility.accessibilityData.label
    @property
    def attachment(self) ->Optional[Union[VideoAttachment,PoolAttachment]]:
        if not "backstageAttachment" in self._post_raw:
            return None
        at = self._post_raw["backstageAttachment"]
        if "backstageImageRenderer" in at:
            return get_thumbnails_from_raw(at["backstageImageRenderer"]["image"]["thumbnails"])
        elif "videoRenderer" in at:
            return VideoAttachment(at["videoRenderer"])
        elif "pollRenderer" in at:
            return PoolAttachment(at["pollRenderer"],self._post_raw["pollStatus"])
        else:
            NotImplemented
        return None
    def get_comments_getter(self):
        return CommentGetter(self.initial_data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][0][
            "tabRenderer"]["content"]["sectionListRenderer"]["contents"][1]["itemSectionRenderer"][
                "contents"][0]["continuationItemRenderer"]["continuationEndpoint"]["continuationCommand"]["token"],browse=True)
    def __repr__(self)->str:
        return f"<Post {self.published_time} content=\"{self.content[:125]}...\"/>"
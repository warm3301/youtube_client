from typing import Union,Optional,List
from functools import cached_property
from .base_youtube import BaseYoutube
from . import innertube
from . import extract
from .comments import CommentGetter
from .query import get_thumbnails_from_raw,ThumbnailQuery
from abc import ABC,abstractproperty
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

class PostBase(ABC):
    def __init__(self,raw:dict,default_initial_data:dict=None):
        self.raw = raw
        self.initial_data = default_initial_data
        #TODO from url
        #contents.twoColumnBrowseResultsRenderer.tabs.0.tabRenderer.content.sectionListRenderer.contents.0.itemSectionRenderer.contents.0.backstagePostThreadRenderer
        #contents.twoColumnBrowseResultsRenderer.tabs.0.tabRenderer.content.sectionListRenderer.contents.1.itemSectionRenderer.contents.0.
        #continuationItemRenderer.continuationEndpoint.continuationCommand.token

        self.id:str = raw["postId"]
        self.url:str = get_post_url(self.id)
    def get_comments_getter(self)->CommentGetter:#TODO reuse commentGetter object
        if not self.initial_data:
            self.initial_data = BaseYoutube(self.url).initial_data
        return CommentGetter(self.initial_data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][0][
            "tabRenderer"]["content"]["sectionListRenderer"]["contents"][1]["itemSectionRenderer"][
                "contents"][0]["continuationItemRenderer"]["continuationEndpoint"]["continuationCommand"]["token"],browse=True)
    @abstractproperty
    def content(self)->str:...
    @abstractproperty
    def author_name(self)->str:...
    @abstractproperty
    def author_id(self)->str:...
    @abstractproperty
    def author_url(self)->str:...
    @property
    def published_time(self)->str:
        return self.raw["publishedTimeText"]["runs"][0]["text"]

class PostThread(PostBase):
    def __init__(self,raw:dict,comments_getter_method=None,default_initial_data:dict=None):#TODO comments_getter_method Callable ->  CommentGetter
        self._comment_getter_method=comments_getter_method
        super().__init__(raw,default_initial_data)
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
    @property
    def attachment(self) ->Optional[Union[VideoAttachment,PoolAttachment]]:
        if not "backstageAttachment" in self.raw:
            return None
        at = self.raw["backstageAttachment"]
        if "backstageImageRenderer" in at:
            return get_thumbnails_from_raw(at["backstageImageRenderer"]["image"]["thumbnails"])
        elif "videoRenderer" in at:
            return VideoAttachment(at["videoRenderer"])
        elif "pollRenderer" in at:
            return PoolAttachment(at["pollRenderer"],self.raw["pollStatus"])
        else:
            NotImplemented
        return None
    def get_comments_getter(self)->CommentGetter:
        if self._comment_getter_method:
            return self._comment_getter_method()
        return super().get_comments_getter()
    def __repr__(self)->str:
        return f"<PostThread {self.published_time} content=\"{self.content[:125]}...\"/>"

class PostShared(PostBase):
    def __init__(self,raw:dict,default_initial_data:dict=None):
        super().__init__(raw,default_initial_data)
    def __repr__(self)->str:
        return f"<PostShared \"{self.content[:50]}...\"  add to post \"{self.get_source().content[:50]}...\" />"
    @property
    def source_id(self)->str:
        return self.raw["originalPost"]["backstagePostRenderer"]["postId"]
    @property
    def source_url(self)->str:
        return get_post_url(id=self.source_id)
    def get_source(self)->PostThread:
        """
        From shared info and content
        """
        return PostThread(self.raw["originalPost"]["backstagePostRenderer"],lambda : self.get_comments_getter())
    @property
    def content(self)->str:
        return " ".join([x["text"] for x in self.raw["content"]["runs"]])
    @property
    def author_name(self)->str:
        return self.raw["displayName"]["runs"][0]["text"]
    @property
    def author_id(self)->str:
        return self.raw["displayName"]["runs"][0]["navigationEndpoint"]["browseEndpoint"]["browseId"]
    @property
    def author_url(self)->str:
        return "https://youtube.com" + self.raw["displayName"]["runs"][0]["navigationEndpoint"]["browseEndpoint"]["canonicalBaseUrl"]
    @property
    def thumbnails(self)->ThumbnailQuery:#TODO author_thumbnails?
        return get_thumbnails_from_raw(self.raw["thumbnail"]["thumbnails"])


def _get_post_from_may_shared_raw(raw:dict,default_initial_data:dict=None)->Union[PostShared,PostThread]:
    if "sharedPostRenderer" in raw:
        return PostShared(raw = raw["sharedPostRenderer"],default_initial_data=default_initial_data)
    else:
        return PostThread(raw = raw["backstagePostRenderer"],default_initial_data=default_initial_data)
def get_post_by_url(url:str)->Union[PostShared,PostThread]:
    r = BaseYoutube(url).initial_data
    post_raw = r["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][0][
            "tabRenderer"]["content"]["sectionListRenderer"]["contents"][0][
            "itemSectionRenderer"]["contents"][0]["backstagePostThreadRenderer"]["post"]
    post = _get_post_from_may_shared_raw(post_raw,r)
    return post
from typing import Optional
from .thumbnail import Thumbnail
from. query import get_thumbnails_from_raw,ThumbnailQuery
from . import innertube
new_comments = "new"
top_comments = "top"
class CommentSortType:
    def __init__(self,raw,index:int):
        self.raw = raw
        self._index:int =index

    @property
    def index(self)->int:
        return self._index
    @property
    def title(self)->str:
        return self.raw["title"]
    @property
    def is_selected(self)->bool:
        return self.raw["selected"]
    @property
    def continuation_token(self)->str:
        return self.raw["serviceEndpoint"]["continuationCommand"]["token"]#API.next
    def __repr__(self)->str:
        return f"<CommentSortType select={self.is_selected} {self.title}/>"
    @staticmethod
    def get_comment_sort_types_from_raw(raw)->"[CommentSortType]":
        res = []
        for i,x in enumerate(raw):
            res.append(CommentSortType(x,i))
        return res

class EmojiCategory:
    def __init__(self,raw):
        self._raw = raw
    def __repr__(self)->str:
        return f"<Emoji category {self.title} count={len(self._raw['emojiIds'])}/>"
    @property
    def category_id(self)->str:
        return self._raw["categoryId"]
    @property
    def title(self)->str:
        return self._raw["title"]["simpleText"]
    @property
    def category_type(self)->str:
        return self._raw["categoryType"]
    @property
    def is_lazy_load(self)->bool:
        return self._raw.get("imageLoadingLazy",False)
    @property
    def content(self) -> [str]:
        return self._raw["emojiIds"]
class EmojiInfo:
    def __init__(self,raw):
        self._raw = raw
    def __repr__(self)->str:
        return self.content
    @property
    def id(self)->str:
        return self._raw["emoji"]["emojiId"]
    @property
    def content(self)->str:
        return self._raw["text"]
    @property
    def search_terms(self)->Optional[str]:
        if "searchTerms" in self._raw["emoji"]:
            return self._raw["emoji"]["searchTerms"]
        return None
    @property
    def shortcuts(self)->[str]:
        return self._raw["emoji"]["shortcuts"]
    @property
    def images(self)->ThumbnailQuery:
        return get_thumbnails_from_raw(self._raw["emoji"]["image"]["thumbnails"])
class TeaserComment:
    def __init__(self,raw):
        self.raw=raw
        self.owner_name = raw["teaserAvatar"]["accessibility"]["accessibilityData"]["label"]
        self.content = raw["teaserContent"]["simpleText"]
        self.thumbnails = []
        for x in raw["teaserAvatar"]["thumbnails"]:
            th = Thumbnail(x["url"])
            th.width = x["width"]
            th.height = x["height"]
            self.thumbnails.append(th)
    def __repr__(self)->str:
        return f"{self.owner_name} --- {self.content}"

#TODO in actionButtons.commentActionButtonsRenderer.likeButton.toggleButtonRenderer.accessibilityData.accessibilityData.label
# equal "Like this comment along with 18 other people" with concrete number.
class Comment:
    def __init__(self,raw):
        self._raw = raw
        self._trow = None
        #TODO to getter (remove _raw and self._trow = raw)
        try:
            self._trow = raw["commentThreadRenderer"]["comment"]["commentRenderer"]
        except KeyError:
            self._trow = raw["commentRenderer"]
    
    def __repr__(self)->str:
        cont = self.content.replace("\n","  ")
        return f"<Comment {self.votes_count} {self.author_text} {self.publish_date_text}  --- {cont}/>\n"
    @property
    def id(self)->str:
        return self._trow["commentId"]
    @property
    def content(self)->str:
        return "\n".join([x["text"] for x in self._trow["contentText"]["runs"]])
    @property
    def author_text(self)->str:
        return self._trow["authorText"]["simpleText"]
    @property
    def is_liked(self) -> str:
        return self._trow["isLiked"]
        
    @property
    def author_is_channel_owner(self)->bool:
        return self._trow["authorIsChannelOwner"]
    @property
    def author_thumbnails(self)->ThumbnailQuery:
        return get_thumbnails_from_raw(self._trow["authorThumbnail"]["thumbnails"])
    @property
    def author_url(self)->str:
        return "https://youtube.com"+self._trow["authorEndpoint"]["browseEndpoint"]["canonicalBaseUrl"]
    @property
    def author_id(self)->str:
        return self._trow["authorEndpoint"]["browseEndpoint"]["browseId"]
    @property
    def url(self)->str:#TODO move out youtube base url
        return "https://youtube.com"+self._trow["publishedTimeText"]["runs"][0]["navigationEndpoint"][
            "commandMetadata"]["webCommandMetadata"]["url"]
    @property
    def publish_date_text(self)->str:
        return self._trow["publishedTimeText"]["runs"][0]["text"]
    @property
    def is_edited(self)->bool:
        if self.publish_date_text.endswith(")"): return True
        return False
    @property
    def is_disliked(self)->bool:
        return self._trow["actionButtons"]["commentActionButtonsRenderer"]["dislikeButton"]["toggleButtonRenderer"][
            "isToggled"]
    @property
    def dislike_is_disabled(self)->bool:
        return self._trow["actionButtons"]["commentActionButtonsRenderer"]["dislikeButton"]["toggleButtonRenderer"][
            "isDisabled"]
    @property
    def like_is_disabled(self)->bool:
        return self._trow["actionButtons"]["commentActionButtonsRenderer"]["likeButton"]["toggleButtonRenderer"][
            "isDisabled"]
    
    @property
    def like_count(self)->str:#TODO more concrete
        return self._trow["actionButtons"]["commentActionButtonsRenderer"]["likeButton"]["toggleButtonRenderer"][
            "accessibilityData"]["accessibilityData"]["label"]
    @property
    def votes_count(self)->str:
        val = self._trow.get("voteCount")
        if val == None:
            return 0
        return val["accessibility"]["accessibilityData"]["label"]
    @property
    def vote_status(self)->str:
        return self._trow["voteStatus"]
    @property
    def author_is_vereficated(self)->bool:
        try:
            return self._trow["authorCommentBadge"]["authorCommentBadgeRenderer"]["iconTooltip"] == "Verified"
        except:
            pass
        return False
    @property
    def content_with_emoji_info(self)->[]:#TODO anotation
        res = []
        for x in self._trow["contentText"]["runs"]:
            if "emoji" in x:
                res.append(EmojiInfo(x))
            else:
                res.append(x["text"])
        return res
    @property
    def have_creator_heart(self)->bool:
        return self._trow["actionButtons"]["commentActionButtonsRenderer"].get("creatorHeart",{}).get("creatorHeartRenderer",{}).get("isHearted",False)
        
class CommentThread(Comment):
    #TODO read more???? collapseButton
    def __init__(self,raw):
        super().__init__(raw)
        self.base_continuation = None
        try:
            self.base_continuation = raw["commentThreadRenderer"]["replies"]["commentRepliesRenderer"][
                "contents"][0]["continuationItemRenderer"]["continuationEndpoint"]["continuationCommand"][
                "token"]
        except:
            pass
            # try:
            #     self.base_continuation = raw["onResponseReceivedEndpoints"][1][
            #         "reloadContinuationItemsCommand"]["continuationItems"][-1]
    @property 

    def reply_count(self)->int:
        reply_count:int = 0
        try:
            reply_count = self._trow["replyCount"]
        except:
            pass
        return reply_count

    def get_replies_array_next(self) ->[Comment]:
        if self.base_continuation == None:
            return []
        comments = []
        it = innertube.default_obj
        it_res = it.next(continuation=self.base_continuation)
        citems = it_res["onResponseReceivedEndpoints"][0]["appendContinuationItemsAction"]
        if not "continuationItems" in citems:
            return []
        citems = citems["continuationItems"]
        continuation = citems[-1].get("continuationItemRenderer")
        if continuation:
            continuation = continuation["button"]["buttonRenderer"]["command"]["continuationCommand"]["token"]
            citems = citems[:-1]
        self.base_continuation = continuation
        for x in citems:
            comments.append(Comment(x))
        return comments
    def get_all_replies(self):
        while True:
            yield self.get_replies_array_next()
            if self.base_continuation == None:
                break
    #TODO Comment obj????
    @property
    def is_moderated_elq(self)->bool:
        #TODO move to getter
        try:
            return self._raw["commentThreadRenderer"].get("isModeratedElqComment")
        except KeyError:
            return self._raw["commentRenderer"].get("isModeratedElqComment")
    @property
    def rendering_priority(self)->str:
        #TODO move to getter
        try:
            return self._raw["commentThreadRenderer"].get("renderingPriority")
        except KeyError:
            return self._raw["commentRenderer"].get("renderingPriority")
    @property
    def is_pinned(self)->bool:
        return "pinnedCommentBadge" in self._trow
    @property
    def have_author_badge(self)->bool:
        return "authorCommentBadge" in self._trow
#TODO to iterator
class CommentsResponce:
    def __init__(self,raw,sort_change=None):
        self._raw = raw
        self._continuation_token:str = None
        self._raw_comments:[] = None
        self._comment_sort_types = None
        
        ritems = raw["onResponseReceivedEndpoints"][-1]
        items = ritems.get("continuationItems")
        if items == None:
            items = raw["onResponseReceivedEndpoints"][-1].get("reloadContinuationItemsCommand")
            if items == None:
                items = raw["onResponseReceivedEndpoints"][-1]["appendContinuationItemsAction"]["continuationItems"]
            else:
                items = items["continuationItems"]

        cir = items[-1].get("continuationItemRenderer")
        if  cir != None:
            if sort_change == None:
                self._continuation_token = cir["continuationEndpoint"]["continuationCommand"]["token"]
                self._raw_comments = items[0:-1]
            self._raw_comments = items[0:-1]
        else:
            self._raw_comments = items
        
        
        if sort_change: #TODO comment_sort_type obj #sorted_item_tokens[0]["selected"] == true
            sorted_item_token = self._raw["onResponseReceivedEndpoints"][0]["reloadContinuationItemsCommand"]["continuationItems"][0][
                "commentsHeaderRenderer"]["sortMenu"]["sortFilterSubMenuRenderer"]["subMenuItems"]
            if sort_change == new_comments:
                self._continuation_token = sorted_item_token[1]["serviceEndpoint"]["continuationCommand"]["token"]
            elif sort_change == top_comments:
                self._continuation_token =sorted_item_token[0]["serviceEndpoint"]["continuationCommand"]["token"]
            else:#TOOD timeline sponsors
                raise Exception(f"sort by {sort_change} not exist. Only 'new' and 'top'")
    @property
    def content(self)->[CommentThread]:
        comments = []
        for x in self._raw_comments:
            comments.append(CommentThread(x))
        return comments
    @property
    def _comment_renderer(self):
        res = self._raw["onResponseReceivedEndpoints"][0].get("reloadContinuationItemsCommand")
        if res:
            return res["continuationItems"][0]["commentsHeaderRenderer"]
        return None
    @property
    def sort_types(self)->[CommentSortType]:
        if self._comment_sort_types:
            return self._comment_sort_types
        renderer = self._comment_renderer
        if renderer:
            self._comment_sort_types = CommentSortType.get_comment_sort_types_from_raw(renderer["sortMenu"]["sortFilterSubMenuRenderer"]["subMenuItems"])
        return self._comment_sort_types
    @property
    def selected_sort_type(self)->CommentSortType:
        for x in self.sort_types:
            if x.is_selected:
                return x
        return None
    @property
    def comments_count(self)->str:
        renderer = self._comment_renderer
        if renderer:
            return renderer["countText"]["runs"][0]["text"]
        return None
    @property
    def _create_renderer(self):
        renderer = self._comment_renderer
        if renderer:
            return renderer["createRenderer"]["commentSimpleboxRenderer"]
        return None
    @property
    def your_avatar_thumbnails(self)->ThumbnailQuery:
        renderer = self._create_renderer
        if renderer:
            return get_thumbnails_from_raw(renderer["authorThumbnail"]["thumbnails"])
        return None
    @property
    def your_avatar_size(self)->str:
        renderer = self._create_renderer
        if renderer:
            return renderer["avatarSize"]
        return None
    @property
    def soruse_url(self)->str:#TODO if logged in does this work
        renderer = self._create_renderer
        if renderer:
            return "https://youtube.com"+renderer["prepareAccountEndpoint"]["signInEndpoint"]["nextEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
        return None
    @property
    def soruse_id(self)->str:#TODO if logged in does this work
        renderer = self._create_renderer
        if renderer:
            return renderer["prepareAccountEndpoint"]["signInEndpoint"]["nextEndpoint"]["watchEndpoint"]["videoId"]
        return None
    @property
    def emoji_categories_array(self) -> [EmojiCategory]:
        renderer = self._create_renderer
        if renderer:
            return [EmojiCategory(x["emojiPickerCategoryRenderer"]) for x in renderer["emojiPicker"]["emojiPickerRenderer"]["categories"]]
        return None
    @property
    def show_separator(self)->bool:
        return self._comment_renderer.get("showSeparator")
    @property
    def custom_emojis(self)->[EmojiInfo]:
        raw = self._comment_renderer.get("customEmojis")
        if not raw:
            return []
        return [EmojiInfo(x) for x in raw]
    @property
    def unicode_emojis_json_url(self)->str:#TODO download
        self._comment_renderer.get("unicodeEmojisUrl")
    @property
    def pinned_comment(self)->CommentThread:#TODO to query
        for x in self.content: 
            if x.is_pinned: return x
        return None
class CommentGetter:
    def __init__(self,continuation,sort_by=None,browse:bool=False):
        self.continuation =continuation
        self.browse = browse
        if browse and sort_by:
            raise Exception("browse dont support sort")
        if sort_by ==new_comments:
            self.get_comments_next(new_comments)
    def get_comments_next(self,sort_by=None)->CommentsResponce:
        if self.browse and sort_by:
            raise Exception("browse dont support sort")
        if self.continuation == None:
           return None
        response = innertube.default_obj.browse(browse_id=None,continuation=self.continuation) if self.browse else innertube.default_obj.next(continuation=self.continuation)
        cr = CommentsResponce(response,sort_by)
        self.continuation:str = cr._continuation_token
        return cr
    def get_all_comments(self):
        while True:
            if self.continuation == None:
                break
            yield self.get_comments_next()



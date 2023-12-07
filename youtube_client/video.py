from typing import Optional,List,Tuple
from functools import cached_property

from . import request
from . import extract
from .exceptions import ExtractError
from .query import ThumbnailQuery,get_thumbnails_from_raw
from .base_youtube_player import BaseYoutubePlayer
from . import storyboard
from . import comments
from .thumbnail import Thumbnail
from .streams import Stream
from .chapter import Chapter
from .endscreen_panel import Endscreen
from .card import Card,Card_Playlist,Card_Video
from .notification import NotificationCommand,NotificationState
from .music_metadata import MusicMetadata
def get_url(id:str)->str:
    return f"https://youtube.com/watch?v={id}"
def get_embed_url(id:str)->str:
    return f"https://www.youtube.com/embed/{id}"
def get_video_object_from_short(url:str)->"Video":
    return Video(id=extract.short_id(url))
class VideoCategory:
    def __init__(self,raw):
        self.raw = raw
        self.title:str = " ".join(x["text"] for x in raw["title"]["runs"]) if "runs" in raw["title"] else raw["title"]["simpleText"]
        self.url:str = "https://youtube.com" + raw["endpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
        self.browse_id:str = raw["endpoint"]["browseEndpoint"]["browseId"]
    @property
    def thumbnails(self)->ThumbnailQuery:
        return get_thumbnails_from_raw(self.raw["thumbnail"]["thumbnails"])
    def __repr__(self)->str:
        return f"<VideoCategory {self.title}/>"
class Video(BaseYoutubePlayer):
    def __init__(self,url:str=None,id:str=None):
        """
        Args:
            id (str, optional): id of video. Defaults to None.
            url (str, optional): url of video. Defaults to None.

        Raises:
            Exception: Exception, when id and url is None
        """        
        if id == None and url == None:
            raise Exception("id and url is None")
        self.id:str = None
        self.watch_url:str = None
        self.embed_url:str = None
        self.playlist_id:str = None
        if url != None:
            try:
                self.id = extract.video_id(url)
                self.embed_url = get_embed_url(self.id)
            except:
                self.id = None
            self.watch_url = url
        else:
            self.id = id
            try:
                self.watch_url = get_url(id)
                self.embed_url = get_embed_url(id)
            except:
                self.watch_url = url
        try:
            self.playlist_id = extract.playlist_id(url)
        except:
            pass
        super().__init__(url = url if url else self.watch_url)

        

    def __repr__(self)->str:
        return f'<Video id=\"{self.id}\"/>'
    def __eq__(self, o: object) -> bool:
        return type(o) == type(self) and o.watch_url == self.watch_url
    @cached_property
    def embed_html(self)->str:
        return request.default_obj.get(url=self.embed_url)

    
    @cached_property
    def _comment_data(self)->dict:
        return self.initial_data['contents']['twoColumnWatchNextResults']['results']['results']['contents'][-2][
            'itemSectionRenderer']['contents'][0]['commentsEntryPointHeaderRenderer']
    @property#.engagementPanels[-1].engagementPanelSectionListRenderer.header.engagementPanelTitleHeaderRenderer.contextualInfo.runs[0].text
    def comment_count(self)->Optional[str]:
        try:
            return self._comment_data["commentCount"]["simpleText"]
        except KeyError:
            return None
    @cached_property
    def comment_teaser(self)->Optional[comments.TeaserComment]:
        try:
            return comments.TeaserComment(self._comment_data["contentRenderer"]["commentsEntryPointTeaserRenderer"])
        except KeyError:
            return None
    @property
    def _comment_continuation(self)->str:
        return self.initial_data["contents"]["twoColumnWatchNextResults"][
                    "results"]["results"]["contents"][-1]["itemSectionRenderer"]["contents"][0][
                    "continuationItemRenderer"]["continuationEndpoint"]["continuationCommand"]["token"]
    def get_comments_getter(self,sort_by=None)->Optional[comments.CommentGetter]:
        try:
            return comments.CommentGetter(self._comment_continuation,sort_by)
        except KeyError:
            return None
    
    #TODO short doest exists _primary_renderer
    @property
    def _primary_renderer(self)->dict:
        return self.initial_data["contents"]["twoColumnWatchNextResults"][
            "results"]["results"]["contents"][0]["videoPrimaryInfoRenderer"]
    @cached_property #TODO to list
    def tags(self)->Optional[str]:
        try:
            return " ".join([x["text"] for x in self._primary_renderer["superTitleLink"]["runs"]])
        except:
            return None
    

    @property
    def _rating_buttons(self)->Optional[dict]:#TODO sometimees not work
        try:
            return self._primary_renderer["videoActions"]["menuRenderer"]["topLevelButtons"][0]["segmentedLikeDislikeButtonRenderer"]
        except KeyError:
            return None
    @property
    def _rating_buttons2(self)->dict:
        return self._primary_renderer["videoActions"]["menuRenderer"]["topLevelButtons"][0]["segmentedLikeDislikeButtonViewModel"]
    @property
    def _default_like_view_model2(self)->dict:
        return self._rating_buttons2["likeButtonViewModel"]["likeButtonViewModel"]["toggleButtonViewModel"]["toggleButtonViewModel"]["defaultButtonViewModel"]["buttonViewModel"]
    @cached_property
    def likes_count(self)->str:
        rb = self._rating_buttons
        if rb:
            return rb["likeButton"]["toggleButtonRenderer"]["toggledText"]["accessibility"][
            "accessibilityData"]["label"]
        return self._default_like_view_model2["accessibilityText"]
    @cached_property
    def like_status(self)->str:
        rb = self._rating_buttons
        if rb:
            return rb["likeButton"]["toggleButtonRenderer"]["isToggled"]
        return self._rating_buttons2["likeButtonViewModel"]["likeButtonViewModel"]["likeStatusEntity"]["likeStatus"]
    @cached_property
    def like_is_disabled(self)->str:
        rb = self._rating_buttons
        if rb:
            return rb["likeButton"]["toggleButtonRenderer"]["isDisabled"]
        return self._rating_buttons2["likeButtonViewModel"]["likeButtonViewModel"]["toggleButtonViewModel"]["toggleButtonViewModel"]["isTogglingDisabled"]

    
    # @cached_property
    # def dislike_is_togled(self)->bool:
    #     return self._rating_buttons["dislikeButton"]["toggleButtonRenderer"]["isToggled"]
    # @cached_property
    # def dislike_is_disabled(self)->bool:
    #     return self._rating_buttons["dislikeButton"]["toggleButtonRenderer"]["isDisabled"]

    @cached_property
    def money_hand(self)->bool:
        try:
            return self.initial_player["paidContentOverlay"][
                "paidContentOverlayRenderer"]["icon"]["iconType"] == "MONEY_HAND"
        except KeyError:
            return False
    

    @property
    def _chan_info(self)->dict:
        return self.initial_data["contents"]["twoColumnWatchNextResults"]["results"]["results"]["contents"][1][
            "videoSecondaryInfoRenderer"]
    @cached_property
    def owner_subscribers_count(self)->Optional[str]:
        try:
            return self._chan_info["owner"]["videoOwnerRenderer"]["subscriberCountText"]["simpleText"]
        except KeyError:
            return None
    @cached_property
    def owner_is_vereficated(self)->bool:
        try:
            return self._chan_info["owner"]["videoOwnerRenderer"][
                "badges"][0]["metadataBadgeRenderer"]["style"] in ["BADGE_STYLE_TYPE_VERIFIED","BADGE_STYLE_TYPE_VERIFIED_ARTIST"]
        except:
            return False

    @cached_property
    def owner_thumbnails(self)->ThumbnailQuery:
        return get_thumbnails_from_raw(self._chan_info["owner"]["videoOwnerRenderer"]["thumbnail"]["thumbnails"])

    @cached_property
    def is_subscribed(self)->bool:
        try:
            return self._chan_info["subscribeButton"]["subscribeButtonRenderer"]["subscribed"]
        except:
            return False
    @cached_property
    def subscribe_button_is_enabled(self)->bool:
        return self._chan_info["subscribeButton"]["subscribeButtonRenderer"]["enabled"]
    @cached_property
    def subscribe_type(self)->str:
        return self._chan_info["subscribeButton"]["subscribeButtonRenderer"]["type"]
    @cached_property
    def subscribe_show_preferences(self)->bool:
        return self._chan_info["subscribeButton"]["subscribeButtonRenderer"]["showPreferences"]
    

    @property
    def _notification(self)->dict:
        return self._chan_info["subscribeButton"]["subscribeButtonRenderer"][
            "notificationPreferenceButton"]["subscriptionNotificationToggleButtonRenderer"]
    @cached_property
    def notification_current_state(self)->int:
        return self._notification["currentStateId"]
    @cached_property
    def notification_states(self)->List[NotificationState]:
        states = []
        for x in self._notification["states"]:
            states.append(NotificationState(x))
        return states
    @cached_property
    def notification_commands(self)-> List[NotificationCommand]:
        commands = []
        for x in self._notification["command"]["commandExecutorCommand"]["commands"][0]["openPopupAction"][
            "popup"]["menuPopupRenderer"]["items"]:
            commands.append(NotificationCommand(x["menuServiceItemRenderer"]))
        return commands
    @cached_property
    def subscribed_entity_key(self)->str:
        return self._chan_info["subscribeButton"]["subscribeButtonRenderer"]["subscribedEntityKey"]




    #TODO in one func [""engagement-panel-structured-description""]["content"]["structuredDescriptionContentRenderer"]["items"][2 or ""horizontalCardListRenderer""]["cards"]
    @cached_property
    def chapters_is_generated(self)->bool:
        return self._find_engagement_panel("engagement-panel-macro-markers-auto-chapters") != None
    @cached_property
    def chapters(self)->List[Chapter]:
        #TODO interator
        chapters = []
        mkb = None
        try:
            mkb =self.initial_data["playerOverlays"]["playerOverlayRenderer"]["decoratedPlayerBarRenderer"]["decoratedPlayerBarRenderer"]["playerBar"][
                "multiMarkersPlayerBarRenderer"]
        except KeyError:
            return chapters
        generated_chapters=False
        #if description chapters is none search auto chapters
        en_panel = self._find_engagement_panel("engagement-panel-macro-markers-description-chapters")
        if en_panel == None:
            en_panel = self._find_engagement_panel("engagement-panel-macro-markers-auto-chapters")
            generated_chapters = True
        if en_panel == None:
            return chapters
        en_r = mkb["markersMap"][0]["value"]
        if "chapters" in en_r:
            en_r = en_r["chapters"]
        elif "markers" in en_r:
            en_r = mkb["markersMap"][1]["value"]["chapters"]
        else:
            NotImplemented
        for i,x in enumerate(en_r):
            cr = x["chapterRenderer"]
            chapter_panel = en_panel["engagementPanelSectionListRenderer"]["content"]["macroMarkersListRenderer"]["contents"][i+1 if generated_chapters else i]["macroMarkersListItemRenderer"]
            chapter = Chapter()#TODO Chapter.__init__()
            chapter.title = cr["title"]["simpleText"]
            chapter.start_range_ms = cr["timeRangeStartMillis"]
            chapter.time = chapter_panel["timeDescription"]["simpleText"]
            chapter.thumbnails = get_thumbnails_from_raw(cr["thumbnail"]["thumbnails"])
            chapter.time_description = chapter_panel["timeDescriptionA11yLabel"]
            chapters.append(chapter)
        return chapters
    
    
    @cached_property
    def end_screen(self) ->Optional[Endscreen]:
        es = self.initial_player.get("endscreen")
        if es == None:
            return None
        return Endscreen(es["endscreenRenderer"])
    @cached_property
    def cards(self)->List[Card]:
        cards = []
        c = self.initial_data.get("cards")
        if c == None:
            return None
        panel = self._find_engagement_panel("engagement-panel-structured-description")
        if panel == None:
            return cards
        panel = panel["engagementPanelSectionListRenderer"]["content"]["structuredDescriptionContentRenderer"]["items"]
        for x in panel:
            if "videoDescriptionInfocardsSectionRenderer" in x:
                panel = x["videoDescriptionInfocardsSectionRenderer"]["infocards"]
                break
        else:
            return cards
        
        for i,card in enumerate(x["compactInfocardRenderer"]["content"] for x in panel):
            cb = c["cardCollectionRenderer"]["cards"][i]["cardRenderer"]
            if "structuredDescriptionVideoLockupRenderer" in card:
                cards.append(Card_Video(cb,card["structuredDescriptionVideoLockupRenderer"]))
            elif "structuredDescriptionPlaylistLockupRenderer" in card:
                cards.append(Card_Playlist(cb,card["structuredDescriptionPlaylistLockupRenderer"]))
            else:
                NotImplemented
        return cards
    @property
    def creative_commons(self)->Optional[Tuple[str,str]]:
        """Return tuple info about licence and url to full information
        If licence of video is not creative commons function return None

        Returns:
            Optional[Tuple[str,str]]: first is text, second is url. 
        """        
        mrkr = self.initial_data["contents"]["twoColumnWatchNextResults"]["results"]["results"]["contents"][1]["videoSecondaryInfoRenderer"][
            "metadataRowContainer"]["metadataRowContainerRenderer"]
        if not "rows" in mrkr:
            return None
        for row in mrkr["rows"]:
            try:
                value = row["metadataRowRenderer"]["contents"][0]["runs"][0]
                return (value["text"],value["navigationEndpoint"][
                "urlEndpoint"]["url"])
            except KeyError:
                return None
    @property
    def video_category(self)->List[VideoCategory]:
        categories = []
        mrkr = self.initial_data["contents"]["twoColumnWatchNextResults"]["results"]["results"]["contents"][1]["videoSecondaryInfoRenderer"][
            "metadataRowContainer"]["metadataRowContainerRenderer"]
        if not "rows" in mrkr:
            return categories
        mrkr = mrkr["rows"][0]
        if not "richMetadataRowRenderer" in mrkr:
            return categories
        for raw in mrkr["richMetadataRowRenderer"]["contents"]:
            categories.append(VideoCategory(raw["richMetadataRenderer"]))
        return categories

    @cached_property
    def explicit_lyrics(self)->Optional[str]:
        try:
            return self.initial_data["contents"]["twoColumnWatchNextResults"]["results"]["results"]["contents"][1][
                "videoSecondaryInfoRenderer"]["metadataRowContainer"]["metadataRowContainerRenderer"][
                    "rows"][0]["metadataRowRenderer"]["contents"][0]["simpleText"] #"Explicit lyrics"
        except KeyError:
            return None
    @cached_property
    def attributed_description(self)->Optional[str]:
        try:
            return self.initial_data["contents"]["twoColumnWatchNextResults"]["results"]["results"]["contents"][1][
                "videoSecondaryInfoRenderer"]["attributedDescription"]["content"]
        except KeyError:
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
        _ = hcvr["header"]["richListHeaderRenderer"]["title"]["simpleText"]
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
        owner_id = hcvr["footerButton"]["buttonViewModel"]["onTap"]["innertubeCommand"]["browseEndpoint"]["browseId"]          
        #footerButton.buttonViewModel.titleFormatted.content 'music'
        owner_url = hcvr["footerButton"]["buttonViewModel"]["onTap"]["innertubeCommand"]["commandMetadata"]["webCommandMetadata"]["url"]

        all_info = None
        dmessages = card["overflowMenuOnTap"]["innertubeCommand"]["confirmDialogEndpoint"]["content"][
            "confirmDialogRenderer"]["dialogMessages"][0]
        if dmessages and len(dmessages)>0:
            all_info = " ".join([x["text"] for x in  dmessages['runs']])
        return MusicMetadata(title,orientation,sizingRule,subtitle,secondary_subtitle,thumbnail,all_info,owner_id)
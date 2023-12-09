from .streams import Stream
from .thumbnail import Thumbnail
from .captions import Caption
from collections.abc import Mapping, Sequence
from typing import Union,List,Callable,Optional,Tuple
from functools import cached_property
class StreamQuery(Sequence):
    def __init__(self,streams:[Stream]):
        self.items:[Stream] = streams
        self.current_index = 0
    def get_by_itag(self,itag)->Stream:
        for x in self.items:
            if int(x.itag) == int(itag):
                return x
        return None
    #TODO to public
    def _filter(self, filters: [Callable[[Stream],bool]]) -> "StreamQuery":
        fmt_streams = self.items
        for filter_lambda in filters:
            fmt_streams = filter(filter_lambda, fmt_streams)
        return StreamQuery(list(fmt_streams))
    def filter(
        self,
        fps=None,
        res=None,
        resolution=None,
        mime_type=None,
        type=None,
        subtype=None,
        file_extension=None,
        size_less_than:str=None,
        abr=None,
        bitrate=None,
        video_codec=None,
        audio_codec=None,
        only_audio=None,
        only_video=None,
        contains_audio=None,
        contains_video=None,
        progressive=None,
        adaptive=None,
        is_dash=None,
        contains_audio_track_info:bool=None,
        audio_track_id:str=None,
        custom_filter_functions=None,
    ):
    
        """Apply the given filtering criterion.

        :param fps:
            (optional) The frames per second.
        :type fps:
            int or None

        :param resolution:
            (optional) Alias to ``res``.
        :type res:
            str or None

        :param res:
            (optional) The video resolution.
        :type resolution:
            str or None

        :param mime_type:
            (optional) Two-part identifier for file formats and format contents
            composed of a "type", a "subtype".
        :type mime_type:
            str or None

        :param type:
            (optional) Type part of the ``mime_type`` (e.g.: audio, video).
        :type type:
            str or None

        :param subtype:
            (optional) Sub-type part of the ``mime_type`` (e.g.: mp4, mov).
        :type subtype:
            str or None

        :param file_extension:
            (optional) Alias to ``sub_type``.
        :type file_extension:
            str or None

        :param abr:
            (optional) Average bitrate (ABR) refers to the average amount of
            data transferred per unit of time (e.g.: 64kbps, 192kbps).
        :type abr:
            str or None

        :param bitrate:
            (optional) Alias to ``abr``.
        :type bitrate:
            str or None

        :param video_codec:
            (optional) Video compression format.
        :type video_codec:
            str or None

        :param audio_codec:
            (optional) Audio compression format.
        :type audio_codec:
            str or None

        :param bool progressive:
            Excludes adaptive streams (one file contains both audio and video
            tracks).

        :param bool adaptive:
            Excludes progressive streams (audio and video are on separate
            tracks).

        :param bool is_dash:
            Include/exclude dash streams.

        :param bool only_audio:
            Excludes streams with only video tracks.

        :param bool only_video:
            Excludes streams with only audio tracks.

        :param bool contains_video:
            Excludes streams with video tracks.

        :param bool contains_audio:
            Excludes streams with audio tracks.

        :param custom_filter_functions:
            (optional) Interface for defining complex filters without
            subclassing.
        :type custom_filter_functions:
            list or None

        """
        filters = []
        if res or resolution:
            if isinstance(res, str) or isinstance(resolution, str):
                filters.append(lambda s: s.resolution == (res or resolution))
            elif isinstance(res, list) or isinstance(resolution, list):
                filters.append(lambda s: s.resolution in (res or resolution))

        if fps:
            filters.append(lambda s: s.fps == fps)

        if mime_type:
            filters.append(lambda s: s.mime_type == mime_type)

        if type:
            filters.append(lambda s: s.type == type)

        if subtype or file_extension:
            filters.append(lambda s: s.subtype == (subtype or file_extension))

        if abr or bitrate:
            filters.append(lambda s: s.abr == (abr or bitrate))

        if video_codec:
            filters.append(lambda s: s.video_codec == video_codec)

        if audio_codec:
            filters.append(lambda s: s.audio_codec == audio_codec)

        if only_audio:
            filters.append(
                lambda s: (
                    s.only_audio
                ),
            )

        if only_video:
            filters.append(
                lambda s: (
                    s.only_video
                ),
            )
        if contains_audio:
            filters.append(
                lambda s:{
                    s.includes_audio
                }
            )
        if contains_video:
            filters.append(
                lambda s:{
                    s.includes_video
                }
            )
        if progressive:
            filters.append(lambda s: s.is_progressive)

        if adaptive:
            filters.append(lambda s: s.is_adaptive)

        if custom_filter_functions:
            filters.extend(custom_filter_functions)

        if is_dash is not None:
            filters.append(lambda s: s.is_dash == is_dash)
        
        if contains_audio_track_info is not None:
            filters.append(lambda s: s.contains_audio_track_info == contains_audio_track_info)
        if audio_track_id is not None:
            filters.append(lambda s: s.contains_audio_track_info and s.audio_track_info.id == audio_track_id)
        if size_less_than is not None:
            rfilter = None
            if isinstance(size_less_than,str):
                size_less_than = size_less_than.lower()
            if isinstance(size_less_than,int):
                rfilter = lambda s: s.filesize_approx < s.int(size_less_than[:-1])
            elif size_less_than.endswith("b"):
                rfilter = lambda s: s.filesize_approx < int(size_less_than[:-1])
            elif size_less_than.endswith("kb"):
                rfilter = lambda s: s.filesize_approx_kb < int(size_less_than[:-2])
            elif size_less_than.endswith("mb"):
                rfilter = lambda s: s.filesize_approx_mb < int(size_less_than[:-2])
            elif size_less_than.endswith("gb"):
                rfilter = lambda s: s.filesize_approx_gb < int(size_less_than[:-2])
            else:
                raise Exception(f"not understand command {rfilter}")
            filters.append(rfilter)
        return self._filter(filters)
    def order_by(self, attribute_name: str,reverse:bool=False) -> "StreamQuery":
        """Apply a sort order. Filters out stream the do not have the attribute.

        :param str attribute_name:
            The name of the attribute to sort by.
        """
        has_attribute = [
            s
            for s in self.items
            if getattr(s, attribute_name) is not None
        ]
        # Check that the attributes have string values.
        if has_attribute and isinstance(
            getattr(has_attribute[0], attribute_name), str
        ):
            # Try to return a StreamQuery sorted by the integer representations
            # of the values.
            try:
                return StreamQuery(
                    sorted(
                        has_attribute,
                        key=lambda s: int(
                            "".join(
                                filter(str.isdigit, getattr(s, attribute_name))
                            )
                        ),reverse=reverse
                    )
                )
            except ValueError:
                pass

        return StreamQuery(
            sorted(has_attribute, key=lambda s: getattr(s, attribute_name))
        )
    def sort_by_filesize(self,reverse:bool=False)->"StreamQuery":
        return self.order_by("filesize_approx",reverse=reverse)

    def sort_by_audio_sample_rate(self,reverse:bool=False)->"StreamQuery":
        return self.filter(contains_audio=True).order_by("audio_sample_rate",reverse)
    def sort_by_bitrate(self,reverse:bool=False)->"StreamQuery":
        return self.order_by("bitrate",reverse)
    def get_by_itag(self,itag:int)->Stream:
        return self._filter(lambda x: x.itag == itag)
    def get_by_audio_codec(self,codec:str)->"StreamQuery":
        return self.filter(audio_codec=codec)

    def get_progressive(self)->"StreamQuery":
        return self.filter(progressive=True)
    def get_adaptive(self)->"StreamQuery":
        return self.filter(adaptive=True)
    def get_by_video_codec(self,codec:str)->"StreamQuery":
        return self.filter(video_codec=codec)
    def get_by_resolution(self,resolution)->"StreamQuery":
        return self.filter(resolution=resolution)
    def get_lowest_resolution(self)->Stream:
        return self.filter().order_by("resolution").first
    def get_highest_resolution(self)->Stream:
        return self.filter().order_by("resolution",reverse=True).first
    def get_audio_only(self)->"StreamQuery":
        return self.filter(only_audio=True)
    def get_video_only(self)->"StreamQuery":
        return self.filter(only_video=True)
    def get_video_contains(self)->"StreamQuery":
        return self.filter(contains_video=True)
    def get_audio_contains(self)->"StreamQuery":
        return self.filter(contains_audio=True)
    def otf(self,otf:bool=False)->"StreamQuery":
        return self._filter([lambda s: s.is_otf == is_otf])
    def contains_audio_track_info(self,val:bool=True)->"StreamQuery":
        return self.filter(contains_audio_track_info=True)
    def get_by_audio_track_id(self,id:str)->"StreamQuery":
        return self.filter(audio_track_id=id)
    def get_by_audio_track_name(self,name:str)->"StreamQuery":
        ln = name.lower()
        return self._filter([lambda x: contains_audio_track_info and audio_track_info.name.lower()==ln])
    def max_filesize(self,filesize:str):...#TODO max size
    def get_by_ext(self,ext:str)->"StreamQuery":
        return self.filter(subtype=ext)
    def hdr(self,hdr=True)->"StreamQuery":
        return self._filter([lambda s: s.is_hdr == hdr])
    def threeD(self,threeD=True)->"StreamQuery":
        return self._filter([lambda s:s.is_3d == threeD])

    @property
    def first(self)->Stream:
        return self.items[0]
    @property
    def last(self)->Stream:
        return self.items[-1]
    @property
    def reversed(self)->"StreamQuery":
        return StreamQuery(self.items[::-1])
    def __getitem__(self,i:Union[slice,int])->"Union[StreamQuery,Stream]":
        if isinstance(i,slice):
            return StreamQuery(self.items[i])
        return self.items[i]
    def __len__(self)->int:
        return len(self.items)
    def __repr__(self)->str:
        return f"<StreamQuery {self.items}/>"
    def __iter__(self):
        self.current_index = 0
        return self
    def __next__(self)->Stream:
        if self.current_index >= len(self.items):
            raise StopIteration()
        val = self.items[self.current_index]
        self.current_index += 1
        return val

class ThumbnailQuery(Sequence):
    def __init__(self,thumbnails:[Thumbnail]):
        self.items:[Thumbnail] = thumbnails
        self.current_index = 0
    def sort_by_resolution(self,reverse=False)->"ThumbnailQuery":
        return ThumbnailQuery(self.items.sort(key=lambda x: x.height,reverse=reverse))
    def get_highest_resolution(self)->Thumbnail:
        return max(self.items,key=lambda th: th.height)
    def get_lowest_resolution(self)->Thumbnail:
        return min(self.items,key=lambda th: th.height)
    @property
    def first(self)->Thumbnail:
        return self.items[0]
    @property
    def last(self)->Thumbnail:
        return self.items[-1]
    @property
    def reversed(self)->"ThumbnailQuery":
        return ThumbnailQuery(self.items[::-1])
    def __getitem__(self, i:Union[slice, int])->Union["ThumbnailQuery",Thumbnail]:
        if isinstance(i,slice):
            return ThumbnailQuery(self.items[i])
        return self.items[i]
        
    def __len__(self) -> int:
        return len(self.items)
    def __repr__(self) -> str:
        return f"<ThumbnailQuery {self.items} />"
    def __iter__(self):
        self.current_index = 0
        return self
    def __next__(self)->Thumbnail:
        if self.current_index >= len(self.items):
            raise StopIteration()
        val = self.items[self.current_index]
        self.current_index += 1
        return val
def get_thumbnails_from_raw(raw_list)->ThumbnailQuery:
    ths =[]
    for x in raw_list:
        th = Thumbnail(x["url"])
        th.width = x["width"]
        th.height = x["height"]
        ths.append(th)
    return ThumbnailQuery(ths)


class CaptionQuery(Mapping):
    def __init__(self,items:[Caption],translation_languages:[(str,str)]):
        self.captions = items
        self.translation_languages = translation_languages
    def _filter(self,filters:[Callable[[Caption],bool]])->"CaptionQuery":
        caps = self.captions
        for filter_lambda in filters:
            caps = filter(filter_lambda, caps)
        return CaptionQuery(list(caps),self.translation_languages)
    def filter(
        self,
        l_code:str = None,
        vss_id:str = None,
        is_generated:bool=None,
        is_translatable:bool=None,
        name:str=None,
        rtl:bool=None,
        kind:str=None,
        custom_filter_function:Callable=None
        ):
        filters = []
        if l_code:
            filters.append(lambda x: x.l_code == l_code)
        if vss_id:
            filters.append(lambda x: x.vss_id == vss_id)
        if is_generated:
            filters.append(lambda x: x.is_generated == is_generated)
        if is_translatable:
            filters.append(lambda x: x.is_translatable == is_translatable)
        if name:
            filters.append(lambda x: x.name == name)
        if rtl:
            filters.append(lambda x: x.rtl == rtl)
        if kind:
            filters.append(lambda x: x.kind == kind)
        if custom_filter_function:
            filters.append(custom_filter_function)
        return self._filter(filters)

    def auto_created(self)->"CaptionQuery":#TODO only one caption? create @property original_language
        return self.filter(is_generated=True)
    def user_created(self)->"CaptionQuery":
        return self.filter(is_generated=False)
    def translatable(self)->"CaptionQuery":
        return self.filter(is_translatable=True)
    def get_by_name(self,name:str)->Caption:
        return filter(name=name).first
    def get_by_lcode(self,l_code:str)->"CaptionQuery":
        return filter(l_code=l_code)
    def get_by_vvs_id(self,vss_id:str)->Caption:
        return filter(vss_id=vss_id).first
    @property
    def first(self)->Caption:
        return self.captions[0]
    @property
    def last(self)->Caption:
        return self.captions[-1]
    def __getitem__(self, i: Union[str,int,slice])->Union["CaptionQuery",Caption]:
        """vss_id or int index or slice"""
        if isinstance(i,int):
            return self.captions[i]
        elif isinstance(i,slice):
            return StreamQuery(self.captions[i],self.translation_languages)
        elif isinstance(i,str):
            return self.filter(vss_id=i).first
    @property
    def keys(self)->str:
        return [x.vss_id for x in self.captions]
    @property
    def values(self)->[Caption]:
        return self.captions
    @property
    def items(self)->[(str,Caption)]:
        return list(zip(self.keys,self.values))
            
    def __len__(self) -> int:
        return len(self.captions)
    def __iter__(self):
        return iter(self.captions)
    def __repr__(self) -> str:
        return f"<CaptionQuery {self.captions}/>"

class CaptionQueryFirst(CaptionQuery):
    def __init__(self,items:[Caption],translationLanguages:[(str,str)]):
        super().__init__(items,translationLanguages)
    @cached_property
    def caption_base_generated(self)->Caption:
        val = self.filter(is_generated=True)
        if len(val.captions)>0:return val.first
        return None
    

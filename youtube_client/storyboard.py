#YT_DLP extractor/youtube.py
from typing import Iterable,List
import math
import requests#TODO work with my my downloader

import io
from .helpers import int_or_none

class Storyboard:
    """
     Several images cut from the video sequence.
     A Pillow is required to select individual frames:
     in the get_all_fragments,get_images_in_fragment,get_all_images methods"""
    def __init__(self,url,width,height,fps,rows,columns,fragments,spec,rlvl):
        self.url = url
        self.width = width
        self.height = height
        self.fps =fps
        self.rows =rows
        self.columns = columns
        self.fragments = fragments
        self.spec = spec
        self.rlvl = rlvl
    def __repr__(self)->str:
        return f"<Storyboard {self.width}*{self.height}px {self.rows}*{self.columns} images fps={self.fps:.2f}/>"
    def get_all_fragments(self)->"Iterable[Image.Image]":#TODO to thumbnail
        """Returns fragments that have not yet been cut, consisting of several images"""
        from PIL import Image
        for s in self.fragments:
            yield Image.open(io.BytesIO(requests.get(s["url"]).content))

    def _cut_images_in_fragment(self,fragment_image:"Image.Image")->"Iterable[Image.Image]":
        from PIL import Image
        for y in range(self.rows):
            for x in range(self.columns):
                yield fragment_image.crop((x*self.width,y*self.height,(x+1)*self.width,(y+1)*self.height))

    def get_all_images(self)->"Iterable[Image.Image]":
        """Returns the final cut images"""
        from PIL import Image
        for s in self.get_all_fragments():
            yield self._cut_images_in_fragment(s)
                    
def get_groups(renderer:dict,duration:int)->List[Storyboard]:
    sbimgrops = []
    specr = renderer['spec']
    rlvl = renderer.get("recommendedLevel")
    spec = specr.split('|')[::-1]
    base_url = spec.pop()
    L = len(spec)-1
    for i, args in enumerate(spec):
        args = args.split('#')
        counts = list(map(int_or_none, args[:5]))
        if len(args) != 8 or not all(counts):
            print(f'Malformed storyboard {i}: {"#".join(args)}{bug_reports_message()}')
            continue
        width, height, frame_count, cols, rows = counts
        N, sigh = args[6:]

        url = base_url.replace('$L', str(L - i)).replace('$N', N) + f'&sigh={sigh}'
        fragment_count = frame_count / (cols * rows)
        
        fragment_duration = duration / fragment_count
        sbimgrops.append(Storyboard(url,width,height,frame_count/duration,rows,cols,[{
                'url': url.replace('$M', str(j)),
                'duration': min(fragment_duration, duration - (j * fragment_duration)),
            } for j in range(math.ceil(fragment_count))],specr,rlvl))
        
    return sbimgrops
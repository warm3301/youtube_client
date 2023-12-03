# youtube_client
This is the same library as pytube but with slightly more functionality.
**do not guarantee backward compatibility before the release**

### Features
- Download video and audio
- Get storyboards (with PIL), cards, chapters in videos
- Get info about video, live, short, channel
- Get comments
- Get subtitles
- Search

### Simple example to download
```
from youtube_client import Video
from youtube_client.downloaders import SingleDownlower
v = Video(url="https://youtube.com/watch?v=jNQXAC9IVRw")
print(v.title)

def progress(obj,bytes,receive):
    print(f"receive {receive} bytes")

stream = v.streams.get_progressive().get_highest_resolution()#progressive streams contains video with audio
dwnl = SingleDownlower(stream,on_progress=progress)
file_path = dwnl.download()
print(f"downloaded to {file_path}")
```

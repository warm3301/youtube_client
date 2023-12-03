# youtube_client
This is the same library as pytube but with slightly more functionality.

**I do not guarantee backward compatibility before the release**

### Features
- Download video and audio
- Get storyboards (with PIL), cards, chapters in videos
- Get info about video, short, live, playlist, channel
- Get videos, shorts, lives, playlists, posts from channel
- Get comments
- Get subtitles and translate it to other languages
- Get different audio tracks in one video
- Search

### Simple example to download
```
from youtube_client import Video
from youtube_client.downloaders import SingleDownlower

v = Video(url="https://youtube.com/watch?v=jNQXAC9IVRw")
print(v.title)

def progress(obj,bytes,receive):
    print(f"receive {receive} bytes")

# progressive streams contains video with audio
stream = v.streams.get_progressive().get_highest_resolution()
dwnl = SingleDownlower(stream,on_progress=progress)
file_path = dwnl.download()

print(f"downloaded to {file_path}")
```

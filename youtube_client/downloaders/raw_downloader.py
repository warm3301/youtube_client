from typing import Optional,Callable,Any,BinaryIO
from .base_downloader import VideoDownloader
from ..streams import Stream
from .. import request
class SingleDownlower(VideoDownloader):
    def __init__(self,
    stream:Stream,
    output_path:str=None,
    ext_in_path:bool=False,
    skip_existing: bool = True,
    on_progress:Optional[Callable[[Any, bytes, int],None]]=None,
    on_complete:Optional[Callable[[Any, Optional[str]],None]]=None,
    default_title:str = "Unknown youtube video"
    ):#stream_getter also save title and lenght in cashe(and other if possible)
        self.on_progress:Optional[Callable[[Any, bytes, int],None]] = on_progress
        super().__init__(stream=stream,on_complete=on_complete,default_title=default_title,output_path=output_path,ext_in_path=ext_in_path,skip_existing=skip_existing)

    def _on_progress(self, chunk: bytes, file_handler: BinaryIO, bytes_remaining: int):
        file_handler.write(chunk)
        if self.on_progress:
            self.on_progress(self,chunk,bytes_remaining)

    def stream_to_buffer(self, buffer: BinaryIO) -> None:
        """Write the media stream to buffer

        :rtype: io.BytesIO buffer
        """
        bytes_remaining = self.stream.filesize
        for chunk in request.stream(self.stream.url):
            # reduce the (bytes) remainder by the length of the chunk.
            bytes_remaining -= len(chunk)
            # send to the on_progress callback.
            self._on_progress(chunk, buffer, bytes_remaining)
        self._on_complete(None)
    def download(
        self,
        timeout: int = None,
        max_retries:int = 0
    ) -> str:
        if self.skip:
            self._on_complete(self.file_path)
            return self.file_path

        bytes_remaining = self.stream.filesize

        with open(self.file_path, "wb") as fh:
            try:
                for chunk in request.stream(
                    self.stream.url,
                    timeout=timeout,
                    max_retries=max_retries
                ):
                    # reduce the (bytes) remainder by the length of the chunk.
                    bytes_remaining -= len(chunk)
                    # send to the on_progress callback.
                    self._on_progress(chunk, fh, bytes_remaining)
            except HTTPError as e:
                if e.code != 404:
                    raise
                # Some adaptive streams need to be requested with sequence numbers
                for chunk in request.seq_stream(
                    self.stream.url,
                    timeout=timeout,
                    max_retries=max_retries
                ):
                    # reduce the (bytes) remainder by the length of the chunk.
                    bytes_remaining -= len(chunk)
                    # send to the on_progress callback.
                    self._on_progress(chunk, fh, bytes_remaining)
        self._on_complete(self.file_path)
        return self.file_path

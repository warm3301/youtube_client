"""Implements a simple wrapper around urlopen."""
import http.client
import json
import logging
import re
import socket
from functools import lru_cache
from urllib import parse
from urllib.error import URLError
import urllib.request
from urllib.request import urlopen
from .exceptions import RegexMatchError, MaxRetriesExceeded
from .helpers import regex_search
from requests import Session

languages = {"RU":"ru,en;q=0.5","EN":"en-US,en"}
base_user_agent = "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0"
class Request:
    def __init__(self,language="RU"):
        self.session:Session = Session()
        self.base_headers = {
            "User-Agent": base_user_agent, 
            "accept-language": languages[language]
            }
        self.session.headers.update(self.base_headers)
    #TODO encode and getting params in other method
    def _data_encode(self,data):
        res = data
        if res:
            if not isinstance(res, bytes):
                res = bytes(json.dumps(res), encoding="utf-8")
        return res
    def get(self,url,data:dict=None,headers=None)->str:
        if not url.lower().startswith("http"):
            raise ValueError("Invalid url")
        resp = self.session.get(url,data=self._data_encode(data),headers=headers)
        if resp.status_code >= 400:
            raise Exception(f"responce status code {resp.status_code}")
        return resp.content.decode("utf-8")
    def post(self,url,data:dict=None,headers=None)->dict:
        if not url.lower().startswith("http"):
            raise ValueError("Invalid url")
        resp = self.session.post(url,data=self._data_encode(data),headers=headers)
        if resp.status_code >= 400:
            raise Exception(f"responce status code {resp.status_code}")
        return json.loads(resp.content.decode("utf-8"))
    def head(self,url,data:dict=None,headers=None)->[str]:
        if not url.lower().startswith("http"):
            raise ValueError("Invalid url")
        return self.session.head(url,data=self._data_encode(data),headers=headers).headers
    def filesize(self,url,data=None,headers=None)->int:
        try:
            return int(self.head(url,data,headers)["content-length"])
        except KeyError:
            return 0

logger = logging.getLogger(__name__)
default_range_size = 9437184  # 9MB №download remaining 8552551


def _execute_request(
    url,
    method=None,
    headers=None,
    data=None,
    timeout=socket._GLOBAL_DEFAULT_TIMEOUT
):
    base_headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0", "accept-language": "en-US,en"}
    if headers:
        base_headers.update(headers)
    if data:
        # encode data for request
        if not isinstance(data, bytes):
            data = bytes(json.dumps(data), encoding="utf-8")
    if url.lower().startswith("http"):
        request = urllib.request.Request(url, headers=base_headers, method=method, data=data)
    else:
        raise ValueError("Invalid URL")
    return urlopen(request, timeout=timeout)  # nosec


def get(url, extra_headers=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT,language=languages["RU"]):
    """Send an http GET request.

    :param str url:
        The URL to perform the GET request for.
    :param dict extra_headers:
        Extra headers to add to the request
    :rtype: str
    :returns:
        UTF-8 encoded string of response
    """
    
    if extra_headers is None:
        extra_headers = {}
    extra_headers["accept-language"]=language
    response = _execute_request(url, headers=extra_headers, timeout=timeout)
    return response.read().decode("utf-8")


def post(url, extra_headers=None, data=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
    """Send an http POST request.

    :param str url:
        The URL to perform the POST request for.
    :param dict extra_headers:
        Extra headers to add to the request
    :param dict data:
        The data to send on the POST request
    :rtype: str
    :returns:
        UTF-8 encoded string of response
    """
    # could technically be implemented in get,
    # but to avoid confusion implemented like this
    if extra_headers is None:
        extra_headers = {}
    if data is None:
        data = {}
    # required because the youtube servers are strict on content type
    # raises HTTPError [400]: Bad Request otherwise
    extra_headers.update({"Content-Type": "application/json"})
    response = _execute_request(
        url,
        headers=extra_headers,
        data=data,
        timeout=timeout
    )
    return response.read().decode("utf-8")


def seq_stream(
    url,
    timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
    max_retries=0
):
    """Read the response in sequence.
    :param str url: The URL to perform the GET request for.
    :rtype: Iterable[bytes]
    """
    # YouTube expects a request sequence number as part of the parameters.
    split_url = parse.urlsplit(url)
    base_url = '%s://%s/%s?' % (split_url.scheme, split_url.netloc, split_url.path)

    querys = dict(parse.parse_qsl(split_url.query))

    # The 0th sequential request provides the file headers, which tell us
    #  information about how the file is segmented.
    querys['sq'] = 0
    url = base_url + parse.urlencode(querys)

    segment_data = b''
    for chunk in stream(url, timeout=timeout, max_retries=max_retries):
        yield chunk
        segment_data += chunk

    # We can then parse the header to find the number of segments
    stream_info = segment_data.split(b'\r\n')
    segment_count_pattern = re.compile(b'Segment-Count: (\\d+)')
    for line in stream_info:
        match = segment_count_pattern.search(line)
        if match:
            segment_count = int(match.group(1).decode('utf-8'))

    # We request these segments sequentially to build the file.
    seq_num = 1
    while seq_num <= segment_count:
        # Create sequential request URL
        querys['sq'] = seq_num
        url = base_url + parse.urlencode(querys)

        yield from stream(url, timeout=timeout, max_retries=max_retries)
        seq_num += 1
    return  # pylint: disable=R1711


def stream(
    url,
    timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
    max_retries=0
):
    """Read the response in chunks.
    :param str url: The URL to perform the GET request for.
    :rtype: Iterable[bytes]
    """
    file_size: int = default_range_size  # fake filesize to start
    downloaded = 0
    while downloaded < file_size:
        stop_pos = min(downloaded + default_range_size, file_size) - 1
        range_header = f"bytes={downloaded}-{stop_pos}"
        tries = 0

        # Attempt to make the request multiple times as necessary.
        while True:
            # If the max retries is exceeded, raise an exception
            if tries >= 1 + max_retries:
                raise MaxRetriesExceeded()

            # Try to execute the request, ignoring socket timeouts
            try:
                ssss = f"&range={downloaded}-{stop_pos}"
                response = _execute_request(
                    url + ssss,
                    method="GET",
                    timeout=timeout
                )
            except URLError as e:
                # We only want to skip over timeout errors, and
                # raise any other URLError exceptions
                if isinstance(e.reason, socket.timeout):
                    pass
                else:
                    raise
            except http.client.IncompleteRead:
                # Allow retries on IncompleteRead errors for unreliable connections
                pass
            else:
                # On a successful request, break from loop
                break
            tries += 1

        if file_size == default_range_size:
            try:
                resp = _execute_request(
                    url + f"&range={0}-{99999999999}",
                    method="GET",
                    timeout=timeout
                )
                content_range = resp.info()["Content-Length"]
                file_size = int(content_range)
            except (KeyError, IndexError, ValueError) as e:
                logger.error(e)
        while True:
            chunk = response.read()
            if not chunk:
                break
            downloaded += len(chunk)
            yield chunk
    return  # pylint: disable=R1711


@lru_cache()
def filesize(url):
    """Fetch size in bytes of file at given URL

    :param str url: The URL to get the size of
    :returns: int: size in bytes of remote file
    """
    try:
        return int(head(url)["content-length"])
    except KeyError:# if live
        return 0


@lru_cache()
def seq_filesize(url):
    """Fetch size in bytes of file at given URL from sequential requests

    :param str url: The URL to get the size of
    :returns: int: size in bytes of remote file
    """
    total_filesize = 0
    # YouTube expects a request sequence number as part of the parameters.
    split_url = parse.urlsplit(url)
    base_url = '%s://%s/%s?' % (split_url.scheme, split_url.netloc, split_url.path)
    querys = dict(parse.parse_qsl(split_url.query))

    # The 0th sequential request provides the file headers, which tell us
    #  information about how the file is segmented.
    querys['sq'] = 0
    url = base_url + parse.urlencode(querys)
    response = _execute_request(
        url, method="GET"
    )

    response_value = response.read()
    # The file header must be added to the total filesize
    total_filesize += len(response_value)

    # We can then parse the header to find the number of segments
    segment_count = 0
    stream_info = response_value.split(b'\r\n')
    segment_regex = b'Segment-Count: (\\d+)'
    for line in stream_info:
        # One of the lines should contain the segment count, but we don't know
        #  which, so we need to iterate through the lines to find it
        try:
            segment_count = int(regex_search(segment_regex, line, 1))
        except RegexMatchError:
            pass

    if segment_count == 0:
        raise RegexMatchError('seq_filesize', segment_regex)

    # We make HEAD requests to the segments sequentially to find the total filesize.
    seq_num = 1
    while seq_num <= segment_count:
        # Create sequential request URL
        querys['sq'] = seq_num
        url = base_url + parse.urlencode(querys)

        total_filesize += int(head(url)['content-length'])
        seq_num += 1
    return total_filesize


def head(url):
    """Fetch headers returned http GET request.

    :param str url:
        The URL to perform the GET request for.
    :rtype: dict
    :returns:
        dictionary of lowercase headers
    """
    response_headers = _execute_request(url, method="HEAD").info()
    return {k.lower(): v for k, v in response_headers.items()}
    
default_obj = Request()
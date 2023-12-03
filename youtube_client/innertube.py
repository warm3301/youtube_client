"""This module is designed to interact with the innertube API.

This module is NOT intended to be used directly by end users, as each of the
interfaces returns raw results. These should instead be parsed to extract
the useful information for the end user.
"""
# Native python imports
import json
import os
import pathlib
import time
from urllib import parse

# Local imports
from . import request

# YouTube on TV client secrets
_client_id = '861556708454-d6dlm3lh05idd8npek18k6be8ba3oc68.apps.googleusercontent.com'
_client_secret = 'SboVhoG9s0rNafixCSGGKXAT'

# Extracted API keys -- unclear what these are linked to.
_api_keys = [
    'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8',
    'AIzaSyCtkvNIR1HCEwzsqK6JuE6KqpyjusIRI30',
    'AIzaSyA8eiZmM1FaDVjRy-df2KTyQ_vz_yYM39w',
    'AIzaSyC8UYZpvA2eknNex0Pjid0_eTLJoDu6los',
    'AIzaSyCjc_pVEDi4qsv5MtC2dMXzpIaDoRFLsxw',
    'AIzaSyDHQ9ipnphqTzDqZsbtd8_Ru4_kiKVQe2k'
]

_default_clients = {
    'WEB': {
        'context': {
            'client': {
                'clientName': 'WEB',
                'clientVersion': '2.20231121.08.00'#'2.20200720.00.02'
            }
        },
        'header': {
            'User-Agent': request.base_user_agent
        },
        'api_key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
    },
    'ANDROID': {
        'context': {
            'client': {
                'clientName': 'ANDROID',
                'clientVersion': '18.36.38',#'17.31.35',
                'androidSdkVersion': 30
            }
        },
        'header': {
            'User-Agent': 'com.google.android.youtube/',
        },
        'api_key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
    },
    'IOS': {
        'context': {
            'client': {
                'clientName': 'IOS',
                'clientVersion': '17.33.2',
                'deviceModel': 'iPhone14,3'
            }
        },
        'header': {
            'User-Agent': 'com.google.ios.youtube/'
        },
        'api_key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
    },

    'WEB_EMBED': {
        'context': {
            'client': {
                'clientName': 'WEB_EMBEDDED_PLAYER',
                'clientVersion': '2.20210721.00.00',
                'clientScreen': 'EMBED'
            }
        },
        'header': {
            'User-Agent': 'Mozilla/5.0'
        },
        'api_key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
    },
    'ANDROID_EMBED': {
        'context': {
            'client': {
                'clientName': 'ANDROID_EMBEDDED_PLAYER',
                'clientVersion': '17.31.35',
                'clientScreen': 'EMBED',
                'androidSdkVersion': 30,
            }
        },
        'header': {
            'User-Agent': 'com.google.android.youtube/'
        },
        'api_key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
    },
    'IOS_EMBED': {
        'context': {
            'client': {
                'clientName': 'IOS_MESSAGES_EXTENSION',
                'clientVersion': '17.33.2',
                'deviceModel': 'iPhone14,3'
            }
        },
        'header': {
            'User-Agent': 'com.google.ios.youtube/'
        },
        'api_key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
    },

    'WEB_MUSIC': {
        'context': {
            'client': {
                'clientName': 'WEB_REMIX',
                'clientVersion': '1.20220727.01.00',
            }
        },
        'header': {
            'User-Agent': 'Mozilla/5.0'
        },
        'api_key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
    },
    'ANDROID_MUSIC': {
        'context': {
            'client': {
                'clientName': 'ANDROID_MUSIC',
                'clientVersion': '5.16.51',
                'androidSdkVersion': 30
            }
        },
        'header': {
            'User-Agent': 'com.google.android.apps.youtube.music/'
        },
        'api_key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
    },
    'IOS_MUSIC': {
        'context': {
            'client': {
                'clientName': 'IOS_MUSIC',
                'clientVersion': '5.21',
                'deviceModel': 'iPhone14,3'
            }
        },
        'header': {
            'User-Agent': 'com.google.ios.youtubemusic/'
        },
        'api_key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
    },

    'WEB_CREATOR': {
        'context': {
            'client': {
                'clientName': 'WEB_CREATOR',
                'clientVersion': '1.20220726.00.00',
            }
        },
        'header': {
            'User-Agent': 'Mozilla/5.0'
        },
        'api_key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
    },
    'ANDROID_CREATOR': {
        'context': {
            'client': {
                'clientName': 'ANDROID_CREATOR',
                'clientVersion': '22.30.100',
                'androidSdkVersion': 30,
            }
        },
        'header': {
            'User-Agent': 'com.google.android.apps.youtube.creator/',
        },
        'api_key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
    },
    'IOS_CREATOR': {
        'context': {
            'client': {
                'clientName': 'IOS_CREATOR',
                'clientVersion': '22.33.101',
                'deviceModel': 'iPhone14,3',
            }
        },
        'header': {
            'User-Agent': 'com.google.ios.ytcreator/'
        },
        'api_key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
    },

    'MWEB': {
        'context': {
            'client': {
                'clientName': 'MWEB',
                'clientVersion': '2.20220801.00.00',
            }
        },
        'header': {
            'User-Agent': 'Mozilla/5.0'
        },
        'api_key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
    },
    'TV_EMBED': {
        'context': {
            'client': {
                'clientName': 'TVHTML5_SIMPLY_EMBEDDED_PLAYER',
                'clientVersion': '2.0',
            }
        },
        'header': {
            'User-Agent': 'Mozilla/5.0'
        },
        'api_key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
    },
}
_token_timeout = 1800
_cache_dir = pathlib.Path(__file__).parent.resolve() / '__cache__'
_token_file = os.path.join(_cache_dir, 'tokens.json')


class InnerTube:
    """Object for interacting with the innertube API."""
    def __init__(self, client='WEB',ro:request.Request = None):
        """Initialize an InnerTube object.

        :param str client:
            Client to use for the object.
            Default to web because it returns the most playback types.
        :param bool use_oauth:
            Whether or not to authenticate to YouTube.
        :param bool allow_cache:
            Allows caching of oauth tokens on the machine.
        """
        self.context = _default_clients[client]['context']
        self.header = _default_clients[client]['header']
        self.api_key = _default_clients[client]['api_key']
        self.ro = ro if ro else request.default_obj

    @property
    def base_url(self):
        """Return the base url endpoint for the innertube API."""
        return 'https://www.youtube.com/youtubei/v1'
    @property
    def base_data(self):
        """Return the base json data to transmit to the innertube API."""
        return {
            'context': self.context
        }

    @property
    def base_params(self):
        """Return the base query parameters to transmit to the innertube API."""
        return {
            'key': self.api_key,
            'prettyPrint':'false'
            # 'contentCheckOk': True,
            # 'racyCheckOk': True
        }

    def _call_api(self, endpoint, query, data):
        """Make a request to a given endpoint with the provided query parameters and data."""
        endpoint_url = f'{endpoint}?{parse.urlencode(query)}'
        headers = {
            'Content-Type': 'application/json',
        }
        headers.update(self.header)
        return request.default_obj.post(endpoint_url,data=data,headers=headers)

    def browse(self,browse_id,continuation=None):
        """Make a request to the browse endpoint.
        """
        endpoint = f'{self.base_url}/browse'  ## noqa:E800
        query = {
            'browseId':browse_id,
        }
        if continuation:
            query["continuation"] = continuation
        query.update(self.base_params)
        data = self.base_data
        data.update({"engagementType":"ENGAGEMENT_TYPE_UNBOUND"})
        return self._call_api(endpoint, query, self.base_data)  # noqa:E800

    def config(self):
        """Make a request to the config endpoint.

        TODO: Figure out how we can use this
        """
        # endpoint = f'{self.base_url}/config'  # noqa:E800
        ...
        # return self._call_api(endpoint, query, self.base_data)  # noqa:E800

    def guide(self):
        """Make a request to the guide endpoint.

        TODO: Figure out how we can use this
        """
        # endpoint = f'{self.base_url}/guide'  # noqa:E800
        #...
        # return self._call_api(endpoint, query, self.base_data)  # noqa:E800

    def next(self,video_id: str = None,
        playlist_id: str = None,index: int = None,
        continuation: str = None):
        """Make a request to the next endpoint."""
        endpoint = f'{self.base_url}/next'  # noqa:E800
        query={ }
        if continuation:
            query["continuation"] = continuation
        if index:
            query["playlistIndex"] = index
        if playlist_id:
            query["playlistId"] = playlist_id
        if video_id:
            query["videoId"] = video_id
        query.update(self.base_params)
        return self._call_api(endpoint, query, self.base_data)  # noqa:E800

    def player(self, video_id):
        """Make a request to the player endpoint.

        :param str video_id:
            The video id to get player info for.
        :rtype: dict
        :returns:
            Raw player info results.
        """
        endpoint = f'{self.base_url}/player'
        query = {
            'videoId': video_id,
        }
        query.update(self.base_params)
        return self._call_api(endpoint, query, self.base_data)

    def search(self, search_query=None, continuation=None):
        """Make a request to the search endpoint.

        :param str search_query:
            The query to search.
        :rtype: dict
        :returns:
            Raw search query results.
        """
        endpoint = f'{self.base_url}/search'
        query = {}
        if search_query:
            query['query'] = search_query
        query.update(self.base_params)
        data = {}
        if continuation:
            data['continuation'] = continuation
        data.update(self.base_data)
        return self._call_api(endpoint, query, data)

    def verify_age(self, video_id):
        """Make a request to the age_verify endpoint.

        Notable examples of the types of video this verification step is for:
        * https://www.youtube.com/watch?v=QLdAhwSBZ3w
        * https://www.youtube.com/watch?v=hc0ZDaAZQT0

        :param str video_id:
            The video id to get player info for.
        :rtype: dict
        :returns:
            Returns information that includes a URL for bypassing certain restrictions.
        """
        endpoint = f'{self.base_url}/verify_age'
        data = {
            'nextEndpoint': {
                'urlEndpoint': {
                    'url': f'/watch?v={video_id}'
                }
            },
            'setControvercy': True
        }
        data.update(self.base_data)
        result = self._call_api(endpoint, self.base_params, data)
        return result

    def get_transcript(self, video_id):
        """Make a request to the get_transcript endpoint.

        This is likely related to captioning for videos, but is currently untested.
        """
        endpoint = f'{self.base_url}/get_transcript'
        query = {
            'videoId': video_id,
        }
        query.update(self.base_params)
        result = self._call_api(endpoint, query, self.base_data)
        return result
default_obj = InnerTube()
streams_it_obj = InnerTube("ANDROID",request.Request())
updated_headers = False
def update_default_headers(ytcfg:dict):
    global updated_headers
    updated_headers = True
    it_client_version = ytcfg["INNERTUBE_CLIENT_VERSION"]
    default_obj.api_key = ytcfg["INNERTUBE_API_KEY"]
    default_obj.header.update(
        {
            "X-Youtube-Client-Version":it_client_version
        })
    default_obj.context = ytcfg["INNERTUBE_CONTEXT"]
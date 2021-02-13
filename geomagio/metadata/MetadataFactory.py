import os
import json
import requests
import urllib
from typing import Dict, List, Optional

from obspy import UTCDateTime
from pydantic import parse_obj_as

from ..residual import Reading
from .Metadata import Metadata
from .MetadataCategory import MetadataCategory

HOST = os.getenv("EDGE_HOST", "127.0.0.1:8000")

class MetadataFactory(object):
    def __init__(self, url:str = None):
        self.url = url or f"http://{HOST}/ws/secure/metadata"

    def get_metadata(
        self,
        category: Optional[MetadataCategory] = None,
        starttime: Optional[UTCDateTime] = None,
        endtime: Optional[UTCDateTime] = None,
        created_after: Optional[UTCDateTime] = None,
        created_before: Optional[UTCDateTime] = None,
        network: Optional[str] = None,
        station: Optional[str] = None,
        channel: Optional[str] = None,
        location: Optional[str] = None,
        data_valid: Optional[bool] = None,
        metadata_valid: Optional[bool] = True,
        # returns interior base models from metadata.metadata
        return_objects: str = False,
    ) -> List[Metadata]:
        args = parse_params(params=locals())
        response = web_request(url=f"{self.url}?{args}")
        metadata = self.format_metadata(data=response, return_objects=return_objects)
        return metadata

    def put_metadata(self):
        raise NotImplementedError

    def format_metadata(self, data: Dict, return_objects: bool = False):
        # formats responses as Metadata objects
        data = parse_obj_as(List[Metadata], data)
        if not return_objects:
            return data
        formatted_metadata = []
        for metadata in data:
            category = metadata.category
            if category == MetadataCategory.ADJUSTED_MATRIX:
                raise NotImplementedError
            elif category == MetadataCategory.FLAG:
                raise NotImplementedError
            elif category == MetadataCategory.READING:
                formatted_metadata.append(parse_obj_as(Reading, metadata.metadata))
            # observatory and instrument metadata do not have a confining object other than metadata
        return formatted_metadata


def web_request(url:str) -> Dict:
    client_id=os.getenv("OPENID_CLIENT_ID")
    client_secret=os.getenv("OPENID_CLIENT_SECRET")
    response = requests.get(url, data={'grant_type' : 'client_credentials'}, auth = (client_id, client_secret))
    metadata = json.loads(response.text)
    return metadata

def parse_params(params: Dict):
    data = {}
    for param in params.keys():
        if params[param] is not None and param != "self":
            p = params[param]
            # convert times to strings
            if type(p) == UTCDateTime:
                p=p.isoformat()
            data[param] = p

    return urllib.parse.urlencode(
            data
        )
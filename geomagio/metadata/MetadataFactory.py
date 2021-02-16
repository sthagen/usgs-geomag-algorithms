import os
import json
import requests
import urllib
from typing import Dict, List, Optional

from obspy import UTCDateTime
from pydantic import parse_obj_as

from ..api.secure import MetadataQuery
from ..residual import Reading
from .Metadata import Metadata
from .MetadataCategory import MetadataCategory


class MetadataFactory(object):
    def __init__(
        self,
        url: str = "http://{}/ws/secure/metadata".format(
            os.getenv("EDGE_HOST", "127.0.0.1:8000")
        ),
    ):
        self.url = url

    def delete_metadata(self, query: MetadataQuery):
        raise NotImplementedError

    def format_metadata(self, data: Dict):
        # formats responses as Metadata objects
        return parse_obj_as(List[Metadata], data)

    def get_metadata(self, query: MetadataQuery) -> List[Metadata]:
        args = parse_params(query=query)
        response = web_request(url=f"{self.url}?{args}")
        metadata = self.format_metadata(data=response)
        return metadata

    def post_metadata(self, query: MetadataQuery):
        raise NotImplementedError

    def update_metadata(self, query: MetadataQuery):
        raise NotImplementedError


def web_request(url: str) -> Dict:
    client_id = os.getenv("OPENID_CLIENT_ID")
    client_secret = os.getenv("OPENID_CLIENT_SECRET")
    response = requests.get(
        url, data={"grant_type": "client_credentials"}, auth=(client_id, client_secret)
    )
    metadata = json.loads(response.text)
    return metadata


def parse_params(query: MetadataQuery):
    d = query.dict()
    data = {}
    for key in d.keys():
        if d[key] is None:
            continue
        # convert times to strings
        if type(d[key]) == UTCDateTime:
            d[key] = d[key].isoformat()
        if key == "category":
            d[key] = d[key].value
        data[key] = d[key]

    return urllib.parse.urlencode(data)

import json
from json.decoder import JSONDecodeError
import os
import requests
from typing import Dict, List, Optional
import urllib

from obspy import UTCDateTime

from ..api.secure.MetadataQuery import MetadataQuery
from .Metadata import Metadata


class MetadataFactory(object):
    def __init__(
        self,
        url: str = "http://{}/ws/secure/metadata".format(
            os.getenv("EDGE_HOST", "127.0.0.1:8000")
        ),
        token: str = os.getenv("GITLAB_API_TOKEN"),
    ):
        self.url = url
        self.token = token
        self.header = {"Authorization": self.token} if token else None

    def delete_metadata(self, id: int) -> Dict:
        response = requests.delete(url=f"{self.url}/{id}", headers=self.header)
        return response

    def get_metadata(self, query: MetadataQuery) -> List[Dict]:
        args = parse_params(query=query)
        raw_response = requests.get(url=f"{self.url}{args}", headers=self.header)
        try:
            response = json.loads(raw_response.content)
        except JSONDecodeError:
            raise ValueError("Data not found")
        return response

    def post_metadata(
        self, query: MetadataQuery, data: Optional[Dict] = {}
    ) -> requests.Response:
        metadata = parse_metadata(query=query, data=data)
        response = requests.post(url=self.url, data=metadata, headers=self.header)
        return response

    def update_metadata(
        self, id: int, query: MetadataQuery, data: Optional[Dict] = {}
    ) -> requests.Response:
        metadata = parse_metadata(query=query, data=data)
        response = requests.put(
            url=f"{self.url}/{query.id}", data=metadata, headers=self.header
        )
        return response


def parse_metadata(query: MetadataQuery, data: Optional[Dict] = {}) -> str:
    metadata = Metadata(**query.dict())
    metadata.metadata = data
    return metadata.json()


def parse_params(query: MetadataQuery) -> str:
    query = query.dict()
    args = {}
    for key in query.keys():
        element = query[key]
        if element is not None:
            # convert times to strings
            if type(element) == UTCDateTime:
                element = element.isoformat()
            # get string value of metadata category
            if key == "category":
                element = element.value
            elif key == "id":
                return f"/{element}"
            args[key] = element

    return f"?{urllib.parse.urlencode(args)}"

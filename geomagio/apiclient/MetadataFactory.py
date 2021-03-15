import os
import requests
from typing import Dict, List, Union
import urllib

from obspy import UTCDateTime
from pydantic import parse_obj_as

from ..api.secure.MetadataQuery import MetadataQuery
from ..metadata import Metadata


class MetadataFactory(object):
    def __init__(
        self,
        url: str = "http://{}/ws/secure/metadata".format(
            os.getenv("GEOMAG_API_HOST", "127.0.0.1:8000")
        ),
        token: str = os.getenv("GITLAB_API_TOKEN"),
    ):
        self.url = url
        self.token = token
        self.header = {"Authorization": self.token} if token else None

    def delete_metadata(self, metadata: Metadata) -> Dict:
        response = requests.delete(url=f"{self.url}/{metadata.id}", headers=self.header)
        return response

    def get_metadata(self, query: MetadataQuery) -> Union[List[Metadata], Metadata]:
        args = parse_params(query=query)
        if "id" in args:
            self.url = f"{self.url}/{args['id']}"
            args = {}
        responses = requests.get(url=self.url, params=args, headers=self.header)
        try:
            metadata = parse_obj_as(Union[List[Metadata], Metadata], responses.json())
        except:
            raise ValueError("Data not found")
        if isinstance(metadata, Metadata):
            metadata = [metadata]
        return metadata

    def create_metadata(self, metadata: Metadata) -> requests.Response:
        response = requests.post(
            url=self.url, data=metadata.json(), headers=self.header
        )
        return response

    def update_metadata(self, metadata: Metadata) -> requests.Response:
        response = requests.put(
            url=f"{self.url}/{metadata.id}", data=metadata.json(), headers=self.header
        )
        return response


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
                return {"id": element}
            args[key] = element

    return args

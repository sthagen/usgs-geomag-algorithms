import os
import requests
from typing import List, Union

from obspy import UTCDateTime
from pydantic import parse_obj_as

from ..metadata import Metadata, MetadataQuery


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
        self.header = self._get_headers()

    def _get_headers(self):
        return {"Authorization": self.token} if self.token else None

    def delete_metadata(self, metadata: Metadata) -> bool:
        response = requests.delete(url=f"{self.url}/{metadata.id}", headers=self.header)
        if response.status_code == 200:
            return True
        return False

    def get_metadata(self, query: MetadataQuery) -> List[Metadata]:
        if query.id:
            response = self.get_metadata_by_id(id=query.id)
        else:
            args = parse_params(query=query)
            response = requests.get(url=self.url, params=args, headers=self.header)
        metadata = parse_obj_as(Union[List[Metadata], Metadata], response.json())
        if isinstance(metadata, Metadata):
            metadata = [metadata]
        return metadata

    def get_metadata_by_id(self, id: int) -> requests.Response:
        return requests.get(f"{self.url}/{id}", headers=self.header)

    def create_metadata(self, metadata: Metadata) -> Metadata:
        response = requests.post(
            url=self.url, data=metadata.json(), headers=self.header
        )
        return Metadata(**response.json())

    def update_metadata(self, metadata: Metadata) -> Metadata:
        response = requests.put(
            url=f"{self.url}/{metadata.id}", data=metadata.json(), headers=self.header
        )
        return Metadata(**response.json())


def parse_params(query: MetadataQuery) -> str:
    query = query.dict(exclude_none=True)
    args = {}
    for key in query.keys():
        element = query[key]
        # convert times to strings
        if isinstance(element, UTCDateTime):
            element = element.isoformat()
        # get string value of metadata category
        if key == "category":
            element = element.value
        args[key] = element
    return args

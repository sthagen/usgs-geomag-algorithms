import os
import requests
from typing import List

from obspy import UTCDateTime
from pydantic import parse_obj_as

from .Metadata import Metadata
from .MetadataQuery import MetadataQuery


GEOMAG_API_HOST = os.getenv("GEOMAG_API_HOST", "geomag.usgs.gov")
GEOMAG_API_URL = f"https://{GEOMAG_API_HOST}/ws/secure/metadata"
if "127.0.0.1" in GEOMAG_API_URL:
    GEOMAG_API_URL = GEOMAG_API_URL.replace("https://", "http://")


class MetadataFactory(object):
    def __init__(
        self,
        url: str = GEOMAG_API_URL,
        token: str = os.getenv("GITLAB_API_TOKEN"),
    ):
        self.url = url
        self.token = token

    def _get_headers(self):
        return {"Authorization": self.token} if self.token else None

    def delete_metadata(self, metadata: Metadata) -> bool:
        response = requests.delete(
            url=f"{self.url}/{metadata.id}",
            headers=self._get_headers(),
        )
        if response.status_code == 200:
            return True
        return False

    def get_metadata(self, query: MetadataQuery) -> List[Metadata]:
        if query.id:
            metadata = [self.get_metadata_by_id(id=query.id)]
        else:
            response = requests.get(
                url=self.url,
                headers=self._get_headers(),
                params=parse_params(query=query),
            )
            metadata = parse_obj_as(List[Metadata], response.json())
        return metadata

    def get_metadata_by_id(self, id: int) -> Metadata:
        response = requests.get(
            url=f"{self.url}/{id}",
            headers=self._get_headers(),
        )
        return Metadata(**response.json())

    def create_metadata(self, metadata: Metadata) -> Metadata:
        response = requests.post(
            url=self.url,
            data=metadata.json(),
            headers=self._get_headers(),
        )
        return Metadata(**response.json())

    def update_metadata(self, metadata: Metadata) -> Metadata:
        response = requests.put(
            url=f"{self.url}/{metadata.id}",
            data=metadata.json(),
            headers=self._get_headers(),
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

from typing import Dict

from fastapi import APIRouter, Response

from .Observatory import OBSERVATORIES, OBSERVATORY_INDEX


router = APIRouter()


@router.get(
    "/observatories/",
    description="Information regarding available geomagnetic observatories",
)
def get_observatories() -> Dict:
    return {
        "type": "FeatureCollection",
        "features": [o.geojson() for o in OBSERVATORIES],
    }


@router.get(
    "/observatories/{id}",
    description="Search observatories by 3-letter observatory code",
)
async def get_observatory_by_id(id: str) -> Dict:
    try:
        return OBSERVATORY_INDEX[id].geojson()
    except KeyError:
        return Response(status_code=404)

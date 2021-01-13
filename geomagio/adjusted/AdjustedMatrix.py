from pydantic import BaseModel
from typing import List, Optional, Any
from obspy import UTCDateTime


class AdjustedMatrix(BaseModel):
    matrix: Any
    pier_correction: float
    starttime: Optional[UTCDateTime] = None
    endtime: Optional[UTCDateTime] = None

from pydantic import BaseModel


class Metric(BaseModel):
    element: str
    mae: float
    std: float

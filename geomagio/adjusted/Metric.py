from pydantic import BaseModel


class Metric(BaseModel):
    """Mean absolute error and standard deviation for a given element

    Attributes
    ----------
    element: Channel that metrics are representative of
    absmean: mean absolute error
    stddev: standard deviation
    """

    element: str
    absmean: float = None
    stddev: float = None

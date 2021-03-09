from typing import List

import numpy as np
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


def get_metric(element: str, expected: List[float], actual: List[float]) -> Metric:
    diff = np.array(expected) - np.array(actual)
    return Metric(element=element, absmean=np.average(abs(diff)), stddev=np.std(diff))

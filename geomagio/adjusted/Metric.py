import numpy as np
from pydantic import BaseModel


class Metric(BaseModel):
    """Mean absolute error and standard deviation for a given element

    Attributes
    ----------
    element: Channel that metrics are representative of
    mae: mean absolute error
    std: standard deviation
    """

    element: str
    mae: float = None
    std: float = None

    def calculate(self, expected, predicted):
        """Calculates mean absolute error and standard deviation between expected and predicted data"""
        self.mae = abs(np.nanmean(expected - predicted))
        self.std = np.nanstd(expected - predicted)

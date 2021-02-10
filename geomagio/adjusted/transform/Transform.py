import numpy as np
from obspy import UTCDateTime
from pydantic import BaseModel
from typing import List, Optional, Tuple


class Transform(BaseModel):
    """Method for generating an affine matrix.

    Attributes
    ----------
    acausal: if true, future readings are used in calculations
    memory: Controls impact of measurements from the past
    Defaults to infinite(equal weighting)
    """

    acausal: bool = False
    memory: Optional[float] = None
    ndims = 3

    def get_weights(self, times: UTCDateTime, time: int = None) -> List[float]:
        """
        Calculate time-dependent weights according to exponential decay.

        Inputs:
        times: array of times, or any time-like index whose relative values represent spacing between events
        Output:
        weights: array of vector distances/metrics
        """

        # convert to array of floats
        times = np.asarray(times).astype(float)

        if time is None:
            time = float(max(times))

        # if memory is actually infinite, return equal weights
        if np.isinf(self.memory):
            return np.ones(times.shape)

        # initialize weights
        weights = np.zeros(times.shape)

        # calculate exponential decay time-dependent weights
        weights[times <= time] = np.exp((times[times <= time] - time) / self.memory)
        weights[times >= time] = np.exp((time - times[times >= time]) / self.memory)

        if not self.acausal:
            weights[times > time] = 0.0

        return weights

    def calculate(
        self,
        ordinates: Tuple[List[float], List[float], List[float]],
        absolutes: Tuple[List[float], List[float], List[float]],
        weights: List[float],
    ) -> np.array:
        """Type skeleton inherited by any instance of Transform

        Attributes
        ----------
        ordinates: H, E and Z ordinates
        absolutes: X, Y and Z absolutes(NOTE: absolutes must be rotated from original H, E and Z values)
        weights: time weights to apply during calculations of matrices
        """
        return

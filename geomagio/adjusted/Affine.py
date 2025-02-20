from functools import reduce
import numpy as np
from obspy import UTCDateTime
from pydantic import BaseModel, Field
from typing import List, Optional, Tuple

from ..residual.Reading import (
    Reading,
    get_absolutes_xyz,
    get_ordinates,
)
from .. import pydantic_utcdatetime
from .AdjustedMatrix import AdjustedMatrix
from .transform import RotationTranslationXY, TranslateOrigins, Transform


class Affine(BaseModel):
    """Creates AdjustedMatrix objects from readings

    Attributes
    ----------
    observatory: 3-letter observatory code
    starttime: beginning time for matrix creation
    endtime: end time for matrix creation
    update_interval: window of time(in seconds) a matrix is representative of
    transforms: methods for matrix calculations
    """

    observatory: str = None
    starttime: UTCDateTime = Field(default_factory=lambda: UTCDateTime() - (86400 * 7))
    endtime: UTCDateTime = Field(default_factory=lambda: UTCDateTime())
    update_interval: Optional[int] = 86400 * 7
    transforms: List[Transform] = [
        RotationTranslationXY(memory=(86400 * 100), acausal=True),
        TranslateOrigins(memory=(86400 * 10), acausal=True),
    ]

    def calculate(
        self, readings: List[Reading], epochs: Optional[List[UTCDateTime]] = None
    ) -> List[AdjustedMatrix]:
        """Calculates affine matrices for a range of times

        Attributes
        ----------
        readings: readings containing absolutes
        epochs: optional time markers for unreliable observations

        Outputs
        -------
        Ms: AdjustedMatrix objects created from calculations
        """
        # default set to create one matrix between starttime and endtime
        update_interval = self.update_interval or (self.endtime - self.starttime)
        all_readings = [r for r in readings if r.valid]
        Ms = []
        time = self.starttime
        # search for "bad" H values
        epochs = epochs or [
            r.time for r in all_readings if r.get_absolute("H").absolute == 0
        ]
        while time < self.endtime:
            # update epochs for current time
            epoch_start, epoch_end = get_epochs(epochs=epochs, time=time)
            # utilize readings that occur after or before a bad reading
            readings = [
                r
                for r in all_readings
                if (epoch_start is None or r.time > epoch_start)
                or (epoch_end is None or r.time < epoch_end)
            ]
            M = self.calculate_matrix(time, readings)
            M.starttime = epoch_start
            M.endtime = epoch_end
            time += update_interval

            Ms.append(M)

        return Ms

    def calculate_matrix(
        self, time: UTCDateTime, readings: List[Reading]
    ) -> AdjustedMatrix:
        """Calculates affine matrix for a given time

        Attributes
        ----------
        time: time within calculation interval
        readings: list of valid readings

        Outputs
        -------
        AdjustedMatrix object containing result
        """
        absolutes = get_absolutes_xyz(readings)
        ordinates = get_ordinates(readings)
        Ms = []
        weights = []
        inputs = ordinates

        for transform in self.transforms:
            weights = transform.get_weights(
                readings=readings,
                time=time.timestamp,
            )
            # raise ValueError if no valid observations
            if np.sum(weights) == 0:
                raise ValueError(f"No valid observations for: {time}")

            M = transform.calculate(
                ordinates=inputs, absolutes=absolutes, weights=weights
            )

            # apply latest M matrix to inputs to get intermediate inputs
            inputs = np.vstack([*inputs, np.ones_like(inputs[0])])
            inputs = np.dot(M, inputs)[0:3]
            Ms.append(M)

        # compose affine transform matrices using reverse ordered matrices
        M_composed = reduce(np.dot, reversed(Ms))
        pier_correction = np.average(
            [reading.pier_correction for reading in readings], weights=weights
        )
        matrix = AdjustedMatrix(
            matrix=M_composed.tolist(),
            pier_correction=pier_correction,
        )
        matrix.metrics = matrix.get_metrics(readings=readings)
        return matrix


def get_epochs(
    epochs: List[float],
    time: UTCDateTime,
) -> Tuple[float, float]:
    """Updates valid start/end time for a given interval

    Attributes
    ----------
    epochs: bad data times
    time: current time epoch is being evaluated at

    Outputs
    -------
    epoch_start: start of current valid interval
    epoch_end: end of current valid interval
    """
    epoch_start = None
    epoch_end = None
    for e in epochs:
        if e > time:
            if epoch_end is None or e < epoch_end:
                epoch_end = e
        if e < time:
            if epoch_start is None or e > epoch_start:
                epoch_start = e
    return epoch_start, epoch_end

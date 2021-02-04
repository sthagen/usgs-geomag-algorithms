import numpy as np
from typing import List, Optional, Tuple

from .Transform import Transform


class LeastSq(Transform):
    """Intance of Transform. Applies least squares to generate matrices"""

    def get_stacked_absolutes(self, absolutes):
        """Formats absolutes for least squares method

        Attributes
        ----------
        absolutes: Rotated X, Y, and Z absolutes

        Output
        ------
        X, Y and Z absolutes placed end to end and transposed
        """
        return np.vstack([absolutes[0], absolutes[1], absolutes[2]]).T.ravel()

    def get_weighted_values(
        self,
        values: Tuple[List[float], List[float], List[float]],
        weights: Optional[List[float]],
    ) -> Tuple[List[float], List[float], List[float]]:
        """Application of weights for least squares methods, which calls for square rooting of weights

        Attributes
        ----------
        values: absolutes or ordinates

        Outputs
        -------
        tuple of weights applied to each element of values

        """
        if weights is None:
            return values
        weights = np.sqrt(weights)
        weights = np.vstack((weights, weights, weights)).T.ravel()
        return values * weights

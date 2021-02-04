import numpy as np
from typing import List, Optional, Tuple

from .Transform import Transform


class SVD(Transform):
    """Instance of Transform. Applies singular value decomposition to generate matrices"""

    def get_stacked_values(self, values, weighted_values, ndims=3) -> np.array:
        """Supports intermediate mathematical steps by differencing and shaping values for SVD

        Attributes
        ----------
        values: absolutes or ordinates
        weighted_values: absolutes or ordinates with weights applied
        ndims: number of rows desired in return array(case specific). Default set to 3 dimensions(XYZ/HEZ)

        Outputs
        -------
        Stacked and differenced values from their weighted counterparts
        """
        return np.vstack([[values[i] - weighted_values[i]] for i in range(ndims)])

    def get_weighted_values(
        self,
        values: Tuple[List[float], List[float], List[float]],
        weights: Optional[List[float]],
    ) -> Tuple[List[float], List[float], List[float]]:
        """Application of weights for SVD methods, which call for weighted averages"""
        if weights is None:
            weights = np.ones_like(values[0])
        return (
            np.average(values[0], weights=weights),
            np.average(values[1], weights=weights),
            np.average(values[2], weights=weights),
        )

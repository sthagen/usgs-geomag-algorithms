import numpy as np
import scipy.linalg as spl
from typing import List, Optional, Tuple

from .LeastSq import LeastSq


class TranslateOrigins(LeastSq):
    """Calculates affine using using least squares, constrained to tanslate origins"""

    def get_weighted_values(
        self,
        values: Tuple[List[float], List[float], List[float]],
        weights: Optional[List[float]],
    ):
        """Weights are applied after matrix creation steps,
        requiring weights to be stacked similar to ordinates and absolutes"""
        if weights is not None:
            weights = np.sqrt(weights)
            weights = np.vstack((weights, weights, weights)).T.ravel()
        else:
            weights = 1
        return values * weights

    def calculate(
        self,
        ordinates: Tuple[List[float], List[float], List[float]],
        absolutes: Tuple[List[float], List[float], List[float]],
        weights: List[float],
    ) -> np.array:

        abs_stacked = self.get_stacked_absolutes(absolutes)
        ord_stacked = np.zeros((3, len(ordinates[0]) * 3))

        ord_stacked[0, 0::3] = 1.0
        ord_stacked[1, 1::3] = 1.0
        ord_stacked[2, 2::3] = 1.0

        # subtract ords from abs to force simple translation
        abs_stacked[0::3] = absolutes[0] - ordinates[0]
        abs_stacked[1::3] = absolutes[1] - ordinates[1]
        abs_stacked[2::3] = absolutes[2] - ordinates[2]

        # apply weights
        ord_stacked = self.get_weighted_values(values=ord_stacked, weights=weights)
        abs_stacked = self.get_weighted_values(values=abs_stacked, weights=weights)

        # regression matrix M that minimizes L2 norm
        M_r, res, rank, sigma = spl.lstsq(ord_stacked.T, abs_stacked.T)
        if rank < 3:
            print("Poorly conditioned or singular matrix, returning NaNs")
            return np.nan * np.ones((4, 4))

        return [
            [1.0, 0.0, 0.0, M_r[0]],
            [0.0, 1.0, 0.0, M_r[1]],
            [0.0, 0.0, 1.0, M_r[2]],
            [0.0, 0.0, 0.0, 1.0],
        ]

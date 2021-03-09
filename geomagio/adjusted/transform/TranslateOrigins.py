import numpy as np
from typing import List, Optional, Tuple

from .LeastSq import LeastSq


class TranslateOrigins(LeastSq):
    """Calculates affine using using least squares, constrained to tanslate origins"""

    def get_matrix(
        self,
        matrix: List[List[float]],
        absolutes: Optional[Tuple[List[float], List[float], List[float]]] = None,
        ordinates: Optional[Tuple[List[float], List[float], List[float]]] = None,
        weights: Optional[List[float]] = None,
    ) -> np.array:
        return [
            [1.0, 0.0, 0.0, matrix[0]],
            [0.0, 1.0, 0.0, matrix[1]],
            [0.0, 0.0, 1.0, matrix[2]],
            [0.0, 0.0, 0.0, 1.0],
        ]

    def get_stacked_ordinates(
        self, ordinates: Tuple[List[float], List[float], List[float]]
    ) -> List[List[float]]:
        ord_stacked = np.zeros((3, len(ordinates[0]) * 3))
        ord_stacked[0, 0::3] = 1.0
        ord_stacked[1, 1::3] = 1.0
        ord_stacked[2, 2::3] = 1.0
        return ord_stacked

    def get_stacked_values(
        self,
        absolutes: Tuple[List[float], List[float], List[float]],
        ordinates: Tuple[List[float], List[float], List[float]],
        weights: Optional[List[float]] = None,
    ) -> Tuple[List[float], List[List[float]]]:
        # LHS, or dependent variables
        abs_stacked = self.get_stacked_absolutes(absolutes)
        # subtract ords from abs to force simple translation
        abs_stacked[0::3] = absolutes[0] - ordinates[0]
        abs_stacked[1::3] = absolutes[1] - ordinates[1]
        abs_stacked[2::3] = absolutes[2] - ordinates[2]
        # RHS, or independent variables
        ord_stacked = self.get_stacked_ordinates(ordinates)
        return abs_stacked, ord_stacked

    def get_weighted_values(
        self,
        values: Tuple[List[float], List[float], List[float]],
        weights: Optional[List[float]],
    ) -> List[float]:
        """Weights are applied after matrix creation steps,
        requiring weights to be stacked similar to ordinates and absolutes"""
        if weights is not None:
            weights = np.sqrt(weights)
            weights = np.vstack((weights, weights, weights)).T.ravel()
        else:
            weights = 1
        return values * weights

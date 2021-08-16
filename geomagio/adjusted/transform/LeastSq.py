import numpy as np
import scipy.linalg as spl
from typing import List, Optional, Tuple, Union

from .Transform import Transform


class LeastSq(Transform):
    """Intance of Transform. Applies least squares to generate matrices"""

    def calculate(
        self,
        ordinates: Tuple[List[float], List[float], List[float]],
        absolutes: Tuple[List[float], List[float], List[float]],
        weights: Optional[List[float]] = None,
    ) -> np.array:
        """Calculates matrix with least squares and accompanying methods
        Defaults to least squares calculation with no constraints
        """
        abs_stacked, ord_stacked = self.get_stacked_values(
            absolutes, ordinates, weights
        )
        ord_stacked = self.get_weighted_values(ord_stacked, weights)
        abs_stacked = self.get_weighted_values(abs_stacked, weights)
        # regression matrix M that minimizes L2 norm
        matrix, res, rank, sigma = spl.lstsq(ord_stacked.T, abs_stacked.T)
        if self.valid(rank):
            return self.get_matrix(matrix, absolutes, ordinates, weights)
        print("Poorly conditioned or singular matrix, returning NaNs")
        return np.nan * np.ones((4, 4))

    def get_matrix(
        self,
        matrix: List[List[float]],
        absolutes: Optional[Tuple[List[float], List[float], List[float]]] = None,
        ordinates: Optional[Tuple[List[float], List[float], List[float]]] = None,
        weights: Optional[List[float]] = None,
    ) -> np.array:
        """Returns matrix formatted for no constraints
        NOTE: absolutes, ordinates, and weights are only used by QRFactorization's child function
        """
        return np.array(
            [
                [matrix[0], matrix[1], matrix[2], matrix[3]],
                [matrix[4], matrix[5], matrix[6], matrix[7]],
                [matrix[8], matrix[9], matrix[10], matrix[11]],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )

    def get_stacked_absolutes(
        self, absolutes: Tuple[List[float], List[float], List[float]]
    ) -> List[float]:
        """Formats absolutes for least squares method

        Attributes
        ----------
        absolutes: Rotated X, Y, and Z absolutes

        Output
        ------
        X, Y and Z absolutes placed end to end and transposed
        """
        return np.vstack([absolutes[0], absolutes[1], absolutes[2]]).T.ravel()

    def get_stacked_ordinates(
        self, ordinates: Tuple[List[float], List[float], List[float]]
    ) -> List[List[float]]:
        """Formats ordinates for least squares method"""
        # (reduces degrees of freedom by 4:
        #  - 4 for the last row of zeros and a one)
        ord_stacked = np.zeros((12, len(ordinates[0]) * 3))
        ord_stacked[0, 0::3] = ordinates[0]
        ord_stacked[1, 0::3] = ordinates[1]
        ord_stacked[2, 0::3] = ordinates[2]
        ord_stacked[3, 0::3] = 1.0
        ord_stacked[4, 1::3] = ordinates[0]
        ord_stacked[5, 1::3] = ordinates[1]
        ord_stacked[6, 1::3] = ordinates[2]
        ord_stacked[7, 1::3] = 1.0
        ord_stacked[8, 2::3] = ordinates[0]
        ord_stacked[9, 2::3] = ordinates[1]
        ord_stacked[10, 2::3] = ordinates[2]
        ord_stacked[11, 2::3] = 1.0

        return ord_stacked

    def get_stacked_values(
        self,
        absolutes: Tuple[List[float], List[float], List[float]],
        ordinates: Tuple[List[float], List[float], List[float]],
        weights: Optional[List[float]] = None,
    ) -> Tuple[List[float], List[List[float]]]:
        """Gathers stacked stacked absolutes/ordinates
        NOTE: weights are only used in QRFactorization's child function
        """
        # LHS, or dependent variables
        # [A[0,0], A[1,0], A[2,0], A[0,1], A[1,1], A[2,1], ...]
        abs_stacked = self.get_stacked_absolutes(absolutes)
        # RHS, or independent variables
        # [
        # [o[0,0], 0, 0, o[0,1], 0, 0, ...],
        # [0, o[1,0], 0, 0, o[1,1], 0, ...],
        # [0, 0, o[2,0], 0, 0, o[2,1], ...],
        # ...
        # ]
        ord_stacked = self.get_stacked_ordinates(ordinates)
        return abs_stacked, ord_stacked

    def get_weighted_values(
        self,
        values: Tuple[List[float], List[float], List[float]],
        weights: Optional[List[float]] = None,
    ) -> Union[List[float], List[List[float]]]:
        """Application of weights for least squares methods, which calls for square roots

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

    def valid(self, rank: float) -> bool:
        """validates whether or not a matrix can reliably transform the method's number of dimensions"""
        if rank < self.ndims:
            return False
        return True

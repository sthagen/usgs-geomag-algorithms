import numpy as np
from typing import List, Optional, Tuple

from .LeastSq import LeastSq
from .SVD import SVD


class QRFactorization(LeastSq):
    """Calculates affine using least squares with QR factorization"""

    ndims: int = 2
    svd: SVD = SVD(ndims=ndims)

    def get_matrix(
        self,
        matrix: List[List[float]],
        absolutes: Tuple[List[float], List[float], List[float]],
        ordinates: Tuple[List[float], List[float], List[float]],
        weights: List[float],
    ) -> np.array:
        """ performs QR factorization steps and formats result within the returned matrix """
        # QR fatorization
        # NOTE: forcing the diagonal elements of Q to be positive
        #       ensures that the determinant is 1, not -1, and is
        #       therefore a rotation, not a reflection
        Q, R = np.linalg.qr(matrix.T)
        neg = np.diag(Q) < 0
        Q[:, neg] = -1 * Q[:, neg]
        R[neg, :] = -1 * R[neg, :]

        # isolate scales from shear
        S = np.diag(np.diag(R))
        H = np.dot(np.linalg.inv(S), R)

        # combine shear and rotation
        QH = np.dot(Q, H)

        weighted_absolutes = self.svd.get_weighted_values(absolutes, weights)
        weighted_ordinates = self.svd.get_weighted_values(ordinates, weights)

        # now get translation using weighted centroids and R
        T = self.svd.get_translation_matrix(QH, weighted_absolutes, weighted_ordinates)

        return [
            [QH[0, 0], QH[0, 1], 0.0, T[0]],
            [QH[1, 0], QH[1, 1], 0.0, T[1]],
            [
                0.0,
                0.0,
                1.0,
                np.array(weighted_absolutes[self.ndims])
                - np.array(weighted_ordinates[self.ndims]),
            ],
            [0.0, 0.0, 0.0, 1.0],
        ]

    def get_stacked_values(
        self,
        absolutes: Tuple[List[float], List[float], List[float]],
        ordinates: Tuple[List[float], List[float], List[float]],
        weights: Optional[List[float]] = None,
    ) -> Tuple[List[List[float]], List[List[float]]]:
        """ stacks and weights absolutes/ordinates """
        weighted_absolutes = self.svd.get_weighted_values(
            values=absolutes, weights=weights
        )
        weighted_ordinates = self.svd.get_weighted_values(
            values=ordinates, weights=weights
        )
        # LHS, or dependent variables
        abs_stacked = self.svd.get_stacked_values(
            values=absolutes,
            weighted_values=weighted_absolutes,
        )

        # RHS, or independent variables
        ord_stacked = self.svd.get_stacked_values(
            values=ordinates,
            weighted_values=weighted_ordinates,
        )
        return abs_stacked, ord_stacked

    def get_weighted_values(
        self,
        values: Tuple[List[float], List[float], List[float]],
        weights: Optional[List[float]] = None,
    ) -> List[List[float]]:
        """ Applies least squares weights in two dimensions(X and Y)"""
        if weights is None:
            return values
        weights = np.sqrt(weights)
        return np.array([values[i] * weights for i in range(self.ndims)])

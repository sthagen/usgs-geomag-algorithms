import numpy as np
import scipy.linalg as spl
from typing import List, Optional, Tuple

from .LeastSq import LeastSq
from .SVD import SVD


class QRFactorization(LeastSq):
    """Calculates affine using singular value decomposition with QR factorization"""

    ndims = 2
    svd = SVD(ndims=ndims)

    def get_weighted_values(
        self,
        values: Tuple[List[float], List[float], List[float]],
        weights: Optional[List[float]],
    ):
        """ Applies least squares weights in two dimensions(X and Y)"""
        if weights is None:
            return values
        weights = np.sqrt(weights)
        return np.array([values[i] * weights for i in range(self.ndims)])

    def get_stacked_values(self, absolutes, ordinates, weights):
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

    def get_matrix(self, matrix, absolutes, ordinates, weights):
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

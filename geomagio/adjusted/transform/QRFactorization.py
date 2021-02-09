import numpy as np
import scipy.linalg as spl
from typing import List, Optional, Tuple

from .SVD import SVD


class QRFactorization(SVD):
    """Calculates affine using singular value decomposition with QR factorization"""

    ndims = 2

    def get_weighted_values_lstsq(
        self,
        values: Tuple[List[float], List[float], List[float]],
        weights: Optional[List[float]],
    ):
        """ Applies least squares weights in two dimensions(X and Y)"""
        if weights is None:
            return values
        weights = np.sqrt(weights)
        return np.array(
            [
                values[0] * weights,
                values[1] * weights,
            ]
        )

    def calculate(
        self,
        ordinates: Tuple[List[float], List[float], List[float]],
        absolutes: Tuple[List[float], List[float], List[float]],
        weights: List[float],
    ) -> np.array:

        if weights is None:
            weights = np.ones_like(ordinates[0])

        weighted_absolutes = self.get_weighted_values(values=absolutes, weights=weights)
        weighted_ordinates = self.get_weighted_values(values=ordinates, weights=weights)
        # LHS, or dependent variables
        abs_stacked = self.get_stacked_values(
            values=absolutes,
            weighted_values=weighted_absolutes,
        )

        # RHS, or independent variables
        ord_stacked = self.get_stacked_values(
            values=ordinates,
            weighted_values=weighted_ordinates,
        )

        abs_stacked = self.get_weighted_values_lstsq(
            values=abs_stacked,
            weights=weights,
        )
        ord_stacked = self.get_weighted_values_lstsq(
            values=ord_stacked,
            weights=weights,
        )

        # regression matrix M that minimizes L2 norm
        M_r, res, rank, sigma = spl.lstsq(ord_stacked.T, abs_stacked.T)
        if rank < 2:
            print("Poorly conditioned or singular matrix, returning NaNs")
            return np.nan * np.ones((4, 4))

        # QR fatorization
        # NOTE: forcing the diagonal elements of Q to be positive
        #       ensures that the determinant is 1, not -1, and is
        #       therefore a rotation, not a reflection
        Q, R = np.linalg.qr(M_r.T)
        neg = np.diag(Q) < 0
        Q[:, neg] = -1 * Q[:, neg]
        R[neg, :] = -1 * R[neg, :]

        # isolate scales from shear
        S = np.diag(np.diag(R))
        H = np.dot(np.linalg.inv(S), R)

        # combine shear and rotation
        QH = np.dot(Q, H)

        # now get translation using weighted centroids and R
        T = np.array([weighted_absolutes[0], weighted_absolutes[1]]) - np.dot(
            QH, [weighted_ordinates[0], weighted_ordinates[1]]
        )

        return [
            [QH[0, 0], QH[0, 1], 0.0, T[0]],
            [QH[1, 0], QH[1, 1], 0.0, T[1]],
            [
                0.0,
                0.0,
                1.0,
                np.array(weighted_absolutes[2]) - np.array(weighted_ordinates[2]),
            ],
            [0.0, 0.0, 0.0, 1.0],
        ]

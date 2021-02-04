import numpy as np
from typing import List, Tuple

from .SVD import SVD


class RotationTranslationXY(SVD):
    """Calculates affine using singular value decomposition,
    constrained to rotation and translation in XY(no scale or shear),
    and only translation in Z"""

    def calculate(
        self,
        ordinates: Tuple[List[float], List[float], List[float]],
        absolutes: Tuple[List[float], List[float], List[float]],
        weights: List[float],
    ) -> np.array:
        if weights is None:
            weights = np.ones_like(ordinates[0])
        weighted_ordinates = self.get_weighted_values(values=ordinates, weights=weights)
        weighted_absolutes = self.get_weighted_values(values=absolutes, weights=weights)
        # return generate_affine_8(ord_hez, abs_xyz, weights)
        # generate weighted "covariance" matrix
        H = np.dot(
            self.get_stacked_values(
                values=ordinates,
                weighted_values=weighted_ordinates,
                ndims=2,
            ),
            np.dot(
                np.diag(weights),
                self.get_stacked_values(
                    values=absolutes,
                    weighted_values=weighted_absolutes,
                    ndims=2,
                ).T,
            ),
        )

        # Singular value decomposition, then rotation matrix from L&R eigenvectors
        # (the determinant guarantees a rotation, and not a reflection)
        U, S, Vh = np.linalg.svd(H)
        if np.sum(S) < 2:
            print("Poorly conditioned or singular matrix, returning NaNs")
            return np.nan * np.ones((4, 4))

        R = np.dot(Vh.T, np.dot(np.diag([1, np.linalg.det(np.dot(Vh.T, U.T))]), U.T))

        # now get translation using weighted centroids and R
        T = np.array([weighted_absolutes[0], weighted_absolutes[1]]) - np.dot(
            R, [weighted_ordinates[0], weighted_ordinates[1]]
        )

        return [
            [R[0, 0], R[0, 1], 0.0, T[0]],
            [R[1, 0], R[1, 1], 0.0, T[1]],
            [
                0.0,
                0.0,
                1.0,
                np.array(weighted_absolutes[2]) - np.array(weighted_ordinates[2]),
            ],
            [0.0, 0.0, 0.0, 1.0],
        ]

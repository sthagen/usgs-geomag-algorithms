import numpy as np
from typing import List, Optional, Tuple

from .Transform import Transform


class SVD(Transform):
    """Instance of Transform. Applies singular value decomposition to generate matrices"""

    def get_covariance_matrix(self, absolutes, ordinates, weights):
        weighted_ordinates = self.get_weighted_values(values=ordinates, weights=weights)
        weighted_absolutes = self.get_weighted_values(values=absolutes, weights=weights)
        # generate weighted "covariance" matrix
        H = np.dot(
            self.get_stacked_values(
                values=ordinates,
                weighted_values=weighted_ordinates,
            ),
            np.dot(
                np.diag(weights),
                self.get_stacked_values(
                    values=absolutes,
                    weighted_values=weighted_absolutes,
                ).T,
            ),
        )
        return H

    def get_stacked_values(self, values, weighted_values) -> np.array:
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
        return np.vstack([[values[i] - weighted_values[i]] for i in range(self.ndims)])

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

    def get_rotation_matrix(self, U, Vh):
        return np.dot(
            Vh.T, np.dot(np.diag([1, 1, np.linalg.det(np.dot(Vh.T, U.T))]), U.T)
        )

    def get_translation_matrix(self, R, weighted_absolutes, weighted_ordinates):
        return np.array([weighted_absolutes[i] for i in range(self.ndims)]) - np.dot(
            R, [weighted_ordinates[i] for i in range(self.ndims)]
        )

    def valid(self, singular_values):
        if np.sum(singular_values) < self.ndims:
            return False
        return True

    def calculate(
        self,
        ordinates: Tuple[List[float], List[float], List[float]],
        absolutes: Tuple[List[float], List[float], List[float]],
        weights: List[float],
    ) -> np.array:
        weighted_ordinates = self.get_weighted_values(values=ordinates, weights=weights)
        weighted_absolutes = self.get_weighted_values(values=absolutes, weights=weights)
        # generate weighted "covariance" matrix
        H = self.get_covariance_matrix(absolutes, ordinates, weights)
        # Singular value decomposition, then rotation matrix from L&R eigenvectors
        # (the determinant guarantees a rotation, and not a reflection)
        U, S, Vh = np.linalg.svd(H)
        if self.valid(S):
            R = self.get_rotation_matrix(U, Vh)
            # now get translation using weighted centroids and R
            T = self.get_translation_matrix(R, weighted_absolutes, weighted_ordinates)
            return self.get_matrix(R, T, weighted_absolutes, weighted_ordinates)
        print("Poorly conditioned or singular matrix, returning NaNs")
        return np.nan * np.ones((4, 4))

    def get_matrix(
        self,
        R,
        T,
        weighted_absolutes=None,
        weighted_ordinates=None,
    ):
        return [
            [R[0, 0], R[0, 1], R[0, 2], T[0]],
            [R[1, 0], R[1, 1], R[1, 2], T[1]],
            [R[2, 0], R[2, 1], R[2, 2], T[2]],
            [0.0, 0.0, 0.0, 1.0],
        ]

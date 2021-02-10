import numpy as np
from typing import List, Optional, Tuple

from .Transform import Transform


class SVD(Transform):
    """Instance of Transform. Applies singular value decomposition to generate matrices"""

    def calculate(
        self,
        ordinates: Tuple[List[float], List[float], List[float]],
        absolutes: Tuple[List[float], List[float], List[float]],
        weights: List[float],
    ) -> np.array:
        """Calculates matrix with singular value decomposition and accompanying methods
        Defaults to singular value decomposition constrained for 3D rotation/translation
        """
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

    def get_covariance_matrix(
        self,
        absolutes: Tuple[List[float], List[float], List[float]],
        ordinates: Tuple[List[float], List[float], List[float]],
        weights: List[float],
    ) -> List[List[float]]:
        """ calculate covariance matrix with weighted absolutes/ordinates """
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

    def get_matrix(
        self,
        R: List[List[float]],
        T: List[List[float]],
        weighted_absolutes: Optional[
            Tuple[List[float], List[float], List[float]]
        ] = None,
        weighted_ordinates: Optional[
            Tuple[List[float], List[float], List[float]]
        ] = None,
    ) -> np.array:
        """Returns matrix formatted for 3D rotation/translation
        NOTE: weighted absolutes/ordinates are only used by RotationTranslationXY's child function
        """
        return [
            [R[0, 0], R[0, 1], R[0, 2], T[0]],
            [R[1, 0], R[1, 1], R[1, 2], T[1]],
            [R[2, 0], R[2, 1], R[2, 2], T[2]],
            [0.0, 0.0, 0.0, 1.0],
        ]

    def get_rotation_matrix(
        self, U: List[List[float]], Vh: List[List[float]]
    ) -> List[List[float]]:
        """ computes rotation matrix from products of singular value decomposition """
        return np.dot(
            Vh.T, np.dot(np.diag([1, 1, np.linalg.det(np.dot(Vh.T, U.T))]), U.T)
        )

    def get_stacked_values(
        self,
        values: Tuple[List[float], List[float], List[float]],
        weighted_values: Tuple[List[float], List[float], List[float]],
    ) -> np.array:
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

    def get_translation_matrix(
        self,
        R: List[List[float]],
        weighted_absolutes: Tuple[List[float], List[float], List[float]],
        weighted_ordinates: Tuple[List[float], List[float], List[float]],
    ) -> List[List[float]]:
        """ computes translation matrix from rotation matrix and weighted absolutes/ordinates """
        return np.array([weighted_absolutes[i] for i in range(self.ndims)]) - np.dot(
            R, [weighted_ordinates[i] for i in range(self.ndims)]
        )

    def get_weighted_values(
        self,
        values: Tuple[List[float], List[float], List[float]],
        weights: Optional[List[float]],
    ) -> Tuple[float, float, float]:
        """Application of weights for SVD methods, which call for weighted averages"""
        if weights is None:
            weights = np.ones_like(values[0])
        return (
            np.average(values[0], weights=weights),
            np.average(values[1], weights=weights),
            np.average(values[2], weights=weights),
        )

    def valid(self, singular_values: List[float]) -> bool:
        """ validates whether or not a matrix can reliably transform the method's number of dimensions """
        if np.sum(singular_values) < self.ndims:
            return False
        return True

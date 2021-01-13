import numpy as np
from typing import List, Tuple, Optional
import scipy.linalg as spl
from obspy import UTCDateTime


class Transform(object):
    def __init__(self, memory=np.inf):
        self.memory = memory

    def get_weights(self, times: UTCDateTime, time: int = None) -> List[float]:
        """
        Calculate time-dependent weights according to exponential decay.

        Inputs:
        times     - 1D array of times, or any time-like index whose
                    relative values represent spacing between events
        memory    - exp(-1) time scale; weights will be ~37% of max
                    weight when time difference equals memory, and ~5%
                    of max weight when time difference is 3X memory

        Options:
        epoch     - time at which weights maximize
                    (default = max(times))

        Outout:
        weights - an M element array of vector distances/metrics

        NOTE:  ObsPy UTCDateTime objects can be passed in times, but
            memory must then be specified in seconds
        FIXME: Python datetime objects not supported yet

        """

        # convert to array of floats
        # (allows UTCDateTimes, but not datetime.datetimes)
        times = np.asarray(times).astype(float)

        if time is None:
            time = float(max(times))

        # if memory is actually infinite, return equal weights
        if np.isinf(self.memory):
            return np.ones(times.shape)

        # initialize weights
        weights = np.zeros(times.shape)

        # calculate exponential decay time-dependent weights
        weights[times <= time] = np.exp((times[times <= time] - time) / self.memory)
        weights[times >= time] = np.exp((time - times[times >= time]) / self.memory)

        return weights

    def calculate(
        self,
        ordinates: Tuple[List[float], List[float], List[float]],
        absolutes: Tuple[List[float], List[float], List[float]],
        weights: List[float],
    ) -> np.array:
        return


class LeastSq(Transform):
    def get_stacked_absolutes(self, absolutes):
        return np.vstack([absolutes[0], absolutes[1], absolutes[2]]).T.ravel()

    def get_weighted_values(
        self,
        values: Tuple[List[float], List[float], List[float]],
        weights: Optional[List[float]],
    ):
        if weights is None:
            return values
        weights = np.sqrt(weights)
        return (
            values[0] * weights,
            values[1] * weights,
            values[2] * weights,
        )


class SingularValueDecomposition(Transform):
    def get_stacked_values(self, values, weighted_values, ndims=3):
        return np.vstack([[values[i] - weighted_values[i]] for i in range(ndims)])

    def get_weighted_values(
        self,
        values: Tuple[List[float], List[float], List[float]],
        weights: Optional[List[float]],
    ):
        if weights is None:
            weights = np.ones_like(values[0])
        return (
            np.average(values[0], weights=weights),
            np.average(values[1], weights=weights),
            np.average(values[2], weights=weights),
        )


class NoConstraints(LeastSq):
    def calculate(
        self,
        ordinates: Tuple[List[float], List[float], List[float]],
        absolutes: Tuple[List[float], List[float], List[float]],
        weights: List[float],
    ) -> np.array:
        ordinates = self.get_weighted_values(ordinates, weights)
        absolutes = self.get_weighted_values(absolutes, weights)
        # LHS, or dependent variables
        #
        # [A[0,0], A[1,0], A[2,0], A[0,1], A[1,1], A[2,1], ...]
        abs_stacked = self.get_stacked_absolutes(absolutes)
        # return generate_affine_0(ord_hez, abs_xyz, weights)
        # RHS, or independent variables
        # (reduces degrees of freedom by 4:
        #  - 4 for the last row of zeros and a one)
        # [
        # [o[0,0], 0, 0, o[0,1], 0, 0, ...],
        # [0, o[1,0], 0, 0, o[1,1], 0, ...],
        # [0, 0, o[2,0], 0, 0, o[2,1], ...],
        # ...
        # ]
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

        # regression matrix M that minimizes L2 norm
        M_r, res, rank, sigma = spl.lstsq(ord_stacked.T, abs_stacked.T)

        if rank < 3:
            print("Poorly conditioned or singular matrix, returning NaNs")
            return np.nan * np.ones((4, 4))
        return np.array(
            [
                [M_r[0], M_r[1], M_r[2], M_r[3]],
                [M_r[4], M_r[5], M_r[6], M_r[7]],
                [M_r[8], M_r[9], M_r[10], M_r[11]],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )


class ZRotationShear(LeastSq):
    def calculate(
        self,
        ordinates: Tuple[List[float], List[float], List[float]],
        absolutes: Tuple[List[float], List[float], List[float]],
        weights: List[float],
    ) -> np.array:
        ordinates = self.get_weighted_values(ordinates, weights)
        absolutes = self.get_weighted_values(absolutes, weights)
        # LHS, or dependent variables
        #
        abs_stacked = self.get_stacked_absolutes(absolutes)
        # return generate_affine_1(ord_hez, abs_xyz, weights)
        # RHS, or independent variables
        # (reduces degrees of freedom by 8:
        #  - 2 for making x,y independent of z;
        #  - 2 for making z independent of x,y
        #  - 4 for the last row of zeros and a one)
        ord_stacked = np.zeros((8, len(ordinates[0]) * 3))
        ord_stacked[0, 0::3] = ordinates[0]
        ord_stacked[1, 0::3] = ordinates[1]
        ord_stacked[2, 0::3] = 1.0
        ord_stacked[3, 1::3] = ordinates[0]
        ord_stacked[4, 1::3] = ordinates[1]
        ord_stacked[5, 1::3] = 1.0
        ord_stacked[6, 2::3] = ordinates[2]
        ord_stacked[7, 2::3] = 1.0

        # regression matrix M that minimizes L2 norm
        M_r, res, rank, sigma = spl.lstsq(ord_stacked.T, abs_stacked.T)

        if rank < 3:
            print("Poorly conditioned or singular matrix, returning NaNs")
            return np.nan * np.ones((4, 4))

        return [
            [M_r[0], M_r[1], 0.0, M_r[2]],
            [M_r[3], M_r[4], 0.0, M_r[5]],
            [0.0, 0.0, M_r[6], M_r[7]],
            [0.0, 0.0, 0.0, 1.0],
        ]


class ZRotationHscale(LeastSq):
    def calculate(
        self,
        ordinates: Tuple[List[float], List[float], List[float]],
        absolutes: Tuple[List[float], List[float], List[float]],
        weights: List[float],
    ) -> np.array:
        ordinates = self.get_weighted_values(ordinates, weights)
        absolutes = self.get_weighted_values(absolutes, weights)
        # LHS, or dependent variables
        #
        abs_stacked = self.get_stacked_absolutes(absolutes)
        # RHS, or independent variables
        # (reduces degrees of freedom by 10:
        #  - 2 for making x,y independent of z;
        #  - 2 for making z independent of x,y
        #  - 2 for not allowing shear in x,y; and
        #  - 4 for the last row of zeros and a one)
        ord_stacked = np.zeros((6, len(ordinates[0]) * 3))
        ord_stacked[0, 0::3] = ordinates[0]
        ord_stacked[0, 1::3] = ordinates[1]
        ord_stacked[1, 0::3] = ordinates[1]
        ord_stacked[1, 1::3] = -ordinates[0]
        ord_stacked[2, 0::3] = 1.0
        ord_stacked[3, 1::3] = 1.0
        ord_stacked[4, 2::3] = ordinates[2]
        ord_stacked[5, 2::3] = 1.0

        # regression matrix M that minimizes L2 norm
        M_r, res, rank, sigma = spl.lstsq(ord_stacked.T, abs_stacked.T)

        if rank < 3:
            print("Poorly conditioned or singular matrix, returning NaNs")
            return np.nan * np.ones((4, 4))

        return [
            [M_r[0], M_r[1], 0.0, M_r[2]],
            [-M_r[1], M_r[0], 0.0, M_r[3]],
            [0.0, 0.0, M_r[4], M_r[5]],
            [0.0, 0.0, 0.0, 1.0],
        ]


class ZRotationHscaleZbaseline(LeastSq):
    def rotate_values(self, values):
        return (
            np.sqrt(values[0] ** 2 + values[1] ** 2),
            np.arctan2(values[1], values[0]),
            values[2],
        )

    def calculate(
        self,
        ordinates: Tuple[List[float], List[float], List[float]],
        absolutes: Tuple[List[float], List[float], List[float]],
        weights: List[float],
    ) -> np.array:
        # RHS, or independent variables
        # (reduces degrees of freedom by 13:
        #  - 2 for making x,y independent of z;
        #  - 2 for making z independent of x,y;
        #  - 2 for not allowing shear in x,y;
        #  - 2 for not allowing translation in x,y;
        #  - 1 for not allowing scaling in z; and
        #  - 4 for the last row of zeros and a one)
        ord_stacked = np.zeros((3, len(ordinates[0]) * 3))
        ord_stacked[0, 0::3] = ordinates[0]
        ord_stacked[0, 1::3] = ordinates[1]
        ord_stacked[1, 0::3] = ordinates[1]
        ord_stacked[1, 1::3] = -ordinates[0]
        ord_stacked[2, 2::3] = 1.0

        # subtract z_o from z_a to force simple z translation
        abs_stacked = self.get_stacked_absolutes(absolutes)
        abs_stacked[2::3] = absolutes[2] - ordinates[2]

        abs_stacked = self.get_weighted_values(values=abs_stacked, weights=weights)
        ord_stacked = self.get_weighted_values(values=ord_stacked, weights=weights)

        # regression matrix M that minimizes L2 norm
        M_r, res, rank, sigma = spl.lstsq(ord_stacked.T, abs_stacked.T)

        if rank < 3:
            print("Poorly conditioned or singular matrix, returning NaNs")
            return np.nan * np.ones((4, 4))

        return [
            [M_r[0], M_r[1], 0.0, 0.0],
            [-M_r[1], M_r[0], 0.0, 0.0],
            [0.0, 0.0, 1.0, M_r[2]],
            [0.0, 0.0, 0.0, 1.0],
        ]


class RotationTranslation3D(SingularValueDecomposition):
    def calculate(
        self,
        ordinates: Tuple[List[float], List[float], List[float]],
        absolutes: Tuple[List[float], List[float], List[float]],
        weights: List[float],
    ) -> np.array:
        weighted_ordinates = self.get_weighted_values(values=ordinates, weights=weights)
        weighted_absolutes = self.get_weighted_values(values=absolutes, weights=weights)
        # generate weighted "covariance" matrix
        H = np.dot(
            self.get_stacked_values(
                values=ordinates,
                weighted_values=weighted_ordinates,
                ndims=3,
            ),
            self.get_stacked_values(
                values=absolutes,
                weighted_values=weighted_absolutes,
                ndims=3,
            ).T,
        )
        # Singular value decomposition, then rotation matrix from L&R eigenvectors
        # (the determinant guarantees a rotation, and not a reflection)
        U, S, Vh = np.linalg.svd(H)

        if np.sum(S) < 3:
            print("Poorly conditioned or singular matrix, returning NaNs")
            return np.nan * np.ones((4, 4))

        R = np.dot(Vh.T, np.dot(np.diag([1, 1, np.linalg.det(np.dot(Vh.T, U.T))]), U.T))

        # now get translation using weighted centroids and R
        T = np.array(
            [weighted_absolutes[0], weighted_absolutes[1], weighted_absolutes[2]]
        ) - np.dot(
            R, [weighted_ordinates[0], weighted_ordinates[1], weighted_ordinates[2]]
        )

        return [
            [R[0, 0], R[0, 1], R[0, 2], T[0]],
            [R[1, 0], R[1, 1], R[1, 2], T[1]],
            [R[2, 0], R[2, 1], R[2, 2], T[2]],
            [0.0, 0.0, 0.0, 1.0],
        ]


class Rescale3D(LeastSq):
    def calculate(
        self,
        ordinates: Tuple[List[float], List[float], List[float]],
        absolutes: Tuple[List[float], List[float], List[float]],
        weights: List[float],
    ) -> np.array:
        absolutes = self.get_weighted_values(values=absolutes, weights=weights)
        ordinates = self.get_weighted_values(values=ordinates, weights=weights)
        abs_stacked = self.get_stacked_absolutes(absolutes=absolutes)
        # RHS, or independent variables
        # (reduces degrees of freedom by 13:
        #  - 2 for making x independent of y,z;
        #  - 2 for making y,z independent of x;
        #  - 1 for making y independent of z;
        #  - 1 for making z independent of y;
        #  - 3 for not translating xyz
        #  - 4 for the last row of zeros and a one)
        ord_stacked = np.zeros((3, len(ordinates[0]) * 3))
        ord_stacked[0, 0::3] = ordinates[0]
        ord_stacked[1, 1::3] = ordinates[1]
        ord_stacked[2, 2::3] = ordinates[2]

        # regression matrix M that minimizes L2 norm
        M_r, res, rank, sigma = spl.lstsq(ord_stacked.T, abs_stacked.T)

        if rank < 3:
            print("Poorly conditioned or singular matrix, returning NaNs")
            return np.nan * np.ones((4, 4))

        return [
            [M_r[0], 0.0, 0.0, 0.0],
            [0.0, M_r[1], 0.0, 0.0],
            [0.0, 0.0, M_r[2], 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]


class TranslateOrigins(LeastSq):
    def get_weighted_values(
        self,
        values: Tuple[List[float], List[float], List[float]],
        weights: Optional[List[float]],
    ):
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


class ShearYZ(LeastSq):
    def calculate(
        self,
        ordinates: Tuple[List[float], List[float], List[float]],
        absolutes: Tuple[List[float], List[float], List[float]],
        weights: List[float],
    ) -> np.array:
        ordinates = self.get_weighted_values(values=ordinates, weights=weights)
        # return generate_affine_7(ord_hez, abs_xyz, weights)
        # RHS, or independent variables
        # (reduces degrees of freedom by 13:
        #  - 2 for making x independent of y,z;
        #  - 1 for making y independent of z;
        #  - 3 for not scaling each axis
        #  - 4 for the last row of zeros and a one)
        ord_stacked = np.zeros((3, len(ordinates[0]) * 3))
        ord_stacked[0, 0::3] = 1.0
        ord_stacked[1, 0::3] = ordinates[0]
        ord_stacked[1, 1::3] = 1.0
        ord_stacked[2, 0::3] = ordinates[0]
        ord_stacked[2, 1::3] = ordinates[1]
        ord_stacked[2, 2::3] = 1.0

        # regression matrix M that minimizes L2 norm
        abs_stacked = self.get_stacked_absolutes(absolutes=absolutes)
        M_r, res, rank, sigma = spl.lstsq(ord_stacked.T, abs_stacked.T)

        if rank < 3:
            print("Poorly conditioned or singular matrix, returning NaNs")
            return np.nan * np.ones((4, 4))

        return [
            [1.0, 0.0, 0.0, 0.0],
            [M_r[0], 1.0, 0.0, 0.0],
            [M_r[1], M_r[2], 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]


class RotationTranslationXY(SingularValueDecomposition):
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


class QRFactorization(SingularValueDecomposition):
    def get_weighted_values_lstsq(
        self,
        values: Tuple[List[float], List[float], List[float]],
        weights: Optional[List[float]],
    ):
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

        # return generate_affine_9(ord_hez, abs_xyz, weights)
        # LHS, or dependent variables
        abs_stacked = self.get_stacked_values(
            values=absolutes,
            weighted_values=weighted_absolutes,
            ndims=2,
        )

        # RHS, or independent variables
        ord_stacked = self.get_stacked_values(
            values=ordinates,
            weighted_values=weighted_ordinates,
            ndims=2,
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

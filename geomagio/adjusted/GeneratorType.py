import enum
import numpy as np
import scipy.linalg as spl


class GeneratorType(str, enum.Enum):
    NO_CONSTRAINTS = "no constraints"
    Z_ROTATION = "z rotation"
    Z_ROTATION_HSCALE = "z rotation hscale"
    Z_ROTATION_HSCALE_ZBASELINE = "z rotation hscale zbaseline"
    ROTATION_TRANSLATION_3D = "rotation translation 3D"
    RESCALE_3D = "rescale 3D"
    TRANSLATE_ORIGINS = "translate origins"
    SHEAR_YZ = "shear yz"
    ROTATION_TRANSLATION_XY = "rotation translation xy"
    QR_FACTORIZATION = "QR factorization"

    def calculate_matrix(self, ord_hez, abs_xyz, weights):

        # extract measurements
        h_o = ord_hez[0]
        e_o = ord_hez[1]
        z_o = ord_hez[2]
        x_a = abs_xyz[0]
        y_a = abs_xyz[1]
        z_a = abs_xyz[2]

        if self in [
            GeneratorType.NO_CONSTRAINTS,
            GeneratorType.Z_ROTATION,
            GeneratorType.Z_ROTATION_HSCALE,
            GeneratorType.Z_ROTATION_HSCALE_ZBASELINE,
            GeneratorType.RESCALE_3D,
            GeneratorType.TRANSLATE_ORIGINS,
            GeneratorType.SHEAR_YZ,
        ]:
            if weights is not None:
                weights = np.sqrt(weights)
                weights = np.vstack((weights, weights, weights)).T.ravel()

            else:
                weights = 1

            # LHS, or dependent variables
            abs_st = np.vstack([x_a, y_a, z_a])
            abs_st_r = abs_st.T.ravel()
            ord_st = np.vstack([h_o, e_o, z_o])
            ord_st_r = ord_st.T.ravel()
        if self in [
            GeneratorType.QR_FACTORIZATION,
            GeneratorType.ROTATION_TRANSLATION_3D,
            GeneratorType.ROTATION_TRANSLATION_XY,
        ]:
            if weights is None:
                # equal weighting
                weights = np.ones_like(ord_hez[0])

            # weighted centroids
            h_o_cent = np.average(h_o, weights=weights)
            e_o_cent = np.average(e_o, weights=weights)
            z_o_cent = np.average(z_o, weights=weights)
            x_a_cent = np.average(x_a, weights=weights)
            y_a_cent = np.average(y_a, weights=weights)
            z_a_cent = np.average(z_a, weights=weights)

        if self == GeneratorType.NO_CONSTRAINTS:
            # return generate_affine_0(ord_hez, abs_xyz, weights)
            # RHS, or independent variables
            # (reduces degrees of freedom by 4:
            #  - 4 for the last row of zeros and a one)
            ord_st_m = np.zeros((12, ord_st_r.size))
            ord_st_m[0, 0::3] = ord_st_r[0::3]
            ord_st_m[1, 0::3] = ord_st_r[1::3]
            ord_st_m[2, 0::3] = ord_st_r[2::3]
            ord_st_m[3, 0::3] = 1.0
            ord_st_m[4, 1::3] = ord_st_r[0::3]
            ord_st_m[5, 1::3] = ord_st_r[1::3]
            ord_st_m[6, 1::3] = ord_st_r[2::3]
            ord_st_m[7, 1::3] = 1.0
            ord_st_m[8, 2::3] = ord_st_r[0::3]
            ord_st_m[9, 2::3] = ord_st_r[1::3]
            ord_st_m[10, 2::3] = ord_st_r[2::3]
            ord_st_m[11, 2::3] = 1.0

            # apply weights
            ord_st_m = ord_st_m * weights
            abs_st_r = abs_st_r * weights

            # regression matrix M that minimizes L2 norm
            M_r, res, rank, sigma = spl.lstsq(ord_st_m.T, abs_st_r.T)

            if rank < 3:
                print("Poorly conditioned or singular matrix, returning NaNs")
                return np.nan * np.ones((4, 4))
            return [
                [M_r[0], M_r[1], M_r[2], M_r[3]],
                [M_r[4], M_r[5], M_r[6], M_r[7]],
                [M_r[8], M_r[9], M_r[10], M_r[11]],
                [0.0, 0.0, 0.0, 1.0],
            ]
        if self == GeneratorType.Z_ROTATION:
            # return generate_affine_1(ord_hez, abs_xyz, weights)
            # RHS, or independent variables
            # (reduces degrees of freedom by 8:
            #  - 2 for making x,y independent of z;
            #  - 2 for making z independent of x,y
            #  - 4 for the last row of zeros and a one)
            ord_st_m = np.zeros((8, ord_st_r.size))
            ord_st_m[0, 0::3] = ord_st_r[0::3]
            ord_st_m[1, 0::3] = ord_st_r[1::3]
            ord_st_m[2, 0::3] = 1.0
            ord_st_m[3, 1::3] = ord_st_r[0::3]
            ord_st_m[4, 1::3] = ord_st_r[1::3]
            ord_st_m[5, 1::3] = 1.0
            ord_st_m[6, 2::3] = ord_st_r[2::3]
            ord_st_m[7, 2::3] = 1.0

            # apply weights
            ord_st_m = ord_st_m * weights
            abs_st_r = abs_st_r * weights

            # regression matrix M that minimizes L2 norm
            M_r, res, rank, sigma = spl.lstsq(ord_st_m.T, abs_st_r.T)

            if rank < 3:
                print("Poorly conditioned or singular matrix, returning NaNs")
                return np.nan * np.ones((4, 4))

            return [
                [M_r[0], M_r[1], 0.0, M_r[2]],
                [M_r[3], M_r[4], 0.0, M_r[5]],
                [0.0, 0.0, M_r[6], M_r[7]],
                [0.0, 0.0, 0.0, 1.0],
            ]
        if self == GeneratorType.Z_ROTATION_HSCALE:
            # return generate_affine_2(ord_hez, abs_xyz, weights)
            # RHS, or independent variables
            # (reduces degrees of freedom by 10:
            #  - 2 for making x,y independent of z;
            #  - 2 for making z independent of x,y
            #  - 2 for not allowing shear in x,y; and
            #  - 4 for the last row of zeros and a one)
            ord_st_m = np.zeros((6, ord_st_r.size))
            ord_st_m[0, 0::3] = ord_st_r[0::3]
            ord_st_m[0, 1::3] = ord_st_r[1::3]
            ord_st_m[1, 0::3] = ord_st_r[1::3]
            ord_st_m[1, 1::3] = -ord_st_r[0::3]
            ord_st_m[2, 0::3] = 1.0
            ord_st_m[3, 1::3] = 1.0
            ord_st_m[4, 2::3] = ord_st_r[2::3]
            ord_st_m[5, 2::3] = 1.0

            # apply weights
            ord_st_m = ord_st_m * weights
            abs_st_r = abs_st_r * weights

            # regression matrix M that minimizes L2 norm
            M_r, res, rank, sigma = spl.lstsq(ord_st_m.T, abs_st_r.T)

            if rank < 3:
                print("Poorly conditioned or singular matrix, returning NaNs")
                return np.nan * np.ones((4, 4))

            return [
                [M_r[0], M_r[1], 0.0, M_r[2]],
                [-M_r[1], M_r[0], 0.0, M_r[3]],
                [0.0, 0.0, M_r[4], M_r[5]],
                [0.0, 0.0, 0.0, 1.0],
            ]
        if self == GeneratorType.Z_ROTATION_HSCALE_ZBASELINE:
            # return generate_affine_3(ord_hez, abs_xyz, weights)
            # re-estimate cylindrical vectors from Cartesian
            h_ord = np.sqrt(h_o ** 2 + e_o ** 2)
            d_ord = np.arctan2(e_o, h_o)
            z_ord = z_o
            h_abs = np.sqrt(x_a ** 2 + y_a ** 2)
            d_abs = np.arctan2(y_a, x_a)
            z_abs = z_a

            # generate average rotation from ord to abs, then convert
            # to rotation affine transform matrix
            dRavg = (d_abs - d_ord).mean()
            Rmtx = np.eye(4)
            Rmtx[0, 0] = np.cos(dRavg)
            Rmtx[0, 1] = -np.sin(dRavg)
            Rmtx[1, 0] = np.sin(dRavg)
            Rmtx[1, 1] = np.cos(dRavg)

            # generate average ratio of h_abs/h_ord, use this to
            # define a scaling affine transform matrix
            rHavg = (h_abs / h_ord).mean()
            Smtx = np.eye(4)
            Smtx[0, 0] = rHavg
            Smtx[1, 1] = rHavg

            # apply average rotations and scales to HE data, determine the
            # average translations, then generate affine transform matrix
            dXavg = (
                x_a - (h_o * rHavg * np.cos(dRavg) - e_o * rHavg * np.sin(dRavg))
            ).mean()
            dYavg = (
                y_a - (h_o * rHavg * np.sin(dRavg) + e_o * rHavg * np.cos(dRavg))
            ).mean()
            dZavg = (z_a - z_o).mean()
            Tmtx = np.eye(4)
            Tmtx[0, 3] = dXavg
            Tmtx[1, 3] = dYavg
            Tmtx[2, 3] = dZavg

            # combine rotation, scale, and translation matrices
            M = np.dot(np.dot(Rmtx, Smtx), Tmtx)

            #     # NOTE: the preceding isn't quite how Definitive/Quasi-Definitive
            #     # processing works; the following is closer, but the two generate
            #     # very similar output, with most of the tiny discrepancy arising
            #     # due to the fact that the operation below *adds* an H baseline,
            #     # something that is not easy (or possible?) with an affine transform,
            #     # so instead, a scaling factor is used to adjust he to match xy.

            # RHS, or independent variables
            # (reduces degrees of freedom by 13:
            #  - 2 for making x,y independent of z;
            #  - 2 for making z independent of x,y;
            #  - 2 for not allowing shear in x,y;
            #  - 2 for not allowing translation in x,y;
            #  - 1 for not allowing scaling in z; and
            #  - 4 for the last row of zeros and a one)
            ord_st_m = np.zeros((3, ord_st_r.size))
            ord_st_m[0, 0::3] = ord_st_r[0::3]
            ord_st_m[0, 1::3] = ord_st_r[1::3]
            ord_st_m[1, 0::3] = ord_st_r[1::3]
            ord_st_m[1, 1::3] = -ord_st_r[0::3]
            ord_st_m[2, 2::3] = 1.0

            # subtract z_o from z_a to force simple z translation
            abs_st_r[2::3] = abs_st_r[2::3] - ord_st_r[2::3]

            # apply weights
            ord_st_m = ord_st_m * weights
            abs_st_r = abs_st_r * weights

            # regression matrix M that minimizes L2 norm
            M_r, res, rank, sigma = spl.lstsq(ord_st_m.T, abs_st_r.T)

            if rank < 3:
                print("Poorly conditioned or singular matrix, returning NaNs")
                return np.nan * np.ones((4, 4))

            return [
                [M_r[0], M_r[1], 0.0, 0.0],
                [-M_r[1], M_r[0], 0.0, 0.0],
                [0.0, 0.0, 1.0, M_r[2]],
                [0.0, 0.0, 0.0, 1.0],
            ]
        if self == GeneratorType.ROTATION_TRANSLATION_3D:
            # return generate_affine_4(ord_hez, abs_xyz, weights)
            # generate weighted "covariance" matrix
            H = np.dot(
                np.vstack([h_o - h_o_cent, e_o - e_o_cent, z_o - z_o_cent]),
                np.dot(
                    np.diag(weights),
                    np.vstack([x_a - x_a_cent, y_a - y_a_cent, z_a - z_a_cent]).T,
                ),
            )

            # Singular value decomposition, then rotation matrix from L&R eigenvectors
            # (the determinant guarantees a rotation, and not a reflection)
            U, S, Vh = np.linalg.svd(H)

            if np.sum(S) < 3:
                print("Poorly conditioned or singular matrix, returning NaNs")
                return np.nan * np.ones((4, 4))

            R = np.dot(
                Vh.T, np.dot(np.diag([1, 1, np.linalg.det(np.dot(Vh.T, U.T))]), U.T)
            )

            # now get translation using weighted centroids and R
            T = np.array([x_a_cent, y_a_cent, z_a_cent]) - np.dot(
                R, [h_o_cent, e_o_cent, z_o_cent]
            )

            return [
                [R[0, 0], R[0, 1], R[0, 2], T[0]],
                [R[1, 0], R[1, 1], R[1, 2], T[1]],
                [R[2, 0], R[2, 1], R[2, 2], T[2]],
                [0.0, 0.0, 0.0, 1.0],
            ]
        if self == GeneratorType.RESCALE_3D:
            # return generate_affine_5(ord_hez, abs_xyz, weights)
            # RHS, or independent variables
            # (reduces degrees of freedom by 13:
            #  - 2 for making x independent of y,z;
            #  - 2 for making y,z independent of x;
            #  - 1 for making y independent of z;
            #  - 1 for making z independent of y;
            #  - 3 for not translating xyz
            #  - 4 for the last row of zeros and a one)
            ord_st_m = np.zeros((3, ord_st_r.size))
            ord_st_m[0, 0::3] = ord_st_r[0::3]
            ord_st_m[1, 1::3] = ord_st_r[1::3]
            ord_st_m[2, 2::3] = ord_st_r[2::3]

            # apply weights
            ord_st_m = ord_st_m * weights

            # regression matrix M that minimizes L2 norm
            M_r, res, rank, sigma = spl.lstsq(ord_st_m.T, abs_st_r.T)

            if rank < 3:
                print("Poorly conditioned or singular matrix, returning NaNs")
                return np.nan * np.ones((4, 4))

            return [
                [M_r[0], 0.0, 0.0, 0.0],
                [0.0, M_r[1], 0.0, 0.0],
                [0.0, 0.0, M_r[2], 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        if self == GeneratorType.TRANSLATE_ORIGINS:
            # return generate_affine_6(ord_hez, abs_xyz, weights)
            # RHS, or independent variables
            # (reduces degrees of freedom by 10:
            #  - 2 for making x independent of y,z;
            #  - 2 for making y,z independent of x;
            #  - 1 for making y independent of z;
            #  - 1 for making z independent of y;
            #  - 3 for not scaling each axis
            #  - 4 for the last row of zeros and a one)
            ord_st_m = np.zeros((3, ord_st_r.size))
            ord_st_m[0, 0::3] = 1.0
            ord_st_m[1, 1::3] = 1.0
            ord_st_m[2, 2::3] = 1.0

            # subtract ords from abs to force simple translation
            abs_st_r[0::3] = abs_st_r[0::3] - ord_st_r[0::3]
            abs_st_r[1::3] = abs_st_r[1::3] - ord_st_r[1::3]
            abs_st_r[2::3] = abs_st_r[2::3] - ord_st_r[2::3]

            # apply weights
            ord_st_m = ord_st_m * weights
            abs_st_r = abs_st_r * weights

            # regression matrix M that minimizes L2 norm
            M_r, res, rank, sigma = spl.lstsq(ord_st_m.T, abs_st_r.T)

            if rank < 3:
                print("Poorly conditioned or singular matrix, returning NaNs")
                return np.nan * np.ones((4, 4))

            return [
                [1.0, 0.0, 0.0, M_r[0]],
                [0.0, 1.0, 0.0, M_r[1]],
                [0.0, 0.0, 1.0, M_r[2]],
                [0.0, 0.0, 0.0, 1.0],
            ]
        if self == GeneratorType.SHEAR_YZ:
            # return generate_affine_7(ord_hez, abs_xyz, weights)
            # RHS, or independent variables
            # (reduces degrees of freedom by 13:
            #  - 2 for making x independent of y,z;
            #  - 1 for making y independent of z;
            #  - 3 for not scaling each axis
            #  - 4 for the last row of zeros and a one)
            ord_st_m = np.zeros((3, ord_st_r.size))
            ord_st_m[0, 0::3] = 1.0
            ord_st_m[1, 0::3] = ord_st_r[0::3]
            ord_st_m[1, 1::3] = 1.0
            ord_st_m[2, 0::3] = ord_st_r[0::3]
            ord_st_m[2, 1::3] = ord_st_r[1::3]
            ord_st_m[2, 2::3] = 1.0

            # apply weights
            ord_st_m = ord_st_m * weights

            # regression matrix M that minimizes L2 norm
            M_r, res, rank, sigma = spl.lstsq(ord_st_m.T, abs_st_r.T)

            if rank < 3:
                print("Poorly conditioned or singular matrix, returning NaNs")
                return np.nan * np.ones((4, 4))

            return [
                [1.0, 0.0, 0.0, 0.0],
                [M_r[0], 1.0, 0.0, 0.0],
                [M_r[1], M_r[2], 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        if self == GeneratorType.ROTATION_TRANSLATION_XY:
            # return generate_affine_8(ord_hez, abs_xyz, weights)
            # generate weighted "covariance" matrix
            H = np.dot(
                np.vstack([h_o - h_o_cent, e_o - e_o_cent]),
                np.dot(np.diag(weights), np.vstack([x_a - x_a_cent, y_a - y_a_cent]).T),
            )

            # Singular value decomposition, then rotation matrix from L&R eigenvectors
            # (the determinant guarantees a rotation, and not a reflection)
            U, S, Vh = np.linalg.svd(H)

            if np.sum(S) < 2:
                print("Poorly conditioned or singular matrix, returning NaNs")
                return np.nan * np.ones((4, 4))

            R = np.dot(
                Vh.T, np.dot(np.diag([1, np.linalg.det(np.dot(Vh.T, U.T))]), U.T)
            )

            # now get translation using weighted centroids and R
            T = np.array([x_a_cent, y_a_cent]) - np.dot(R, [h_o_cent, e_o_cent])

            return [
                [R[0, 0], R[0, 1], 0.0, T[0]],
                [R[1, 0], R[1, 1], 0.0, T[1]],
                [0.0, 0.0, 1.0, np.array(z_a_cent) - np.array(z_o_cent)],
                [0.0, 0.0, 0.0, 1.0],
            ]
        if self == GeneratorType.QR_FACTORIZATION:
            # return generate_affine_9(ord_hez, abs_xyz, weights)
            # LHS, or dependent variables
            abs_st = np.vstack([x_a - x_a_cent, y_a - y_a_cent])

            # RHS, or independent variables
            ord_st = np.vstack([h_o - h_o_cent, e_o - e_o_cent])

            # apply weights
            ord_st = ord_st * np.sqrt(weights)
            abs_st = abs_st * np.sqrt(weights)

            # regression matrix M that minimizes L2 norm
            M_r, res, rank, sigma = spl.lstsq(ord_st.T, abs_st.T)

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
            T = np.array([x_a_cent, y_a_cent]) - np.dot(QH, [h_o_cent, e_o_cent])

            return [
                [QH[0, 0], QH[0, 1], 0.0, T[0]],
                [QH[1, 0], QH[1, 1], 0.0, T[1]],
                [0.0, 0.0, 1.0, np.array(z_a_cent) - np.array(z_o_cent)],
                [0.0, 0.0, 0.0, 1.0],
            ]

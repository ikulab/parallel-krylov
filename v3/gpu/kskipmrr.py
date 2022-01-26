from numpy import float64
import cupy as cp
from cupy import dot
from cupy.linalg import norm

from .common import start, finish, init, MultiGpu


def kskipmrr(A, b, x=None, tol=1e-05, maxiter=None, k=0, M=None, callback=None, atol=None) -> tuple:
    # 初期化
    T = float64
    MultiGpu.init()
    b, x, maxiter, b_norm, N, residual, num_of_solution_updates = init(b, x, maxiter)
    MultiGpu.alloc(A, b, T)

    Ar = cp.zeros((k + 2, N), T)
    Ay = cp.zeros((k + 1, N), T)
    alpha = cp.zeros(2 * k + 3, T)
    beta = cp.zeros(2 * k + 2, T)
    delta = cp.zeros(2 * k + 1, T)

    # 初期残差
    Ar[0] = b - MultiGpu.dot(A, x)
    residual[0] = norm(Ar[0]) / b_norm

    # 初期反復
    start_time = start(method_name='k-skip MrR + GPU', k=k)
    Ar[1] = MultiGpu.dot(A, Ar[0])
    zeta = dot(Ar[0], Ar[1]) / dot(Ar[1], Ar[1])
    Ay[0] = zeta * Ar[1]
    z = -zeta * Ar[0]
    Ar[0] -= Ay[0]
    x -= z
    num_of_solution_updates[1] = 1
    i = 1
    index = 1

    # 反復計算
    while i < maxiter:
        # 収束判定
        residual[index] = norm(Ar[0]) / b_norm
        if residual[index] < tol:
            isConverged = True
            break

        # 基底計算
        for j in range(1, k + 2):
            Ar[j] = MultiGpu.dot(A, Ar[j-1])
        for j in range(1, k + 1):
            Ay[j] = MultiGpu.dot(A, Ay[j-1])

        # 係数計算
        for j in range(2 * k + 3):
            jj = j // 2
            alpha[j] = dot(Ar[jj], Ar[jj + j % 2])
        for j in range(1, 2 * k + 2):
            jj = j//2
            beta[j] = dot(Ay[jj], Ar[jj + j % 2])
        for j in range(2 * k + 1):
            jj = j // 2
            delta[j] = dot(Ay[jj], Ay[jj + j % 2])

        # MrRでの1反復(解の更新)
        d = alpha[2] * delta[0] - beta[1] ** 2
        zeta = alpha[1] * delta[0] / d
        eta = -alpha[1] * beta[1] / d
        Ay[0] = eta * Ay[0] + zeta * Ar[1]
        z = eta * z - zeta * Ar[0]
        Ar[0] -= Ay[0]
        Ar[1] = MultiGpu.dot(A, Ar[0])
        x -= z

        # MrRでのk反復
        for j in range(k):
            delta[0] = zeta ** 2 * alpha[2] + eta * zeta * beta[1]
            alpha[0] -= zeta * alpha[1]
            delta[1] = eta ** 2 * delta[1] + 2 * eta * \
                zeta * beta[2] + zeta ** 2 * alpha[3]
            beta[1] = eta * beta[1] + zeta * alpha[2] - delta[1]
            alpha[1] = -beta[1]
            for l in range(2, 2 * (k - j) + 1):
                delta[l] = eta ** 2 * delta[l] + 2 * eta * \
                    zeta * beta[l+1] + zeta ** 2 * alpha[l + 2]
                tau = eta * beta[l] + zeta * alpha[l + 1]
                beta[l] = tau - delta[l]
                alpha[l] -= tau + beta[l]
            # 解の更新
            d = alpha[2] * delta[0] - beta[1] ** 2
            zeta = alpha[1] * delta[0] / d
            eta = -alpha[1] * beta[1] / d
            Ay[0] = eta * Ay[0] + zeta * Ar[1]
            z = eta * z - zeta * Ar[0]
            Ar[0] -= Ay[0]
            Ar[1] = MultiGpu.dot(A, Ar[0])
            x -= z

        i += (k + 1)
        index += 1
        num_of_solution_updates[index] = i
    else:
        isConverged = False
        residual[index] = norm(Ar[0]) / b_norm

    elapsed_time = finish(start_time, isConverged, i, residual[index])
    info = {
        'time': elapsed_time,
        'nosl': num_of_solution_updates[:index+1],
        'residual': residual[:index+1],
    }
    return x, info

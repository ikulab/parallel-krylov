import cupy as cp
from cupy import dot
from cupy.linalg import norm

from ..common import start, end
from .common import init


def k_skip_cg(A, b, epsilon, k, T=cp.float64):
    """[summary]

    Args:
        A (np.ndarray): 係数行列A
        b (np.ndarray): bベクトル
        epsilon (float): 収束判定子
        k (int): k
        T ([type], optional): 浮動小数精度 Defaults to np.float64.

    Returns:
        float: 経過時間
        np.ndarray: 残差更新履歴
        np.ndarray: 残差履歴
    """
    # 初期化
    A, b, x, b_norm, N, max_iter, residual, num_of_solution_updates = init(A, b, T)
    Ar = cp.zeros((k + 2, N), T)
    Ap = cp.zeros((k + 3, N), T)
    a = cp.zeros(2 * k + 2, T)
    f = cp.zeros(2 * k + 4, T)
    c = cp.zeros(2 * k + 2, T)

    # 初期残差
    Ar[0] = b - dot(A, x)
    Ap[0] = Ar[0]

    # 反復計算
    start_time = start(method_name='k-skip CG', k=k)
    for i in range(0, max_iter):
        # 収束判定
        residual[i] = norm(Ar[0]) / b_norm
        if residual[i] < epsilon:
            isConverged = True
            break

        # 事前計算
        for j in range(1, k + 1):
            Ar[j] = dot(A, Ar[j-1])
        for j in range(1, k + 2):
            Ap[j] = dot(A, Ap[j-1])
        for j in range(2 * k + 1):
            jj = j // 2
            a[j] = dot(Ar[jj], Ar[jj + j % 2])
        for j in range(2 * k + 4):
            jj = j // 2
            f[j] = dot(Ap[jj], Ap[jj + j % 2])
        for j in range(2 * k + 2):
            jj = j // 2
            c[j] = dot(Ar[jj], Ap[jj + j % 2])

        # CGでの1反復
        alpha = a[0] / f[1]
        beta = alpha ** 2 * f[2] / a[0] - 1
        x += alpha * Ap[0]
        Ar[0] -= alpha * Ap[1]
        Ap[0] = Ar[0] + beta * Ap[0]
        Ap[1] = dot(A, Ap[0])

        # CGでのk反復
        for j in range(0, k):
            for l in range(0, 2*(k-j)+1):
                a[l] += alpha*(alpha*f[l+2] - 2*c[l+1])
                d = c[l] - alpha*f[l+1]
                c[l] = a[l] + d*beta
                f[l] = c[l] + beta*(d + beta*f[l])

            # 解の更新
            alpha = a[0] / f[1]
            beta = alpha ** 2 * f[2] / a[0] - 1
            x += alpha * Ap[0]
            Ar[0] -= alpha * Ap[1]
            Ap[0] = Ar[0] + beta * Ap[0]
            Ap[1] = dot(A, Ap[0])

        num_of_solution_updates[i+1] = num_of_solution_updates[i] + k + 1

    else:
        isConverged = False

    num_of_iter = i
    elapsed_time = end(start_time, isConverged, num_of_iter, residual[num_of_iter]) 

    return elapsed_time, num_of_solution_updates[:num_of_iter+1].get(), residual[:num_of_iter+1].get()

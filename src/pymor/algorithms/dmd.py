import numpy as np
import scipy.linalg as spla

from pymor.algorithms.svd_va import method_of_snapshots, qr_svd
from pymor.core.defaults import defaults
from pymor.core.logger import getLogger
from pymor.operators.constructions import LowRankOperator
from pymor.vectorarrays.interface import VectorArray


@defaults('svd_method')
def dmd(X, Y=None, svd_rank=None, dt=1, modes='exact', svd_method='qr_svd',
        return_A_approx=False, return_A_tilde=False):
    """Dynamic Mode Decomposition.

    See Algorithm 1 and Algorithm 2 in :cite:`TRLBK14`.

    Parameters
    ----------
    X
        The |VectorArray| for which the DMD algorithm is performed.
        If `Y` is given, `X` and `Y` are the left resp. right snapshot series.
    Y
        The |VectorArray| of the right snapshot series.
    svd_rank
        Number of DMD modes to be computed. If `None`, `svd_rank = len(X)`.
    dt
        Factor specifying the time difference between the observations, default `dt = 1`.
    modes
        - 'standard': uses the standard definition to compute the dynamic modes
            `Wk = U * evecs`, where `U` are the left singular vectors of `X`.
        - 'exact' : computes the exact dynamic modes, `Wk = (1/evals) * Y * V * Sigma_inv * evecs`.
    svd_method
        Which SVD method from :mod:`~pymor.algorithms.svd_va` to use
        (`'method_of_snapshots'` or `'qr_svd'`).
    return_A_approx
        If `True` the approximation of the operator `A` with `AX=Y` is returned as
        |LowRankOperator|.
    return_A_tilde
        If `True` the low-rank dynamics are returned.

    Returns
    -------
    Wk
        |VectorArray| containing the dynamic modes.
    omega
        Time scaled eigenvalues: `ln(l)/dt`.
    A_approx
        |LowRankOperator| contains the approximation of the operator `A` with `AX=Y`.
    A_tilde
         Low-rank dynamics.
    """
    assert isinstance(X, VectorArray)
    assert isinstance(Y, VectorArray) or Y is None
    assert svd_rank is None or svd_rank <= X.dim
    assert modes in ('exact', 'standard')
    assert svd_method in ('qr_svd', 'method_of_snapshots')

    logger = getLogger('pymor.algorithms.dmd.dmd')

    if Y is None:
        assert svd_rank is None or svd_rank < len(X)
        # X = z_0, ..., z_{m-1}; Y = z_1, ..., z_m
        Y = X[1:]
        X = X[:-1]
    else:
        assert svd_rank is None or svd_rank <= len(X)
        assert len(X) == len(Y)

    rank = len(X) if svd_rank is None else svd_rank
    svd = qr_svd if svd_method == 'qr_svd' else method_of_snapshots

    logger.info('SVD of X...')
    U, s, Vh = svd(X, product=None, modes=rank)

    V = Vh.conj().T

    # solve the least-squares problem
    A_tilde = U.inner(Y) @ V / s

    logger.info('Calculating eigenvalue decomposition...')
    evals, evecs = spla.eig(A_tilde)

    omega = np.log(evals) / dt

    # ordering
    sort_idx = np.argsort(omega.real)[::-1]
    evecs = evecs[:, sort_idx]
    evals = evals[sort_idx]
    omega = omega[sort_idx]

    logger.info('Reconstructing eigenvectors...')
    if modes == 'standard':
        Wk = U.lincomb(evecs.T)
    elif modes == 'exact':
        Wk = Y.lincomb(((V / s) @ evecs).T)
        Wk.scal(1 / evals)
    else:
        assert False

    retval = [Wk, omega]

    if return_A_approx:
        A_approx = LowRankOperator(Y.lincomb(V.T), np.diag(s), U, inverted=True)
        retval.append(A_approx)

    if return_A_tilde:
        retval.append(A_tilde)

    return tuple(retval)

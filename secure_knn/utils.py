import numpy as np


def our_knn(enc_data: np.ndarray, enc_query: np.ndarray, k: int = 3) -> np.ndarray:
    """Return the indices of the ``k`` nearest neighbours.

    This is the only server-side (cloud) computation in the secure k-NN
    scheme: a dot product between the transformed encrypted dataset and the
    encrypted query vector, followed by an ascending sort.

    Per SecureNN-ICISS-2023.pdf §5 (Lemma 1), in the encrypted domain
        (p''_i - p''_j) . q̃vec  ≈  β1·β2·(D(p_i,q)^2 - D(p_j,q)^2)
    so the SIGNED dot product is monotone in squared distance and the row
    with the smallest signed dot product is the nearest neighbour. Taking
    np.abs() destroys this ordering (a large-negative score means "very
    near", and abs flips it to "very far").

    All data/query encryption now happens client-side in the browser
    (see frontend/src/crypto/aspe.js). The pre-webapp Python implementation
    of those steps is archived under Version_0.0/.
    """
    scores = np.dot(enc_data, enc_query)
    return np.argsort(scores)[:k]

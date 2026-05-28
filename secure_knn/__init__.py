"""Server-side utilities for secure k-NN.

The cloud only ever runs ``our_knn`` on ciphertexts; all encryption happens
client-side (frontend/src/crypto/aspe.js).
"""

from .utils import our_knn

__all__ = ["our_knn"]

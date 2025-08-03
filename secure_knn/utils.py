import os
from typing import Tuple

import numpy as np


def generate_m_temp(eta: int, q_max: float, max_norm: float) -> np.ndarray:
    """Generate a random matrix with constraints used during query encryption."""
    while True:
        matrix = np.random.rand(eta, eta)
        np.fill_diagonal(matrix, np.random.randint(max_norm, max_norm + 100, size=eta))
        mask = np.eye(eta, dtype=bool)
        matrix[~mask] = np.random.randint(q_max, q_max + 100, size=eta * eta - eta)
        if np.linalg.det(matrix) != 0:
            break
    return matrix


def get_max_norm(matrix: np.ndarray) -> float:
    """Return the maximum norm of the rows in ``matrix``."""
    return float(np.max(np.linalg.norm(matrix, axis=1)))


def generate_and_save_secrets(eta: int, c: int, d: int, secrets_dir: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generate secret matrices/vectors and persist them.

    Parameters
    ----------
    eta: int
        Dimension of the square secret matrix.
    c: int
        Number of elements in the ``w_vector``.
    d: int
        Dimension of the original data.
    secrets_dir: str
        Directory where the generated secrets are stored.
    """
    os.makedirs(secrets_dir, exist_ok=True)
    while True:
        m_base = np.random.randint(0, 100, size=(eta, eta))
        if np.linalg.det(m_base) != 0:
            break
    sec_vector = np.random.randint(0, 10, size=d + 1)
    w_vector = np.random.randint(0, 10, size=c)
    np.savetxt(os.path.join(secrets_dir, "m_base.csv"), m_base, delimiter=",")
    np.savetxt(os.path.join(secrets_dir, "sec_vector.csv"), sec_vector, delimiter=",")
    np.savetxt(os.path.join(secrets_dir, "w_vector.csv"), w_vector, delimiter=",")
    return m_base, sec_vector, w_vector


def encrypt_original_data_user_cloud(
    original_data: np.ndarray,
    sec_vector: np.ndarray,
    m_base_inv: np.ndarray,
    w_vector: np.ndarray,
    ep: int,
) -> np.ndarray:
    """Encrypt ``original_data`` for storage on the cloud."""
    n, d = original_data.shape
    nita = m_base_inv.shape[0]
    encrypted_original_data = np.zeros((n, nita))
    for i in range(n):
        pi = original_data[i]
        encrypted_pi = sec_vector[:d] - 2 * pi
        square_root_avg = np.linalg.norm(pi[:d] ** 2)
        pi_dplus1 = sec_vector[d] + square_root_avg
        extra_cols = np.concatenate((encrypted_pi, [pi_dplus1]))
        z_vector = np.random.randint(0, 100, size=ep)
        final_pi = np.concatenate((extra_cols, w_vector))
        final_pi = np.concatenate((final_pi, z_vector))
        encrypted_original_data[i] = final_pi
    encrypted_original_data = np.dot(encrypted_original_data, m_base_inv)
    return encrypted_original_data


def transform_data_for_query(original_enc_data: np.ndarray, m_temp: np.ndarray) -> np.ndarray:
    """Apply user-provided transformation matrix to encrypted data."""
    n, eta = original_enc_data.shape
    m_temp_inv = np.linalg.inv(m_temp)
    transformed_data = np.zeros((n, eta))
    for i in range(n):
        pi = original_enc_data[i]
        pi_dash = np.dot(pi, m_temp_inv)
        transformed_data[i] = pi_dash
    return transformed_data


def our_knn(enc_data: np.ndarray, enc_query: np.ndarray, k: int = 3) -> np.ndarray:
    """Return the indices of the ``k`` nearest neighbours."""
    distance_vec = np.abs(np.dot(enc_data, enc_query))
    return np.round(np.argsort(distance_vec)[:k])

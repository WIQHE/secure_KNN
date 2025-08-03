import os

import numpy as np

from secure_knn import (
    encrypt_original_data_user_cloud,
    generate_and_save_secrets,
    generate_m_temp,
    get_max_norm,
)

DATA_DIR = os.environ.get("DATA_DIR", "data_user")
CLOUD_DIR = os.environ.get("CLOUD_DIR", "cloud")
QUERY_DIR = os.environ.get("QUERY_DIR", "query_user")
SECRETS_DIR = os.path.join(DATA_DIR, "secrets")

original_path = os.path.join(DATA_DIR, "data_og.csv")
orignal_data = np.loadtxt(original_path, delimiter=",")

max_norm = get_max_norm(orignal_data)

n, d = orignal_data.shape
c = 5
ep = 3
eta = d + 1 + c + ep

if not os.path.exists(SECRETS_DIR):
    generate_and_save_secrets(eta, c, d, SECRETS_DIR)

m_base = np.loadtxt(os.path.join(SECRETS_DIR, "m_base.csv"), delimiter=",")
sec_vector = np.loadtxt(os.path.join(SECRETS_DIR, "sec_vector.csv"), delimiter=",")
w_vector = np.loadtxt(os.path.join(SECRETS_DIR, "w_vector.csv"), delimiter=",")

m_base_inv = np.linalg.inv(m_base)

enc_path = os.path.join(CLOUD_DIR, "enc_data_cloud_1.csv")
if not os.path.exists(enc_path):
    enc_data = encrypt_original_data_user_cloud(
        orignal_data, sec_vector, m_base_inv, w_vector, ep
    )
    os.makedirs(CLOUD_DIR, exist_ok=True)
    np.savetxt(enc_path, enc_data, delimiter=",")

enc_data = np.loadtxt(enc_path, delimiter=",")

query1_path = os.path.join(DATA_DIR, "enc_query_1.csv")
if os.path.exists(query1_path):
    enc_q = np.loadtxt(query1_path)
    q_max = np.max(enc_q)
    m_temp = generate_m_temp(eta, q_max, max_norm)
    q_dash = np.concatenate((enc_q, [1], np.random.randint(0, 10, size=c), np.zeros(ep)))
    q_eta = np.diag(q_dash)
    m_sec = np.dot(m_temp, m_base)
    beta_2 = np.random.rand()
    err = np.random.randint(q_max, q_max + 100, size=(eta, eta))
    q_enc_final = beta_2 * (np.dot(m_sec, q_eta) + err)
    os.makedirs(CLOUD_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(QUERY_DIR, exist_ok=True)
    np.savetxt(os.path.join(CLOUD_DIR, "user_1.csv"), m_temp, delimiter=",")
    np.savetxt(os.path.join(DATA_DIR, "beta_2.txt"), np.array([beta_2]))
    np.savetxt(os.path.join(DATA_DIR, "err.csv"), err, delimiter=",")
    np.savetxt(os.path.join(QUERY_DIR, "enc_query_2.csv"), q_enc_final, delimiter=",")

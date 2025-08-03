import os

import numpy as np

from secure_knn import our_knn, transform_data_for_query

DATA_DIR = os.environ.get("DATA_DIR", "data_user")
CLOUD_DIR = os.environ.get("CLOUD_DIR", "cloud")
QUERY_DIR = os.environ.get("QUERY_DIR", "query_user")
SECRETS_DIR = os.path.join(DATA_DIR, "secrets")


def check_implementation(enc_data, q, m_temp):
    m_base = np.loadtxt(os.path.join(SECRETS_DIR, "m_base.csv"), delimiter=",")
    beta_1 = np.loadtxt(os.path.join(QUERY_DIR, "beta_1.txt"), delimiter=",")
    err = np.loadtxt(os.path.join(DATA_DIR, "err.csv"), delimiter=",")
    N_dash_inv = np.loadtxt(os.path.join(QUERY_DIR, "n_dash_inv.csv"), delimiter=",")
    err_dash = np.dot(err, N_dash_inv)
    n, eta = enc_data.shape
    err_vec = [np.sum(err_dash[i][:eta]) for i in range(eta)]
    m_temp_inv = np.linalg.inv(m_temp)
    m_base_inv = np.linalg.inv(m_base)
    value_1 = beta_1 * q
    value_2 = np.dot(np.dot(m_base_inv, m_temp_inv), np.array(err_vec).reshape(-1, 1)).flatten()
    values_3 = value_1 > value_2
    is_correct = all(values_3)
    print("This implementation is " + ("True" if is_correct else "False"))


def main():
    og_enc_data = np.loadtxt(os.path.join(CLOUD_DIR, "enc_data_cloud_1.csv"), delimiter=",")
    m_temp = np.loadtxt(os.path.join(CLOUD_DIR, "user_1.csv"), delimiter=",")
    trans_enc_data = transform_data_for_query(og_enc_data, m_temp)
    q_cloud = np.loadtxt(os.path.join(CLOUD_DIR, "q_dash_vec.csv"), delimiter=",")
    check_implementation(trans_enc_data, q_cloud, m_temp)
    result = our_knn(trans_enc_data, q_cloud)
    np.savetxt(os.path.join(QUERY_DIR, "knnResult.csv"), result, delimiter=",")


if __name__ == "__main__":
    main()

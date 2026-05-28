import numpy as np

def run_simulation(beta_1_val, include_error=True):
    # Set seed for reproducibility
    np.random.seed(42)
    
    n, d = 100, 8
    c, ep = 5, 3
    eta = d + 1 + c + ep
    
    # 1. Generate data and query
    data = np.random.randn(n, d) * 10
    query = np.random.randn(d) * 10
    
    # Compute true distances and k-NN
    true_dists = np.sum((data - query) ** 2, axis=1)
    true_knn = np.argsort(true_dists)[:3]
    
    # 2. DO generates secrets
    while True:
        m_base = np.random.randint(1, 100, size=(eta, eta))
        if np.linalg.det(m_base) != 0:
            break
    m_base_inv = np.linalg.inv(m_base)
    
    s = np.random.randint(1, 10, size=d + 1)
    w = np.random.randint(1, 10, size=c)
    
    # 3. DO encrypts dataset
    enc_data = np.zeros((n, eta))
    for i in range(n):
        pi = data[i]
        shifted = s[:d] - 2 * pi
        norm_sq = np.sum(pi ** 2)
        pi_dplus1 = s[d] + norm_sq
        z = np.random.randint(1, 100, size=ep)
        p_tilde = np.concatenate((shifted, [pi_dplus1], w, z))
        enc_data[i] = np.dot(p_tilde, m_base_inv)
        
    # 4. QU Step 1
    N_diag = np.random.randint(1, 10, size=d)
    N = np.diag(N_diag)
    q_dot = beta_1_val * query * N_diag
    
    # 5. DO Step 2
    max_norm = np.max(np.linalg.norm(data, axis=1))
    q_max = np.max(q_dot)
    
    # Build Mt
    while True:
        Mt = np.random.rand(eta, eta)
        for i in range(eta):
            for j in range(eta):
                if i == j:
                    # Let's scale up Mt's diagonal to make error negligible
                    Mt[i, j] = np.random.randint(10000, 20000)
                else:
                    Mt[i, j] = np.random.randint(100, 200)
        if np.linalg.det(Mt) != 0:
            break
            
    m_sec = np.dot(Mt, m_base)
    x = np.random.randint(1, 10, size=c)
    q_prime = np.concatenate((q_dot, [1], x, np.zeros(ep)))
    q_eta_eta = np.diag(q_prime)
    
    if include_error:
        E = np.random.randint(int(np.ceil(q_max)), int(np.ceil(q_max)) + 100, size=(eta, eta))
    else:
        E = np.zeros((eta, eta))
        
    beta_2 = np.random.rand() + 0.5
    q_hat = beta_2 * (np.dot(m_sec, q_eta_eta) + E)
    
    # CSP updates database
    enc_data_double = np.dot(enc_data, np.linalg.inv(Mt))
    
    # 6. QU Step 3
    N_prime_values = np.concatenate((N_diag, np.ones(eta - d)))
    N_prime_inv = np.diag(1.0 / N_prime_values)
    
    q_tilde_enc = np.dot(q_hat, N_prime_inv)
    q_tilde_vec = np.sum(q_tilde_enc, axis=1)
    
    # 7. CSP k-NN computation
    scores = np.dot(enc_data_double, q_tilde_vec)
    computed_knn = np.argsort(scores)[:3]
    
    return true_knn, computed_knn, true_dists

if __name__ == "__main__":
    print("--- CASE 1: No Noise (E = 0), beta_1 = 5 (As described in the paper) ---")
    true_knn, computed_knn, true_dists = run_simulation(beta_1_val=5, include_error=False)
    print(f"True k-NN:      {true_knn}")
    print(f"Computed k-NN:  {computed_knn}")
    print(f"Match:          {list(true_knn) == list(computed_knn)}")
    if list(true_knn) != list(computed_knn):
        print(f"Mismatch! True dists for true: {[round(true_dists[idx], 2) for idx in true_knn]}")
        print(f"Mismatch! True dists for comp: {[round(true_dists[idx], 2) for idx in computed_knn]}")

    print("\n--- CASE 2: No Noise (E = 0), beta_1 = 1 (As corrected in the code) ---")
    true_knn, computed_knn, true_dists = run_simulation(beta_1_val=1, include_error=False)
    print(f"True k-NN:      {true_knn}")
    print(f"Computed k-NN:  {computed_knn}")
    print(f"Match:          {list(true_knn) == list(computed_knn)}")
    
    print("\n--- CASE 3: With Noise (E != 0), beta_1 = 1 (Full Scheme with correct beta_1) ---")
    true_knn, computed_knn, true_dists = run_simulation(beta_1_val=1, include_error=True)
    print(f"True k-NN:      {true_knn}")
    print(f"Computed k-NN:  {computed_knn}")
    print(f"Match:          {list(true_knn) == list(computed_knn)}")


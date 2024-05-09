import numpy as np
import os



def generate_m_temp(eta, q_max, max_norm):
    while True:
        
        matrix = np.random.rand(eta, eta)
        
        # Adjust diagonal elements to be greater than p
        np.fill_diagonal(matrix, np.random.randint(max_norm, max_norm+100, size=eta))
        
        # Adjust non-diagonal elements to be greater than q
        mask = np.eye(eta, dtype=bool)  # Mask to exclude diagonal elements
        matrix[~mask] = np.random.randint(q_max, q_max+100, size=eta*eta-eta)
        
        if np.linalg.det(matrix) != 0:
            break
        
    return matrix



def get_max_norm(matrix):
    # Calculate the squared sum of elements for each row
    row_sums_squared = np.sum(matrix**2, axis=1)
    
    # Calculate the max norm among all rows
    max_norm = np.sqrt(np.max(row_sums_squared))
    
    return max_norm


def generate_and_save_secrets(eta, c, d):
    
    while True:
        m_base = np.random.randint(0, 100, size=(eta, eta))
        if np.linalg.det(m_base) != 0:
            break
        
    sec_vector = np.random.randint(0, 10, size=d + 1)
    w_vector = np.random.randint(0, 10, size=c)
    np.savetxt('data_user/secrets/m_base.csv', m_base, delimiter=',')
    np.savetxt('data_user/secrets/sec_vector.csv', sec_vector,delimiter=',')
    np.savetxt('data_user/secrets/w_vector.csv', w_vector,delimiter=',')


def encrypt_original_data_user_cloud(original_data, sec_vector, m_base_inv, w_vector, ep):
    n, d = original_data.shape
    nita = len(m_base_inv[0])

    # Step 2: Encrypting each element of original_data
    encrypted_original_data = np.zeros((n,nita))
    for i in range(n):
        
        
        pi = original_data[i]  # Reshape the row into a column vector
        # print(pi)
        
        
        # Step 2: Encrypting each element of pi
        encrypted_pi = sec_vector[:d] - 2 * pi
        # print(encrypted_pi)
        
        # Step 3: Adding extra columns to pi
        square_root_avg = np.sqrt(np.mean(pi[:d]**2))
        
        pi_dplus1 = sec_vector[d] + square_root_avg
        
        extra_cols = np.concatenate((encrypted_pi, [pi_dplus1]))
        
        
        # Step 4: Adding w_vector and a random z_vector
        z_vector = np.random.randint(0, 100, size=ep)
        # print(z_vector)
        final_pi = np.concatenate((extra_cols, w_vector))
        final_pi = np.concatenate((final_pi, z_vector))
        # print(final_pi)
        
        
        
        encrypted_original_data[i] = final_pi
        # print(encrypted_original_data)
        
        
    # Encrypting with the inverse of m_base
    # print(encrypted_original_data)
    encrypted_original_data = np.dot(encrypted_original_data, m_base_inv)
    
    return encrypted_original_data





orignal_data = np.loadtxt('data_user/data_og.csv', delimiter=',')


max_norm = get_max_norm(orignal_data);

n , d = orignal_data.shape

# public paramaters
c = 5

ep = 3

eta = d + 1 + c + ep

if not os.path.exists('data_user/m_base.csv'):
    generate_and_save_secrets(eta, c, d)

m_base = np.loadtxt('data_user/secrets/m_base.csv', delimiter=',')
sec_vector = np.loadtxt('data_user/secrets/sec_vector.csv', delimiter=',')
w_vector = np.loadtxt('data_user/secrets/w_vector.csv', delimiter=',')

m_base_inv = np.linalg.inv(m_base)


#check if the data is enc or not 
if not os.path.exists('cloud/enc_data_cloud_1.csv'):
    enc_data = encrypt_original_data_user_cloud(orignal_data, sec_vector, m_base_inv, w_vector,ep)

    np.savetxt('cloud/enc_data_cloud_1.csv', enc_data, delimiter=',')

#load the enc data
enc_data = np.loadtxt('cloud/enc_data_cloud_1.csv', delimiter=',')


#check if there is a query
if os.path.exists('data_user/enc_query_1.csv'):

    enc_q = np.loadtxt('data_user/enc_query_1.csv')
    
    q_max = np.max(enc_q)
    
    #generate the m_temp
    m_temp = generate_m_temp(eta, q_max, max_norm)

    q_dash = np.concatenate((enc_q,[1], np.random.randint(0,10,size=c), np.zeros(ep)))

    q_eta = np.diag(q_dash)

    m_sec = np.dot(m_temp, m_base)
    beta_2 = np.random.rand()
    err = np.random.randint(q_max, q_max+100, size=(eta,eta))

    q_enc_final = beta_2 * (np.dot(m_sec, q_eta) + err)
    
    np.savetxt('cloud/user_1.csv', m_temp, delimiter=',') # To be used by / sent to CSP
    np.savetxt('data_user/beta_2.txt', np.array([beta_2]))
    np.savetxt('data_user/err.csv', err, delimiter=',')
    np.savetxt('query_user/enc_query_2.csv', q_enc_final, delimiter=',') # Used by Query User
    







import numpy as np
from sklearn.neighbors import NearestNeighbors


def find_k_nearest_neighbors(data_matrix, query_points, k):
    # Using sklearn's NearestNeighbors for efficiency
    nbrs = NearestNeighbors(n_neighbors=k, algorithm='auto').fit(data_matrix)
    distances, indices = nbrs.kneighbors(query_points)
    return distances, indices







def enc_check(data, query, error_vec):
    
    
    n, eta = data.shape
    
    new_data = np.ones(n)
    
    for i in range(n):
        new_data[i] = np.dot(data[i], query)
    
    print("\nthe new data")
    print(new_data)
    print("\n")
    
    
    for i in range(n):
        for j in range(n):
            if(abs(new_data[i]-new_data[j]) <= abs(error_vec[i] - error_vec[j])):return False
    
    return True





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


def get_max(enc_q):
    q_max = -1e-10
    for i in enc_q:
        q_max = max(q_max,np.sqrt(np.mean(i**2)))
    return q_max

def get_max_norm(matrix):
    # Calculate the squared sum of elements for each row
    row_sums_squared = np.sum(matrix**2, axis=1)
    
    # Calculate the max norm among all rows
    max_norm = np.sqrt(np.max(row_sums_squared))
    
    return max_norm



def transform_data_for_querry(orignal_enc_data, m_temp):
    n, eta = orignal_enc_data.shape
    m_temp_inv = np.linalg.inv(m_temp)
    
    transformed_data = np.zeros((n,eta))
    for i in range(n):
        
        pi = orignal_enc_data[i]
        
        pi_dash = np.dot(pi,m_temp_inv)
        
        transformed_data[i] = pi_dash
        
        
    return transformed_data



def encrypt_original_data_user_cloud(original_data, sec_vector, m_base_inv, w_vector, ep):
    n, d = original_data.shape
    nita = len(m_base[0])

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
        print(z_vector)
        final_pi = np.concatenate((extra_cols, w_vector))
        final_pi = np.concatenate((final_pi, z_vector))
        # print(final_pi)
        
        
        
        encrypted_original_data[i] = final_pi
        # print(encrypted_original_data)
        
        
    # Encrypting with the inverse of m_base
    print(encrypted_original_data)
    encrypted_original_data = np.dot(encrypted_original_data, m_base_inv)
    
    return encrypted_original_data

# Step 1: Generate 2D integer original_data array of size n*d
n = 3
d = 3
original_data = np.random.randint(0, 100, size=(n, d))
max_norm = get_max_norm(original_data);
# Step 2: Compute eta
c = 2
ep = 2
eta = d + 1 + c + ep

# Step 3: Generate random invertible 2D array m_base of size eta*eta
while True:
    m_base = np.random.randint(0, 100, size=(eta, eta))
    if np.linalg.det(m_base) != 0:
        break
m_base_inv = np.linalg.inv(m_base)


# Step 4: Generate sec_vector and w_vector
sec_vector = np.random.randint(0, 10, size=d + 1)
w_vector = np.random.randint(0, 10, size=c)



# Step 5: querry user secret generate
q_0 = np.random.randint(0,70,size=(d))

N = np.zeros((d, d))

beta_1 = np.random.randint(1, 10)

for _ in range(d): N[_][_] = np.random.randint(1, 10)

enc_q = np.dot(q_0 , beta_1 * N) # this enc_q is sent to the data owner



# Step 6 : enc_q re-encrypted by DataOwner

#generate the m_temp
q_max = get_max(enc_q)
m_temp = generate_m_temp(eta, q_max, max_norm)

q_dash = np.concatenate((enc_q,[1], np.random.randint(0,10,size=c), np.zeros(ep)))

q_eta = np.diag(q_dash)

m_sec = np.dot(m_temp, m_base)
beta_2 = np.random.rand()
err = np.random.randint(q_max, q_max+100, size=(eta,eta))

q_enc_final = beta_2 * (np.dot(m_sec, q_eta) + err);


# print("the final querry \n")
# print(q_enc_final)
# print("\n")
# print(m_sec)
# print("\n")
# print(m_temp)
# print("\n")
# print(m_base)
# print("\n")
# print(err)
# print("\n")
# print(q_max)
# print("\n")
# print(beta_2)


#Step7 a: DO send the user_id of QU to cloud with the temp ephermal m_temp as (user_id, m_temp)
# @ CSP

# we already have the encrypted orignal data at cloud D_dash

org_enc_data = encrypt_original_data_user_cloud(original_data, sec_vector, m_base_inv, w_vector, ep)

transformed_data = transform_data_for_querry(org_enc_data, m_temp)


print("\nTransformed data\n")
print(transformed_data)






#Step7 b: DO send the enc q_final to QU and QU remove the decryption


N_values = np.dot(np.ones(d), N)

N_values = np.concatenate((N_values, np.ones(eta - d)))

N_dash = np.diag(N_values)
N_dash_inv  = np.linalg.inv(N_dash)
print("\nthe Nvaules")
print(N_values)
print("\n")
q_dash_enc = np.dot(q_enc_final, N_dash_inv)

print("\nthe q\n")
print(q_dash_enc)
print("\n")


q_dash_vec=np.ones(eta)


for i in range(eta):
    q_dash_vec[i] = (np.sum(q_dash_enc[i][:eta]))

print("\nthe q sum\n")
print(q_dash_vec)
print("\n")


# now this q_dash_vec is sent to CPS with its user id and that can perform the k-NN on cloud 




# KNN on cloud





# k-NN on the cloud with encryption is correct is it satisfies the condition
#  beta_1 . q_dash_vec > m_base_inv . m_temp_inv . err_vec

err_dash = np.dot(err, N_dash_inv)

err_vec=[]
for i in range(eta):
    err_vec.append(np.sum(err_dash[i][:eta]))

m_temp_inv = np.linalg.inv(m_temp)
value_1 = beta_1 * q_dash_vec 
value_2 = np.dot(np.dot(m_base_inv, m_temp_inv), np.array(err_vec).reshape(-1,1)).flatten()

print(len(value_1))
print(beta_1)
print(len(value_2))

print(value_1)
print(value_2)

# column_vector = np.array(python_list).reshape(-1, 1)

#checking weather the system is correct 
print("\n")
print(value_1 > value_2)

print("\nthe q sum\n")
print(len(q_dash_vec))
print("\n")




# # Displaying generated original_data
# print("Generated original_data:")
# print(original_data)
# print("\nGenerated m_base:")
# print(m_base)
# print("\nGenerated sec vector:")
# print(sec_vector)
# print("\nGenerated w vector:")
# print(w_vector)
# print("\n")
# print(encrypt_original_data_user_cloud(original_data, sec_vector, m_base, w_vector, ep))
# print(N)
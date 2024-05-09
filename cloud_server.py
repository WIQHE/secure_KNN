import numpy as np
import os



def transform_data_for_querry(orignal_enc_data, m_temp):
    n, eta = orignal_enc_data.shape
    m_temp_inv = np.linalg.inv(m_temp)
    
    transformed_data = np.zeros((n,eta))
    for i in range(n):
        
        pi = orignal_enc_data[i]
        
        pi_dash = np.dot(pi,m_temp_inv)
        
        transformed_data[i] = pi_dash
        
        
    return transformed_data





# k-NN implementation






og_enc_data = np.loadtxt('cloud/enc_data_cloud_1.csv', delimiter=',')
m_temp = np.loadtxt('cloud/user_1.csv', delimiter=',')
m_base = np.loadtxt('data_user/secrets/m_base.csv', delimiter=',')
beta_1 = np.loadtxt('query_user/beta_1.txt', delimiter=',')
trans_enc_data = transform_data_for_querry(og_enc_data, m_temp)

q_cloud = np.loadtxt('cloud/q_dash_vec.csv', delimiter=',')
err = np.loadtxt('data_user/err.csv', delimiter=',')
N_dash_inv = np.loadtxt('query_user/n_dash_inv.csv', delimiter=',')

err_dash = np.dot(err, N_dash_inv)

n, eta = og_enc_data.shape

err_vec=[]
for i in range(eta):
    err_vec.append(np.sum(err_dash[i][:eta]))

m_temp_inv = np.linalg.inv(m_temp)
m_base_inv = np.linalg.inv(m_base)

value_1 = beta_1 * q_cloud 
value_2 = np.dot(np.dot(m_base_inv, m_temp_inv), np.array(err_vec).reshape(-1,1)).flatten()

values_3 = value_1 > value_2
print(values_3)
isCorrect = 'True'
for i in values_3:
    if not i:
        isCorrect = 'False'
        break

print("This implementation is " + isCorrect)
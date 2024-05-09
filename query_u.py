import numpy as np 
import os




if os.path.exists('query_user/enc_query_2.csv'):
    
    
    enc_q_final = np.loadtxt('query_user/enc_query_2.csv', delimiter=',');
    
    N = np.loadtxt('query_user/N.csv', delimiter=',')
    eta = len(enc_q_final[0])
    d = len(N[0])
        
    N_values = np.dot(np.ones(d), N)

    N_values = np.concatenate((N_values, np.ones(eta - d)))

    N_dash = np.diag(N_values)
    
    N_dash_inv  = np.linalg.inv(N_dash)
    
    q_dash_enc = np.dot(enc_q_final, N_dash_inv)

    q_dash_vec=np.ones(eta)

    for i in range(eta):
        q_dash_vec[i] = (np.sum(q_dash_enc[i][:eta]))
    np.savetxt('cloud/q_dash_vec.csv', q_dash_vec, delimiter=',')
    np.savetxt('query_user/n_dash_inv.csv', N_dash_inv, delimiter=',')




else:
    
    q_0 = np.loadtxt('query_user/query_og.csv', delimiter=',')


    d = len(q_0)

    N = np.zeros((d, d))

    beta_1 = [np.random.randint(1, 10)]

    for _ in range(d): N[_][_] = np.random.randint(1, 10)

    enc_q = np.dot(q_0 , beta_1 * N) # this enc_q is sent to the data owner
    
    np.savetxt('data_user/enc_query_1.csv', enc_q, delimiter=',')
    np.savetxt('query_user/N.csv', N, delimiter=',')
    np.savetxt('query_user/beta_1.txt', beta_1)
    




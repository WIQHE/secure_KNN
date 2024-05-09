import numpy as np 

n = 10
d = 8
c = 5
ep = 3
eta = d + 1 + c + ep

data_to_save = np.random.randint(0,100, size=(n, d))

# Save data to a CSV file
np.savetxt('data_user/data_og.csv', data_to_save, delimiter=',')
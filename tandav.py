import numpy as np 
import os

names = [
    'cloud/enc_data_cloud_1.csv',
    'cloud/user_1.csv',
    'cloud/q_dash_vec.csv',
    'data_user/secrets/m_base.csv',
    'data_user/secrets/sec_vector.csv',
    'data_user/secrets/w_vector.csv',
    'data_user/beta_2.txt',
    'data_user/data_og.csv',
    'data_user/err.csv',
    'data_user/enc_query_1.csv',
    'query_user/N.csv',
    'query_user/n_dash_inv.csv',
    'query_user/enc_query_2.csv',
    'query_user/query_og.csv',
    'query_user/beta_1.txt',
    'query_user/knnResult.csv'
]

for i in names:
    file_name = i  # Replace "example.txt" with your file name

    # Check if the file exists before attempting to delete
    if os.path.exists(file_name):
        # Delete the file
        os.remove(file_name)
        print("File", file_name, "deleted successfully.")
    else:
        print("File", file_name, "does not exist.")
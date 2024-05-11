# Secure k-NN Computation on Cloud using Homomorphic Encryption

![Secure k-NN](insert-image-url-here)

## Introduction
This project implements the concept of secure k-nearest neighbors (k-NN) computation on the cloud using homomorphic encryption. The implementation is based on the scheme proposed in the paper titled "Secure KNN on Cloud" by Virendra Singh and Tikaram Sanyashi.

Cloud computing has become increasingly popular for outsourcing database and query services to alleviate local storage and computing pressures. However, storing and processing private data in the cloud poses risks to data privacy and confidentiality. Therefore, sensitive applications running on the cloud necessitate encryption before storage. Additionally, certain data mining algorithms, such as k-NN, require data to be in an encrypted domain that supports computation-friendly ciphertexts.

## Abstract
The project addresses the challenges of ensuring both data privacy and query privacy in cloud-based k-NN computation. It leverages an Asymmetric Scalar-Product-Preserving Encryption (ASPE) scheme, which initially assumed trusted query users. Subsequent enhancements demonstrated that trusted query users are no longer necessary with the adoption of the Paillier cryptosystem.

This work demonstrates that query privacy within the cryptosystem can be achieved solely using the ASPE technique, obviating the need for the Paillier cryptosystem. Utilizing ASPE for query encryption not only maintains query privacy but also reduces query encryption time, enhancing the practicality of the encryption scheme.

## Key Features
- 🛡️ **Homomorphic Encryption:** The project employs homomorphic encryption to enable secure computation on encrypted data.
- 🔒 **ASPE Scheme:** Utilizes the Asymmetric Scalar-Product-Preserving Encryption scheme for secure k-NN computation, ensuring both data and query privacy.
- 🕵️ **Query Privacy:** Achieves query privacy without relying on trusted query users, enhancing the security of the system.
- ⏱️ **Efficiency:** Reduces query encryption time, improving the practicality and efficiency of the encryption scheme.

## Implementation
The implementation of this project involves integrating the ASPE scheme into the k-NN computation process on the cloud. It includes the encryption of both the dataset and query vectors before outsourcing them to the cloud for computation. The ASPE technique ensures that the privacy of both data and queries is preserved throughout the computation process.

## Usage
To use the secure k-NN computation on the cloud with homomorphic encryption:
1. Encrypt the dataset using the ASPE scheme.
2. Encrypt the query vectors using the ASPE technique.
3. Send the encrypted dataset and query vectors to the cloud for computation.
4. Perform k-NN computation on the encrypted data in the cloud.
5. Decrypt the results using the appropriate decryption key.

## Conclusion
This project presents a practical solution for conducting secure k-nearest neighbors computation on the cloud while preserving both data and query privacy. By leveraging homomorphic encryption and the ASPE scheme, it addresses the challenges of ensuring privacy in cloud-based data mining applications. The implementation offers an efficient and secure method for conducting k-NN computations in a cloud environment.

![Empty Image 1](insert-empty-image-url-1-here)
![Empty Image 2](insert-empty-image-url-2-here)

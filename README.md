# Secure k-NN Computation on Cloud using Homomorphic Encryption

## Project Overview
This project implements the concept of **secure k-nearest neighbors (k-NN) computation on the cloud** using homomorphic encryption. It is based on the scheme proposed in the paper titled *"Secure KNN on Cloud"* by Virendra Singh and Tikaram Sanyashi.

The primary goal of this project is to allow a Data Owner to outsource their dataset to a Cloud Service Provider (CSP) and allow a Query User to query this data for k-NN **without revealing the plaintext data or the query** to the Cloud. It achieves this using an **Asymmetric Scalar-Product-Preserving Encryption (ASPE)** scheme. The implementation eliminates the need for trusted query users or heavier cryptosystems (like Paillier), ensuring both data privacy and query privacy while maintaining computation efficiency.

---

## State of the Project
The project is currently a functional proof-of-concept with both a **Script-based Pipeline** and a **FastAPI Backend Service**.

1. **Script Pipeline**: Individual Python scripts (`generate_data.py`, `generate_query.py`, `data_owner.py`, `query_u.py`, `cloud_server.py`, `om.py`, `tandav.py`) that can be run sequentially to simulate the different actors (Data Owner, Query User, Cloud Server).
2. **FastAPI Backend** (`fastapi_app.py`): A robust REST API layer that wraps the core logic into discrete endpoints, allowing programmatic execution of the pipeline, state checking, and cleanup. It includes a simple threading lock to prevent concurrent pipeline execution conflicts over the file system.

The project relies heavily on the **local file system** to pass state and artifacts (matrices, encrypted vectors, keys) between the different simulated actors, storing them in specific directories: `cloud/`, `data_user/`, `query_user/`, and `data_user/secrets/`.

---

## Complete Workflow & Pipeline Context

The workflow is broken down into distinct cryptographic and operational stages, representing interactions between the **Data Owner**, the **Query User**, and the **Cloud Server**.

### 1. Data & Query Generation
- **Actor**: System/Simulation
- **Action**: Generates synthetic plaintext data and query vectors.
- **Files**: `generate_data.py`, `generate_query.py`
- **API Endpoints**: `POST /pipeline/step/generate_data`, `POST /pipeline/step/generate_query`
- **Output**: `data_user/data_og.csv`, `query_user/query_og.csv`

### 2. Query Stage 1 (Query User Encryption)
- **Actor**: Query User
- **Action**: Initiates the query encryption process. Multiplies the plaintext query by a secret matrix `N` and a scalar `beta_1`.
- **File**: `query_u.py` (First branch)
- **API Endpoint**: `POST /pipeline/step/query_stage1`
- **Output**: `data_user/enc_query_1.csv` (Sent to Data Owner), `query_user/N.csv`, `query_user/beta_1.txt`

### 3. Data Owner Processing
- **Actor**: Data Owner
- **Action**: 
  - Generates secret keys and base matrices (`m_base`, `sec_vector`, `w_vector`).
  - Encrypts the entire original dataset using these secrets and the ASPE technique (adding artificial dimensions to preserve scalar products securely).
  - Takes the Query User's partially encrypted query (`enc_query_1`) and further encrypts it with its own secrets (`m_temp`, `beta_2`, error matrices).
- **File**: `data_owner.py`
- **API Endpoint**: `POST /pipeline/step/data_owner`
- **Output**: 
  - Data Secrets: `data_user/secrets/*`
  - Cloud Data: `cloud/enc_data_cloud_1.csv`, `cloud/user_1.csv` (m_temp)
  - Query Data: `query_user/enc_query_2.csv` (Sent back to Query User)

### 4. Query Stage 2 (Query Finalization)
- **Actor**: Query User
- **Action**: Receives the double-encrypted query from the Data Owner and removes their initial secret `N` matrix, finalizing the query vector for the cloud.
- **File**: `query_u.py` (Second branch)
- **API Endpoint**: `POST /pipeline/step/query_stage2`
- **Output**: `cloud/q_dash_vec.csv` (Sent to Cloud Server)

### 5. Cloud k-NN Computation
- **Actor**: Cloud Server
- **Action**: Performs a transformation on the encrypted dataset using `m_temp`. Calculates the absolute dot product (distance) between the transformed encrypted data and the finalized encrypted query. Sorts the distances to find the top `k` nearest neighbors.
- **File**: `cloud_server.py`
- **API Endpoint**: `POST /pipeline/step/cloud_knn`
- **Output**: `query_user/knnResult.csv` (Indices of the nearest neighbors returned to the Query User)

### Orchestration and Cleanup
- **`om.py` / `POST /pipeline/run`**: Automates all the above steps in the correct order.
- **`tandav.py` / `POST /cleanup`**: Deletes all generated artifacts (CSV and TXT files) to reset the environment for a fresh run.

---

## Agent Context & Important Details
If you are an AI agent analyzing or modifying this repository, keep the following in mind:
- **Math & Cryptography**: The security of this scheme relies on **matrix multiplications, artificial dimension expansion, and random noise/error injection**. Ensure that any refactoring of numpy operations in `data_owner.py` or `cloud_server.py` preserves the mathematical integrity of the ASPE scheme.
- **State Management**: The API and scripts use the file system (`np.savetxt` and `np.loadtxt`) as a pseudo-database. Concurrency is limited because file paths are statically defined (e.g., `cloud/enc_data_cloud_1.csv`). 
- **Idempotency**: The FastAPI app attempts to make steps idempotent by checking if prerequisite files exist.

---

## Proposed Changes & Future Improvements

To take this project from a research proof-of-concept to a production-ready application, the following improvements are proposed:

### 1. Storage & State Architecture
- **Eliminate File-System State**: Replace the local `.csv` and `.txt` file drops with a database (e.g., PostgreSQL for metadata, AWS S3/MinIO for matrix blobs) or an in-memory datastore like Redis.
- **Session/Job IDs**: Introduce unique job identifiers for each pipeline run so multiple users can process queries concurrently without overwriting each other's files.

### 2. FastAPI & Backend Enhancements
- **Remove Threading Lock**: The current `PIPELINE_LOCK` in `fastapi_app.py` blocks concurrent requests. Shifting state to a database and using Job IDs will allow safe parallel execution.
- **Asynchronous Task Queue**: Move the heavy matrix computations (especially dataset encryption in `data_owner.py`) to background task workers using **Celery** or **ARQ**, rather than blocking the FastAPI HTTP event loop.

### 3. Cryptographic Flexibility
- **Configurable Parameters**: Currently, dimensions and artificial variables (`c`, `ep`) are hardcoded or passed as simple parameters. Move these to a unified configuration file (`config.yaml` or `.env`).
- **Algorithm Updates**: While ASPE is fast, integrating modern Fully Homomorphic Encryption (FHE) libraries like **TenSEAL** (CKKS/BFV schemes) could provide mathematically provable security bounds against known plaintext/ciphertext attacks.

### 4. Code Quality & Testing
- **Type Hinting & Linting**: Enhance Python type hints across the numerical scripts and enforce formatting (e.g., using `black`, `ruff`, or `mypy`).
- **Unit Tests**: Add a `pytest` suite that verifies the mathematical correctness of the distance calculations (ensuring the encrypted k-NN result matches the plaintext k-NN result).

# Secure k-NN demo — test queries

Dataset: `sample_data/clusters_8d.csv` — 100 rows × 8 features, 5 clusters of 20 points each.
Encrypted dimensionality η = 8 + 1 + 5 + 3 = **17**.

For each query, paste the vector into the Query User console, set k=5, and submit.
The 'expected indices' are the plaintext top-5; ASPE typically returns a permutation with ~3-4 matches due to its inherent error tolerance.
The 'expected clusters' line shows which cluster each top-5 row belongs to — that should be **fully** consistent (all from the right cluster).

## Q0 — deep in cluster 0

- **Vector**: `25,22,19,22,16,16,15,24`
- **Plaintext top-5**: `[64, 39, 95, 50, 51]` (distances²: [89, 93, 117, 261, 278])
- **Cluster labels of top-5**: `[0, 0, 0, 0, 0]`

## Q1 — deep in cluster 1

- **Vector**: `82,78,25,19,18,23,20,21`
- **Plaintext top-5**: `[10, 94, 96, 41, 78]` (distances²: [100, 107, 164, 177, 214])
- **Cluster labels of top-5**: `[1, 1, 1, 1, 1]`

## Q2 — deep in cluster 2

- **Vector**: `25,26,82,81,16,21,18,19`
- **Plaintext top-5**: `[20, 8, 88, 52, 13]` (distances²: [82, 96, 149, 226, 285])
- **Cluster labels of top-5**: `[2, 2, 2, 2, 2]`

## Q3 — deep in cluster 3

- **Vector**: `19,22,15,20,85,79,78,82`
- **Plaintext top-5**: `[81, 9, 24, 15, 58]` (distances²: [86, 193, 195, 213, 219])
- **Cluster labels of top-5**: `[3, 3, 3, 3, 3]`

## Q4 — deep in cluster 4

- **Vector**: `84,18,78,23,81,20,87,20`
- **Plaintext top-5**: `[56, 18, 42, 70, 61]` (distances²: [66, 66, 155, 181, 188])
- **Cluster labels of top-5**: `[4, 4, 4, 4, 4]`

## Q5 — between 0 and 1

- **Vector**: `50,50,20,20,20,20,20,20`
- **Plaintext top-5**: `[7, 64, 67, 76, 50]` (distances²: [1008, 1158, 1171, 1301, 1364])
- **Cluster labels of top-5**: `[0, 0, 1, 1, 0]`

## Q6 — between 2 and 3

- **Vector**: `20,20,50,50,50,50,50,50`
- **Plaintext top-5**: `[43, 46, 3, 26, 21]` (distances²: [3966, 4068, 4197, 4371, 4455])
- **Cluster labels of top-5**: `[3, 3, 0, 2, 2]`

## Q7 — far from everything

- **Vector**: `50,50,50,50,50,50,50,50`
- **Plaintext top-5**: `[46, 9, 3, 30, 8]` (distances²: [5688, 5713, 5817, 6140, 6210])
- **Cluster labels of top-5**: `[3, 3, 0, 4, 2]`

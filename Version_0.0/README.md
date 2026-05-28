# Version 0.0 — archived pre-webapp pipeline

This directory is a frozen snapshot of the **original command-line pipeline**
that predates the current web application. It is kept for reference only and is
**not used** by the live app. Nothing here is imported by `webapp/` or
`frontend/`.

## What's here

| File / dir | Role in the old CLI flow |
|---|---|
| `data_owner.py` | Data owner: generated secrets, encrypted the dataset, performed the query re-encryption (step 2). |
| `query_u.py` | Query user: two-branch script for query encryption (step 1) and layer removal (step 3). |
| `cloud_server.py` | Cloud: transformed the encrypted dataset with `M_t` and ran k-NN. |
| `secure_knn/` | Full legacy version of the crypto helpers (`generate_m_temp`, `get_max_norm`, `generate_and_save_secrets`, `encrypt_original_data_user_cloud`, `transform_data_for_query`, `our_knn`). |
| `cloud/`, `data_user/`, `query_user/` | Stale input/output CSVs from old CLI runs (datasets, secrets, encrypted queries, results). |

## Why it was retired

The CLI pipeline had two relevant problems that the live app fixes:

1. **Random `β1` (correctness).** `query_u.py` drew `β1 ∈ [1,10)`. The paper's
   Lemma 1 silently assumes the resulting scores are monotone in `‖p−q‖²`, but
   expanding `p̃_i · q''_η` shows `β1` only multiplies the dot-product terms, not
   `‖p_i‖²`. With `β1 ≠ 1` the ranking is distorted and k-NN returns wrong
   neighbours on close pairs. The live client (`frontend/src/crypto/aspe.js`)
   forces `β1 = 1`.
2. **Architecture.** Encryption ran on whatever machine executed the scripts.
   The live app moves all encryption client-side (data-owner browser and
   query-user browser); the server (`webapp/app.py`) only stores ciphertexts and
   runs `our_knn`.

## Running the archived pipeline (optional)

It is self-contained — run from inside this directory so the relative paths and
the bundled `secure_knn/` package resolve:

```bash
cd Version_0.0
python data_owner.py     # then query_u.py / cloud_server.py per the old order
```

For the current, working system see the top-level `README.md`, `webapp/`, and
`frontend/`.

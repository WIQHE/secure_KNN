"""Thin CSP server for the Secure k-NN demo.

Architecture (two-browser + polling):

    Data Owner browser                     Cloud (this server)                Query User browser
    ------------------                     -------------------                ------------------
    encrypt dataset client-side  ---->     POST /dataset
                                           (stores ENC_DATA, eta)
                                                                              POST /query/submit
                                                                              <----  q_dot, user_id
                                                                              { query_id }
    GET /query/pending           <----     pending queue
    DO step 2 (q_hat, M_t)
    POST /query/reencrypt        ---->     stores q_hat, M_t
                                                                              GET /query/<id>/reencrypted
                                                                              <----  q_hat
                                                                              QU step 3
                                                                              POST /query/<id>/finalize
                                                                              ---->  q_tilde_vec, k
                                           compute D'' = ENC_DATA . M_t^{-1}
                                           run our_knn(D'', q_tilde_vec)
                                                                              GET /results/<result_id>

This server never sees the plaintext dataset, the plaintext query, or any of
the DO/QU secrets (s, M_base, w, N, beta_1, beta_2). It only stores ciphertexts
and runs the (linear-algebra) k-NN computation.
"""

import os
import uuid
from threading import Lock

import numpy as np
from flask import Flask, jsonify, request, send_from_directory

from secure_knn import our_knn

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
FRONTEND_DIR = os.path.join(REPO_ROOT, "frontend")

app = Flask(__name__)

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.getcwd(), "data_user"))
CLOUD_DIR = os.environ.get("CLOUD_DIR", os.path.join(os.getcwd(), "cloud"))

# -- In-memory CSP state -------------------------------------------------------
# Only ciphertexts and per-query bookkeeping live here.
ENC_DATA = None  # np.ndarray of shape (n, eta) — encrypted dataset p'_i
ETA = None       # int — dimensionality of encrypted vectors

# Pending queries waiting for the DO to perform step 2.
#   { query_id: {"user_id": str, "q_dot": list[float]} }
PENDING_QUERIES = {}

# Re-encrypted queries waiting for the QU to perform step 3.
#   { query_id: {"user_id": str, "q_hat": list[list[float]], "m_t": list[list[float]]} }
REENCRYPTED_QUERIES = {}

# Final k-NN results.
#   { result_id: {"indices": list[int]} }
RESULTS = {}

_state_lock = Lock()


def _bad(msg, status=400):
    return jsonify({"error": msg}), status


# -- Endpoints -----------------------------------------------------------------

@app.route("/dataset", methods=["POST"])
def upload_dataset():
    """DO uploads an already-encrypted dataset D'.

    Payload (JSON):
        { "enc_data": [[float, ...], ...] }   # shape (n, eta)
    """
    global ENC_DATA, ETA
    payload = request.get_json(force=True, silent=True) or {}
    enc_data = payload.get("enc_data")
    if not enc_data or not isinstance(enc_data, list):
        return _bad("missing 'enc_data' (list of rows)")
    arr = np.array(enc_data, dtype=float)
    if arr.ndim != 2:
        return _bad("'enc_data' must be a 2D array")
    with _state_lock:
        ENC_DATA = arr
        ETA = arr.shape[1]
        # Clear any in-flight queries tied to the previous dataset.
        PENDING_QUERIES.clear()
        REENCRYPTED_QUERIES.clear()
    os.makedirs(CLOUD_DIR, exist_ok=True)
    np.savetxt(os.path.join(CLOUD_DIR, "enc_data.csv"), arr, delimiter=",")
    return jsonify({"message": "dataset stored", "n": int(arr.shape[0]), "eta": int(ETA)})


@app.route("/query/submit", methods=["POST"])
def submit_query():
    """QU step-1 output: posts q_dot and gets back a query_id."""
    if ENC_DATA is None:
        return _bad("dataset not loaded", 409)
    payload = request.get_json(force=True, silent=True) or {}
    user_id = str(payload.get("user_id", "")).strip()
    q_dot = payload.get("q_dot")
    if not user_id:
        return _bad("missing 'user_id'")
    if not isinstance(q_dot, list) or not q_dot:
        return _bad("missing 'q_dot' (1D list)")
    query_id = str(uuid.uuid4())
    with _state_lock:
        PENDING_QUERIES[query_id] = {"user_id": user_id, "q_dot": list(map(float, q_dot))}
    return jsonify({"query_id": query_id})


@app.route("/query/pending", methods=["GET"])
def list_pending():
    """DO poll: returns every query awaiting step-2 re-encryption."""
    with _state_lock:
        pending = [
            {"query_id": qid, "user_id": entry["user_id"], "q_dot": entry["q_dot"]}
            for qid, entry in PENDING_QUERIES.items()
        ]
    return jsonify({"pending": pending, "eta": ETA})


@app.route("/query/reencrypt", methods=["POST"])
def reencrypt_query():
    """DO step-2 output: q_hat (eta x eta) and M_t (eta x eta) for a query_id."""
    payload = request.get_json(force=True, silent=True) or {}
    query_id = str(payload.get("query_id", "")).strip()
    q_hat = payload.get("q_hat")
    m_t = payload.get("m_t")
    if not query_id:
        return _bad("missing 'query_id'")
    if not isinstance(q_hat, list) or not isinstance(m_t, list):
        return _bad("missing 'q_hat' / 'm_t' (2D lists)")
    q_hat_arr = np.array(q_hat, dtype=float)
    m_t_arr = np.array(m_t, dtype=float)
    if q_hat_arr.ndim != 2 or m_t_arr.ndim != 2:
        return _bad("'q_hat' and 'm_t' must be 2D arrays")
    with _state_lock:
        entry = PENDING_QUERIES.pop(query_id, None)
        if entry is None:
            return _bad("query_id not in pending queue", 404)
        REENCRYPTED_QUERIES[query_id] = {
            "user_id": entry["user_id"],
            "q_hat": q_hat_arr.tolist(),
            "m_t": m_t_arr.tolist(),
        }
    return jsonify({"message": "re-encrypted", "query_id": query_id})


@app.route("/query/<query_id>/reencrypted", methods=["GET"])
def fetch_reencrypted(query_id: str):
    """QU poll: returns q_hat once the DO has processed the query."""
    with _state_lock:
        entry = REENCRYPTED_QUERIES.get(query_id)
    if entry is None:
        return jsonify({"ready": False})
    return jsonify({"ready": True, "q_hat": entry["q_hat"]})


@app.route("/query/<query_id>/finalize", methods=["POST"])
def finalize_query(query_id: str):
    """QU step-3 output: q_tilde_vec (length eta). Server runs k-NN."""
    if ENC_DATA is None:
        return _bad("dataset not loaded", 409)
    payload = request.get_json(force=True, silent=True) or {}
    q_tilde_vec = payload.get("q_tilde_vec")
    k = int(payload.get("k", 3))
    if not isinstance(q_tilde_vec, list) or not q_tilde_vec:
        return _bad("missing 'q_tilde_vec' (1D list)")
    with _state_lock:
        entry = REENCRYPTED_QUERIES.pop(query_id, None)
        if entry is None:
            return _bad("query_id not ready for finalization", 404)
        m_t = np.array(entry["m_t"], dtype=float)
        enc_data_local = ENC_DATA  # snapshot reference
    try:
        m_t_inv = np.linalg.inv(m_t)
    except np.linalg.LinAlgError:
        return _bad("M_t is singular; cannot invert", 422)
    d_double_prime = np.dot(enc_data_local, m_t_inv)
    q_vec = np.array(q_tilde_vec, dtype=float)
    if q_vec.shape[0] != d_double_prime.shape[1]:
        return _bad(
            f"q_tilde_vec length {q_vec.shape[0]} != eta {d_double_prime.shape[1]}",
            422,
        )
    indices = our_knn(d_double_prime, q_vec, k).astype(int).tolist()
    result_id = str(uuid.uuid4())
    with _state_lock:
        RESULTS[result_id] = {"indices": indices, "user_id": entry["user_id"]}
    return jsonify({"result_id": result_id, "indices": indices})


@app.route("/results/<result_id>", methods=["GET"])
def fetch_results(result_id: str):
    with _state_lock:
        entry = RESULTS.get(result_id)
    if entry is None:
        return _bad("result not found", 404)
    return jsonify(entry)


# -- Frontend (served from same origin so the browser has no CORS friction) ---

@app.route("/", methods=["GET"])
def serve_index():
    return send_from_directory(os.path.join(FRONTEND_DIR, "public"), "index.html")


@app.route("/public/<path:filename>", methods=["GET"])
def serve_public(filename: str):
    return send_from_directory(os.path.join(FRONTEND_DIR, "public"), filename)


@app.route("/src/<path:filename>", methods=["GET"])
def serve_src(filename: str):
    return send_from_directory(os.path.join(FRONTEND_DIR, "src"), filename)


@app.route("/health", methods=["GET"])
def health():
    with _state_lock:
        return jsonify({
            "dataset_loaded": ENC_DATA is not None,
            "eta": ETA,
            "pending": len(PENDING_QUERIES),
            "reencrypted": len(REENCRYPTED_QUERIES),
            "results": len(RESULTS),
        })


if __name__ == "__main__":
    # Default to 5050 because macOS Monterey+ binds AirPlay Receiver to 5000.
    port = int(os.environ.get("PORT", "5050"))
    app.run(host="127.0.0.1", port=port, debug=True)

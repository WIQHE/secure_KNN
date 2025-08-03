import os
import uuid

import numpy as np
from flask import Flask, jsonify, request

from secure_knn import (
    encrypt_original_data_user_cloud,
    generate_and_save_secrets,
    get_max_norm,
    our_knn,
)

app = Flask(__name__)

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.getcwd(), "data_user"))
CLOUD_DIR = os.environ.get("CLOUD_DIR", os.path.join(os.getcwd(), "cloud"))
SECRETS_DIR = os.path.join(DATA_DIR, "secrets")

# In-memory stores
RESULTS = {}
ENC_DATA = None


@app.route("/dataset", methods=["POST"])
def upload_dataset():
    """Upload a dataset and store its encrypted form."""
    global ENC_DATA
    if "file" not in request.files:
        return jsonify({"error": "missing file"}), 400
    file = request.files["file"]
    original_data = np.loadtxt(file, delimiter=",")
    max_norm = get_max_norm(original_data)
    n, d = original_data.shape
    c = int(request.form.get("c", 5))
    ep = int(request.form.get("ep", 3))
    eta = d + 1 + c + ep
    m_base, sec_vector, w_vector = generate_and_save_secrets(
        eta, c, d, SECRETS_DIR
    )
    m_base_inv = np.linalg.inv(m_base)
    ENC_DATA = encrypt_original_data_user_cloud(
        original_data, sec_vector, m_base_inv, w_vector, ep
    )
    os.makedirs(CLOUD_DIR, exist_ok=True)
    np.savetxt(os.path.join(CLOUD_DIR, "enc_data.csv"), ENC_DATA, delimiter=",")
    return jsonify({"message": "dataset uploaded", "max_norm": max_norm})


@app.route("/query", methods=["POST"])
def query_dataset():
    """Submit an encrypted query vector and run k-NN."""
    if ENC_DATA is None:
        return jsonify({"error": "dataset not loaded"}), 400
    payload = request.get_json(force=True)
    vector = np.array(payload.get("vector", []))
    k = int(payload.get("k", 3))
    result = our_knn(ENC_DATA, vector, k).astype(int).tolist()
    result_id = str(uuid.uuid4())
    RESULTS[result_id] = result
    return jsonify({"id": result_id})


@app.route("/results/<result_id>", methods=["GET"])
def fetch_results(result_id: str):
    """Retrieve results for a previously submitted query."""
    if result_id not in RESULTS:
        return jsonify({"error": "result not found"}), 404
    return jsonify({"result": RESULTS[result_id]})


if __name__ == "__main__":
    app.run(debug=True)

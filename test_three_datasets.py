import os
import io
import time
import numpy as np
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test_datasets.db"

from fastapi_app import app
from database import engine, Base

Base.metadata.create_all(bind=engine)
client = TestClient(app)

def generate_csv_bytes(data):
    s_io = io.BytesIO()
    np.savetxt(s_io, data, delimiter=",")
    s_io.seek(0)
    return s_io.read()

def run_test_case(name, data, query, k, c, ep):
    print(f"\n==================================================")
    print(f"TEST CASE: {name}")
    print(f"==================================================")
    
    # 1. Create a session
    resp = client.post("/sessions")
    assert resp.status_code == 200
    session_id = resp.json()["session_id"]
    print(f"Session Created: {session_id}")
    
    # 2. Upload dataset CSV
    csv_bytes = generate_csv_bytes(data)
    upload_resp = client.post(
        f"/sessions/{session_id}/upload",
        files={"file": (f"{name}.csv", csv_bytes, "text/csv")}
    )
    assert upload_resp.status_code == 200, upload_resp.text
    print(f"Uploaded Dataset. Shape: {data.shape}")
    
    # Save the original query in the database for the pipeline
    from db_utils import save_numpy_to_db
    from database import get_db
    db = next(get_db())
    save_numpy_to_db(db, session_id, "query_og", query)
    print(f"Set Query Vector. Length: {len(query)}")
    
    # 3. Run full secure pipeline (starting from query_stage1 since data is uploaded)
    pipeline_resp = client.post(f"/sessions/{session_id}/pipeline/run", json={
        "steps": [
            "query_stage1",
            "data_owner",
            "query_stage2",
            "cloud_knn"
        ],
        "params": {
            "data_owner": {"c": c, "ep": ep},
            "cloud_knn": {"k": k}
        }
    })
    assert pipeline_resp.status_code == 200, pipeline_resp.text
    secure_duration = pipeline_resp.json()["duration_sec"]
    print(f"Secure k-NN pipeline completed in {secure_duration:.4f} seconds.")
    
    # 4. Run baseline plaintext k-NN
    baseline_resp = client.post(f"/sessions/{session_id}/baseline_knn", json={"k": k})
    assert baseline_resp.status_code == 200, baseline_resp.text
    baseline_duration = float(baseline_resp.json()["result"]["duration_sec"])
    print(f"Plaintext k-NN completed in {baseline_duration:.4f} seconds.")
    
    # 5. Verify accuracy
    status_resp = client.get(f"/sessions/{session_id}/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    secure_indices = status_data["secure_knn_indices"]
    baseline_indices = status_data["baseline_knn_indices"]
    
    print(f"\nRESULTS for {name} (K = {k}):")
    print(f"  Secure k-NN indices:   {secure_indices}")
    print(f"  Baseline k-NN indices: {baseline_indices}")
    
    # Accuracy validation
    match = secure_indices == baseline_indices
    if match:
        print(f"  ✅ SUCCESS: Exact 100% match!")
    else:
        print(f"  ❌ FAILURE: Indices mismatch!")
    
    # Display relative timing
    overhead = secure_duration - baseline_duration
    print(f"  Cryptographic overhead: {overhead * 1000:.2f} ms")
    
    # Cleanup session
    client.post(f"/sessions/{session_id}/cleanup")
    
    return match, secure_indices, baseline_indices

def main():
    os.makedirs("sample_data", exist_ok=True)
    
    np.random.seed(42)
    
    # --- Dataset 1: Low-Dimensional Space ---
    # 20 samples, 2D coordinates, query for K=3
    low_dim_data = np.random.randint(0, 100, size=(20, 2)).astype(float)
    low_dim_query = np.random.randint(0, 100, size=2).astype(float)
    np.savetxt("sample_data/low_dim_2d.csv", low_dim_data, delimiter=",")
    np.savetxt("sample_data/low_dim_query.csv", low_dim_query, delimiter=",")
    
    # --- Dataset 2: Medium-Dimensional Space ---
    # 100 samples, 8D coordinates, query for K=5
    med_dim_data = np.random.randn(100, 8) * 50
    med_dim_query = np.random.randn(8) * 50
    np.savetxt("sample_data/med_dim_8d.csv", med_dim_data, delimiter=",")
    np.savetxt("sample_data/med_dim_query.csv", med_dim_query, delimiter=",")
    
    # --- Dataset 3: High-Dimensional Space ---
    # 500 samples, 20D coordinates, query for K=10
    high_dim_data = np.random.randn(500, 20) * 100
    high_dim_query = np.random.randn(20) * 100
    np.savetxt("sample_data/high_dim_20d.csv", high_dim_data, delimiter=",")
    np.savetxt("sample_data/high_dim_query.csv", high_dim_query, delimiter=",")
    
    print("Successfully generated all three CSV datasets under 'sample_data/'.")
    
    # Run the tests
    r1, s1, b1 = run_test_case("Low-Dim (2D)", low_dim_data, low_dim_query, k=3, c=3, ep=2)
    r2, s2, b2 = run_test_case("Med-Dim (8D)", med_dim_data, med_dim_query, k=5, c=5, ep=3)
    r3, s3, b3 = run_test_case("High-Dim (20D)", high_dim_data, high_dim_query, k=10, c=8, ep=5)
    
    print("\n" + "="*50)
    print("FINAL SUMMARY REPORT")
    print("="*50)
    print(f"1. Low-Dim 2D (K=3):   {'SUCCESS (100% Match)' if r1 else 'FAILED'} -> Secure: {s1}")
    print(f"2. Med-Dim 8D (K=5):   {'SUCCESS (100% Match)' if r2 else 'FAILED'} -> Secure: {s2}")
    print(f"3. High-Dim 20D (K=10): {'SUCCESS (100% Match)' if r3 else 'FAILED'} -> Secure: {s3}")
    print("="*50)

if __name__ == "__main__":
    try:
        main()
    finally:
        if os.path.exists("./test_datasets.db"):
            os.remove("./test_datasets.db")

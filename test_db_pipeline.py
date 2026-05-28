import os
from fastapi.testclient import TestClient

# We will use SQLite for testing so it doesn't require a running postgres container.
# This proves the DB integration works regardless of the engine.
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from fastapi_app import app
from database import engine, Base
from models import PipelineSession, Artifact

# Create tables in sqlite
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_full_pipeline():
    print("Creating new session...")
    response = client.post("/sessions")
    assert response.status_code == 200
    session_id = response.json()["session_id"]
    print(f"Session ID: {session_id}")
    
    print("Running full pipeline...")
    response = client.post(f"/sessions/{session_id}/pipeline/run", json={
        "steps": [
            "generate_data",
            "generate_query",
            "query_stage1",
            "data_owner",
            "query_stage2",
            "cloud_knn"
        ],
        "params": {
            "generate_data": {"n": 20, "d": 5},
            "generate_query": {"d": 5},
            "data_owner": {"c": 3, "ep": 2},
            "cloud_knn": {"k": 3}
        }
    })
    
    assert response.status_code == 200, response.text
    print("Pipeline completed successfully!")
    print(f"Duration: {response.json()['duration_sec']:.2f} seconds")
    
    print("Getting session status...")
    status_resp = client.get(f"/sessions/{session_id}/status")
    assert status_resp.status_code == 200
    artifacts = status_resp.json()["artifacts"]
    print(f"Artifacts generated: {len(artifacts)}")
    assert len(artifacts) > 10

    print("Running baseline plaintext k-NN...")
    baseline_resp = client.post(f"/sessions/{session_id}/baseline_knn", json={"k": 3})
    assert baseline_resp.status_code == 200

    print("Verifying secure k-NN matches baseline...")
    status_resp = client.get(f"/sessions/{session_id}/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    secure_indices = status_data["secure_knn_indices"]
    baseline_indices = status_data["baseline_knn_indices"]
    print(f"Secure k-NN indices:   {secure_indices}")
    print(f"Baseline k-NN indices: {baseline_indices}")
    assert secure_indices == baseline_indices, f"Mismatch! Secure: {secure_indices}, Baseline: {baseline_indices}"
    print("SUCCESS: Secure k-NN matches plaintext k-NN exactly!")

if __name__ == "__main__":
    test_full_pipeline()
    # Cleanup local sqlite test DB
    if os.path.exists("./test.db"):
        os.remove("./test.db")

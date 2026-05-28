"""FastAPI backend exposing the secure k-NN pipeline with PostgreSQL session isolation.

Endpoints:
  GET  /sessions               List all sessions
  POST /sessions               Create a new pipeline session
  GET  /sessions/{id}/status   Current artefact presence + session info
  POST /sessions/{id}/upload   Upload custom dataset
  POST /sessions/{id}/baseline_knn Run plaintext k-NN
  POST /sessions/{id}/pipeline/run           Run full pipeline
  POST /sessions/{id}/pipeline/step/{name}   Run an individual step
  POST /sessions/{id}/cleanup                Delete generated artefacts for session
"""
from __future__ import annotations

import time
import io
from typing import List, Dict, Any

import numpy as np
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import uuid

from database import get_db, engine, Base
from models import PipelineSession, Artifact
from db_utils import save_numpy_to_db, load_numpy_from_db, save_float_to_db, load_float_from_db

# Auto-create tables (for POC, usually use Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Secure k-NN Pipeline API (PostgreSQL)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev purposes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Low-level step functions ---------- #

def step_generate_data(db: Session, session_id: str, n: int = 10, d: int = 8, c: int = 5, ep: int = 3) -> Dict[str, Any]:
    # Check if a custom dataset is already uploaded
    existing = load_numpy_from_db(db, session_id, "data_og")
    if existing is not None:
        n, d = existing.shape
        return {"shape": list(existing.shape), "n": n, "d": d, "note": "Using uploaded dataset"}
        
    data = np.random.randint(0, 100, size=(n, d))
    save_numpy_to_db(db, session_id, "data_og", data)
    return {"shape": list(data.shape), "n": n, "d": d, "note": "Generated synthetic dataset"}


def step_generate_query(db: Session, session_id: str, d: int = 8, c: int = 5, ep: int = 3) -> Dict[str, Any]:
    existing_data = load_numpy_from_db(db, session_id, "data_og")
    if existing_data is not None:
        d = existing_data.shape[1]
        
    q = np.random.randint(0, 100, size=d)
    save_numpy_to_db(db, session_id, "query_og", q)
    return {"length": int(len(q))}


def step_query_stage1(db: Session, session_id: str) -> Dict[str, Any]:
    q_0 = load_numpy_from_db(db, session_id, "query_og")
    if q_0 is None:
        raise HTTPException(status_code=400, detail="query_og missing. Run generate_query first.")
    if q_0.ndim != 1:
        q_0 = q_0.flatten()
    d = len(q_0)
    N = np.zeros((d, d))
    beta_1 = np.array([1.0])
    for i in range(d):
        N[i][i] = np.random.randint(1, 10)
    enc_q = np.dot(q_0, beta_1 * N)
    
    save_numpy_to_db(db, session_id, "enc_query_1", enc_q)
    save_numpy_to_db(db, session_id, "N", N, is_secret=True)
    save_float_to_db(db, session_id, "beta_1", float(beta_1[0]), is_secret=True)
    return {"enc_query_shape": list(np.atleast_1d(enc_q).shape), "beta_1": float(beta_1[0])}


def generate_m_temp(eta: int, q_max: float, max_norm: float) -> np.ndarray:
    while True:
        matrix = np.random.rand(eta, eta)
        np.fill_diagonal(matrix, np.random.randint(int(max_norm) * 10000, int(max_norm) * 10000 + 100000, size=eta))
        mask = np.eye(eta, dtype=bool)
        matrix[~mask] = np.random.randint(int(q_max), int(q_max) + 100, size=eta * eta - eta)
        if np.linalg.det(matrix) != 0:
            return matrix


def get_max_norm(matrix: np.ndarray) -> float:
    return float(np.max(np.linalg.norm(matrix, axis=1)))


def encrypt_original_data_user_cloud(original_data: np.ndarray, sec_vector: np.ndarray, m_base_inv: np.ndarray, w_vector: np.ndarray, ep: int) -> np.ndarray:
    n, d = original_data.shape
    eta = len(m_base_inv[0])
    encrypted_original_data = np.zeros((n, eta))
    for i in range(n):
        pi = original_data[i]
        encrypted_pi = sec_vector[:d] - 2 * pi
        norm_squared = np.sum(pi[:d] ** 2)
        pi_dplus1 = sec_vector[d] + norm_squared
        extra_cols = np.concatenate((encrypted_pi, [pi_dplus1]))
        z_vector = np.random.randint(0, 100, size=ep)
        final_pi = np.concatenate((extra_cols, w_vector))
        final_pi = np.concatenate((final_pi, z_vector))
        encrypted_original_data[i] = final_pi
    return np.dot(encrypted_original_data, m_base_inv)


def step_data_owner(db: Session, session_id: str, c: int = 5, ep: int = 3) -> Dict[str, Any]:
    original_data = load_numpy_from_db(db, session_id, "data_og")
    enc_q1 = load_numpy_from_db(db, session_id, "enc_query_1")
    
    if original_data is None:
        raise HTTPException(status_code=400, detail="data_og missing. Run generate_data first.")
    if enc_q1 is None:
        raise HTTPException(status_code=400, detail="enc_query_1 missing. Run query_stage1 first.")
        
    if original_data.ndim == 1:
        original_data = original_data.reshape(1, -1)
    n, d = original_data.shape
    eta = d + 1 + c + ep
    
    # Check secrets or generate
    m_base = load_numpy_from_db(db, session_id, "m_base")
    if m_base is None:
        while True:
            m_base = np.random.randint(0, 100, size=(eta, eta))
            if np.linalg.det(m_base) != 0:
                break
        sec_vector = np.random.randint(0, 10, size=d + 1)
        w_vector = np.random.randint(0, 10, size=c)
        save_numpy_to_db(db, session_id, "m_base", m_base, is_secret=True)
        save_numpy_to_db(db, session_id, "sec_vector", sec_vector, is_secret=True)
        save_numpy_to_db(db, session_id, "w_vector", w_vector, is_secret=True)
    else:
        sec_vector = load_numpy_from_db(db, session_id, "sec_vector")
        w_vector = load_numpy_from_db(db, session_id, "w_vector")
        
    m_base_inv = np.linalg.inv(m_base)
    
    # Encrypt dataset if not already
    enc_data = load_numpy_from_db(db, session_id, "enc_data_cloud_1")
    if enc_data is None:
        enc_data = encrypt_original_data_user_cloud(original_data, sec_vector, m_base_inv, w_vector, ep)
        save_numpy_to_db(db, session_id, "enc_data_cloud_1", enc_data)
        
    # Query processing
    q_max = float(np.max(enc_q1))
    max_norm = get_max_norm(original_data)
    m_temp = generate_m_temp(eta, q_max, max_norm)
    q_dash = np.concatenate((np.atleast_1d(enc_q1), [1], np.random.randint(0, 10, size=c), np.zeros(ep)))
    q_eta = np.diag(q_dash)
    m_sec = np.dot(m_temp, m_base)
    beta_2 = np.random.rand()
    err = np.random.randint(int(q_max), int(q_max) + 100, size=(eta, eta))
    q_enc_final = beta_2 * (np.dot(m_sec, q_eta) + err)
    
    save_numpy_to_db(db, session_id, "user_1_m_temp", m_temp)
    save_float_to_db(db, session_id, "beta_2", float(beta_2), is_secret=True)
    save_numpy_to_db(db, session_id, "err", err, is_secret=True)
    save_numpy_to_db(db, session_id, "enc_query_2", q_enc_final)
    
    return {"eta": eta}


def step_query_stage2(db: Session, session_id: str) -> Dict[str, Any]:
    enc_q_final = load_numpy_from_db(db, session_id, "enc_query_2")
    if enc_q_final is None:
        raise HTTPException(status_code=400, detail="enc_query_2 missing. Run data_owner step first.")
        
    N = load_numpy_from_db(db, session_id, "N")
    eta = enc_q_final.shape[0] if enc_q_final.ndim > 1 else len(enc_q_final)
    d = N.shape[0]
    
    N_values = np.dot(np.ones(d), N)
    N_values = np.concatenate((N_values, np.ones(eta - d)))
    N_dash = np.diag(N_values)
    N_dash_inv = np.linalg.inv(N_dash)
    
    q_dash_enc = np.dot(enc_q_final, N_dash_inv)
    q_dash_vec = np.ones(eta)
    for i in range(eta):
        q_dash_vec[i] = np.sum(q_dash_enc[i][:eta]) if q_dash_enc.ndim > 1 else q_dash_enc[i]
        
    save_numpy_to_db(db, session_id, "q_dash_vec", q_dash_vec)
    save_numpy_to_db(db, session_id, "n_dash_inv", N_dash_inv, is_secret=True)
    
    return {"q_dash_vec_len": int(len(q_dash_vec))}


def transform_data_for_query(original_enc_data: np.ndarray, m_temp: np.ndarray) -> np.ndarray:
    n, eta = original_enc_data.shape
    m_temp_inv = np.linalg.inv(m_temp)
    transformed_data = np.zeros((n, eta))
    for i in range(n):
        transformed_data[i] = np.dot(original_enc_data[i], m_temp_inv)
    return transformed_data


def step_cloud_knn(db: Session, session_id: str, k: int = 3) -> Dict[str, Any]:
    og_enc_data = load_numpy_from_db(db, session_id, "enc_data_cloud_1")
    q_cloud = load_numpy_from_db(db, session_id, "q_dash_vec")
    m_temp = load_numpy_from_db(db, session_id, "user_1_m_temp")
    
    if og_enc_data is None or q_cloud is None or m_temp is None:
        raise HTTPException(status_code=400, detail="Missing prerequisites. Run all previous steps.")
        
    if og_enc_data.ndim == 1:
        og_enc_data = og_enc_data.reshape(1, -1)
        
    trans_enc_data = transform_data_for_query(og_enc_data, m_temp)
    distance_vec = np.dot(trans_enc_data, q_cloud)
    idx = np.round(np.argsort(distance_vec)[:k]).astype(int)
    
    save_numpy_to_db(db, session_id, "knnResult", idx)
    return {"k": k, "indices": idx.tolist()}


def compute_baseline_knn(db: Session, session_id: str, k: int = 3):
    data_og = load_numpy_from_db(db, session_id, "data_og")
    query_og = load_numpy_from_db(db, session_id, "query_og")
    
    if data_og is None or query_og is None:
        raise HTTPException(status_code=400, detail="Missing plaintext data or query.")
        
    start_time = time.time()
    # Euclidean distance
    distances = np.linalg.norm(data_og - query_og, axis=1)
    idx = np.argsort(distances)[:k]
    end_time = time.time()
    
    save_numpy_to_db(db, session_id, "baselineKnnResult", idx.astype(int))
    return {
        "k": k,
        "indices": idx.tolist(),
        "duration_sec": end_time - start_time
    }

# ---------- API Schemas ---------- #

class GenerateDataRequest(BaseModel):
    n: int = 10
    d: int = 8
    c: int = 5
    ep: int = 3
    return_data: bool = False

class GenerateQueryRequest(BaseModel):
    d: int = 8
    return_data: bool = False

class QueryStage1Request(BaseModel):
    return_data: bool = False

class DataOwnerRequest(BaseModel):
    c: int = 5
    ep: int = 3
    return_data: bool = False

class QueryStage2Request(BaseModel):
    return_data: bool = False

class CloudKNNRequest(BaseModel):
    k: int = 3
    return_data: bool = False

class BaselineKNNRequest(BaseModel):
    k: int = 3
    return_data: bool = False

class CleanupRequest(BaseModel):
    keep_secrets: bool = False

class PipelineRunRequest(BaseModel):
    steps: List[str] | None = Field(default=None, description="Ordered subset of steps to run; default is full pipeline")
    params: Dict[str, Dict[str, Any]] | None = Field(default=None, description="Per-step parameter overrides")

class PipelineRunResponse(BaseModel):
    session_id: str
    steps: List[str]
    duration_sec: float
    results: Dict[str, Any]


STEP_FUNCTIONS = {
    "generate_data": step_generate_data,
    "generate_query": step_generate_query,
    "query_stage1": step_query_stage1,
    "data_owner": step_data_owner,
    "query_stage2": step_query_stage2,
    "cloud_knn": step_cloud_knn,
}

# ---------- API Routes ---------- #

def _check_session(db: Session, session_id: str):
    try:
        uid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format")
    session = db.query(PipelineSession).filter(PipelineSession.id == uid).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

def _maybe_inline_array(db: Session, session_id: str, name: str, return_data: bool):
    if not return_data:
        return None
    arr = load_numpy_from_db(db, session_id, name)
    if arr is None:
        return None
    if arr.size > 2000:
        return {"shape": list(arr.shape), "truncated": True}
    return arr.tolist()


@app.get("/sessions")
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(PipelineSession).order_by(PipelineSession.created_at.desc()).all()
    return [{"id": str(s.id), "status": s.status, "dataset_name": s.dataset_name, "created_at": s.created_at, "secure_duration": s.secure_duration, "baseline_duration": s.baseline_duration} for s in sessions]


@app.post("/sessions")
def create_session(dataset_name: str = Form("Smoke Test"), db: Session = Depends(get_db)):
    new_session = PipelineSession(dataset_name=dataset_name)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return {"session_id": str(new_session.id), "status": new_session.status, "dataset_name": new_session.dataset_name}


@app.get("/sessions/{session_id}/status")
def session_status(session_id: str, db: Session = Depends(get_db)):
    session = _check_session(db, session_id)
    uid = uuid.UUID(session_id)
    artifacts = db.query(Artifact).filter(Artifact.session_id == uid).all()
    artifact_names = [a.name for a in artifacts]

    # Load result indices for correctness comparison
    secure_indices = load_numpy_from_db(db, session_id, "knnResult")
    baseline_indices = load_numpy_from_db(db, session_id, "baselineKnnResult")
    data_og = load_numpy_from_db(db, session_id, "data_og")
    query_og = load_numpy_from_db(db, session_id, "query_og")

    return {
        "session_id": session_id, 
        "dataset_name": session.dataset_name,
        "status": session.status,
        "secure_duration": session.secure_duration,
        "baseline_duration": session.baseline_duration,
        "artifacts": artifact_names,
        "secure_knn_indices": secure_indices.astype(int).tolist() if secure_indices is not None else None,
        "baseline_knn_indices": baseline_indices.astype(int).tolist() if baseline_indices is not None else None,
        "data_og": data_og.tolist() if data_og is not None and data_og.size <= 2000 else None,
        "query_og": query_og.tolist() if query_og is not None else None,
    }


@app.post("/sessions/{session_id}/upload")
async def upload_dataset(session_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    session = _check_session(db, session_id)
    content = await file.read()
    try:
        # Expecting a CSV file
        data = np.genfromtxt(io.BytesIO(content), delimiter=',')
        if np.isnan(data).all():
            raise ValueError("Could not parse numeric data from CSV")
        save_numpy_to_db(db, session_id, "data_og", data)
        
        session.dataset_name = file.filename
        db.commit()
        return {"message": "Dataset uploaded successfully", "shape": list(data.shape)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")


@app.post("/sessions/{session_id}/baseline_knn")
def api_baseline_knn(session_id: str, req: BaselineKNNRequest, db: Session = Depends(get_db)):
    session = _check_session(db, session_id)
    res = compute_baseline_knn(db, session_id, req.k)
    session.baseline_duration = str(res["duration_sec"])
    db.commit()
    
    if req.return_data:
        res["data_og"] = _maybe_inline_array(db, session_id, "data_og", True)
        res["query_og"] = _maybe_inline_array(db, session_id, "query_og", True)
    return {"step": "baseline_knn", "result": res}


@app.post("/sessions/{session_id}/pipeline/step/generate_data")
def api_generate_data(session_id: str, req: GenerateDataRequest, db: Session = Depends(get_db)):
    _check_session(db, session_id)
    result = step_generate_data(db, session_id, req.n, req.d, req.c, req.ep)
    if req.return_data:
        result["data"] = _maybe_inline_array(db, session_id, "data_og", True)
    return {"step": "generate_data", "result": result}


@app.post("/sessions/{session_id}/pipeline/step/generate_query")
def api_generate_query(session_id: str, req: GenerateQueryRequest, db: Session = Depends(get_db)):
    _check_session(db, session_id)
    result = step_generate_query(db, session_id, req.d)
    if req.return_data:
        result["query"] = _maybe_inline_array(db, session_id, "query_og", True)
    return {"step": "generate_query", "result": result}


@app.post("/sessions/{session_id}/pipeline/step/query_stage1")
def api_query_stage1(session_id: str, req: QueryStage1Request, db: Session = Depends(get_db)):
    _check_session(db, session_id)
    result = step_query_stage1(db, session_id)
    if req.return_data:
        result["enc_query_1"] = _maybe_inline_array(db, session_id, "enc_query_1", True)
    return {"step": "query_stage1", "result": result}


@app.post("/sessions/{session_id}/pipeline/step/data_owner")
def api_data_owner(session_id: str, req: DataOwnerRequest, db: Session = Depends(get_db)):
    _check_session(db, session_id)
    result = step_data_owner(db, session_id, req.c, req.ep)
    if req.return_data:
        result["enc_data"] = _maybe_inline_array(db, session_id, "enc_data_cloud_1", True)
        result["m_temp"] = _maybe_inline_array(db, session_id, "user_1_m_temp", True)
    return {"step": "data_owner", "result": result}


@app.post("/sessions/{session_id}/pipeline/step/query_stage2")
def api_query_stage2(session_id: str, req: QueryStage2Request, db: Session = Depends(get_db)):
    _check_session(db, session_id)
    result = step_query_stage2(db, session_id)
    if req.return_data:
        result["q_dash_vec"] = _maybe_inline_array(db, session_id, "q_dash_vec", True)
    return {"step": "query_stage2", "result": result}


@app.post("/sessions/{session_id}/pipeline/step/cloud_knn")
def api_cloud_knn(session_id: str, req: CloudKNNRequest, db: Session = Depends(get_db)):
    _check_session(db, session_id)
    result = step_cloud_knn(db, session_id, req.k)
    if req.return_data:
        result["knn_indices"] = _maybe_inline_array(db, session_id, "knnResult", True)
    return {"step": "cloud_knn", "result": result}


@app.post("/sessions/{session_id}/pipeline/run", response_model=PipelineRunResponse)
def run_full_pipeline(session_id: str, req: PipelineRunRequest, db: Session = Depends(get_db)):
    session = _check_session(db, session_id)
    start = time.time()
    
    session.status = "running"
    db.commit()

    results: Dict[str, Any] = {}
    default_order = [
        "generate_data",
        "generate_query",
        "query_stage1",
        "data_owner",
        "query_stage2",
        "cloud_knn",
    ]
    ordered = req.steps or default_order
    params = req.params or {}
    
    try:
        for step in ordered:
            if step not in STEP_FUNCTIONS:
                raise HTTPException(status_code=400, detail=f"Unknown step in pipeline: {step}")
            kwargs = params.get(step, {})
            results[step] = STEP_FUNCTIONS[step](db=db, session_id=session_id, **kwargs)
        
        session.status = "completed"
    except Exception as e:
        session.status = f"failed: {str(e)}"
        db.commit()
        raise e
    finally:
        end = time.time()
        duration = end - start
        session.secure_duration = str(duration)
        db.commit()
        
    return PipelineRunResponse(
        session_id=session_id, 
        steps=ordered, 
        duration_sec=duration, 
        results=results
    )


@app.post("/sessions/{session_id}/cleanup")
def cleanup(session_id: str, req: CleanupRequest, db: Session = Depends(get_db)):
    _check_session(db, session_id)
    uid = uuid.UUID(session_id)
    query = db.query(Artifact).filter(Artifact.session_id == uid)
    if req.keep_secrets:
        query = query.filter(Artifact.is_secret == False)
    
    deleted_count = query.delete(synchronize_session=False)
    db.commit()
    return {"deleted_artifacts": deleted_count}


# Serve built static files from Vite app
import os
dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")
if os.path.exists(dist_dir):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")
    
    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(dist_dir, "index.html"))
else:
    @app.get("/")
    def root():
        return {"message": "Secure k-NN pipeline API (PostgreSQL). See /docs for interactive spec."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("fastapi_app:app", host="0.0.0.0", port=8000, reload=True)

import io
import numpy as np
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from models import Artifact

def save_numpy_to_db(db: Session, session_id: str, name: str, array: np.ndarray, is_secret: bool = False):
    """Saves a numpy array to the database as binary data."""
    out_stream = io.BytesIO()
    np.save(out_stream, array)
    binary_data = out_stream.getvalue()

    # Update or Create
    uid = uuid.UUID(session_id)
    artifact = db.query(Artifact).filter(Artifact.session_id == uid, Artifact.name == name).first()
    if artifact:
        artifact.data = binary_data
        artifact.is_secret = is_secret
    else:
        artifact = Artifact(session_id=uid, name=name, data=binary_data, is_secret=is_secret)
        db.add(artifact)
    
    db.commit()

def load_numpy_from_db(db: Session, session_id: str, name: str) -> Optional[np.ndarray]:
    """Loads a numpy array from the database."""
    uid = uuid.UUID(session_id)
    artifact = db.query(Artifact).filter(Artifact.session_id == uid, Artifact.name == name).first()
    if not artifact or not artifact.data:
        return None
    
    in_stream = io.BytesIO(artifact.data)
    array = np.load(in_stream)
    return array

def save_float_to_db(db: Session, session_id: str, name: str, value: float, is_secret: bool = False):
    """Saves a single float/scalar as a 1D numpy array."""
    save_numpy_to_db(db, session_id, name, np.array([value]), is_secret)

def load_float_from_db(db: Session, session_id: str, name: str) -> Optional[float]:
    """Loads a single float/scalar from a 1D numpy array."""
    arr = load_numpy_from_db(db, session_id, name)
    if arr is not None and len(arr) > 0:
        return float(arr[0])
    return None

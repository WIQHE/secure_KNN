import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base

class PipelineSession(Base):
    __tablename__ = "pipeline_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="created")
    dataset_name = Column(String, default="Smoke Test")
    secure_duration = Column(String, nullable=True)
    baseline_duration = Column(String, nullable=True)

    artifacts = relationship("Artifact", back_populates="session", cascade="all, delete")

class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("pipeline_sessions.id"), index=True)
    name = Column(String, index=True)
    data = Column(LargeBinary, nullable=True)
    is_secret = Column(Boolean, default=False)

    session = relationship("PipelineSession", back_populates="artifacts")

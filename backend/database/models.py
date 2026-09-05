from sqlalchemy import Column, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String(255), unique=True, nullable=False)
    device_id = Column(String(255), nullable=True)
    status = Column(String(64), default="NORMAL")
    trust_score = Column(Float, default=0.5)
    trust_level = Column(String(32), default="MEDIUM")
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)


class TelemetryRecord(Base):
    __tablename__ = "telemetry"
    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String(255), nullable=False, index=True)
    message_id = Column(String(255), nullable=False)
    sequence = Column(Integer, nullable=False)
    timestamp = Column(Float, nullable=False)
    posx = Column(Float, nullable=False)
    posy = Column(Float, nullable=False)
    posz = Column(Float, nullable=False)
    spdx = Column(Float, nullable=False)
    spdy = Column(Float, nullable=False)
    spdz = Column(Float, nullable=False)
    aclx = Column(Float, nullable=False)
    acly = Column(Float, nullable=False)
    aclz = Column(Float, nullable=False)
    hedx = Column(Float, nullable=False)
    hedy = Column(Float, nullable=False)
    hedz = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=True)
    __table_args__ = (UniqueConstraint("vehicle_id", "message_id", "sequence", name="ux_vehicle_message_seq"),)


class PredictionRecord(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String(255), nullable=False, index=True)
    telemetry_id = Column(Integer, nullable=True)
    class_id = Column(Integer, nullable=False)
    label = Column(String(128), nullable=False)
    confidence = Column(Float, nullable=False)
    model_version = Column(String(64), default="1.0.0")
    created_at = Column(DateTime, nullable=True)


class TrustHistoryRecord(Base):
    __tablename__ = "trust_scores"
    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String(255), nullable=False, index=True)
    score = Column(Float, nullable=False)
    previous_score = Column(Float, nullable=False)
    classification = Column(String(128), nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)


class SecurityEvent(Base):
    __tablename__ = "security_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String(255), nullable=False, index=True)
    event_type = Column(String(128), nullable=False)
    severity = Column(String(32), default="MEDIUM")
    description = Column(Text, nullable=True)
    message_id = Column(String(255), nullable=True)
    timestamp = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=True)


class ShardRecord(Base):
    __tablename__ = "shards"
    id = Column(Integer, primary_key=True, autoincrement=True)
    shard_id = Column(String(64), unique=True, nullable=False)
    validator = Column(String(255), nullable=True)
    vehicle_count = Column(Integer, default=0)
    updated_at = Column(DateTime, nullable=True)


class ValidatorRecord(Base):
    __tablename__ = "validators"
    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String(255), unique=True, nullable=False)
    shard_id = Column(String(64), nullable=True)
    trust_score = Column(Float, default=0.5)
    status = Column(String(32), default="ACTIVE")
    updated_at = Column(DateTime, nullable=True)


class LedgerEvent(Base):
    __tablename__ = "ledger_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    shard_id = Column(String(64), nullable=False)
    validator = Column(String(255), nullable=False)
    index = Column(Integer, nullable=False)
    previous_hash = Column(String(255), nullable=True)
    current_hash = Column(String(255), nullable=True)
    payload = Column(Text, nullable=False)
    timestamp = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=True)

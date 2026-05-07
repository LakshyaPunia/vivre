from supabase import create_client, Client
from app.config import get_settings
import uuid
from datetime import datetime, timezone
from typing import Any

_client: Client | None = None


def get_db() -> Client | None:
    global _client
    settings = get_settings()
    if not settings.supabase_enabled:
        return None
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _client


# ── In-memory fallback store (dev mode, no Supabase) ────────────
_store: dict[str, list] = {
    "vitals_readings": [],
    "alerts": [],
    "location_logs": [],
}


_VITALS_COLUMNS = {
    "id", "patient_id", "device_id", "timestamp",
    "heart_rate", "spo2", "systolic_bp", "diastolic_bp", "body_temp",
    "respiratory_rate", "glucose_level", "activity_score", "sleep_quality",
    "stress_level", "hydration_level", "fall_detected", "fall_frequency",
    "ecg_abnormality", "medication_adherence",
    "heart_rate_alert", "spo2_alert", "bp_alert", "temp_alert",
    "predicted_disease", "disease_confidence", "health_score", "health_band",
    "is_anomaly", "created_at",
}


def store_vitals(reading: dict) -> dict:
    db = get_db()
    reading.setdefault("id", str(uuid.uuid4()))
    reading.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    if db:
        row = {k: v for k, v in reading.items() if k in _VITALS_COLUMNS}
        # Coerce integer columns — Python floats like 0.0 fail Postgres int check
        for col in ("fall_frequency",):
            if col in row and row[col] is not None:
                row[col] = int(row[col])
        result = db.table("vitals_readings").insert(row).execute()
        return result.data[0]
    _store["vitals_readings"].append(reading)
    return reading


def store_alert(alert: dict) -> dict:
    db = get_db()
    alert.setdefault("id", str(uuid.uuid4()))
    alert.setdefault("triggered_at", datetime.now(timezone.utc).isoformat())
    if db:
        result = db.table("alerts").insert(alert).execute()
        return result.data[0]
    _store["alerts"].append(alert)
    return alert


def get_patient(patient_id: str) -> dict | None:
    db = get_db()
    if db:
        result = db.table("patients").select("*").eq("id", patient_id).single().execute()
        return result.data
    return {"id": patient_id, "name": "Demo Patient", "age": 74, "gender": "Female"}


def get_patient_vitals(patient_id: str, limit: int = 50) -> list[dict]:
    db = get_db()
    if db:
        result = (
            db.table("vitals_readings")
            .select("*")
            .eq("patient_id", patient_id)
            .order("timestamp", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data
    readings = [r for r in _store["vitals_readings"] if r.get("patient_id") == patient_id]
    return sorted(readings, key=lambda r: r.get("timestamp", ""), reverse=True)[:limit]


def get_patient_alerts(patient_id: str, limit: int = 20) -> list[dict]:
    db = get_db()
    if db:
        result = (
            db.table("alerts")
            .select("*")
            .eq("patient_id", patient_id)
            .order("triggered_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data
    alerts = [a for a in _store["alerts"] if a.get("patient_id") == patient_id]
    return sorted(alerts, key=lambda a: a.get("triggered_at", ""), reverse=True)[:limit]


def acknowledge_alert(alert_id: str, acknowledged_by: str) -> dict | None:
    db = get_db()
    if db:
        result = (
            db.table("alerts")
            .update({"acknowledged_by": acknowledged_by, "resolved_at": datetime.now(timezone.utc).isoformat()})
            .eq("id", alert_id)
            .execute()
        )
        return result.data[0] if result.data else None
    for alert in _store["alerts"]:
        if alert["id"] == alert_id:
            alert["acknowledged_by"] = acknowledged_by
            alert["resolved_at"] = datetime.now(timezone.utc).isoformat()
            return alert
    return None


def store_location(location: dict) -> dict:
    db = get_db()
    location.setdefault("id", str(uuid.uuid4()))
    location.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    if db:
        result = db.table("location_logs").insert(location).execute()
        return result.data[0]
    _store["location_logs"].append(location)
    return location


def get_latest_location(patient_id: str) -> dict | None:
    db = get_db()
    if db:
        result = (
            db.table("location_logs")
            .select("*")
            .eq("patient_id", patient_id)
            .order("timestamp", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None
    locs = [l for l in _store["location_logs"] if l.get("patient_id") == patient_id]
    return sorted(locs, key=lambda l: l.get("timestamp", ""), reverse=True)[0] if locs else None


def list_patients(limit: int = 100) -> list[dict]:
    db = get_db()
    if db:
        result = db.table("patients").select("*").limit(limit).execute()
        return result.data
    return [{"id": "00000000-0000-0000-0000-000000000001", "name": "Ruth Thomas",
             "age": 76, "gender": "Female", "city": "Chicago", "device_id": "DEV-000001"}]

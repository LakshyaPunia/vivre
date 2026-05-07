from fastapi import APIRouter
from datetime import datetime, timezone
from app.schemas import VitalReading, IngestResponse
from app import ml, database
import uuid
import numpy as np

router = APIRouter()


def _to_python(v):
    if isinstance(v, np.integer): return int(v)
    if isinstance(v, np.floating): return float(v)
    if isinstance(v, np.bool_): return bool(v)
    return v


@router.post("/ingest", response_model=IngestResponse, summary="Receive wearable reading")
async def ingest_reading(reading: VitalReading):
    payload = reading.model_dump()
    payload["timestamp"] = payload.get("timestamp") or datetime.now(timezone.utc).isoformat()
    reading_id = str(uuid.uuid4())
    payload["id"] = reading_id

    disease_result = ml.predict_disease(payload)
    health_score   = ml.compute_health_score(payload)
    band           = ml.score_band(health_score)
    anomaly_result = ml.detect_anomaly(payload)

    payload["predicted_disease"] = disease_result["predicted_disease"]
    payload["disease_confidence"] = disease_result["confidence"]
    payload["health_score"]       = health_score
    payload["health_band"]        = band
    payload["is_anomaly"]         = bool(anomaly_result["is_anomaly"])

    # Convert numpy scalars to native Python types for JSON serialisation
    payload = {k: _to_python(v) for k, v in payload.items()}

    database.store_vitals(payload)

    alerts = ml.generate_alerts(
        payload,
        disease_result["predicted_disease"],
        health_score,
        anomaly_result["is_anomaly"],
    )
    for alert in alerts:
        database.store_alert(alert)

    return IngestResponse(
        reading_id=reading_id,
        predicted_disease=disease_result["predicted_disease"],
        confidence=disease_result["confidence"],
        health_score=health_score,
        health_band=band,
        is_anomaly=anomaly_result["is_anomaly"],
        alerts_triggered=len(alerts),
        timestamp=payload["timestamp"],
    )

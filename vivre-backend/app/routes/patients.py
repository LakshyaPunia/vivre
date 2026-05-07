from fastapi import APIRouter, HTTPException, Query
from app import database, ml

router = APIRouter()


@router.get("/patients", summary="List all patients")
async def list_patients(limit: int = Query(default=50, le=200)):
    return database.list_patients(limit=limit)


@router.get("/patients/{patient_id}", summary="Get patient profile + latest vitals")
async def get_patient(patient_id: str):
    patient = database.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    vitals = database.get_patient_vitals(patient_id, limit=1)
    latest = vitals[0] if vitals else None

    return {
        "patient": patient,
        "latest_vitals": latest,
        "health_score": latest.get("health_score") if latest else None,
        "health_band": latest.get("health_band") if latest else None,
        "predicted_disease": latest.get("predicted_disease") if latest else None,
    }


@router.get("/patients/{patient_id}/vitals", summary="Get vitals history")
async def get_vitals(
    patient_id: str,
    limit: int = Query(default=50, le=500),
):
    return database.get_patient_vitals(patient_id, limit=limit)


@router.get("/patients/{patient_id}/health-score", summary="Current health score")
async def get_health_score(patient_id: str):
    vitals = database.get_patient_vitals(patient_id, limit=1)
    if not vitals:
        raise HTTPException(status_code=404, detail="No readings found for patient")
    latest = vitals[0]
    score = latest.get("health_score", ml.compute_health_score(latest))
    return {
        "patient_id": patient_id,
        "health_score": score,
        "health_band": ml.score_band(score),
        "timestamp": latest.get("timestamp"),
    }


@router.get("/patients/{patient_id}/alerts", summary="Get patient alerts")
async def get_alerts(
    patient_id: str,
    limit: int = Query(default=20, le=100),
):
    return database.get_patient_alerts(patient_id, limit=limit)

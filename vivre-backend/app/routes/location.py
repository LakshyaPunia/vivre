from fastapi import APIRouter, HTTPException
from app.schemas import LocationUpdate
from app import database

router = APIRouter()


@router.post("/location", summary="Update patient location")
async def update_location(body: LocationUpdate):
    return database.store_location(body.model_dump())


@router.get("/patients/{patient_id}/location", summary="Get latest patient location")
async def get_location(patient_id: str):
    loc = database.get_latest_location(patient_id)
    if not loc:
        raise HTTPException(status_code=404, detail="No location data for patient")
    return loc

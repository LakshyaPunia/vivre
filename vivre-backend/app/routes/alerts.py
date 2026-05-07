from fastapi import APIRouter, HTTPException
from app.schemas import AlertAcknowledge
from app import database

router = APIRouter()


@router.patch("/alerts/{alert_id}/acknowledge", summary="Acknowledge an alert")
async def acknowledge_alert(alert_id: str, body: AlertAcknowledge):
    result = database.acknowledge_alert(alert_id, body.acknowledged_by)
    if not result:
        raise HTTPException(status_code=404, detail="Alert not found")
    return result

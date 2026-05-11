from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class VitalReading(BaseModel):
    patient_id: str
    device_id: Optional[str] = None
    timestamp: Optional[str] = None

    # Vitals
    heart_rate: float = Field(..., ge=20, le=250)
    spo2: float = Field(..., ge=50, le=100)
    systolic_bp: float = Field(..., ge=60, le=250)
    diastolic_bp: float = Field(..., ge=40, le=150)
    body_temp: float = Field(..., ge=33.0, le=42.0)
    respiratory_rate: float = Field(default=16, ge=8, le=40)
    glucose_level: float = Field(default=100, ge=20, le=600)

    # Lifestyle
    activity_score: Optional[float] = Field(default=50, ge=0, le=100)
    sleep_quality: Optional[float] = Field(default=5, ge=1, le=10)
    stress_level: Optional[float] = Field(default=5, ge=1, le=10)
    hydration_level: Optional[float] = Field(default=70, ge=0, le=100)

    # Safety
    fall_detected: Optional[bool] = False
    fall_frequency: Optional[float] = 0

    # Categorical
    ecg_abnormality: Optional[str] = "Normal"
    medication_adherence: Optional[str] = "Moderate"

    # Patient context (needed for ML features)
    age: Optional[float] = 74
    gender: Optional[str] = "Female"
    bmi: Optional[float] = 25.0
    mobility_level: Optional[str] = "Assisted"
    comorbidity_count: Optional[float] = 2

    # Pre-computed alerts from device (optional)
    heart_rate_alert: Optional[str] = "Normal"
    spo2_alert: Optional[str] = "Normal"
    bp_alert: Optional[str] = "Normal"
    temp_alert: Optional[str] = "Normal"


class IngestResponse(BaseModel):
    reading_id: str
    predicted_disease: str
    confidence: float
    health_score: float
    health_band: str
    is_anomaly: bool
    alerts_triggered: int
    timestamp: str


class ChatRequest(BaseModel):
    patient_id: Optional[str] = ""
    message: str
    conversation_history: Optional[list[dict]] = []


class ChatResponse(BaseModel):
    reply: str
    patient_id: str


class LocationUpdate(BaseModel):
    patient_id: str
    lat: float
    lng: float
    accuracy: Optional[float] = None
    address: Optional[str] = None


class AlertAcknowledge(BaseModel):
    acknowledged_by: str

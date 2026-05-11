from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import get_settings
from app.routes import ingest, patients, alerts, location, chat
from app import ml, database
from app.schemas import VitalReading
from app.routes.ingest import ingest_reading
import asyncio
import random
import uuid
from datetime import datetime, timezone

# ── Demo patients for background simulator ───────────────────────
_SIM_PATIENTS = [
    {"id": "00000000-0000-0000-0000-000000000001", "name": "Ruth Thomas",
     "age": 76, "gender": "Female", "bmi": 24.0, "mobility_level": "Assisted", "comorbidity_count": 3,
     "baseline": {"hr": 78, "spo2": 96, "sbp": 128, "dbp": 78, "temp": 36.8, "gluc": 115}},
    {"id": "00000000-0000-0000-0000-000000000002", "name": "Harold Wilson",
     "age": 82, "gender": "Male", "bmi": 27.5, "mobility_level": "Limited", "comorbidity_count": 4,
     "baseline": {"hr": 88, "spo2": 93, "sbp": 148, "dbp": 92, "temp": 37.1, "gluc": 185}},
    {"id": "00000000-0000-0000-0000-000000000003", "name": "Dorothy Clark",
     "age": 69, "gender": "Female", "bmi": 22.1, "mobility_level": "Independent", "comorbidity_count": 1,
     "baseline": {"hr": 65, "spo2": 98, "sbp": 118, "dbp": 72, "temp": 36.6, "gluc": 88}},
]


def _jitter(value: float, pct: float = 0.05) -> float:
    return round(value * (1 + random.uniform(-pct, pct)), 2)


def _build_reading(patient: dict, deteriorate: bool = False) -> VitalReading:
    b = patient["baseline"]
    mult = 1.15 if deteriorate else 1.0
    return VitalReading(
        patient_id=patient["id"],
        device_id=f"DEV-SIM-{patient['id'][-4:]}",
        timestamp=datetime.now(timezone.utc).isoformat(),
        heart_rate=max(40, min(200, _jitter(b["hr"] * mult, 0.08))),
        spo2=max(70, min(100, _jitter(b["spo2"] / mult, 0.03))),
        systolic_bp=max(70, min(220, _jitter(b["sbp"] * mult, 0.06))),
        diastolic_bp=max(40, min(140, _jitter(b["dbp"] * mult, 0.05))),
        body_temp=max(34.0, min(41.0, _jitter(b["temp"] * (1.02 if deteriorate else 1.0), 0.01))),
        respiratory_rate=max(8, min(40, round(random.gauss(18, 3)))),
        glucose_level=max(40, min(500, _jitter(b["gluc"] * mult, 0.10))),
        activity_score=random.randint(10, 90),
        sleep_quality=random.randint(3, 9),
        stress_level=random.randint(2, 8),
        hydration_level=random.randint(50, 95),
        fall_detected=random.random() < (0.05 if deteriorate else 0.01),
        fall_frequency=random.randint(0, 2),
        ecg_abnormality=random.choice(["Normal", "Normal", "Mild", "Severe"]) if deteriorate
                        else random.choice(["Normal", "Normal", "Normal", "Mild"]),
        medication_adherence=random.choice(["Poor", "Moderate", "Good", "Excellent"]),
        age=patient["age"],
        gender=patient["gender"],
        bmi=patient["bmi"],
        mobility_level=patient["mobility_level"],
        comorbidity_count=patient["comorbidity_count"],
    )


async def _simulator_loop(interval: int = 30):
    """Continuously ingests simulated vitals for all demo patients."""
    await asyncio.sleep(5)  # let startup finish first
    cycle = 0
    while True:
        cycle += 1
        for i, patient in enumerate(_SIM_PATIENTS):
            deteriorate = (i == 1 and cycle % 10 == 0)
            try:
                reading = _build_reading(patient, deteriorate=deteriorate)
                result = await ingest_reading(reading)
                print(
                    f"[SIM] {patient['name']:<18} "
                    f"Score={result.health_score}/100 ({result.health_band}) "
                    f"{'⚠ DETERIORATING' if deteriorate else ''}"
                )
            except Exception as e:
                print(f"[SIM ERROR] {patient['name']}: {e}")
        await asyncio.sleep(interval)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ml._load_models()
    settings = get_settings()
    print("[OK] ML models loaded")
    print(f"[OK] Supabase: {'connected' if settings.supabase_enabled else 'not configured (in-memory mode)'}")
    print(f"[OK] Chatbot:  {'enabled' if settings.chatbot_enabled else 'disabled (set OPENAI_API_KEY)'}")
    task = asyncio.create_task(_simulator_loop(interval=10))
    print("[OK] Background simulator started (10s interval)")
    yield
    task.cancel()


settings = get_settings()

app = FastAPI(
    title="Vivre API",
    description="AI-powered health monitoring backend for elderly care",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router,   prefix="/api/v1", tags=["Ingest"])
app.include_router(patients.router, prefix="/api/v1", tags=["Patients"])
app.include_router(alerts.router,   prefix="/api/v1", tags=["Alerts"])
app.include_router(location.router, prefix="/api/v1", tags=["Location"])
app.include_router(chat.router,     prefix="/api/v1", tags=["Chat"])


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "Vivre API", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "supabase": settings.supabase_enabled,
        "chatbot": settings.chatbot_enabled,
    }

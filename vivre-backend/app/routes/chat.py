from fastapi import APIRouter, HTTPException
from app.schemas import ChatRequest, ChatResponse
from app.config import get_settings
from app import database
from openai import OpenAI
import json

router = APIRouter()

SYSTEM_PROMPT = """You are Vivre's AI health assistant — a knowledgeable, warm, and concise medical companion.
You are speaking with a family member monitoring their elderly loved one's health.

Your role:
- Answer questions about the patient's current health status using their real data
- Flag concerns clearly but without causing unnecessary alarm
- Explain medical terms in plain English
- Suggest when to contact a doctor, but never diagnose or prescribe
- Be empathetic — the user cares deeply about this person

Always ground your answers in the patient data provided. If data is missing, say so honestly.
Keep responses under 150 words unless a detailed explanation is clearly needed.
Never make up values or invent health events."""


def _build_patient_context(patient_id: str) -> str:
    patient = database.get_patient(patient_id)
    vitals  = database.get_patient_vitals(patient_id, limit=5)
    alerts  = database.get_patient_alerts(patient_id, limit=5)

    ctx_parts = []

    if patient:
        ctx_parts.append(f"PATIENT PROFILE:\n{json.dumps(patient, indent=2)}")

    if vitals:
        latest = vitals[0]
        ctx_parts.append(f"""
LATEST VITALS ({latest.get('timestamp', 'unknown time')}):
- Heart Rate: {latest.get('heart_rate')} bpm
- SpO2: {latest.get('spo2')}%
- Blood Pressure: {latest.get('systolic_bp')}/{latest.get('diastolic_bp')} mmHg
- Temperature: {latest.get('body_temp')}°C
- Glucose: {latest.get('glucose_level')} mg/dL
- Respiratory Rate: {latest.get('respiratory_rate')} breaths/min
- Health Score: {latest.get('health_score')}/100 ({latest.get('health_band', 'unknown')})
- Predicted Condition: {latest.get('predicted_disease', 'unknown')}
- Fall Detected: {latest.get('fall_detected', False)}
- ECG: {latest.get('ecg_abnormality', 'Normal')}
- Sleep Quality: {latest.get('sleep_quality')}/10
- Stress Level: {latest.get('stress_level')}/10
- Activity Score: {latest.get('activity_score')}/100
- Medication Adherence: {latest.get('medication_adherence', 'unknown')}""")

    if len(vitals) > 1:
        trend_scores = [v.get("health_score") for v in vitals if v.get("health_score")]
        if trend_scores:
            ctx_parts.append(f"RECENT HEALTH SCORES (newest first): {trend_scores}")

    if alerts:
        active = [a for a in alerts if not a.get("resolved_at")]
        if active:
            alert_lines = [f"- [{a['severity'].upper()}] {a['message']}" for a in active[:3]]
            ctx_parts.append("ACTIVE ALERTS:\n" + "\n".join(alert_lines))

    return "\n\n".join(ctx_parts)


@router.post("/chat", response_model=ChatResponse, summary="AI health chatbot")
async def chat(body: ChatRequest):
    settings = get_settings()
    if not settings.chatbot_enabled:
        raise HTTPException(status_code=503, detail="AI chatbot not configured — set OPENAI_API_KEY in .env")

    patient_context = _build_patient_context(body.patient_id)
    system_content  = f"{SYSTEM_PROMPT}\n\n---\nCURRENT PATIENT DATA:\n{patient_context}"

    messages = [{"role": "system", "content": system_content}]
    for msg in (body.conversation_history or []):
        if msg.get("role") in ("user", "assistant"):
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": body.message})

    client   = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=512,
        temperature=0.4,
    )

    return ChatResponse(
        reply=response.choices[0].message.content,
        patient_id=body.patient_id,
    )

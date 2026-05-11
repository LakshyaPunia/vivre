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
- Answer historical questions using the vitals history provided (each row has a timestamp)
- Flag concerns clearly but without causing unnecessary alarm
- Explain medical terms in plain English
- Suggest when to contact a doctor, but never diagnose or prescribe
- Be empathetic — the user cares deeply about this person

Always ground your answers in the patient data provided. If data is missing, say so honestly.
When asked about a specific date or time, search the VITALS HISTORY for readings from that date.
Keep responses under 150 words unless a detailed explanation is clearly needed.
Never make up values or invent health events."""


def _format_vitals_row(v: dict) -> str:
    ts = v.get("timestamp") or v.get("created_at", "unknown")
    return (
        f"  {ts[:19]}  HR={v.get('heart_rate')} SpO2={v.get('spo2')}% "
        f"BP={v.get('systolic_bp')}/{v.get('diastolic_bp')} "
        f"Temp={v.get('body_temp')}°C Score={v.get('health_score')}"
    )


def _build_patient_context(patient_id: str) -> str:
    ctx_parts = []

    # Global mode — no specific patient, summarise all patients
    if not patient_id or patient_id in ("global", "null", "undefined", ""):
        patients = database.list_patients(limit=20)
        if patients:
            summaries = []
            for p in patients:
                vitals = database.get_patient_vitals(p["id"], limit=1)
                latest = vitals[0] if vitals else {}
                summaries.append(
                    f"- {p.get('name')} (age {p.get('age')}, {p.get('city', '')}): "
                    f"HR={latest.get('heart_rate')} SpO2={latest.get('spo2')}% "
                    f"BP={latest.get('systolic_bp')}/{latest.get('diastolic_bp')} "
                    f"Score={latest.get('health_score')} ({latest.get('health_band', '')})"
                )
            ctx_parts.append("ALL PATIENTS — LATEST VITALS:\n" + "\n".join(summaries))
        return "\n\n".join(ctx_parts)

    patient = database.get_patient(patient_id)
    vitals  = database.get_patient_vitals(patient_id, limit=200)
    alerts  = database.get_patient_alerts(patient_id, limit=10)

    if patient:
        p = patient
        ctx_parts.append(
            f"PATIENT: {p.get('name')}, age {p.get('age')}, {p.get('gender')}, {p.get('city', '')}"
        )

    if vitals:
        latest = vitals[0]
        ctx_parts.append(
            f"LATEST VITALS ({(latest.get('timestamp') or '')[:19]}):\n"
            f"- Heart Rate: {latest.get('heart_rate')} bpm\n"
            f"- SpO2: {latest.get('spo2')}%\n"
            f"- Blood Pressure: {latest.get('systolic_bp')}/{latest.get('diastolic_bp')} mmHg\n"
            f"- Temperature: {latest.get('body_temp')}°C\n"
            f"- Glucose: {latest.get('glucose_level')} mg/dL\n"
            f"- Respiratory Rate: {latest.get('respiratory_rate')} breaths/min\n"
            f"- Health Score: {latest.get('health_score')}/100 ({latest.get('health_band', '')})\n"
            f"- Predicted Condition: {latest.get('predicted_disease', 'unknown')}\n"
            f"- ECG: {latest.get('ecg_abnormality', 'Normal')}\n"
            f"- Sleep Quality: {latest.get('sleep_quality')}/10\n"
            f"- Stress Level: {latest.get('stress_level')}/10\n"
            f"- Activity Score: {latest.get('activity_score')}/100\n"
            f"- Medication Adherence: {latest.get('medication_adherence', 'unknown')}"
        )

        # Compact history table for date-specific questions
        history_lines = [_format_vitals_row(v) for v in vitals]
        ctx_parts.append("VITALS HISTORY (newest first):\n" + "\n".join(history_lines))

        trend_scores = [v.get("health_score") for v in vitals[:20] if v.get("health_score")]
        if trend_scores:
            ctx_parts.append(f"HEALTH SCORE TREND (last {len(trend_scores)} readings): {trend_scores}")

    if alerts:
        active = [a for a in alerts if not a.get("resolved_at")]
        if active:
            alert_lines = [f"- [{a.get('severity','').upper()}] {a.get('message')}" for a in active[:5]]
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

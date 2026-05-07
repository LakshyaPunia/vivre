import joblib
import numpy as np
import json
import os
from pathlib import Path
from app.config import get_settings
from functools import lru_cache


@lru_cache
def _load_models() -> dict:
    models_dir = Path(get_settings().models_dir)
    return {
        "classifier":    joblib.load(models_dir / "disease_classifier.pkl"),
        "label_encoder": joblib.load(models_dir / "disease_label_encoder.pkl"),
        "features":      joblib.load(models_dir / "feature_list.pkl"),
        "anomaly":       joblib.load(models_dir / "anomaly_detector.pkl"),
        "anomaly_scaler":joblib.load(models_dir / "anomaly_scaler.pkl"),
        "anomaly_feats": joblib.load(models_dir / "anomaly_features.pkl"),
        "score_config":  json.loads((models_dir / "score_config.json").read_text()),
    }


# Encoding maps — must match train_models.py
_ALERT_MAP  = {"Normal": 0, "Low": 1, "High": 2}
_ECG_MAP    = {"Normal": 0, "Mild": 1, "Severe": 2}
_ADH_MAP    = {"Poor": 0, "Moderate": 1, "Good": 2}
_MOB_MAP    = {"Independent": 3, "Assisted": 2, "Limited": 1, "Wheelchair": 0}
_GENDER_MAP = {"Female": 0, "Male": 1}


def _encode_reading(reading: dict) -> dict:
    r = dict(reading)
    r["Fall Detection"]       = 1 if r.get("fall_detected") else 0
    r["Heart Rate Alert"]     = _ALERT_MAP.get(r.get("heart_rate_alert", "Normal"), 0)
    r["SpO2 Level Alert"]     = _ALERT_MAP.get(r.get("spo2_alert", "Normal"), 0)
    r["Blood Pressure Alert"] = _ALERT_MAP.get(r.get("bp_alert", "Normal"), 0)
    r["Temperature Alert"]    = _ALERT_MAP.get(r.get("temp_alert", "Normal"), 0)
    r["ECG Abnormality"]      = _ECG_MAP.get(r.get("ecg_abnormality", "Normal"), 0)
    r["Medication Adherence"] = _ADH_MAP.get(r.get("medication_adherence", "Moderate"), 1)
    r["Mobility Level"]       = _MOB_MAP.get(r.get("mobility_level", "Assisted"), 2)
    r["Gender"]               = _GENDER_MAP.get(r.get("gender", "Female"), 0)
    return r


def _map_col(r: dict, col: str) -> float:
    mapping = {
        "Age":                                    "age",
        "Gender":                                 "Gender",
        "Heart Rate (bpm)":                       "heart_rate",
        "SpO2 Level (%)":                         "spo2",
        "Systolic Blood Pressure (mmHg)":         "systolic_bp",
        "Diastolic Blood Pressure (mmHg)":        "diastolic_bp",
        "Body Temperature (°C)":                  "body_temp",
        "Respiratory Rate":                       "respiratory_rate",
        "Glucose Level":                          "glucose_level",
        "BMI":                                    "bmi",
        "Stress Level":                           "stress_level",
        "Sleep Quality":                          "sleep_quality",
        "Activity Score":                         "activity_score",
        "Hydration Level":                        "hydration_level",
        "Fall Detection":                         "Fall Detection",
        "Fall Frequency":                         "fall_frequency",
        "ECG Abnormality":                        "ECG Abnormality",
        "Medication Adherence":                   "Medication Adherence",
        "Mobility Level":                         "Mobility Level",
        "Comorbidity Count":                      "comorbidity_count",
        "Heart Rate Alert":                       "Heart Rate Alert",
        "SpO2 Level Alert":                       "SpO2 Level Alert",
        "Blood Pressure Alert":                   "Blood Pressure Alert",
        "Temperature Alert":                      "Temperature Alert",
    }
    key = mapping.get(col, col)
    return float(r.get(key, 0) or 0)


def predict_disease(reading: dict) -> dict:
    m = _load_models()
    r = _encode_reading(reading)
    features = m["features"]
    X = np.array([[_map_col(r, f) for f in features]])
    pred_idx = m["classifier"].predict(X)[0]
    proba = m["classifier"].predict_proba(X)[0]
    classes = m["label_encoder"].classes_
    return {
        "predicted_disease": m["label_encoder"].inverse_transform([pred_idx])[0],
        "confidence": round(float(proba[pred_idx]), 4),
        "probabilities": {cls: round(float(p), 4) for cls, p in zip(classes, proba)},
    }


def compute_health_score(reading: dict) -> float:
    score = 100.0
    hr   = float(reading.get("heart_rate", 70))
    spo2 = float(reading.get("spo2", 97))
    sbp  = float(reading.get("systolic_bp", 120))
    temp = float(reading.get("body_temp", 37.0))
    gluc = float(reading.get("glucose_level", 100))
    ecg  = _ECG_MAP.get(reading.get("ecg_abnormality", "Normal"), 0)
    fall = 1 if reading.get("fall_detected") else 0
    fall_freq   = float(reading.get("fall_frequency", 0))
    sleep_q     = float(reading.get("sleep_quality", 5))
    stress      = float(reading.get("stress_level", 5))
    activity    = float(reading.get("activity_score", 50))
    hydration   = float(reading.get("hydration_level", 70))
    adh         = _ADH_MAP.get(reading.get("medication_adherence", "Moderate"), 1)
    comorbidity = float(reading.get("comorbidity_count", 0))

    if hr < 50 or hr > 130:    score -= 20
    elif hr < 60 or hr > 110:  score -= 10
    if spo2 < 90:              score -= 25
    elif spo2 < 95:            score -= 12
    if sbp > 180 or sbp < 90:  score -= 20
    elif sbp > 140 or sbp < 100: score -= 10
    if temp > 38.5 or temp < 35.5: score -= 15
    elif temp > 37.8 or temp < 36.0: score -= 7
    if gluc > 250 or gluc < 60: score -= 15
    elif gluc > 180 or gluc < 80: score -= 7

    score -= ecg * 8
    score -= fall * 10
    score -= min(fall_freq * 3, 15)
    score += (sleep_q - 5) * 1.5
    score -= (stress - 5) * 1.5
    score += (activity - 50) * 0.1
    score += (hydration - 70) * 0.1
    score += {0: -10, 1: 0, 2: 8}.get(adh, 0)
    score -= comorbidity * 3

    return round(float(np.clip(score, 0, 100)), 1)


def score_band(score: float) -> str:
    if score >= 90: return "excellent"
    if score >= 75: return "good"
    if score >= 60: return "fair"
    if score >= 40: return "poor"
    return "critical"


def detect_anomaly(reading: dict) -> dict:
    m = _load_models()
    feats = m["anomaly_feats"]
    r = _encode_reading(reading)
    col_map = {
        "Heart Rate (bpm)":                    "heart_rate",
        "SpO2 Level (%)":                      "spo2",
        "Systolic Blood Pressure (mmHg)":      "systolic_bp",
        "Diastolic Blood Pressure (mmHg)":     "diastolic_bp",
        "Body Temperature (°C)":               "body_temp",
        "Respiratory Rate":                    "respiratory_rate",
        "Glucose Level":                       "glucose_level",
        "ECG Abnormality":                     "ECG Abnormality",
    }
    X_raw = np.array([[float(r.get(col_map.get(f, f), 0) or 0) for f in feats]])
    X_scaled = m["anomaly_scaler"].transform(X_raw)
    label = m["anomaly"].predict(X_scaled)[0]          # -1 anomaly, 1 normal
    score = float(m["anomaly"].decision_function(X_scaled)[0])
    return {
        "is_anomaly": label == -1,
        "anomaly_score": round(score, 4),
    }


def generate_alerts(reading: dict, disease: str, health_score: float, anomaly: bool) -> list[dict]:
    alerts = []
    patient_id = reading.get("patient_id", "")

    def _alert(type_: str, severity: str, message: str):
        alerts.append({"patient_id": patient_id, "type": type_,
                        "severity": severity, "message": message})

    hr   = float(reading.get("heart_rate", 70))
    spo2 = float(reading.get("spo2", 97))
    sbp  = float(reading.get("systolic_bp", 120))
    temp = float(reading.get("body_temp", 37.0))
    gluc = float(reading.get("glucose_level", 100))

    if hr > 130 or hr < 45:
        _alert("heart_rate", "critical", f"Heart rate critically abnormal: {hr} bpm")
    elif hr > 110 or hr < 55:
        _alert("heart_rate", "warning", f"Heart rate out of range: {hr} bpm")

    if spo2 < 90:
        _alert("spo2", "critical", f"Dangerously low blood oxygen: {spo2}%")
    elif spo2 < 94:
        _alert("spo2", "warning", f"Low blood oxygen: {spo2}%")

    if sbp > 180:
        _alert("blood_pressure", "critical", f"Hypertensive crisis: {sbp} mmHg systolic")
    elif sbp > 160:
        _alert("blood_pressure", "warning", f"High blood pressure: {sbp} mmHg systolic")

    if temp > 38.5:
        _alert("temperature", "warning", f"Fever detected: {temp}°C")
    elif temp < 35.5:
        _alert("temperature", "critical", f"Hypothermia risk: {temp}°C")

    if gluc > 250:
        _alert("glucose", "critical", f"Critically high blood glucose: {gluc} mg/dL")
    elif gluc < 60:
        _alert("glucose", "critical", f"Hypoglycaemia risk: {gluc} mg/dL")

    if reading.get("fall_detected"):
        _alert("fall", "critical", "Fall detected — immediate check recommended")

    if health_score < 40:
        _alert("health_score", "critical", f"Health score critically low: {health_score}/100")
    elif health_score < 60:
        _alert("health_score", "warning", f"Health score declining: {health_score}/100")

    if anomaly:
        _alert("anomaly", "warning", "Unusual vital pattern detected by AI — monitor closely")

    return alerts

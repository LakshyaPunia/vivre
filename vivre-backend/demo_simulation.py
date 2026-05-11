"""
Vivre Demo Simulation
Runs a scripted scenario to demonstrate all UI states:
  Phase 1 (0-20s):  All 3 patients — normal/stable readings
  Phase 2 (20-40s): Harold deteriorates — BP spikes, SpO2 drops, ECG worsens
  Phase 3 (40-50s): Harold has a FALL — critical alert fires
  Phase 4 (50-70s): Harold stabilises — scores recover
  Phase 5 (70s+):   All patients loop normally
"""
import httpx, time, random
from datetime import datetime, timezone

API = "http://localhost:8000/api/v1"

PATIENTS = {
    "ruth":    {"id": "00000000-0000-0000-0000-000000000001", "age": 76, "gender": "Female", "bmi": 24.0, "mobility": "Assisted",    "comorbidity": 3},
    "harold":  {"id": "00000000-0000-0000-0000-000000000002", "age": 82, "gender": "Male",   "bmi": 27.5, "mobility": "Limited",     "comorbidity": 4},
    "dorothy": {"id": "00000000-0000-0000-0000-000000000003", "age": 69, "gender": "Female", "bmi": 22.1, "mobility": "Independent", "comorbidity": 1},
}

def reading(patient_key, overrides={}):
    p = PATIENTS[patient_key]
    defaults = {
        "ruth":    {"hr": 78,  "spo2": 96, "sbp": 128, "dbp": 78, "temp": 36.8, "gluc": 110, "rr": 16, "act": 55, "sleep": 7, "stress": 3, "hyd": 75, "fall": False, "ff": 0, "ecg": "Normal",  "adh": "Good"},
        "harold":  {"hr": 88,  "spo2": 93, "sbp": 148, "dbp": 92, "temp": 37.1, "gluc": 180, "rr": 20, "act": 30, "sleep": 5, "stress": 6, "hyd": 60, "fall": False, "ff": 1, "ecg": "Mild",    "adh": "Moderate"},
        "dorothy": {"hr": 65,  "spo2": 98, "sbp": 118, "dbp": 72, "temp": 36.6, "gluc": 88,  "rr": 14, "act": 75, "sleep": 8, "stress": 2, "hyd": 85, "fall": False, "ff": 0, "ecg": "Normal",  "adh": "Good"},
    }
    d = {**defaults[patient_key], **overrides}

    def j(v, pct=0.04): return round(v * (1 + random.uniform(-pct, pct)), 1)

    return {
        "patient_id":          p["id"],
        "age":                 p["age"],
        "gender":              p["gender"],
        "bmi":                 p["bmi"],
        "mobility_level":      p["mobility"],
        "comorbidity_count":   p["comorbidity"],
        "heart_rate":          j(d["hr"], 0.06),
        "spo2":                min(100, j(d["spo2"], 0.02)),
        "systolic_bp":         j(d["sbp"], 0.05),
        "diastolic_bp":        j(d["dbp"], 0.04),
        "body_temp":           j(d["temp"], 0.01),
        "respiratory_rate":    int(j(d["rr"], 0.08)),
        "glucose_level":       j(d["gluc"], 0.08),
        "activity_score":      max(0, min(100, d["act"] + random.randint(-5, 5))),
        "sleep_quality":       d["sleep"],
        "stress_level":        d["stress"],
        "hydration_level":     d["hyd"],
        "fall_detected":       d["fall"],
        "fall_frequency":      d["ff"],
        "ecg_abnormality":     d["ecg"],
        "medication_adherence": d["adh"],
        "timestamp":           datetime.now(timezone.utc).isoformat(),
    }

def post(payload, client):
    try:
        r = client.post(f"{API}/ingest", json=payload, timeout=8)
        d = r.json()
        name = next(k for k,v in PATIENTS.items() if v["id"] == payload["patient_id"])
        alerts = f"  ** {d['alerts_triggered']} alert(s)" if d["alerts_triggered"] else ""
        anom   = "  [ANOMALY]" if d["is_anomaly"] else ""
        fall   = "  [FALL DETECTED]" if payload["fall_detected"] else ""
        print(f"  {name.capitalize():<10} score={d['health_score']:>5}/100  {d['health_band']:<10}  {d['predicted_disease']:<22}{alerts}{anom}{fall}")
    except Exception as e:
        print(f"  ERROR: {e}")

def banner(msg):
    print(f"\n{'-'*60}")
    print(f"  {msg}")
    print(f"{'-'*60}")

print("=" * 60)
print("  VIVRE DEMO SIMULATION")
print("  Watch your Lovable app for live updates")
print("=" * 60)

with httpx.Client() as c:

    # ── Phase 1: Normal readings ─────────────────────────────────
    banner("PHASE 1 — All patients stable (20s)")
    for cycle in range(4):
        print(f"\n  Cycle {cycle+1}/4  [{datetime.now().strftime('%H:%M:%S')}]")
        post(reading("ruth"),    c)
        post(reading("harold"),  c)
        post(reading("dorothy"), c)
        time.sleep(5)

    # ── Phase 2: Harold deteriorates ────────────────────────────
    banner("PHASE 2 — Harold deteriorating (20s)")
    deterioration_steps = [
        {"sbp": 158, "dbp": 98,  "spo2": 91, "hr": 105, "ecg": "Mild",   "stress": 8},
        {"sbp": 165, "dbp": 102, "spo2": 89, "hr": 112, "ecg": "Severe", "stress": 9, "gluc": 220},
        {"sbp": 172, "dbp": 106, "spo2": 87, "hr": 118, "ecg": "Severe", "stress": 9, "gluc": 240},
        {"sbp": 178, "dbp": 108, "spo2": 86, "hr": 124, "ecg": "Severe", "stress": 9, "gluc": 255},
    ]
    for i, overrides in enumerate(deterioration_steps):
        print(f"\n  Deterioration step {i+1}/4  [{datetime.now().strftime('%H:%M:%S')}]")
        post(reading("ruth"),    c)
        post(reading("harold", overrides), c)
        post(reading("dorothy"), c)
        time.sleep(5)

    # ── Phase 3: Fall event ──────────────────────────────────────
    banner("PHASE 3 — FALL DETECTED for Harold!")
    print(f"\n  [{datetime.now().strftime('%H:%M:%S')}]")
    post(reading("ruth"),    c)
    post(reading("harold", {"sbp": 182, "dbp": 110, "spo2": 85, "hr": 130, "ecg": "Severe", "fall": True, "ff": 3, "stress": 10}), c)
    post(reading("dorothy"), c)
    time.sleep(8)

    # ── Phase 4: Harold stabilising ─────────────────────────────
    banner("PHASE 4 — Harold stabilising (20s)")
    recovery_steps = [
        {"sbp": 168, "dbp": 104, "spo2": 88, "hr": 118, "ecg": "Severe", "stress": 8},
        {"sbp": 158, "dbp": 98,  "spo2": 91, "hr": 108, "ecg": "Mild",   "stress": 7},
        {"sbp": 152, "dbp": 95,  "spo2": 92, "hr": 100, "ecg": "Mild",   "stress": 6},
        {"sbp": 148, "dbp": 92,  "spo2": 93, "hr": 92,  "ecg": "Mild",   "stress": 5},
    ]
    for i, overrides in enumerate(recovery_steps):
        print(f"\n  Recovery step {i+1}/4  [{datetime.now().strftime('%H:%M:%S')}]")
        post(reading("ruth"),    c)
        post(reading("harold", overrides), c)
        post(reading("dorothy"), c)
        time.sleep(5)

    # ── Phase 5: Continuous normal loop ─────────────────────────
    banner("PHASE 5 — Continuous live feed (Ctrl+C to stop)")
    cycle = 0
    while True:
        cycle += 1
        print(f"\n  Live cycle {cycle}  [{datetime.now().strftime('%H:%M:%S')}]")
        post(reading("ruth"),    c)
        post(reading("harold"),  c)
        post(reading("dorothy"), c)
        time.sleep(4)

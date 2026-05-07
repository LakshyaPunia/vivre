"""
Vivre Wearable Simulator
Streams realistic vitals to the API to simulate live wearable devices.
Usage: python simulator.py [--url http://localhost:8000] [--patients 3] [--interval 5]
"""
import httpx
import time
import random
import argparse
from datetime import datetime, timezone

DEMO_PATIENTS = [
    {"id": "00000000-0000-0000-0000-000000000001", "name": "Ruth Thomas",   "age": 76, "gender": "Female",
     "bmi": 24.0, "mobility_level": "Assisted",   "comorbidity_count": 3,
     "baseline": {"hr": 78,  "spo2": 96, "sbp": 128, "dbp": 78, "temp": 36.8, "gluc": 115}},
    {"id": "00000000-0000-0000-0000-000000000002", "name": "Harold Wilson",  "age": 82, "gender": "Male",
     "bmi": 27.5, "mobility_level": "Limited",    "comorbidity_count": 4,
     "baseline": {"hr": 88,  "spo2": 93, "sbp": 148, "dbp": 92, "temp": 37.1, "gluc": 185}},
    {"id": "00000000-0000-0000-0000-000000000003", "name": "Dorothy Clark",  "age": 69, "gender": "Female",
     "bmi": 22.1, "mobility_level": "Independent","comorbidity_count": 1,
     "baseline": {"hr": 65,  "spo2": 98, "sbp": 118, "dbp": 72, "temp": 36.6, "gluc": 88}},
]


def jitter(value: float, pct: float = 0.05) -> float:
    return round(value * (1 + random.uniform(-pct, pct)), 2)


def build_reading(patient: dict, deteriorate: bool = False) -> dict:
    b = patient["baseline"]
    mult = 1.15 if deteriorate else 1.0

    hr   = jitter(b["hr"]  * mult, 0.08)
    spo2 = min(100, jitter(b["spo2"] / mult, 0.03))
    sbp  = jitter(b["sbp"] * mult, 0.06)
    dbp  = jitter(b["dbp"] * mult, 0.05)
    temp = jitter(b["temp"] * (1 + 0.02 if deteriorate else 1), 0.01)
    gluc = jitter(b["gluc"] * mult, 0.10)

    return {
        "patient_id":          patient["id"],
        "device_id":           f"DEV-SIM-{patient['id']}",
        "timestamp":           datetime.now(timezone.utc).isoformat(),
        "heart_rate":          max(40, min(200, hr)),
        "spo2":                max(70, min(100, spo2)),
        "systolic_bp":         max(70, min(220, sbp)),
        "diastolic_bp":        max(40, min(140, dbp)),
        "body_temp":           max(34.0, min(41.0, temp)),
        "respiratory_rate":    round(random.gauss(18, 3)),
        "glucose_level":       max(40, min(500, gluc)),
        "activity_score":      random.randint(10, 90),
        "sleep_quality":       random.randint(3, 9),
        "stress_level":        random.randint(2, 8),
        "hydration_level":     random.randint(50, 95),
        "fall_detected":       random.random() < (0.05 if deteriorate else 0.01),
        "fall_frequency":      random.randint(0, 3),
        "ecg_abnormality":     random.choice(["Normal", "Normal", "Normal", "Mild", "Severe"]) if deteriorate
                               else random.choice(["Normal", "Normal", "Normal", "Normal", "Mild"]),
        "medication_adherence": random.choice(["Poor", "Moderate", "Good"]),
        "age":                 patient["age"],
        "gender":              patient["gender"],
        "bmi":                 patient["bmi"],
        "mobility_level":      patient["mobility_level"],
        "comorbidity_count":   patient["comorbidity_count"],
    }


def run(base_url: str, n_patients: int, interval: int):
    patients = DEMO_PATIENTS[:n_patients]
    print(f"Vivre Simulator — streaming {n_patients} patient(s) every {interval}s to {base_url}")
    print("Press Ctrl+C to stop.\n")

    cycle = 0
    with httpx.Client(timeout=10) as client:
        while True:
            cycle += 1
            # Simulate deterioration for patient 2 every 10th cycle for demo
            for i, patient in enumerate(patients):
                deteriorate = (i == 1 and cycle % 10 == 0)
                reading = build_reading(patient, deteriorate=deteriorate)
                try:
                    r = client.post(f"{base_url}/api/v1/ingest", json=reading)
                    data = r.json()
                    flag = "⚠ DETERIORATING" if deteriorate else ""
                    alert_str = f"🔔 {data['alerts_triggered']} alert(s)" if data["alerts_triggered"] else ""
                    print(
                        f"[{datetime.now().strftime('%H:%M:%S')}] "
                        f"{patient['name']:<18} "
                        f"Score: {data['health_score']:>5}/100 ({data['health_band']:<9}) "
                        f"Disease: {data['predicted_disease']:<20} "
                        f"Anomaly: {'YES' if data['is_anomaly'] else 'no '} "
                        f"{alert_str} {flag}"
                    )
                except Exception as e:
                    print(f"[ERROR] {patient['name']}: {e}")

            print()
            time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vivre wearable simulator")
    parser.add_argument("--url",      default="http://localhost:8000")
    parser.add_argument("--patients", type=int, default=3)
    parser.add_argument("--interval", type=int, default=5)
    args = parser.parse_args()
    run(args.url, args.patients, args.interval)

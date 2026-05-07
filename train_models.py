import pandas as pd
import numpy as np
import joblib
import json
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, accuracy_score
from xgboost import XGBClassifier
from sklearn.ensemble import IsolationForest, RandomForestClassifier

os.makedirs("models", exist_ok=True)

df = pd.read_csv("elderly_healthcare_digital_twin_dataset_augmented.csv")

print("=" * 60)
print("VIVRE — ML MODEL TRAINING")
print("=" * 60)

# ─── Re-engineer disease labels from clinical rules ─────────────
# The original synthetic labels are randomly assigned (no correlation
# to features). We replace them with clinically grounded rules so
# the classifier learns real signal.

def assign_disease(row):
    scores = {"Hypertension": 0, "Diabetes Mellitus": 0,
              "Arrhythmia": 0, "Asthma": 0, "Normal": 0}

    # Hypertension
    if row["Systolic Blood Pressure (mmHg)"] > 140:  scores["Hypertension"] += 3
    if row["Diastolic Blood Pressure (mmHg)"] > 90:  scores["Hypertension"] += 2
    if row["BMI"] > 30:                               scores["Hypertension"] += 1
    if row["Stress Level"] > 7:                       scores["Hypertension"] += 1

    # Diabetes Mellitus
    if row["Glucose Level"] > 180:   scores["Diabetes Mellitus"] += 4
    if row["Glucose Level"] > 126:   scores["Diabetes Mellitus"] += 2
    if row["BMI"] > 28:              scores["Diabetes Mellitus"] += 1
    if row["Activity Score"] < 30:   scores["Diabetes Mellitus"] += 1

    # Arrhythmia
    ecg = row["ECG Abnormality"] if isinstance(row["ECG Abnormality"], (int, float)) else \
          {"Normal": 0, "Mild": 1, "Severe": 2}.get(row["ECG Abnormality"], 0)
    if ecg >= 2:                                      scores["Arrhythmia"] += 4
    if ecg == 1:                                      scores["Arrhythmia"] += 2
    if row["Heart Rate (bpm)"] > 120:                 scores["Arrhythmia"] += 2
    if row["Heart Rate (bpm)"] < 50:                  scores["Arrhythmia"] += 2

    # Asthma
    if row["SpO2 Level (%)"] < 92:                    scores["Asthma"] += 4
    if row["SpO2 Level (%)"] < 95:                    scores["Asthma"] += 2
    if row["Respiratory Rate"] > 24:                  scores["Asthma"] += 2
    if row["Activity Score"] < 40:                    scores["Asthma"] += 1

    best = max(scores, key=scores.get)
    # If no condition dominates, label Normal
    if scores[best] <= 1:
        return "Normal"
    return best

print("Re-engineering disease labels from clinical rules...")
df["Predicted Disease"] = df.apply(assign_disease, axis=1)
dist = df["Predicted Disease"].value_counts()
print(f"  New label distribution:\n{dist.to_string()}\n")

# ─── Feature engineering ────────────────────────────────────────
# Encode categorical vitals/flags
bool_map = {"Yes": 1, "No": 0}
alert_map = {"Normal": 0, "Low": 1, "High": 2}
ecg_map = {"Normal": 0, "Mild": 1, "Severe": 2}
adh_map = {"Poor": 0, "Moderate": 1, "Good": 2}
mob_map = {"Independent": 3, "Assisted": 2, "Limited": 1, "Wheelchair": 0}
gender_map = {"Female": 0, "Male": 1}

df["Fall Detection"] = df["Fall Detection"].map(bool_map).fillna(0).astype(int)
df["Heart Rate Alert"] = df["Heart Rate Alert"].map(alert_map).fillna(0).astype(int)
df["SpO2 Level Alert"] = df["SpO2 Level Alert"].map(alert_map).fillna(0).astype(int)
df["Blood Pressure Alert"] = df["Blood Pressure Alert"].map(alert_map).fillna(0).astype(int)
df["Temperature Alert"] = df["Temperature Alert"].map(alert_map).fillna(0).astype(int)
df["ECG Abnormality"] = df["ECG Abnormality"].map(ecg_map).fillna(0).astype(int)
df["Medication Adherence"] = df["Medication Adherence"].map(adh_map).fillna(1).astype(int)
df["Mobility Level"] = df["Mobility Level"].map(mob_map).fillna(2).astype(int)
df["Gender"] = df["Gender"].map(gender_map).fillna(0).astype(int)

FEATURES = [
    "Age", "Gender",
    "Heart Rate (bpm)", "SpO2 Level (%)",
    "Systolic Blood Pressure (mmHg)", "Diastolic Blood Pressure (mmHg)",
    "Body Temperature (°C)", "Respiratory Rate",
    "Glucose Level", "BMI",
    "Stress Level", "Sleep Quality", "Activity Score",
    "Hydration Level", "Fall Detection", "Fall Frequency",
    "ECG Abnormality", "Medication Adherence", "Mobility Level",
    "Comorbidity Count",
    "Heart Rate Alert", "SpO2 Level Alert",
    "Blood Pressure Alert", "Temperature Alert",
]

X = df[FEATURES]
joblib.dump(FEATURES, "models/feature_list.pkl")


# ════════════════════════════════════════════════════════════════
# MODEL 1 — Disease Prediction Classifier
# ════════════════════════════════════════════════════════════════
print("\n[1/3] Training Disease Prediction Classifier...")

le = LabelEncoder()
y_disease = le.fit_transform(df["Predicted Disease"])
joblib.dump(le, "models/disease_label_encoder.pkl")

X_train, X_test, y_train, y_test = train_test_split(
    X, y_disease, test_size=0.2, random_state=42, stratify=y_disease
)

disease_model = XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    use_label_encoder=False,
    eval_metric="mlogloss",
    random_state=42,
    n_jobs=-1,
)
disease_model.fit(X_train, y_train)

y_pred = disease_model.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f"  Accuracy: {acc:.4f} ({acc*100:.1f}%)")
print(f"\n  Per-class report:")
print(classification_report(y_test, y_pred, target_names=le.classes_, digits=3))

joblib.dump(disease_model, "models/disease_classifier.pkl")

# Feature importance
importance = dict(zip(FEATURES, disease_model.feature_importances_))
top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]
print("  Top 10 features:")
for feat, score in top_features:
    print(f"    {feat:<45} {score:.4f}")


# ════════════════════════════════════════════════════════════════
# MODEL 2 — Health Score Generator (0–100)
# ════════════════════════════════════════════════════════════════
print("\n[2/3] Building Health Score Generator...")

def compute_health_score(row):
    score = 100.0

    # Vitals penalties
    hr = row["Heart Rate (bpm)"]
    if hr < 50 or hr > 130:   score -= 20
    elif hr < 60 or hr > 110: score -= 10

    spo2 = row["SpO2 Level (%)"]
    if spo2 < 90:   score -= 25
    elif spo2 < 95: score -= 12

    sbp = row["Systolic Blood Pressure (mmHg)"]
    if sbp > 180 or sbp < 90:   score -= 20
    elif sbp > 140 or sbp < 100: score -= 10

    temp = row["Body Temperature (°C)"]
    if temp > 38.5 or temp < 35.5: score -= 15
    elif temp > 37.8 or temp < 36.0: score -= 7

    glucose = row["Glucose Level"]
    if glucose > 250 or glucose < 60: score -= 15
    elif glucose > 180 or glucose < 80: score -= 7

    # ECG (encoded 0/1/2)
    ecg_val = int(row["ECG Abnormality"]) if pd.notna(row["ECG Abnormality"]) else 0
    score -= ecg_val * 8

    # Fall risk
    score -= row["Fall Detection"] * 10
    score -= min(row["Fall Frequency"] * 3, 15)

    # Lifestyle factors (positive/negative)
    score += (row["Sleep Quality"] - 5) * 1.5      # 1-10 scale, 5 is neutral
    score -= (row["Stress Level"] - 5) * 1.5
    score += (row["Activity Score"] - 50) * 0.1
    score += (row["Hydration Level"] - 70) * 0.1

    # Medication adherence
    adh_bonus = {0: -10, 1: 0, 2: 8}
    score += adh_bonus.get(row["Medication Adherence"], 0)

    # Comorbidity burden
    score -= row["Comorbidity Count"] * 3

    return round(float(np.clip(score, 0, 100)), 1)

df["Health Score"] = df.apply(compute_health_score, axis=1)

print(f"  Health Score stats:")
print(f"    Mean:  {df['Health Score'].mean():.1f}")
print(f"    Std:   {df['Health Score'].std():.1f}")
print(f"    Min:   {df['Health Score'].min():.1f}")
print(f"    Max:   {df['Health Score'].max():.1f}")
print(f"    Distribution:")
bins = [0, 40, 60, 75, 90, 100]
labels = ["Critical (0-40)", "Poor (40-60)", "Fair (60-75)", "Good (75-90)", "Excellent (90-100)"]
for i, label in enumerate(labels):
    count = ((df["Health Score"] >= bins[i]) & (df["Health Score"] < bins[i+1])).sum()
    pct = count / len(df) * 100
    print(f"      {label:<25} {count:>6} ({pct:.1f}%)")

# Save the scoring weights as a config for the API
score_config = {
    "thresholds": {
        "heart_rate": {"critical_low": 50, "critical_high": 130, "warn_low": 60, "warn_high": 110},
        "spo2": {"critical": 90, "warn": 95},
        "systolic_bp": {"critical_high": 180, "critical_low": 90, "warn_high": 140, "warn_low": 100},
        "temperature": {"critical_high": 38.5, "critical_low": 35.5, "warn_high": 37.8, "warn_low": 36.0},
        "glucose": {"critical_high": 250, "critical_low": 60, "warn_high": 180, "warn_low": 80},
    },
    "score_bands": {
        "excellent": [90, 100],
        "good": [75, 90],
        "fair": [60, 75],
        "poor": [40, 60],
        "critical": [0, 40],
    }
}
with open("models/score_config.json", "w") as f:
    json.dump(score_config, f, indent=2)


# ════════════════════════════════════════════════════════════════
# MODEL 3 — Anomaly / Deterioration Detector
# ════════════════════════════════════════════════════════════════
print("\n[3/3] Training Anomaly Detector (Isolation Forest)...")

ANOMALY_FEATURES = [
    "Heart Rate (bpm)", "SpO2 Level (%)",
    "Systolic Blood Pressure (mmHg)", "Diastolic Blood Pressure (mmHg)",
    "Body Temperature (°C)", "Respiratory Rate",
    "Glucose Level", "ECG Abnormality",
]

df[ANOMALY_FEATURES] = df[ANOMALY_FEATURES].fillna(df[ANOMALY_FEATURES].median())

scaler = StandardScaler()
X_anomaly = scaler.fit_transform(df[ANOMALY_FEATURES])

anomaly_model = IsolationForest(
    n_estimators=200,
    contamination=0.05,  # assume ~5% of readings are anomalous
    random_state=42,
    n_jobs=-1,
)
anomaly_model.fit(X_anomaly)

anomaly_scores = anomaly_model.decision_function(X_anomaly)
anomaly_labels = anomaly_model.predict(X_anomaly)  # -1 = anomaly, 1 = normal
n_anomalies = (anomaly_labels == -1).sum()
print(f"  Anomalies detected in training data: {n_anomalies} ({n_anomalies/len(df)*100:.1f}%)")
print(f"  Anomaly score range: [{anomaly_scores.min():.3f}, {anomaly_scores.max():.3f}]")

joblib.dump(anomaly_model, "models/anomaly_detector.pkl")
joblib.dump(scaler, "models/anomaly_scaler.pkl")
joblib.dump(ANOMALY_FEATURES, "models/anomaly_features.pkl")

# ─── Save augmented dataset with health scores ───────────────────
df.to_csv("elderly_healthcare_digital_twin_dataset_augmented.csv", index=False)
print("\n  Dataset updated with Health Score column.")

# ─── Summary ─────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("MODELS SAVED TO ./models/")
print("=" * 60)
files = os.listdir("models")
for f in sorted(files):
    size = os.path.getsize(f"models/{f}")
    print(f"  {f:<45} {size/1024:.1f} KB")

print("\nDone. All models ready for FastAPI serving.")

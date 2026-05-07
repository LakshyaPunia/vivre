import pandas as pd
import numpy as np

np.random.seed(42)

df = pd.read_csv("elderly_healthcare_digital_twin_dataset.csv")
n = len(df)

# --- Age (65–90, realistic geriatric distribution) ---
# Truncated normal centered at 74, most patients between 65-85
raw_ages = np.random.normal(loc=74, scale=6, size=n)
ages = np.clip(raw_ages, 65, 90).astype(int)
df.insert(1, "Age", ages)

# --- Gender (55% Female, 45% Male — women dominate elderly populations) ---
gender = np.random.choice(["Female", "Male"], size=n, p=[0.55, 0.45])
df.insert(2, "Gender", gender)

# --- Patient Name (realistic demo display names) ---
first_names_f = ["Mary", "Margaret", "Patricia", "Barbara", "Dorothy", "Helen",
                 "Nancy", "Betty", "Carol", "Sandra", "Ruth", "Sharon", "Shirley",
                 "Elizabeth", "Linda", "Joan", "Anne", "Martha", "Jean", "Alice"]
first_names_m = ["James", "Robert", "John", "William", "David", "George", "Charles",
                 "Joseph", "Thomas", "Richard", "Edward", "Frank", "Walter", "Harold",
                 "Raymond", "Arthur", "Paul", "Henry", "Kenneth", "Donald"]
last_names    = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
                 "Davis", "Wilson", "Taylor", "Anderson", "Thomas", "Jackson", "White",
                 "Harris", "Martin", "Thompson", "Moore", "Young", "Allen", "Clark",
                 "Lewis", "Robinson", "Walker", "Hall", "King", "Wright", "Green"]

names = []
for g in gender:
    fn = np.random.choice(first_names_f if g == "Female" else first_names_m)
    ln = np.random.choice(last_names)
    names.append(f"{fn} {ln}")
df.insert(3, "Patient Name", names)

# --- Emergency Contact Name (family member) ---
contact_first = ["Sarah", "Michael", "Jennifer", "David", "Emily", "Daniel", "Jessica",
                 "Matthew", "Ashley", "Christopher", "Amanda", "Joshua", "Melissa",
                 "Andrew", "Stephanie", "Kevin", "Nicole", "Ryan", "Elizabeth", "Jason"]
contacts = [f"{np.random.choice(contact_first)} {np.random.choice(last_names)}" for _ in range(n)]
df.insert(4, "Emergency Contact", contacts)

# --- Relation to Contact ---
relations = np.random.choice(
    ["Son", "Daughter", "Grandson", "Granddaughter", "Spouse"],
    size=n,
    p=[0.25, 0.30, 0.15, 0.15, 0.15]
)
df.insert(5, "Relation to Contact", relations)

# --- City (US cities, for demo location context) ---
cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
          "San Antonio", "San Diego", "Dallas", "Jacksonville", "Austin", "Fort Worth",
          "Columbus", "Charlotte", "Indianapolis", "San Francisco", "Seattle", "Denver",
          "Nashville", "Oklahoma City"]
df["City"] = np.random.choice(cities, size=n)

# --- Insurance Status ---
insurance = np.random.choice(
    ["Medicare", "Medicaid", "Medicare + Supplement", "Uninsured", "Private"],
    size=n,
    p=[0.45, 0.20, 0.20, 0.08, 0.07]
)
df["Insurance Status"] = insurance

# --- Comorbidity Count (derived: number of additional conditions on top of primary) ---
# Elderly often have 2–4 comorbidities; correlated loosely with age
base_comorbidity = ((ages - 65) / 10).astype(int)  # 0–2 from age
extra = np.random.randint(0, 3, size=n)
df["Comorbidity Count"] = np.clip(base_comorbidity + extra, 0, 5)

# --- Mobility Level (important for fall risk context) ---
mobility_probs = [0.20, 0.40, 0.30, 0.10]  # Independent, Assisted, Limited, Wheelchair
mobility = np.random.choice(
    ["Independent", "Assisted", "Limited", "Wheelchair"],
    size=n,
    p=mobility_probs
)
df["Mobility Level"] = mobility

# --- Living Situation ---
living = np.random.choice(
    ["Alone", "With Family", "Assisted Living", "Nursing Home"],
    size=n,
    p=[0.28, 0.42, 0.20, 0.10]
)
df["Living Situation"] = living

# --- Wearable Device ID (unique per patient, for device→patient mapping) ---
df["Device ID"] = ["DEV-" + str(pid).zfill(6) for pid in df["Patient Number"]]

# --- Data Quality Score adjustment: age affects sensor reliability slightly ---
# Older patients may have slightly lower data accuracy (thicker skin, movement artifacts)
age_penalty = ((ages - 65) * 0.05).astype(int)  # 0–1 point reduction
df["Data Accuracy (%)"] = np.clip(df["Data Accuracy (%)"].astype(int) - age_penalty, 70, 99)

# --- Reorder: put demographics right after Patient Number for readability ---
cols = df.columns.tolist()
priority = ["Patient Number", "Patient Name", "Age", "Gender",
            "Emergency Contact", "Relation to Contact", "City",
            "Insurance Status", "Living Situation", "Mobility Level",
            "Comorbidity Count", "Device ID"]
rest = [c for c in cols if c not in priority]
df = df[priority + rest]

df.to_csv("elderly_healthcare_digital_twin_dataset_augmented.csv", index=False)

# Summary
print("Augmented dataset saved.")
print(f"Shape: {df.shape}")
print(f"\nNew columns added: Age, Gender, Patient Name, Emergency Contact,")
print(f"Relation to Contact, City, Insurance Status, Living Situation,")
print(f"Mobility Level, Comorbidity Count, Device ID")
print(f"\nAge distribution:")
print(f"  Mean: {ages.mean():.1f}  Std: {ages.std():.1f}  Min: {ages.min()}  Max: {ages.max()}")
print(f"\nGender split:")
print(pd.Series(gender).value_counts().to_string())
print(f"\nInsurance Status:")
print(pd.Series(insurance).value_counts().to_string())
print(f"\nLiving Situation:")
print(pd.Series(living).value_counts().to_string())
print(f"\nMobility Level:")
print(pd.Series(mobility).value_counts().to_string())
print(f"\nSample row:")
print(df.iloc[0].to_string())

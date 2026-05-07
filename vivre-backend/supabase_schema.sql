-- Vivre — Supabase Schema
-- Run this in your Supabase project: SQL Editor > New Query > paste & run

-- ── Patients ────────────────────────────────────────────────────
create table if not exists patients (
  id                uuid primary key default gen_random_uuid(),
  name              text not null,
  age               int,
  gender            text,
  bmi               float,
  city              text,
  insurance_status  text,
  living_situation  text,
  mobility_level    text,
  comorbidity_count int default 0,
  device_id         text unique,
  emergency_contact text,
  relation_to_contact text,
  conditions        text[],
  created_at        timestamptz default now()
);

-- ── Users (family members, doctors, elderly users) ───────────────
create table if not exists users (
  id                uuid primary key default gen_random_uuid(),
  email             text unique not null,
  full_name         text,
  role              text check (role in ('elderly', 'family', 'doctor')) default 'family',
  linked_patient_id uuid references patients(id),
  created_at        timestamptz default now()
);

-- ── Vitals Readings ──────────────────────────────────────────────
create table if not exists vitals_readings (
  id                    uuid primary key default gen_random_uuid(),
  patient_id            uuid references patients(id) on delete cascade,
  device_id             text,
  timestamp             timestamptz not null,
  heart_rate            float,
  spo2                  float,
  systolic_bp           float,
  diastolic_bp          float,
  body_temp             float,
  respiratory_rate      float,
  glucose_level         float,
  activity_score        float,
  sleep_quality         float,
  stress_level          float,
  hydration_level       float,
  fall_detected         boolean default false,
  fall_frequency        int default 0,
  ecg_abnormality       text,
  medication_adherence  text,
  heart_rate_alert      text,
  spo2_alert            text,
  bp_alert              text,
  temp_alert            text,
  predicted_disease     text,
  disease_confidence    float,
  health_score          float,
  health_band           text,
  is_anomaly            boolean default false,
  created_at            timestamptz default now()
);

-- Index for fast patient + time queries
create index if not exists idx_vitals_patient_time
  on vitals_readings(patient_id, timestamp desc);

-- ── Alerts ───────────────────────────────────────────────────────
create table if not exists alerts (
  id               uuid primary key default gen_random_uuid(),
  patient_id       uuid references patients(id) on delete cascade,
  type             text not null,
  severity         text check (severity in ('warning', 'critical')) not null,
  message          text not null,
  triggered_at     timestamptz default now(),
  resolved_at      timestamptz,
  acknowledged_by  text,
  created_at       timestamptz default now()
);

create index if not exists idx_alerts_patient
  on alerts(patient_id, triggered_at desc);

-- ── Location Logs ────────────────────────────────────────────────
create table if not exists location_logs (
  id          uuid primary key default gen_random_uuid(),
  patient_id  uuid references patients(id) on delete cascade,
  lat         float not null,
  lng         float not null,
  accuracy    float,
  address     text,
  timestamp   timestamptz default now()
);

create index if not exists idx_location_patient
  on location_logs(patient_id, timestamp desc);

-- ── Medications ──────────────────────────────────────────────────
create table if not exists medications (
  id               uuid primary key default gen_random_uuid(),
  patient_id       uuid references patients(id) on delete cascade,
  name             text not null,
  dosage           text,
  schedule         text,
  adherence_status text default 'Moderate',
  created_at       timestamptz default now()
);

-- ── Doctor Sessions ──────────────────────────────────────────────
create table if not exists doctor_sessions (
  id          uuid primary key default gen_random_uuid(),
  patient_id  uuid references patients(id),
  doctor_id   uuid references users(id),
  family_id   uuid references users(id),
  started_at  timestamptz default now(),
  ended_at    timestamptz,
  notes       text
);

-- ── Row Level Security ───────────────────────────────────────────
alter table patients       enable row level security;
alter table vitals_readings enable row level security;
alter table alerts          enable row level security;
alter table location_logs   enable row level security;
alter table medications     enable row level security;

-- Service role bypasses RLS — backend uses service key so this is fine for now.
-- Add user-scoped policies when adding auth.

-- ── Seed: 3 demo patients ────────────────────────────────────────
insert into patients (id, name, age, gender, bmi, city, insurance_status,
                      living_situation, mobility_level, comorbidity_count,
                      device_id, emergency_contact, relation_to_contact)
values
  ('00000000-0000-0000-0000-000000000001', 'Ruth Thomas',   76, 'Female', 24.0,
   'Chicago',      'Medicare',              'With Family',   'Assisted',    3,
   'DEV-000001', 'Joshua Miller', 'Daughter'),
  ('00000000-0000-0000-0000-000000000002', 'Harold Wilson', 82, 'Male',   27.5,
   'Houston',       'Medicare + Supplement', 'Alone',         'Limited',     4,
   'DEV-000002', 'Sarah Wilson',  'Son'),
  ('00000000-0000-0000-0000-000000000003', 'Dorothy Clark', 69, 'Female', 22.1,
   'San Francisco', 'Private',               'Assisted Living','Independent', 1,
   'DEV-000003', 'Emily Clark',   'Daughter')
on conflict (id) do nothing;

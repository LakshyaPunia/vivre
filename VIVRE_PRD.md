# Vivre — Product Requirements Document

## Product Overview

**Product Name:** Vivre  
**Tagline:** Live fully, stay connected.  
**Type:** Web application (responsive, mobile-first)  
**Purpose:** AI-powered health monitoring platform that gives family members real-time visibility into the health and safety of their elderly loved ones, with direct access to care and clinical support.

---

## Target Users

### Primary User — Family Member (Guardian)
- Adult children or grandchildren of elderly patients
- Checks the app daily; may receive urgent push alerts
- Wants at-a-glance health status, not raw data
- Needs to act quickly when an alert fires

### Secondary User — Elderly Patient
- Wears the device; minimal interaction with the app
- May view their own health summary on a simplified view

### Tertiary User — Doctor / Clinician
- Reviews flagged patients
- Joins calls initiated by the family member
- Views historical vitals and AI-generated summaries

---

## Core Pages & Features

### 1. Authentication
- Login / Sign up screen
- Role selection: Family Member, Doctor
- Link to a patient by Patient ID or invite code

---

### 2. Dashboard (Home)
The primary screen for family members. Shows overview of all linked patients.

**Components:**
- Header with greeting ("Good morning, Sarah") + notification bell with unread badge
- Patient cards (one per linked patient) showing:
  - Patient name + avatar/initials ring
  - Health score gauge (animated arc, 0–100)
  - Health band label: Critical / Poor / Fair / Good / Excellent
  - Last updated timestamp
  - Top active alert badge (if any)
  - Predicted condition chip
- Active alerts banner at top if any critical alerts exist
- Quick-action fab button: "Add Patient"

**Behaviour:**
- Cards update in real time via Supabase Realtime
- Critical health score (< 40) triggers card to pulse red
- Tap a card → Patient Detail page

---

### 3. Patient Detail Page
Deep-dive view for a single patient.

**Sections:**

#### A. Hero Section
- Patient name, age, city
- Large animated health score ring (fills to score value on load)
- Health band label + last reading timestamp
- Predicted disease chip
- Emergency contact name + quick-call button

#### B. Live Vitals Grid
Six metric cards, each with icon, current value, trend arrow, and a mini sparkline chart:
- Heart Rate (bpm) — pulsing heart icon
- SpO2 (%) — breathing animation
- Blood Pressure (mmHg) — gauge icon
- Body Temperature (°C) — thermometer icon
- Glucose Level (mg/dL) — drop icon
- Respiratory Rate (breaths/min) — wave icon

Each card colour-codes by alert status: green (normal), amber (warning), red (critical).

#### C. Health Trends Chart
- 24-hour line chart showing health score over time
- Togglable: 6h / 24h / 7d
- Overlay dots for alert events
- Animated draw-on effect on load

#### D. Lifestyle Metrics Row
- Sleep Quality, Stress Level, Activity Score, Hydration Level, Medication Adherence
- Displayed as horizontal progress bars with colour gradients

#### E. Alert Feed
- Chronological list of alerts
- Each alert shows: severity icon, message, time, acknowledge button
- Critical alerts are highlighted with red left border + glow

#### F. AI Health Chatbot
- Chat interface at the bottom of the page
- Pre-populated suggested questions:
  - "How is she doing today?"
  - "Should I be worried about her heart rate?"
  - "What does her health score mean?"
- Conversation history persisted per session
- Typing indicator (animated dots) while waiting for response
- Powered by GPT-4o via the Vivre API

---

### 4. Location Tracking Page
- Full-screen Google Maps embed
- Patient's last known location as a pin with their photo/initials
- Last updated timestamp
- Geofence status: "Within safe zone" / "Outside safe zone"
- History of location trail (last 24h) as a polyline

---

### 5. Doctor Connect Page
- List of available doctors with specialty and availability status
- "Connect Now" button triggers a call flow:
  1. App notifies the elderly person's device
  2. Video call interface (Daily.co embed)
  3. Doctor can view patient's live vitals sidebar during call
- Past session history with notes

---

### 6. Alerts Centre
- Unified alert inbox across all linked patients
- Filter by: All / Critical / Warning / Acknowledged
- Each alert links back to the patient detail
- Bulk acknowledge action

---

### 7. Patient Profile / Settings
- Edit patient information
- Manage linked family members
- Medication list management
- Notification preferences (push, email, SMS)
- Wearable device status and battery level

---

## API Integration

**Base URL:** `http://localhost:8000/api/v1` (development) → production Railway URL

**Supabase Config:**
- URL: `https://ibetcczlscpxfmrxaery.supabase.co`
- Anon Key: `sb_publishable_fOpTVyH5ORhYXRYhz3fagQ_xoGdCR77`
- Enable Realtime on: `vitals_readings`, `alerts`

**Endpoints used by frontend:**

| Page | Endpoint |
|---|---|
| Dashboard | `GET /patients` |
| Patient Detail | `GET /patients/{id}`, `GET /patients/{id}/vitals`, `GET /patients/{id}/health-score` |
| Alerts | `GET /patients/{id}/alerts`, `PATCH /alerts/{id}/acknowledge` |
| Location | `GET /patients/{id}/location` |
| Chatbot | `POST /chat` |

**Realtime subscriptions:**
- `vitals_readings` table → update vitals cards live
- `alerts` table → show alert toasts instantly

---

## Demo Patients (pre-seeded in Supabase)

| ID | Name | Age | City | Status |
|---|---|---|---|---|
| `00000000-0000-0000-0000-000000000001` | Ruth Thomas | 76 | Chicago | Active |
| `00000000-0000-0000-0000-000000000002` | Harold Wilson | 82 | Houston | Active — frequent alerts |
| `00000000-0000-0000-0000-000000000003` | Dorothy Clark | 69 | San Francisco | Active |

---

## Non-Functional Requirements

- **Performance:** Initial load < 2s; vitals update visible within 1s of Supabase event
- **Responsive:** Mobile-first; works on 375px width and up; tablet and desktop optimised
- **Accessibility:** WCAG AA contrast ratios; screen-reader labels on all icons
- **Browser support:** Chrome, Safari, Firefox — latest 2 versions

# Vivre — Design PRD

## Design Philosophy

Vivre lives at the intersection of **clinical precision** and **human warmth**. The design must feel like a premium health-tech product — confident, modern, and alive — while never losing sight of the emotional weight of monitoring a loved one's health.

**Three design principles:**
1. **Alive** — Data is not static. Every number breathes, pulses, and moves. The interface should feel like it has a heartbeat.
2. **Clear in a crisis** — When something is wrong, it is unmistakably wrong. Alerts are impossible to miss. Actions are one tap away.
3. **Warm, not clinical** — Dark glass surfaces, soft glows, and human typography. This is a family product, not a hospital terminal.

---

## Visual Identity

### Color System

```
Background Layer
  --bg-base:        #080C14    Deep space navy — primary app background
  --bg-surface:     #0F1623    Card and panel background
  --bg-elevated:    #162035    Elevated surface (modals, drawers)
  --bg-glass:       rgba(22, 32, 53, 0.7)  Glassmorphism surface

Primary Accent — Cyan
  --cyan-400:       #22D3EE
  --cyan-500:       #06B6D4    Primary interactive colour
  --cyan-600:       #0891B2
  --cyan-glow:      rgba(6, 182, 212, 0.35)

Secondary Accent — Violet
  --violet-400:     #A78BFA
  --violet-500:     #8B5CF6    Secondary accent, AI features
  --violet-glow:    rgba(139, 92, 246, 0.35)

Status Colors
  --status-ok:      #10B981    Emerald — normal readings
  --status-ok-glow: rgba(16, 185, 129, 0.3)
  --status-warn:    #F59E0B    Amber — warning readings
  --status-warn-glow: rgba(245, 158, 11, 0.3)
  --status-crit:    #EF4444    Red — critical readings
  --status-crit-glow: rgba(239, 68, 68, 0.4)

Text
  --text-primary:   #F0F4FF
  --text-secondary: #8892A4
  --text-muted:     #4B5563

Borders
  --border-subtle:  rgba(255, 255, 255, 0.06)
  --border-glass:   rgba(255, 255, 255, 0.10)
```

### Typography

```
Font Stack:
  Display / Hero:   "Outfit", sans-serif  — weights 300, 600, 700
  Body / UI:        "Inter", sans-serif   — weights 400, 500, 600
  Mono / Data:      "JetBrains Mono", monospace — weights 400, 500

Scale:
  --text-xs:    11px / 1.4
  --text-sm:    13px / 1.5
  --text-base:  15px / 1.6
  --text-lg:    18px / 1.5
  --text-xl:    22px / 1.4
  --text-2xl:   28px / 1.3
  --text-3xl:   36px / 1.2
  --text-hero:  52px / 1.1  — Outfit 300

Vital Numbers:
  Font: JetBrains Mono 500
  Size: 32–48px depending on card size
  Color: --text-primary with slight glow matching status color
```

### Spacing & Radius

```
Spacing scale (4px base):
  4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80

Border radius:
  --radius-sm:   8px
  --radius-md:   12px
  --radius-lg:   16px
  --radius-xl:   24px
  --radius-2xl:  32px
  --radius-full: 9999px
```

---

## Glassmorphism System

All cards use a consistent glass treatment:

```css
.glass-card {
  background: rgba(22, 32, 53, 0.65);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  box-shadow:
    0 4px 24px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

.glass-card--cyan {
  border-color: rgba(6, 182, 212, 0.2);
  box-shadow:
    0 4px 24px rgba(0, 0, 0, 0.4),
    0 0 40px rgba(6, 182, 212, 0.08),
    inset 0 1px 0 rgba(6, 182, 212, 0.1);
}

.glass-card--critical {
  border-color: rgba(239, 68, 68, 0.3);
  box-shadow:
    0 4px 24px rgba(0, 0, 0, 0.4),
    0 0 40px rgba(239, 68, 68, 0.15),
    inset 0 1px 0 rgba(239, 68, 68, 0.1);
  animation: critical-pulse 2s ease-in-out infinite;
}
```

---

## Animation System

### Core Principles
- **Duration:** Fast UI feedback = 150ms. Standard transitions = 300ms. Dramatic reveals = 600–900ms.
- **Easing:** Use `cubic-bezier(0.16, 1, 0.3, 1)` (ease-out spring) for entrances. `ease-in-out` for loops.
- **Stagger:** List items and grid cards enter with 60ms stagger between each.
- **Never block:** Animations never delay interaction. Use `pointer-events: none` on animating elements.

### Specific Animations

#### 1. Heart Rate Pulse
```css
/* The heart icon and the HR value both pulse at the patient's actual BPM */
@keyframes heartbeat {
  0%, 100% { transform: scale(1);    opacity: 1; }
  14%       { transform: scale(1.3); opacity: 1; }
  28%       { transform: scale(1);   opacity: 0.8; }
  42%       { transform: scale(1.2); opacity: 1; }
}
/* animation-duration = 60000ms / heart_rate */
/* e.g. 78 bpm → duration: 769ms */
```

#### 2. SpO2 Breathing Ring
```css
/* A circular ring around the SpO2 card that slowly expands and contracts */
@keyframes breathe {
  0%, 100% { transform: scale(1);    opacity: 0.6; }
  50%       { transform: scale(1.08); opacity: 1; }
}
/* duration: 4s ease-in-out infinite — simulates breathing rhythm */
```

#### 3. Health Score Arc Fill
```css
/* SVG arc draws from 0 to the score value on page load */
/* Use stroke-dashoffset animation from circumference → (1 - score/100) * circumference */
/* Duration: 1.2s cubic-bezier(0.16, 1, 0.3, 1) */
/* Colour transitions: red → amber → green based on score */
```

#### 4. Vitals Number Count-Up
```
When a new reading arrives or page loads:
- Numbers count up from 0 (or previous value) to current value
- Duration: 800ms ease-out
- Use a number spring animation library (e.g. react-spring or framer-motion's useSpring)
```

#### 5. Alert Slide-In Toast
```css
@keyframes alert-enter {
  from {
    transform: translateX(120%) scale(0.9);
    opacity: 0;
  }
  to {
    transform: translateX(0) scale(1);
    opacity: 1;
  }
}
/* Critical alerts also have a red glow pulse after entering */
@keyframes alert-glow {
  0%, 100% { box-shadow: 0 0 20px rgba(239, 68, 68, 0.3); }
  50%       { box-shadow: 0 0 40px rgba(239, 68, 68, 0.7); }
}
```

#### 6. Card Entrance (Page Load)
```
- Cards fade in + translate Y from +20px to 0
- Duration: 500ms ease-out
- Stagger: 80ms between each card
- Use Framer Motion variants:
  container: { staggerChildren: 0.08 }
  item: { opacity: [0, 1], y: [20, 0], transition: { duration: 0.5 } }
```

#### 7. Chart Draw-On
```
- Line charts animate their path from left to right on mount
- Use SVG pathLength animation: strokeDashoffset from 1 → 0
- Duration: 1.4s cubic-bezier(0.16, 1, 0.3, 1)
- Area fill fades in after line draw completes (300ms delay)
```

#### 8. Realtime Data Flash
```
When a new reading arrives via Supabase Realtime:
- The updated metric card briefly flashes its border to cyan
- The number animates from old → new value
- A small "LIVE" badge pulses for 2s then fades
```

#### 9. Page Transitions
```
- Route changes: current page slides out left (−60px, opacity 0)
- New page slides in from right (+60px → 0, opacity 0 → 1)
- Duration: 300ms cubic-bezier(0.16, 1, 0.3, 1)
```

#### 10. Gesture — Pull to Refresh (Mobile)
```
- Overscroll triggers a circular spinner at top of page
- Spinner uses cyan gradient that rotates
- On release: data refetches, spinner shrinks and disappears
- Haptic feedback on trigger threshold (if supported)
```

#### 11. Swipe to Acknowledge Alert
```
- Alert cards can be swiped right to acknowledge on mobile
- Reveals a green checkmark background as swipe progresses
- On full swipe: card collapses with spring animation
- Haptic feedback on completion
```

#### 12. Doctor Connect Call Entrance
```
- When call starts: video panels slide up from bottom
- Patient vitals sidebar slides in from right
- Both use spring physics: tension 200, friction 20
```

---

## Component Specifications

### Health Score Ring
```
Outer ring:     SVG circle, stroke-width 8px, #162035 (track)
Score arc:      SVG circle, stroke-width 8px, animated fill
                0–39:  stroke #EF4444 + drop-shadow(0 0 8px #EF4444)
                40–59: stroke #F59E0B + drop-shadow(0 0 8px #F59E0B)
                60–74: stroke #3B82F6 + drop-shadow(0 0 8px #3B82F6)
                75–89: stroke #10B981 + drop-shadow(0 0 8px #10B981)
                90–100: stroke #06B6D4 + drop-shadow(0 0 12px #06B6D4)
Center text:    Score number in JetBrains Mono 700 / 36px
                Band label below in Inter 500 / 12px text-secondary
Size:           120px diameter on patient cards, 200px on detail hero
```

### Vital Metric Card
```
Size:           Card min-height 120px, full width of grid cell
Layout:         Icon (top-left) | Label (top) | Value (center-large) | Trend (bottom-right)
Icon:           28px, coloured to match status
Value:          JetBrains Mono 500 / 32px, coloured to match status
Unit:           Inter 400 / 12px text-secondary, inline after value
Trend arrow:    ↑ (green) / ↓ (red) / → (muted) + % change vs previous
Sparkline:      40px tall mini chart at bottom of card, no axes, filled area
Status glow:    Subtle box-shadow matching status color on all 4 sides
On hover:       scale(1.02) + border brightens — 200ms ease
```

### Alert Item
```
Left border:    4px solid — amber (warning) or red (critical)
Icon:           Warning triangle (amber) or siren (red), 20px
Message:        Inter 500 / 14px text-primary
Timestamp:      Inter 400 / 12px text-muted
Acknowledge:    Ghost button, right-aligned, "Mark resolved"
Critical items: Background has subtle red radial gradient from left border
New alerts:     Pulse animation on left border for 5s after arrival
```

### AI Chatbot
```
Container:      Fixed bottom panel (mobile) or right drawer (desktop)
Toggle:         FAB button — violet gradient, brain/spark icon, bottom-right
                Entrance: scale 0 → 1 with spring, 400ms
Panel:          Glassmorphism, 380px wide (desktop), full-width (mobile)
                Slides up from bottom (mobile) or in from right (desktop)

Messages:
  User bubble:  Right-aligned, cyan gradient bg, white text, radius-xl radius-sm bottom-right
  AI bubble:    Left-aligned, glass surface, text-primary, typing indicator first
  Typing:       Three dots, staggered scale pulse animation (150ms offset each)

Input:
  Full-width text field, glass surface, cyan focus ring
  Send button: cyan, icon only, scale pulse on hover
  Quick suggestions: horizontal scrollable chips above input
```

### Navigation
```
Desktop sidebar (240px):
  Logo: "Vivre" in Outfit 600 with a small cyan pulse dot
  Nav items: icon + label, active state = cyan left border + glass bg + text-primary
  Hover: subtle background fill, 150ms ease

Mobile bottom tab bar:
  5 tabs: Home, Patients, Alerts, Location, Chat
  Active tab: cyan icon + label, animated underline pill
  Inactive: muted icon, no label
  Tab switch: icon does a small bounce (scale 1→1.2→1, 200ms spring)
```

### Background
```
Base:           #080C14 solid
Decorative:     2–3 large radial gradients (very subtle, opacity 0.03–0.06):
                - Cyan bloom: top-left area
                - Violet bloom: bottom-right area
                - These slowly drift (very slow animation, 30s cycle, opacity shift)
Grid overlay:   SVG dot grid, 24px spacing, opacity 0.03
```

---

## Page-Specific Layouts

### Dashboard

```
Desktop (1280px+):
┌─────────────────────────────────────────────────────────┐
│ SIDEBAR  │  Header: "Good morning, Sarah"    🔔  Avatar │
│  (240px) ├─────────────────────────────────────────────│
│          │  ⚠ Critical Alert Banner (if active)         │
│  Home    ├─────────────────────────────────────────────│
│  Patients│  Patient Cards Grid — 3 columns              │
│  Alerts  │  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  Location│  │ Ruth T.  │ │Harold W. │ │Dorothy C.│    │
│  Chat    │  │ Score 74 │ │ Score 56 │ │ Score 95 │    │
│          │  │  ●●●●○   │ │  ●●○○○⚠ │ │  ●●●●●  │    │
│  ──────  │  └──────────┘ └──────────┘ └──────────┘    │
│  Settings│                                              │
└─────────────────────────────────────────────────────────┘

Mobile (375px):
Single column, patient cards stack vertically.
Cards are horizontally scrollable on very small screens.
```

### Patient Detail

```
Desktop:
┌──────────┬──────────────────────────────┬───────────────┐
│ Sidebar  │  Hero: Name, Score Ring,      │  AI Chatbot   │
│          │  Disease, Emergency Contact   │  (Right panel)│
│          ├──────────────────────────────┤               │
│          │  Vitals Grid (3×2)            │               │
│          ├──────────────────────────────┤               │
│          │  Health Score Trend Chart     │               │
│          ├──────────────────────────────┤               │
│          │  Lifestyle Metrics            │               │
│          ├──────────────────────────────┤               │
│          │  Alert Feed                   │               │
└──────────┴──────────────────────────────┴───────────────┘

Mobile:
All sections stack vertically. Chatbot is a FAB → full-screen overlay.
```

---

## Iconography

Use **Lucide React** icon set throughout. Key icons:

```
Heart           → heart_rate
Activity        → respiratory_rate / activity score
Droplet         → glucose / hydration
Thermometer     → body temperature
Wind            → SpO2 / breathing
Gauge           → blood pressure
AlertTriangle   → warning alert
Siren/AlertOctagon → critical alert
MapPin          → location
Video           → doctor connect
MessageSquare   → chatbot
BellRing        → notifications
Shield          → health score / safety
Battery         → device status
```

All icons animated on state change: rotate, scale, or color transition.

---

## Micro-interaction Catalogue

| Trigger | Element | Animation |
|---|---|---|
| Page load | All cards | Staggered fade-up (80ms each) |
| New vitals data | Metric value | Count-up spring, border flash cyan |
| Critical reading | Metric card | Red glow pulse, 2s loop |
| New alert | Toast notification | Slide in from right, glow pulse |
| Alert acknowledged | Alert card | Slide out right + collapse height |
| Hover on patient card | Card | scale(1.02), border brightens |
| Tap chatbot FAB | FAB | Scale pulse + panel slides in |
| AI typing | Chat bubble | Three-dot bounce animation |
| Score arc load | SVG arc | Draw from 0 to value, 1.2s |
| Fall detected | Patient card | Red flash + shake animation |
| HR reading | Heart icon | Pulses at actual patient BPM |
| SpO2 card | Ring border | Breathes in/out, 4s cycle |
| Tab navigation (mobile) | Tab icon | Bounce spring on select |
| Pull to refresh | Scroll top | Cyan spinner appears |
| Swipe alert | Alert card | Swipe right to acknowledge |
| Doctor call start | Screen | Video panels spring up |
| Location update | Map pin | Pin bounce + ripple effect |

---

## Responsive Breakpoints

```
Mobile:   375px – 767px   → Single column, bottom nav, full-screen panels
Tablet:   768px – 1023px  → Two columns, collapsible sidebar, side drawers
Desktop:  1024px – 1279px → Three columns, full sidebar
Wide:     1280px+         → Three columns + right panel (chatbot always visible)
```

---

## Loading & Empty States

### Skeleton Screens
- All cards show skeleton loaders on initial load
- Skeletons have a shimmer animation (left → right gradient sweep, 1.5s loop)
- Match exact shape of the real content (no generic rectangles)

### Empty States
- No patients linked: Illustrated empty state + "Add your first patient" CTA
- No alerts: Green checkmark icon + "All clear — no active alerts"
- No vitals yet: Animated device icon + "Waiting for device data..."

### Error States
- API failure: Inline error with retry button, no full-page takeover
- Offline banner: Top ribbon "No internet connection — showing last known data"

---

## Lovable Implementation Notes

Build this as a React application using:
- **Framer Motion** for all animations and page transitions
- **Recharts** or **Tremor** for health trend charts and sparklines
- **Tailwind CSS** with the custom color tokens above (extend the config)
- **Supabase JS client** (`@supabase/supabase-js`) for Realtime subscriptions
- **Lucide React** for icons
- **React Query** (`@tanstack/react-query`) for API data fetching and caching

All glassmorphism effects require `backdrop-filter` — ensure Tailwind's `backdrop-blur` utilities are enabled.

The background gradient blobs should use absolute positioned divs with radial gradients and `pointer-events: none`, layered behind all content.

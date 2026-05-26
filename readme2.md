# ShelfIQ — India's Shelf Intelligence Platform
**Version 3.0 | Prama Innovations India Pvt. Ltd.**

> The first shelf intelligence platform built for India's regional retail chains —
> priced in rupees, alerting on WhatsApp, forecasting around Diwali and IPL,
> and deployable on cameras the store already owns.

---

## WHY THIS EXISTS

India's ₹4.3 trillion FMCG sector runs through 13 million stores. Every global
competitor — Trax ($2.4B), Vispera, Infilect — was built to serve Unilever and
Coca-Cola checking if their products are on shelves. Nobody built for the stores
themselves. Nobody forecasts for Navratri. Nobody alerts on WhatsApp. Nobody runs
on the CCTV cameras already mounted on the wall.

ShelfIQ does all four. That is the product.

---

## PART 1 — AI CODING AGENT PROMPT

*Drop this into Claude Code, Cursor, or any AI coding agent. It encodes the full
India-first product strategy so the agent understands what it's building and why.*

---

```
You are a full-stack engineer and ML systems architect building ShelfIQ
(github.com/vedantpatel-04/Bug404) into a production SaaS product.

## NORTH STAR
ShelfIQ is the first shelf intelligence platform built for India's regional retail
chains. The product positioning is locked:
  - Priced in rupees (₹999–₹4,999/month tiers, UPI billing)
  - Alerts via WhatsApp Business API — not email dashboards
  - Demand forecasting built around Indian festivals: Navratri, Diwali, Uttarayan,
    IPL, Eid, Pongal, Holi (already in codebase — surface it prominently)
  - Runs on cameras the store already owns (existing CCTV/IP cameras, no new hardware)
  - Hindi + Gujarati UI for store associates (English for managers)
  - Targets: regional supermarket chains, D-Mart-scale stores, FMCG distributors
    serving tier-2/3 cities — NOT enterprise CPG brands like Trax does

Every technical decision must reinforce this positioning. If a feature would only
make sense for a ₹50 crore enterprise, deprioritize it.

## EXISTING CODEBASE (do not rewrite ML logic — wrap it)
ShelfIQ is a Python project with:
  - YOLOv8 for shelf product detection (/models/shelf_detector.py)
  - CLIP ViT-B/32 for SKU recognition (/models/sku_recognizer.py)
  - EasyOCR for price tag detection (/planogram/compliance_engine.py)
  - Prophet demand forecasting with Indian event regressors (/forecasting/)
  - Redis Pub/Sub alert system with corrective actions (/alerts/)
  - Streamlit dashboard — 7 pages (/dashboard/) — being replaced with React
  - SQLite — being replaced with PostgreSQL
  - APScheduler for periodic CV jobs (/pipeline/scheduler.py)

## YOUR TASKS — PHASED

───────────────────────────────────────────────────────────
PHASE 1 — Backend API (Weeks 1–2)
───────────────────────────────────────────────────────────

1. Create FastAPI application at /backend/app/ wrapping existing Python modules.

   Core endpoints:
   POST /api/v1/analysis/run           → queue CV pipeline job
   GET  /api/v1/shelves/{store_id}     → current shelf states + stock levels
   GET  /api/v1/alerts                 → paginated alerts (filter: severity, status, aisle)
   POST /api/v1/alerts/{id}/resolve    → mark resolved with resolution note
   GET  /api/v1/forecast/{sku_id}      → Prophet forecast + festival spike annotations
   GET  /api/v1/compliance/{store_id}  → planogram score + violations
   GET  /api/v1/analytics/heatmap      → aisle × hour stockout heatmap
   POST /api/v1/stores                 → onboard a new store
   GET  /api/v1/stores/{id}/cameras    → registered cameras for a store
   WS  /ws/alerts                      → WebSocket for real-time alert streaming

   India-specific endpoints:
   GET  /api/v1/events/upcoming        → next 30 days of Indian festivals/events
                                         with predicted demand impact per SKU
   GET  /api/v1/forecast/festival-preview/{event_name}
                                       → demand spike preview for a named event

2. JWT authentication (RS256). Roles:
     STORE_OWNER   — full access to their stores
     STORE_MANAGER — manage staff, view all alerts
     SHELF_ASSOCIATE — receive WhatsApp tasks, mark resolved
     ANALYST       — read-only, forecasts + heatmaps
     PLATFORM_ADMIN — Prama internal only

3. WhatsApp Business API integration (CRITICAL — this is a core differentiator):
   File: /backend/app/notifications/whatsapp.py

   Use Meta's WhatsApp Business Cloud API (graph.facebook.com/v18.0).
   Send alerts as WhatsApp template messages to registered associate numbers.

   Alert → WhatsApp message format:
   ─────────────────────────────────
   🛒 *ShelfIQ Alert*
   Store: Rajesh Supermart, Bopal
   Aisle: Dairy — Shelf B2
   Issue: Amul Butter 500g is OUT OF STOCK
   Action: Restock from cold storage — suggested qty: 24 units
   Time: 2:14 PM
   [Mark Resolved] ← WhatsApp quick reply button
   ─────────────────────────────────

   WhatsApp quick-reply "Mark Resolved" → hits POST /api/v1/alerts/{id}/resolve
   via webhook. Build the webhook handler at POST /api/v1/webhooks/whatsapp.

   Priority rules (decide channel based on severity):
     CRITICAL (stockout, revenue > ₹500/hr loss) → WhatsApp immediately
     HIGH (low stock, planogram violation)        → WhatsApp within 15 min
     MEDIUM (price mismatch)                      → WhatsApp digest at shift end
     LOW (compliance score drop)                  → Dashboard only

4. Replace SQLite with async PostgreSQL (SQLAlchemy 2.0 + asyncpg).
   Write Alembic migrations. Keep backward compat with existing schema during
   migration — add columns, don't drop.

5. Redis caching:
     Shelf state           → TTL 30 seconds
     Forecast results      → TTL 1 hour (bust on new POS data)
     Festival impact cache → TTL 24 hours
     Compliance scores     → TTL 5 minutes

───────────────────────────────────────────────────────────
PHASE 2 — React Frontend (Weeks 3–4)
───────────────────────────────────────────────────────────

Replace Streamlit with React 18 + TypeScript.
Stack: Vite · TanStack Query v5 · Zustand · Tailwind CSS · shadcn/ui · Recharts.

Language toggle: English (managers) ↔ Hindi ↔ Gujarati.
Store all UI strings in /src/i18n/{en,hi,gu}.json.
Use i18next. Default language detected from browser locale; override in user profile.

Pages (map from existing Streamlit pages):
  /                   → Overview: KPI cards + floor plan + WhatsApp alert feed
  /shelf-monitoring   → Live camera grid with YOLOv8 bounding box overlays (Canvas)
  /compliance         → Planogram gauges + violation table + OCR price mismatches
  /forecast           → Prophet charts + festival spike markers + reorder calendar
  /alerts             → WhatsApp-style alert feed + Kanban task board
  /analytics          → Aisle × Hour heatmap + revenue recovery + festival ROI
  /smart-store        → Customer journey + sensor fusion (existing Smart Store page)
  /settings           → Store setup, camera registration, associate WhatsApp numbers

New page (not in Streamlit — build fresh):
  /festival-dashboard → 30-day festival calendar with per-SKU demand previews.
                        Shows: "Navratri starts in 8 days. Suggested reorder for
                        these 12 SKUs to avoid stockout during peak." 
                        Cards per event: expected demand lift %, current stock,
                        reorder status (Ordered / Pending / At Risk).

Associate mobile view (narrow layout < 480px):
  Simplified view: only WhatsApp-style alert list + one-tap resolve button.
  No charts, no heatmaps. Built for the guy restocking shelves with a phone.

Key components:
  FestivalSpikeBadge  → amber badge on forecast charts marking Indian event dates
  WhatsAppAlertCard   → mimics WhatsApp UI: avatar, message bubble, quick-reply btn
  AisleHeatmap        → Recharts heatmap, aisle on Y-axis, hour on X-axis
  CameraFeed          → Canvas overlay rendering YOLO boxes on MJPEG stream
  StockRiskBadge      → "At Risk for Diwali" warning on low-stock SKUs

───────────────────────────────────────────────────────────
PHASE 3 — India-Specific Product Features (Week 5–6)
───────────────────────────────────────────────────────────

1. UPI Subscription Billing
   Integrate Razorpay for subscription management.
   Three tiers:
     Starter   — ₹999/month   — 1 store, 4 cameras, WhatsApp alerts
     Growth    — ₹2,499/month — 5 stores, 20 cameras, festival dashboard
     Chain     — ₹4,999/month — unlimited stores, API access, custom events

   /backend/app/billing/razorpay.py
   Webhooks: payment.captured → activate subscription
             subscription.halted → grace period 3 days → suspend alerts

2. Quick-Commerce Intelligence (competitive differentiation — no competitor has this)
   File: /backend/app/features/qcommerce_intel.py

   Pull publicly available category trend data from Zepto/Blinkit/Swiggy Instamart
   product pages (scraping or partner APIs if available).
   Map to the store's SKU catalog.
   Surface as: "Zepto near Bopal is trending these 5 SKUs this week.
                Your store currently has 2 of them. Suggest stocking the other 3."
   Show on /analytics page as "Quick-Commerce Watch" section.

3. Edge AI Deployment Mode
   For stores with unreliable internet: package YOLOv8n + CLIP + alert logic
   into a Docker container deployable on a Raspberry Pi 5 or Jetson Nano.
   Shelf analysis runs locally; results sync to cloud when connectivity returns.
   /edge/ directory with Dockerfile.edge and sync daemon.

4. Hindi / Gujarati UI
   All alert messages, corrective action text, and WhatsApp templates must be
   available in English, Hindi, and Gujarati.
   WhatsApp template language selected from associate's profile.
   Gujarati example template:
   "🛒 ShelfIQ ચેતવણી\nSKU: Amul Butter 500g\nAisle: Dairy B2\nSamsya: Stock khatam\nKarar: 24 units refill karo"

───────────────────────────────────────────────────────────
PHASE 4 — Production Infrastructure (Week 7–8)
───────────────────────────────────────────────────────────

1. Docker Compose:
   Services: nginx, react (static), fastapi, celery-cv, celery-forecast,
             celery-alerts, postgres, redis
   GPU-aware CV worker: use NVIDIA runtime in docker-compose.prod.yml
   Edge mode: separate docker-compose.edge.yml for Raspberry Pi / Jetson

2. Celery task queues (separate queues, separate worker pools):
   cv_pipeline     → GPU-accelerated, max 2 concurrent (YOLO + CLIP heavy)
   forecast        → CPU, daily at 2 AM IST
   whatsapp_alerts → high priority, max retries 3, retry delay 30s
   digest_alerts   → batch job, runs at shift end (6 PM, 10 PM IST)

3. GitHub Actions CI/CD:
   On PR:          ruff (Python) + eslint (TS) + pytest + vitest + type check
   On main merge:  build Docker images → push GHCR → deploy staging
   On release tag: staging smoke tests → promote production
   Secrets via GitHub Secrets (never in repo)

## CODING STANDARDS
- Python: async/await, type hints, Pydantic v2 (extra='forbid')
- TypeScript: strict mode, no any, explicit return types
- i18n: every user-facing string through i18next — no hardcoded English in JSX
- WhatsApp templates: register in Meta Business Manager before use in code
- Secrets: env vars only. Never hardcode API keys, phone numbers, or tokens.
- Every endpoint: input validation + structured error response + audit log entry
- Tests: pytest for backend, vitest for frontend. New feature = new test file.
```

---

## PART 2 — INDIA-FIRST PRODUCT DESIGN

### The Four Positioning Pillars (never compromise these)

**1. Priced in rupees, built for Indian margins**

Global competitors price in USD for enterprise budgets. ShelfIQ prices in INR
for store owners who think in monthly margin, not annual software contracts.

| Tier | Price | Target | Stores | Cameras |
|------|-------|--------|--------|---------|
| Starter | ₹999/month | Single supermarket | 1 | 4 |
| Growth | ₹2,499/month | Regional chain | 5 | 20 |
| Chain | ₹4,999/month | Distributor / franchise | Unlimited | Unlimited |

Billing: Razorpay subscription via UPI autopay — the payment method India's
store owners actually use. Annual plan: 2 months free (₹9,990 / ₹24,990 / ₹49,990).

**2. WhatsApp-first alerts — not email dashboards**

The store manager in Surat does not open a Streamlit dashboard at 2 PM on a
Tuesday. He reads WhatsApp. Every competitor sends alerts to a web dashboard
that nobody checks. ShelfIQ sends a WhatsApp message that gets read within 3 minutes.

Alert lifecycle on WhatsApp:
```
Stockout detected (CV pipeline)
    → Alert created in DB
    → WhatsApp message sent to assigned associate
    → Associate taps "Mark Resolved" quick-reply
    → Webhook fires → alert resolved in DB
    → Manager receives resolution confirmation
    → Resolution time recorded as KPI
```

WhatsApp template types to register in Meta Business Manager:
- `shelfiq_stockout_alert`       → Immediate, CRITICAL severity
- `shelfiq_low_stock_alert`      → Within 15 min, HIGH severity
- `shelfiq_shift_digest`         → Batch summary at 6 PM / 10 PM
- `shelfiq_festival_reminder`    → 3 days before major event
- `shelfiq_reorder_confirmation` → When auto-replenishment order placed

**3. Demand forecasting built around Indian festivals**

This is already in the codebase. The product strategy is to make it the most
prominent feature — not a footnote on the forecast page.

Indian event calendar already implemented (surface these, don't hide them):

| Event | Type | Magnitude | Typical Demand Categories |
|-------|------|-----------|--------------------------|
| Navratri (9 nights) | Festival | 3 — National | Snacks, sweets, devotional items |
| Diwali | Festival | 3 — National | Sweets, dry fruits, gifting, lighting |
| Uttarayan / Makar Sankranti | Festival | 2 — State | Sweets, sesame products, kites |
| IPL (match days) | Cricket | 2 — City-wide | Beverages, snacks, frozen food |
| Holi | Festival | 3 — National | Colours, sweets, dairy |
| Eid-ul-Fitr | Festival | 2 — City-wide | Sweets, biryani ingredients, dry fruits |
| Pongal | Festival | 2 — Regional | Rice, jaggery, dairy |
| Janmashtami | Festival | 2 — Regional | Dairy, sweets |
| Sale events (Big Billion Day, etc.) | Sale | 1–2 | Category-wide |

Festival Dashboard page (new — not in current Streamlit):
- 30-day rolling calendar of upcoming events
- Per-SKU demand lift prediction for each event
- Traffic light status per SKU: Green (sufficient stock) / Amber (reorder now) / Red (at risk)
- One-tap bulk reorder for all At Risk SKUs before a festival
- Post-event ROI report: predicted lift vs actual sales, stockout cost avoided

**4. Deployable on cameras the store already owns**

Zero hardware cost is the sales pitch that unlocks SMB adoption. Every Indian
store above 500 sq ft has CCTV cameras already installed. ShelfIQ works with them.

Camera onboarding flow:
1. Store owner enters RTSP stream URL of existing CCTV camera in /settings
2. ShelfIQ tests the stream, runs a calibration frame, maps camera to aisle
3. YOLOv8 inference begins on the stream — no hardware purchase required
4. For stores with poor internet: deploy the Edge AI Docker container on a ₹6,000
   Raspberry Pi 5 — one-time cost, syncs when connectivity returns

Supported camera types (test and certify these):
- Any IP camera with RTSP output (Hikvision, CP Plus, Dahua — dominant in India)
- Any camera accessible via ONVIF protocol
- USB webcam (for small pilot deployments)

---

## PART 3 — REACT FRONTEND ARCHITECTURE

### Technology Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| Framework | React 18 + TypeScript | Type safety, ecosystem |
| Build | Vite 5 | Fast dev, optimized builds |
| Styling | Tailwind CSS + shadcn/ui | Rapid, accessible UI |
| Server state | TanStack Query v5 | Caching, background sync |
| Client state | Zustand | Lightweight, minimal boilerplate |
| Charts | Recharts + D3 | Flexible visualization |
| i18n | i18next | EN / HI / GU language support |
| Real-time | WebSocket native | Alert streaming from FastAPI |
| Testing | Vitest + React Testing Library | Vite-native |

### Folder Structure

```
shelfiq-frontend/
├── src/
│   ├── api/
│   │   ├── client.ts          # axios instance with JWT interceptors
│   │   ├── alerts.ts          # useAlerts, useMutateAlert
│   │   ├── forecast.ts        # useForecast, useFestivalPreview
│   │   ├── shelves.ts         # useShelfState
│   │   ├── qcommerce.ts       # useQCommerceWatch (new feature)
│   │   └── ws/alertSocket.ts  # WebSocket hook for real-time alerts
│   ├── components/
│   │   ├── ui/                # shadcn/ui base
│   │   ├── layout/            # AppShell, Sidebar, Topbar, LanguageToggle
│   │   ├── alerts/
│   │   │   ├── WhatsAppAlertCard.tsx   # mimics WhatsApp UI bubble
│   │   │   ├── AlertKanban.tsx
│   │   │   └── CorrectiveAction.tsx
│   │   ├── forecast/
│   │   │   ├── FestivalSpikeBadge.tsx  # amber badge on chart date axis
│   │   │   ├── FestivalCalendar.tsx    # 30-day event calendar
│   │   │   └── StockRiskBadge.tsx      # "At Risk for Diwali" label
│   │   ├── shelf/
│   │   │   ├── CameraFeed.tsx          # Canvas + MJPEG + YOLO overlay
│   │   │   └── FloorPlanMap.tsx
│   │   └── charts/
│   │       └── AisleHeatmap.tsx        # Recharts heatmap
│   ├── pages/
│   │   ├── Overview.tsx
│   │   ├── ShelfMonitoring.tsx
│   │   ├── PlanogramCompliance.tsx
│   │   ├── DemandForecast.tsx
│   │   ├── AlertCenter.tsx
│   │   ├── Analytics.tsx
│   │   ├── SmartStore.tsx
│   │   ├── FestivalDashboard.tsx    # NEW — no Streamlit equivalent
│   │   └── Settings.tsx             # Camera registration, WhatsApp numbers
│   ├── i18n/
│   │   ├── en.json              # English strings
│   │   ├── hi.json              # Hindi strings
│   │   └── gu.json              # Gujarati strings
│   ├── store/
│   │   ├── authStore.ts
│   │   └── alertStore.ts        # Real-time alert queue from WebSocket
│   └── main.tsx
```

### Key Component: WhatsApp Alert Card

The Alert Center page must look and feel like WhatsApp — because that is the
mental model of every store associate. Cards with green left border, avatar with
initials, quick-reply buttons at the bottom.

```tsx
// src/components/alerts/WhatsAppAlertCard.tsx
interface WhatsAppAlertCardProps {
  alert: Alert;
  onResolve: (id: string) => void;
}

// Visual structure:
// ┌─────────────────────────────────────────────┐
// │ 🟢  ShelfIQ        2:14 PM           URGENT │
// ├─────────────────────────────────────────────┤
// │ Aisle: Dairy — Shelf B2                     │
// │ Amul Butter 500g is OUT OF STOCK           │
// │ Action: Restock from cold storage           │
// │ Suggested qty: 24 units                     │
// ├─────────────────────────────────────────────┤
// │ [Mark Resolved ✓]    [Reassign →]           │
// └─────────────────────────────────────────────┘
```

### Key Component: Festival Spike Badge

```tsx
// Renders on the DemandForecast page X-axis
// When a forecast date falls within 3 days of a registered festival,
// show an amber badge above that date column:
//
//    │  ▲ Navratri    │
//    │  Sep 29–Oct 7  │
//    ├────────────────┤
//    │  ████████████  │  ← demand lift visualized
```

### Associate Mobile View

Associates using the app on their phone during restocking get a stripped-down
view. Detect narrow viewport (< 480px) and render MobileAssociateView:
- Full-screen WhatsApp-style alert list
- Large "Mark Resolved" button at the bottom (thumb-reachable zone)
- No charts, no heatmaps, no navigation sidebar
- Language: defaults to associate's preferred language (Hindi / Gujarati / English)

---

## PART 4 — SECURITY (PRODUCTION REQUIREMENTS)

### 4.1 Authentication

- JWT RS256 — asymmetric keys, rotate every 90 days
- Access tokens: memory only (never localStorage — XSS risk)
- Refresh tokens: httpOnly, Secure, SameSite=Strict cookie only
- Token revocation: Redis blocklist for logout and compromised tokens
- Rate limiting: 5 login attempts per IP per 15 minutes
- TOTP MFA: enforce for STORE_OWNER and PLATFORM_ADMIN roles

### 4.2 WhatsApp Security

- Validate every incoming webhook with X-Hub-Signature-256 header (Meta HMAC)
- Never log phone numbers in plain text — hash or encrypt in audit log
- Webhook endpoint returns 200 immediately, processes async via Celery
- WhatsApp template messages require pre-approval in Meta Business Manager
- Phone numbers stored encrypted (AES-256) in PostgreSQL

### 4.3 Camera Stream Security

- RTSP credentials stored encrypted in DB — never in environment variables
- Camera streams proxied through backend — never exposed directly to frontend
- Per-camera access check on every stream request (associate sees only their aisle)
- No raw footage stored by default — inference only
- If footage storage enabled by store: auto-delete after 30 days, encrypted at rest
- Comply with India's DPDPA 2023 for any customer-identifiable data (Smart Store)

### 4.4 API Security

- All endpoints require authentication except /health and /auth/login
- Pydantic v2 with extra='forbid' rejects unexpected fields
- CORS: restrict allow_origins to registered frontend domains only
- HTTPS enforced by Nginx; all HTTP redirected to HTTPS
- Security headers set by Nginx:
  ```
  Strict-Transport-Security: max-age=63072000; includeSubDomains
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Content-Security-Policy: default-src 'self'
  ```
- Request size limits: image upload 10MB max, JSON body 1MB max
- SQL: SQLAlchemy ORM only — no raw f-string SQL ever
- File uploads: whitelist MIME types, validate magic bytes

### 4.5 Data Security

- PostgreSQL: AES-256 at filesystem level; pgcrypto for sensitive columns
- TLS 1.3 between all services
- Secrets: environment variables in dev; HashiCorp Vault or AWS Secrets Manager
  in production. Zero secrets in Git — run truffleHog on repo before any
  customer deployment.
- Audit log: every data access event (user, action, resource, IP, timestamp)
  written to immutable audit_log table
- Daily automated PostgreSQL backups encrypted with GPG, stored in S3

### 4.6 Pre-Launch Security Checklist

```
□ Penetration test covering OWASP Top 10 minimum
□ pip-audit + npm audit — no HIGH or CRITICAL CVEs unresolved
□ truffleHog scan on full Git history — no secrets committed
□ All auth endpoints return correct 401 vs 403 codes
□ WhatsApp webhook HMAC validation tested with forged payloads
□ RTSP credentials confirmed encrypted in DB (not env vars)
□ SSL certificate auto-renewal via Let's Encrypt / certbot
□ Cloudflare or AWS WAF in front of Nginx (DDoS protection)
□ DPDPA 2023 compliance review for Smart Store customer data
□ Razorpay webhook signature validation implemented and tested
□ Incident response runbook written in Hindi + English
```

---

## PART 5 — DATABASE SCHEMA (INDIA-SPECIFIC ADDITIONS)

```sql
-- Core additions beyond existing models.py

-- Multi-tenant: one organization = one retail chain
CREATE TABLE organizations (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name          VARCHAR(255) NOT NULL,
  gstin         VARCHAR(15),           -- GST Identification Number
  state_code    VARCHAR(2),            -- Indian state (for tax compliance)
  plan          VARCHAR(20) DEFAULT 'starter',
  plan_expires  TIMESTAMPTZ,
  razorpay_sub_id VARCHAR(100),
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Store: each physical location
CREATE TABLE stores (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id        UUID REFERENCES organizations(id),
  name          VARCHAR(255) NOT NULL,
  city          VARCHAR(100),
  state         VARCHAR(100),
  pincode       VARCHAR(6),
  timezone      VARCHAR(50) DEFAULT 'Asia/Kolkata',
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Camera: RTSP streams, mapped to aisles
CREATE TABLE cameras (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  store_id      UUID REFERENCES stores(id),
  name          VARCHAR(100),          -- e.g. "Dairy Aisle Cam 1"
  rtsp_url_enc  BYTEA NOT NULL,        -- AES-256 encrypted RTSP URL
  aisle         VARCHAR(50),
  status        VARCHAR(20) DEFAULT 'active',
  last_frame_at TIMESTAMPTZ
);

-- Indian event calendar (extend existing weather_data events)
CREATE TABLE indian_events (
  id            SERIAL PRIMARY KEY,
  event_name    VARCHAR(100) NOT NULL,
  event_type    VARCHAR(30),           -- festival|holiday|cricket|sale_event
  start_date    DATE NOT NULL,
  end_date      DATE NOT NULL,
  magnitude     SMALLINT,              -- 1=local, 2=city, 3=national
  affected_states VARCHAR[],           -- NULL = nationwide
  demand_categories TEXT[]             -- SKU categories typically affected
);

-- Associate WhatsApp numbers (encrypted)
CREATE TABLE associates (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  store_id      UUID REFERENCES stores(id),
  name          VARCHAR(100),
  whatsapp_enc  BYTEA NOT NULL,        -- AES-256 encrypted phone number
  language      VARCHAR(5) DEFAULT 'en', -- 'en' | 'hi' | 'gu'
  role          VARCHAR(30) DEFAULT 'SHELF_ASSOCIATE',
  active        BOOLEAN DEFAULT TRUE
);

-- Alert resolution tracking (extends existing alerts table)
ALTER TABLE alerts ADD COLUMN assigned_to UUID REFERENCES associates(id);
ALTER TABLE alerts ADD COLUMN whatsapp_sent_at TIMESTAMPTZ;
ALTER TABLE alerts ADD COLUMN resolved_at TIMESTAMPTZ;
ALTER TABLE alerts ADD COLUMN resolution_time_minutes INTEGER;
ALTER TABLE alerts ADD COLUMN resolution_note TEXT;

-- Festival stock risk assessment (NEW)
CREATE TABLE festival_stock_risk (
  id            SERIAL PRIMARY KEY,
  store_id      UUID REFERENCES stores(id),
  sku_id        VARCHAR(50) NOT NULL,
  event_id      INTEGER REFERENCES indian_events(id),
  assessed_at   TIMESTAMPTZ DEFAULT NOW(),
  predicted_lift_pct FLOAT,
  current_stock  INTEGER,
  days_to_event  SMALLINT,
  risk_level     VARCHAR(10),          -- 'green' | 'amber' | 'red'
  reorder_placed BOOLEAN DEFAULT FALSE
);

-- Audit log (append-only, no deletes or updates)
CREATE TABLE audit_log (
  id            BIGSERIAL PRIMARY KEY,
  user_id       UUID,
  action        VARCHAR(100) NOT NULL,
  resource_type VARCHAR(50),
  resource_id   VARCHAR(100),
  ip_address    INET,
  created_at    TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_audit_user ON audit_log(user_id, created_at DESC);
```

---

## PART 6 — DEPLOYMENT ARCHITECTURE

```
Internet
    │
    ▼
[Cloudflare WAF]
    │  (DDoS protection, Indian CDN PoPs for low latency)
    ▼
[Nginx]
    ├── /                → React SPA (static)
    ├── /api/v1/         → FastAPI backend (port 8000)
    ├── /ws/             → WebSocket upgrade
    └── /health          → Health check (public)

[FastAPI]
    ├── [PostgreSQL 15]  → Primary + read replica (analytics queries)
    ├── [Redis 7]        → Cache + Pub/Sub + session store + alert queue
    └── [Celery Workers]
         ├── cv_pipeline     → GPU queue (YOLOv8 + CLIP)
         ├── forecast        → Daily at 2 AM IST (Prophet)
         ├── whatsapp_alerts → High priority (Meta Cloud API calls)
         └── digest_alerts   → Batch at 6 PM + 10 PM IST

[Edge Mode — optional]
    └── Raspberry Pi 5 / Jetson Nano
         └── Docker container: YOLOv8n + alert logic + sync daemon
```

### Environment Variables

```bash
# Backend .env.prod
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/shelfiq
REDIS_URL=redis://:password@redis:6379/0
JWT_PRIVATE_KEY_PATH=/run/secrets/jwt_private_key
JWT_PUBLIC_KEY_PATH=/run/secrets/jwt_public_key
JWT_ACCESS_EXPIRE_MINUTES=15
JWT_REFRESH_EXPIRE_DAYS=7

# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=              # From Meta Business Manager
WHATSAPP_PHONE_NUMBER_ID=          # Your registered business number
WHATSAPP_WEBHOOK_VERIFY_TOKEN=     # Random secret for webhook verification
WHATSAPP_WEBHOOK_SECRET=           # HMAC secret for signature validation

# Razorpay
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=

# Encryption (for RTSP URLs, phone numbers)
FIELD_ENCRYPTION_KEY=              # AES-256 key, 32 bytes, from Vault

# App
ENVIRONMENT=production
ALLOWED_ORIGINS=https://app.shelfiq.in
SENTRY_DSN=
TIMEZONE=Asia/Kolkata
```

---

## PART 7 — PRODUCT ROADMAP

### Month 1 — Foundation

- FastAPI backend wrapping existing ML modules
- PostgreSQL migration with Alembic
- JWT auth + RBAC (5 roles)
- WhatsApp Business API integration (core differentiator — do this first)
- React frontend: Overview + Alert Center + Settings pages
- Razorpay subscription billing (3 tiers)
- Docker Compose deployment on single VPS (DigitalOcean Bangalore region)

### Month 2 — Full Frontend + Festival Intelligence

- React frontend: all 8 pages including Festival Dashboard (new)
- Hindi + Gujarati i18n for all user-facing strings
- Associate mobile view (narrow layout)
- WhatsApp quick-reply webhook (resolve alerts from WhatsApp)
- Festival stock risk assessments surfaced in dashboard
- Festival reminder WhatsApp templates registered and live
- Automated test suite: >70% coverage
- CI/CD pipeline via GitHub Actions

### Month 3 — SMB Go-to-Market

- Edge AI Docker container (Raspberry Pi 5 / Jetson Nano)
- Camera onboarding wizard (store owner self-serve: paste RTSP URL → calibrate)
- First 5 paying pilot stores in Gujarat (Ahmedabad / Surat / Vadodara)
- Quick-Commerce Watch feature (Zepto/Blinkit trend comparison)
- Referral program: ₹500 credit for each store referred

### Month 4 — Scale

- Expand to Mumbai, Pune, Jaipur, Lucknow (Hindi belt)
- White-label option for regional FMCG distributors
- API access tier for Chain plan (let distributors pull stock data into their ERP)
- LLM-powered natural language daily summary:
  "आपकी Dairy aisle में कल ₹8,400 का नुकसान हुआ — 3 stockout events की वजह से।"
  (Your Dairy aisle lost ₹8,400 yesterday due to 3 stockout events.)

---

## PART 8 — MONITORING & OBSERVABILITY

```python
# Structured logging: structlog
# Error tracking: sentry-sdk[fastapi]
# Metrics: prometheus-fastapi-instrumentator
# Uptime: Freshping or UptimeRobot (Indian monitoring services)

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "db": await check_db(),
        "redis": await check_redis(),
        "whatsapp_api": await check_whatsapp_api(),
        "ml_models": check_models_loaded(),
        "version": "3.0.0"
    }
```

### Key Metrics to Track

| Metric | Alert Threshold | Why it matters |
|--------|----------------|----------------|
| WhatsApp delivery rate | < 95% | Core alert channel |
| Alert → WhatsApp latency | > 3 minutes | SLA to customers |
| Stockout → Resolve time | > 45 minutes | Associate performance |
| CV pipeline duration | > 3 minutes | Camera freshness |
| Forecast WMAPE | > 25% | Model quality |
| Festival prediction accuracy | > 80% lift accuracy | Key differentiator |
| Razorpay payment success | < 95% | Revenue health |
| API p95 latency | > 500ms | UX quality |

---

## APPENDIX — Quick Reference Commands

```bash
# Full stack local development
docker compose up --build

# Backend only
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend dev server
cd frontend && npm run dev

# CV worker (GPU)
cd backend && celery -A app.workers worker --loglevel=info -Q cv_pipeline

# WhatsApp alert worker
cd backend && celery -A app.workers worker --loglevel=info -Q whatsapp_alerts

# Daily forecast worker
cd backend && celery -A app.workers beat --loglevel=info  # scheduler
cd backend && celery -A app.workers worker --loglevel=info -Q forecast

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "add_festival_stock_risk"

# Run tests
pytest tests/ -v --cov=app --cov-report=term-missing
cd frontend && npm run test

# Security checks (run before every customer demo)
pip-audit --requirement requirements.txt
npm audit --audit-level=high
trivy image shelfiq-backend:latest

# WhatsApp webhook verification test
curl -X GET "https://api.shelfiq.in/api/v1/webhooks/whatsapp" \
  ?hub.mode=subscribe \
  &hub.challenge=test \
  &hub.verify_token=$WHATSAPP_WEBHOOK_VERIFY_TOKEN
```

---

*Prama Innovations India Pvt. Ltd. | 602 Shapath-5, SG Highway, Ahmedabad 380015*
*ShelfIQ v3.0 | India-First Shelf Intelligence | vedantpatel-04/Bug404*
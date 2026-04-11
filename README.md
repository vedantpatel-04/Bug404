# 🛒 ShelfIQ — Smart Retail Shelf Intelligence

> Computer Vision-Driven Inventory Monitoring and Demand Optimization

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B.svg)](https://streamlit.io)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00FFFF.svg)](https://ultralytics.com)
[![Prophet](https://img.shields.io/badge/Prophet-Meta-blue.svg)](https://facebook.github.io/prophet/)
[![CLIP](https://img.shields.io/badge/CLIP-ViT--B%2F32-purple.svg)](https://github.com/openai/CLIP)

---

## 📋 Overview

ShelfIQ is an intelligent shelf monitoring and inventory optimization system that leverages **computer vision** on existing store camera feeds combined with **demand forecasting** to provide:

- 📷 **Real-time shelf-level visibility** via YOLOv8 object detection
- 🔤 **OCR-based price tag detection** using EasyOCR for price mismatch alerts
- 🧠 **CLIP-powered SKU recognition** (ViT-B/32 embeddings with color histogram fallback)
- 📐 **Planogram compliance checking** with violation detection
- 📈 **Demand forecasting** using Prophet with local event regressors (Navratri, Diwali, IPL)
- 🔔 **Automated alerts** within 5 minutes of stockout detection, with **corrective actions**
- 📊 **WMAPE/MAE/RMSE accuracy dashboard** for forecast model transparency
- 🗺️ **Dynamic store floor plan** with real-time detection overlays
- 🔥 **Stockout heatmap** by aisle and time of day
- 🤖 **Amazon Go-inspired Smart Store** — autonomous customer tracking & sensor fusion

Retail out-of-stock events cost **$1 trillion annually** in lost sales globally. ShelfIQ closes the last-mile visibility gap by turning underutilized store cameras into intelligent inventory sensors.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Camera Feeds / Images                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│   CV Pipeline (YOLOv8 + OpenCV + CLIP)  │
│   • Product detection (YOLOv8n/s/m)     │
│   • SKU recognition (CLIP ViT-B/32)     │
│   • Price tag OCR (EasyOCR)             │
│   • Stock level classification          │
└────────┬───────────┬────────────────────┘
         │           │
         ▼           ▼
┌──────────────┐ ┌──────────────────┐
│  Planogram   │ │  Alert System    │
│  Compliance  │ │  (Redis Pub/Sub) │
│  Engine      │ │  • Dashboard     │
│  • Scoring   │ │  • Email digest  │
│  • Violations│ │  • Mobile push   │
│  • Price OCR │ │  • Corrective    │
│    mismatches│ │    actions       │
└──────┬───────┘ └───────┬──────────┘
       │                 │
       ▼                 ▼
┌─────────────────────────────────┐
│     Streamlit Dashboard          │
│   • Dynamic Floor Plan          │
│   • Stockout Heatmap (Aisle×Hr) │
│   • WMAPE/MAE/RMSE KPIs        │
│   • Forecast Charts              │
│   • Alert Center + Actions       │
│   • Revenue Analytics            │
└─────────────────────────────────┘
       ▲
       │
┌──────┴──────────────────────────┐
│   Forecasting Engine (Prophet)   │
│   • Demand prediction            │
│   • Local event regressors       │
│     (Navratri, Diwali, IPL...)   │
│   • Reorder point calculation    │
│   • Auto replenishment orders    │
└─────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd Bug404
pip install -r requirements.txt
```

### 2. Seed the Database

Generate synthetic data (POS transactions, shelf images, planograms, weather/events):

```bash
python database/seed_data.py
```

### 3. Launch the Dashboard

```bash
streamlit run dashboard/app.py
```

The dashboard opens at [http://localhost:8501](http://localhost:8501)

---

## 📁 Project Structure

```
Bug404/
├── config/settings.py              # Central configuration
├── data/
│   ├── generators/                 # Synthetic data generators
│   │   ├── generate_pos_data.py    # 2yr POS transactions (50 SKUs × 3 stores)
│   │   ├── generate_planograms.py  # Structured shelf layout JSONs
│   │   ├── generate_shelf_images.py# Synthetic shelf images
│   │   └── generate_weather_data.py# Weather + Ahmedabad event calendar
│   ├── sample_images/              # Generated shelf images
│   ├── sample_planograms/          # Planogram JSON files
│   └── pos_data/                   # CSV datasets
├── models/
│   ├── shelf_detector.py           # YOLOv8 product detection
│   ├── sku_recognizer.py           # CLIP + color histogram hybrid recognition
│   └── stock_classifier.py         # Stock level classification
├── planogram/
│   ├── schemas.py                  # Pydantic data models
│   ├── compliance_engine.py        # Planogram comparison + OCR price checking
│   └── compliance_scorer.py        # Scoring & recommendations
├── forecasting/
│   ├── feature_engineering.py      # Feature creation + event regressors
│   ├── demand_forecaster.py        # Prophet forecasting + event-aware
│   ├── reorder_calculator.py       # ROP & safety stock
│   └── replenishment_engine.py     # Auto order generation
├── alerts/
│   ├── alert_models.py             # Alert data structures + corrective actions
│   ├── alert_manager.py            # Priority, dedup & corrective action logic
│   ├── redis_publisher.py          # Redis + in-memory fallback
│   └── notification_channels.py    # Multi-channel delivery
├── pipeline/
│   ├── shelf_analysis_pipeline.py  # End-to-end CV orchestration
│   └── scheduler.py                # Periodic job scheduler
├── dashboard/
│   ├── app.py                      # Streamlit main application
│   ├── views/                      # 7 dashboard pages
│   ├── components/                 # Reusable UI components
│   └── assets/styles.css           # Custom dark-theme CSS
├── database/
│   ├── models.py                   # SQLite schema
│   ├── db_manager.py               # Database operations
│   └── seed_data.py                # Data seeding script
├── tests/                          # Unit tests
└── requirements.txt
```

---

## 🖥️ Dashboard Pages

| Page | Description |
|------|-------------|
| **🏠 Overview** | KPI cards, dynamic floor plan with detection overlay, critical alerts, stockout trends |
| **📷 Shelf Monitoring** | Camera feeds with detection overlays, aisle detail views |
| **📐 Planogram Compliance** | Compliance gauges, aisle scores, violation table, OCR price mismatch detection |
| **📈 Demand Forecast** | Prophet forecast charts, **WMAPE/MAE/RMSE KPI cards**, replenishment orders |
| **🔔 Alert Center** | Real-time alert feed with **corrective actions**, task workflow kanban, associate performance |
| **📊 Analytics** | **Stockout heatmap (Aisle × Hour)**, revenue recovery trends, category performance |
| **🤖 Smart Store** | Amazon Go-inspired autonomous retail: customer journey, sensor fusion, ROI analytics |

---

## 🧠 Key Components

### Computer Vision Pipeline

- **YOLOv8** (Ultralytics) for product detection
- **CLAHE preprocessing** for varying lighting conditions
- **CLIP ViT-B/32 embeddings** for SKU recognition (cosine similarity, threshold 0.75)
- **Color histogram + dominant color fallback** when CLIP is unavailable
- **EasyOCR** for price tag detection and mismatch flagging
- **Rule-based stock classification** (FULL/LOW/EMPTY based on fill ratio)
- Synthetic fallback detection when YOLO weights unavailable
- Lazy model loading for fast dashboard startup


### SKU Recognition (Hybrid)

```
Query Image → CLIP ViT-B/32 → Cosine Similarity (≥0.75) → SKU Match
                    ↓ (if unavailable)
              Color Histogram → Dominant Color → SKU Match
```

- `SKUMatch.method` reports `"clip"` or `"color_hist+dominant"` for traceability
- Reference embeddings built automatically from synthetic catalog at startup
- `build_reference_db(images_dict)` supports custom product image databases

### Planogram Compliance

- Structured JSON planogram definitions
- Detects: misplaced products, missing facings, unauthorized products, **price mismatches via OCR**
- Per-aisle and per-shelf compliance scoring with letter grades (A+ to F)
- Actionable recommendations engine
- Price mismatch violations surfaced as formal compliance violations

### Demand Forecasting

- **Meta Prophet** with yearly/weekly seasonality
- External regressors: promotions, weather, holidays, **local events, event magnitude**
- **Ahmedabad event calendar**: Navratri (9 nights), Diwali, Uttarayan, IPL matches, sale events
- Event types: `festival | holiday | cricket_match | concert | sale_event`
- Event magnitude scoring: 1 (local) → 2 (city-wide) → 3 (national/major)
- Fallback: exponential smoothing with weekly patterns
- Accuracy metrics: **WMAPE**, MAE, RMSE, MAPE
- Automated reorder point calculation: `ROP = (avg_demand × lead_time) + safety_stock`

### Alert System

- **Redis Pub/Sub** with in-memory fallback (no Redis required)
- Priority scoring: `severity × revenue_impact × recency`
- Deduplication with configurable cooldown window
- Multi-channel: dashboard push, email digest, mobile simulation
- **Corrective actions** auto-generated per alert type:
  - `STOCKOUT` → "Restock [product] at [location]. Suggested reorder qty: [N] units."
  - `PLANOGRAM_VIOLATION` → "Move [product] from [current] to [correct position]."
  - `LOW_STOCK` → "Schedule replenishment within [N] hours."
  - `PRICE_MISMATCH` → "Update price tag from [detected] to [expected]."
- < 5 minute alert latency

### 🤖 Smart Store (Amazon Go Concept)

Inspired by Amazon's "Just Walk Out" technology deployed in their London stores:
- **Multi-camera customer tracking** — overhead ceiling cameras track every shopper
- **Weight sensor fusion** — shelf sensors detect product picks/returns within 200ms
- **Customer journey analytics** — shopping funnel, path analysis, dwell time
- **Traffic heatmaps** — real-time overhead view of in-store foot traffic
- **Automated checkout** — zero-friction exit with automatic account charging
- **Before/After ROI dashboard** — quantifying the impact of CV-powered automation
- **Loss prevention** — shrinkage reduction from 3.2% to 1.1% via continuous monitoring

---

## 🔄 Recent Changes (v2.0)

| Change | Feature | Files Modified |
|--------|---------|----------------|
| **1** | OCR-based price tag detection via EasyOCR | `planogram/compliance_engine.py` |
| **2** | CLIP ViT-B/32 SKU recognition with color histogram fallback | `models/sku_recognizer.py` |
| **3** | Stockout heatmap by Aisle × Time of Day | `dashboard/views/analytics_page.py` |
| **4** | Dynamic store floor plan with detection overlay | `dashboard/views/overview_page.py` |
| **5** | Auto-generated corrective actions on every alert | `alerts/alert_models.py`, `alert_manager.py`, `notification_channels.py`, `alerts_page.py` |
| **6** | WMAPE / MAE / RMSE KPI cards on forecast page | `dashboard/views/demand_forecast.py` |
| **7** | Ahmedabad local event calendar (50+ events) in forecasting | `generate_weather_data.py`, `feature_engineering.py`, `demand_forecaster.py` |
| **8** | Comprehensive README documentation | `README.md` |

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test module
python -m pytest tests/test_planogram.py -v
python -m pytest tests/test_forecasting.py -v
python -m pytest tests/test_alerts.py -v
```

---

## 📊 Evaluation Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Object detection mAP | Product detection accuracy | ≥ 0.40 |
| SKU recognition accuracy | CLIP cosine similarity threshold | ≥ 0.75 |
| Planogram compliance precision | Violation detection accuracy | ≥ 0.85 |
| WMAPE | Forecast accuracy (weighted) | ≤ 25% |
| Alert latency | Time from detection to notification | < 5 min |
| False positive rate | Incorrect stockout detections | < 10% |

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| CV Model | YOLOv8 (Ultralytics) |
| SKU Recognition | CLIP ViT-B/32 (OpenAI) + Color Histogram |
| OCR | EasyOCR |
| Image Processing | OpenCV, Pillow |
| Forecasting | Prophet, scikit-learn |
| Database | SQLite |
| Message Queue | Redis (+ in-memory fallback) |
| Dashboard | Streamlit |
| Charts | Plotly |
| Data Models | Pydantic |
| Scheduling | APScheduler |
| Language | Python 3.10+ |

---

## 📦 Dependencies

Core dependencies (see `requirements.txt`):
```
numpy, pandas, Pillow, opencv-python        # Core
ultralytics, torch, torchvision, easyocr     # Computer Vision
openai/CLIP (git)                            # SKU Recognition
prophet, scikit-learn                        # Forecasting
streamlit, plotly                             # Dashboard
redis, pydantic, apscheduler                 # Infrastructure
scipy, faker, requests                       # Utilities
```

---

## 👥 Team

**Bug404** — Built for the Smart Retail Shelf Intelligence Challenge

Prama Innovations India Pvt. Ltd.  
602 Shapath-5 Building, SG Highway, Ahmedabad 380015

---

## 📄 License

This project is built for the Bug404 Hackathon challenge.
# 🛒 ShelfIQ — Smart Retail Shelf Intelligence

> Computer Vision-Driven Inventory Monitoring and Demand Optimization

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B.svg)](https://streamlit.io)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00FFFF.svg)](https://ultralytics.com)
[![Prophet](https://img.shields.io/badge/Prophet-Meta-blue.svg)](https://facebook.github.io/prophet/)

---

## 📋 Overview

ShelfIQ is an intelligent shelf monitoring and inventory optimization system that leverages **computer vision** on existing store camera feeds combined with **demand forecasting** to provide:

- 📷 **Real-time shelf-level visibility** via YOLOv8 object detection
- 📐 **Planogram compliance checking** with violation detection
- 📈 **Demand forecasting** using Prophet with external regressors
- 🔔 **Automated alerts** within 5 minutes of stockout detection
- 🤖 **Amazon Go-inspired Smart Store** — autonomous customer tracking & sensor fusion
- 📊 **Management dashboard** with heatmaps, trends, and revenue metrics

Retail out-of-stock events cost **$1 trillion annually** in lost sales globally. ShelfIQ closes the last-mile visibility gap by turning underutilized store cameras into intelligent inventory sensors.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Camera Feeds / Images                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────┐
│   CV Pipeline (YOLOv8 + OpenCV) │
│   • Product detection            │
│   • SKU recognition              │
│   • Stock level classification   │
└────────┬───────────┬────────────┘
         │           │
         ▼           ▼
┌──────────────┐ ┌──────────────────┐
│  Planogram   │ │  Alert System    │
│  Compliance  │ │  (Redis Pub/Sub) │
│  Engine      │ │  • Dashboard     │
│  • Scoring   │ │  • Email digest  │
│  • Violations│ │  • Mobile push   │
└──────┬───────┘ └───────┬──────────┘
       │                 │
       ▼                 ▼
┌─────────────────────────────────┐
│     Streamlit Dashboard          │
│   • Shelf Map & Heatmaps        │
│   • Compliance Gauges            │
│   • Forecast Charts              │
│   • Alert Center                 │
│   • Revenue Analytics            │
└─────────────────────────────────┘
       ▲
       │
┌──────┴──────────────────────────┐
│   Forecasting Engine (Prophet)   │
│   • Demand prediction            │
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

Generate synthetic data (POS transactions, shelf images, planograms, weather):

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
│   │   └── generate_weather_data.py# Weather & event data
│   ├── sample_images/              # Generated shelf images
│   ├── sample_planograms/          # Planogram JSON files
│   └── pos_data/                   # CSV datasets
├── models/
│   ├── shelf_detector.py           # YOLOv8 product detection
│   ├── sku_recognizer.py           # SKU-level recognition
│   └── stock_classifier.py         # Stock level classification
├── planogram/
│   ├── schemas.py                  # Pydantic data models
│   ├── compliance_engine.py        # Planogram comparison
│   └── compliance_scorer.py        # Scoring & recommendations
├── forecasting/
│   ├── feature_engineering.py      # Feature creation
│   ├── demand_forecaster.py        # Prophet forecasting
│   ├── reorder_calculator.py       # ROP & safety stock
│   └── replenishment_engine.py     # Auto order generation
├── alerts/
│   ├── alert_models.py             # Alert data structures
│   ├── alert_manager.py            # Priority & dedup logic
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
| **🏠 Overview** | KPI cards, store floor map, stock distribution, stockout heatmap |
| **📷 Shelf Monitoring** | Camera feeds with detection overlays, aisle detail views |
| **📐 Planogram Compliance** | Compliance gauges, aisle scores, violation table, recommendations |
| **📈 Demand Forecast** | Interactive Prophet forecast charts, accuracy metrics, replenishment orders |
| **🔔 Alert Center** | Real-time alert feed, priority filtering, alert analytics |
| **📊 Analytics** | Heatmaps, trend analysis, revenue recovery, category performance |
| **🤖 Smart Store** | Amazon Go-inspired autonomous retail: customer journey, sensor fusion, ROI analytics |

---

## 🧠 Key Components

### Computer Vision Pipeline
- **YOLOv8** (Ultralytics) for product detection
- **CLAHE preprocessing** for varying lighting conditions
- **Color histogram + dominant color matching** for SKU recognition
- **Rule-based stock classification** (FULL/LOW/EMPTY based on fill ratio)
- Synthetic fallback detection when YOLO weights unavailable

### Planogram Compliance
- Structured JSON planogram definitions
- Detects: misplaced products, missing facings, unauthorized products, price mismatches
- Per-aisle and per-shelf compliance scoring with letter grades (A+ to F)
- Actionable recommendations engine

### Demand Forecasting
- **Meta Prophet** with yearly/weekly seasonality
- External regressors: promotions, weather, holidays
- Fallback: exponential smoothing with weekly patterns
- Accuracy metrics: WMAPE, MAE, RMSE, MAPE
- Automated reorder point calculation: `ROP = (avg_demand × lead_time) + safety_stock`

### Alert System
- **Redis Pub/Sub** with in-memory fallback (no Redis required)
- Priority scoring: `severity × revenue_impact × recency`
- Deduplication with configurable cooldown window
- Multi-channel: dashboard push, email digest, mobile simulation
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
| SKU recognition accuracy | Correct product identification | ≥ 0.80 |
| Planogram compliance precision | Violation detection accuracy | ≥ 0.85 |
| WMAPE | Forecast accuracy | ≤ 25% |
| Alert latency | Time from detection to notification | < 5 min |
| False positive rate | Incorrect stockout detections | < 10% |

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| CV Model | YOLOv8 (Ultralytics) |
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

## 👥 Team

**Bug404** — Built for the Smart Retail Shelf Intelligence Challenge

Prama Innovations India Pvt. Ltd.  
602 Shapath-5 Building, SG Highway, Ahmedabad 380015

---

## 📄 License

This project is built for the Bug404 Hackathon challenge.

# ☁️ Cloud Cost Analyzer — Advanced FinOps Platform

A production-inspired FinOps intelligence dashboard built with Python
that analyzes AWS billing data, detects cost anomalies, generates
optimization recommendations per resource, forecasts future spend,
and exports a full PDF report — all from a clean Streamlit UI.

---

## 🚀 Features

### 🔍 Smart Data Loading
- CSV validation with required column checks
- Automatic type casting and null row handling
- Date range filter and service multiselect
- Support for custom AWS billing CSV upload

### 📊 Core Analysis
- Total cloud spend summary
- Service-wise and region-wise cost breakdown
- Daily cost trend visualization

### 🚨 Cost Anomaly Detection
- Detects daily cost spikes using 3-day rolling average
- Configurable sensitivity threshold (10%–80%)
- Visual chart with anomaly markers highlighted in red

### 🔮 Cost Forecasting
- Weighted moving average daily cost projection
- Three scenarios: Base, Optimistic (−10%), Pessimistic (+20%)
- Trend direction indicator (upward / downward)

### 💡 Resource Optimization Engine
- Idle EC2 → Stop or terminate immediately
- Low CPU EC2 (<20%) → Downsize instance type
- Idle RDS → Stop or snapshot and terminate
- Underutilized RDS (<15% CPU) → Downgrade instance class
- High S3 storage (>500GB) → Move to IA or Glacier

### 💰 Savings Estimator
- Monthly saving projection per optimization strategy
- Effort and impact rating per recommendation
- Total potential monthly savings summary

### 📄 PDF Report Generator
- Auto-generated 7-section FinOps report
- Covers: Executive Summary, Service Breakdown, Region Breakdown,
  Anomaly Detection, Idle Waste, Recommendations, Savings Summary
- Downloadable directly from the dashboard sidebar

---

## 🛠️ Tech Stack

| Tool         | Purpose                        |
|---|---|
| Python       | Core language                  |
| Pandas       | Data analysis and manipulation |
| Streamlit    | Dashboard UI                   |
| Plotly       | Interactive charts             |
| FPDF2        | PDF report generation          |
| NumPy        | Weighted average forecasting   |

---

## 📁 Project Structure
```
cloud-cost-analyzer/
│
├── data/
│   └── sample_data.csv        ← AWS billing dataset
│
├── outputs/
│   └── finops_report.pdf      ← generated reports
│
├── data_loader.py             ← loading, validation, filtering
├── cost_analyzer.py           ← analysis, anomaly, forecast, savings
├── recommendations.py         ← per-resource optimization engine
├── report_generator.py        ← PDF report builder
├── app.py                     ← Streamlit dashboard
├── requirements.txt           ← dependencies
└── README.md
```

## ▶️ How to Run

1. Clone the repository
2. Create and activate virtual environment:
   python -m venv venv
   source venv/bin/activate  # Mac/Linux
   venv\Scripts\activate     # Windows

3. Install dependencies:
   pip install -r requirements.txt

4. Run the dashboard:
   streamlit run app.py

5. Optional: Upload your own AWS billing CSV via the sidebar

---

## 📊 Sample Dataset

- 61 rows · 11 days · 5 services · 4 regions
- Services: EC2, RDS, S3, Lambda, CloudFront
- Regions: us-east-1, us-west-2, ap-south-1, eu-west-1
- Includes deliberate cost spike on Day 11 for anomaly detection demo
- Includes cpu_utilization and storage_gb for optimization engine

---

## 🧠 FinOps Concepts Demonstrated

- Cost visibility across services and regions
- Idle resource detection and waste quantification
- Rightsizing recommendations based on utilization metrics
- Cost anomaly detection using statistical rolling averages
- Spend forecasting with scenario analysis
- Automated report generation for stakeholder communication
```
# ☁️ Cloud Cost Analyzer — FinOps Dashboard

A Python-based FinOps intelligence dashboard to analyze AWS cloud 
billing data, detect waste, and generate optimization recommendations.

## Features

### Core Analysis
- Total cloud spend summary
- Service-wise and region-wise cost breakdown
- Daily cost trend visualization

### Insights Engine
- Cost percentage per service
- Top cost service detection
- Idle resource waste calculation (cost + % of total spend)

### Recommendations Engine
- Auto-generated optimization actions by priority (High / Medium / Low)
- Estimated savings per recommendation
- Covers EC2, RDS, S3, and Lambda optimization strategies

### Dashboard
- 4 key metric cards
- Interactive bar, pie, and line charts (Plotly)
- Sidebar with file upload + dataset stats
- Idle resource details with wasted cost breakdown
- Raw data viewer

## Tech Stack

| Tool | Purpose |
|---|---|
| Python | Core language |
| Pandas | Data analysis |
| Streamlit | Dashboard UI |
| Plotly | Interactive charts |

## Project Structure
```
cloud-cost-analyzer/
├── analyzer.py       → analysis + insights + recommendations logic
├── app.py            → Streamlit dashboard
├── sample_data.csv   → simulated AWS billing dataset
└── README.md
```

## How to Run

1. Clone the repository
2. Install dependencies:
   pip install pandas streamlit plotly
3. Run the dashboard:
   streamlit run app.py
4. Optional: Upload your own AWS billing CSV via the sidebar

## Sample Dataset

- 58 rows · 10 days · 5 services · 4 regions
- Services: EC2, RDS, S3, Lambda, CloudFront
- Regions: us-east-1, us-west-2, ap-south-1, eu-west-1
- Mix of Active and Idle resources for realistic analysis
```
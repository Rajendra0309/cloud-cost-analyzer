# ☁️ Cloud Cost Analyzer — FinOps Project

A Python-based FinOps dashboard to analyze AWS cloud billing data.

## Features
- Total cloud cost summary
- Service-wise cost breakdown
- Region-wise cost breakdown
- Idle resource detection with wasted cost alert

## Tech Stack
- Python
- Pandas (data analysis)
- Streamlit (dashboard UI)

## How to Run
1. Clone the repository
2. Install dependencies:
   pip install pandas streamlit
3. Run the dashboard:
   streamlit run app.py

## Project Structure
- analyzer.py → analysis logic
- app.py → Streamlit dashboard
- sample_data.csv → sample AWS billing data
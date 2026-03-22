import streamlit as st
import pandas as pd
import analyzer

# Page Configuration
st.set_page_config(
    page_title="Cloud Cost Analyzer",
    page_icon="☁️",
    layout="wide"
)

# Title & Header
st.title("☁️ Cloud Cost Analyzer")
st.caption("FinOps Dashboard - AWS Billing Analysis")
st.divider()

# Load Data
df = analyzer.load_data("sample_data.csv")

# Section 1: Total Cost Metric
st.subheader("💰 Total Cloud Spend")

total = analyzer.get_total_cost(df)
st.metric(label="Total AWS Cost", value=f"${total}")

st.divider()

# Section 2: Service & Region Breakdown
st.subheader("📊 Cost Breakdown")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**By Service**")
    service_df = analyzer.get_service_breakdown(df)
    st.bar_chart(service_df.set_index('service')['total_cost'])
    st.dataframe(service_df, use_container_width=True)

with col2:
    st.markdown("**By Region**")
    region_df = analyzer.get_region_breakdown(df)
    st.bar_chart(region_df.set_index('region')['total_cost'])
    st.dataframe(region_df, use_container_width=True)

st.divider()

# Section 3: Idle Resources Alert
st.subheader("⚠️ Idle Resource Detected")

idle_df = analyzer.get_idle_resources(df)
idle_cost = round(idle_df['cost_usd'].sum(), 2)

if not idle_df.empty:
    st.error(f"🚨 {len(idle_df)} idle resource(s) found - Wasted cost: **${idle_cost}**")
    st.dataframe(idle_df, use_container_width=True)
else:
    st.success("✅ No idle resources found!")

st.divider()

# Section 4: Raw Data Viewer
st.subheader("🗂️ Raw Billing Data")
st.dataframe(df, use_container_width=True)
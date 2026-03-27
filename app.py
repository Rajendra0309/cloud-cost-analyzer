import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

import data_loader
import cost_analyzer
import recommendations as rec_engine
import report_generator

# PAGE CONFIG
st.set_page_config(
    page_title="Cloud Cost Analyzer",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CUSTOM CSS
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #0f1117; }

    /* Metric cards */
    [data-testid="metric-container"] {
        background-color: #1e2130;
        border: 1px solid #2d3250;
        border-radius: 12px;
        padding: 16px;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #13151f;
        border-right: 1px solid #2d3250;
    }

    /* Section headers */
    .section-header {
        background: linear-gradient(90deg, #1a1d2e, #0f1117);
        border-left: 4px solid #007AFF;
        padding: 8px 16px;
        border-radius: 4px;
        margin: 16px 0 8px 0;
        font-weight: 600;
        font-size: 16px;
    }

    /* Anomaly alert */
    .anomaly-alert {
        background-color: #2d1b1b;
        border: 1px solid #dc3545;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
    }

    /* Divider */
    hr { border-color: #2d3250; }

    /* Table styling */
    .stDataFrame { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/"
        "9/93/Amazon_Web_Services_Logo.svg",
        width=100
    )
    st.title("⚙️ Controls")
    st.markdown("---")

    # File Upload
    st.markdown("**📁 Data Source**")
    uploaded_file = st.file_uploader(
        "Upload AWS Billing CSV",
        type=["csv"],
        help="Must include: date, service, region, cost_usd, "
             "usage_hours, resource_id, status, "
             "cpu_utilization, storage_gb"
    )

    if uploaded_file is not None:
        import io
        raw_df = pd.read_csv(uploaded_file)
        raw_df['date'] = pd.to_datetime(raw_df['date'])
        st.success("✅ Custom file loaded!")
    else:
        raw_df = data_loader.load_data("data/sample_data.csv")
        st.info("ℹ️ Using sample dataset")

    st.markdown("---")

    # Date Range Filter
    st.markdown("**📅 Date Range**")
    min_date = raw_df['date'].min().date()
    max_date = raw_df['date'].max().date()

    date_range = st.date_input(
        "Select range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date

    # Service Filter
    st.markdown("**🔧 Services**")
    all_services = sorted(raw_df['service'].unique().tolist())
    selected_services = st.multiselect(
        "Filter by service",
        options=all_services,
        default=all_services
    )

    # Anomaly Threshold
    st.markdown("**⚡ Anomaly Sensitivity**")
    anomaly_threshold = st.slider(
        "Spike threshold (%)",
        min_value=10,
        max_value=80,
        value=30,
        step=5,
        help="Flag a day as anomaly if cost spikes above this % vs rolling average"
    )

    st.markdown("---")

    # Apply Filters
    df = data_loader.filter_by_date(raw_df, start_date, end_date)
    df = data_loader.filter_by_services(df, selected_services)

    # Dataset Stats
    summary = data_loader.get_data_summary(df)
    st.markdown("**📊 Dataset Info**")
    st.markdown(
        f"**Rows:** {summary['total_rows']}  \n"
        f"**Days:** {summary['total_days']}  \n"
        f"**Services:** {len(summary['services'])}  \n"
        f"**Regions:** {len(summary['regions'])}  \n"
        f"**Range:** {summary['date_min']} → {summary['date_max']}"
    )

    st.markdown("---")

    # PDF Download Button
    st.markdown("**📄 Export Report**")
    if st.button("🖨️ Generate PDF Report", use_container_width=True):
        with st.spinner("Generating report..."):
            path = report_generator.generate_report(df)
        with open(path, "rb") as f:
            st.download_button(
                label="⬇️ Download PDF",
                data=f,
                file_name="finops_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

# GUARD: Empty DataFrame
if df.empty:
    st.warning("⚠️ No data found for the selected filters.")
    st.stop()

# PRECOMPUTE ALL DATA
total_cost      = cost_analyzer.get_total_cost(df)
service_df      = cost_analyzer.get_service_breakdown(df)
region_df       = cost_analyzer.get_region_breakdown(df)
top_service     = cost_analyzer.get_top_service(df)
waste           = cost_analyzer.get_idle_waste_summary(df)
forecast        = cost_analyzer.forecast_next_month(df)
anomaly_summary = cost_analyzer.get_anomaly_summary(df, anomaly_threshold)
savings         = cost_analyzer.get_savings_estimate(df)
rec_summary     = rec_engine.get_recommendations_summary(df)
idle_df         = cost_analyzer.get_idle_resources(df)
trend_df        = anomaly_summary['trend']

# HEADER
st.title("☁️ Cloud Cost Analyzer")
st.caption(
    f"FinOps Intelligence Dashboard  |  "
    f"{summary['date_min']} → {summary['date_max']}  |  "
    f"v3.0"
)
st.divider()

# KEY METRICS
st.markdown(
    '<div class="section-header">📌 Key Metrics</div>',
    unsafe_allow_html=True
)

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "💰 Total Spend",
    f"${total_cost:,}"
)
c2.metric(
    "🏆 Top Service",
    top_service['service'],
    delta=f"${top_service['cost']:,}"
)
c3.metric(
    "⚠️ Idle Waste",
    f"${waste['idle_cost']:,}",
    delta=f"{waste['waste_percentage']}% of spend",
    delta_color="inverse"
)
c4.metric(
    "💡 Potential Savings",
    f"${savings['total_monthly']:,}",
    delta="per month",
    delta_color="normal"
)
c5.metric(
    "🔮 Next Month Forecast",
    f"${forecast['forecast']:,}",
    delta=f"{'↑' if forecast['trend_direction'] == 'up' else '↓'} "
          f"{forecast['trend_direction']}ward trend",
    delta_color="inverse" if forecast['trend_direction'] == 'up' else "normal"
)

st.divider()

# ANOMALY DETECTION
st.markdown(
    '<div class="section-header">🚨 Cost Anomaly Detection</div>',
    unsafe_allow_html=True
)

if anomaly_summary['count'] > 0:
    st.error(
        f"🚨 **{anomaly_summary['count']} anomaly day(s) detected!**  "
        f"Worst spike: **{anomaly_summary['worst_spike']}%** above "
        f"rolling average on **{anomaly_summary['worst_day']}**"
    )
else:
    st.success("✅ No cost anomalies detected in the selected period.")

# Anomaly trend chart
fig_anomaly = go.Figure()

fig_anomaly.add_trace(go.Scatter(
    x=trend_df['date'],
    y=trend_df['daily_cost'],
    name='Daily Cost',
    line=dict(color='#00d4ff', width=2.5),
    mode='lines+markers',
    marker=dict(size=6)
))

fig_anomaly.add_trace(go.Scatter(
    x=trend_df['date'],
    y=trend_df['rolling_avg'],
    name='3-Day Rolling Avg',
    line=dict(color='#888888', width=1.5, dash='dash'),
    mode='lines'
))

# Highlight anomaly points in red
anomalies = anomaly_summary['anomalies']
if not anomalies.empty:
    fig_anomaly.add_trace(go.Scatter(
        x=anomalies['date'],
        y=anomalies['daily_cost'],
        name='Anomaly',
        mode='markers',
        marker=dict(color='#dc3545', size=14, symbol='x')
    ))

fig_anomaly.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    legend=dict(
        bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    ),
    xaxis=dict(title='Date', color='white', gridcolor='#2d3250'),
    yaxis=dict(title='Cost (USD)', color='white', gridcolor='#2d3250'),
    font=dict(color='white'),
    height=350
)
st.plotly_chart(fig_anomaly, use_container_width=True)
st.divider()

# COST BREAKDOWN
st.markdown(
    '<div class="section-header">📊 Cost Breakdown</div>',
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

with col1:
    st.markdown("**By Service — Bar Chart**")
    fig_bar = px.bar(
        service_df,
        x='service',
        y='total_cost',
        color='service',
        text='total_cost',
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig_bar.update_traces(
        texttemplate='$%{text:,.2f}',
        textposition='outside'
    )
    fig_bar.update_layout(
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(
            title='Cost (USD)',
            color='white',
            gridcolor='#2d3250'
        ),
        xaxis=dict(title='Service', color='white'),
        font=dict(color='white'),
        height=350
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    st.markdown("**By Service — Donut Chart**")
    fig_pie = px.pie(
        data_frame=service_df,
        names='service',
        values='total_cost',
        hole=0.5,
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig_pie.update_traces(
        textinfo='percent+label',
        textfont=dict(color='white')
    )
    fig_pie.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        showlegend=True,
        height=350
    )
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# REGION BREAKDOWN
st.markdown(
    '<div class="section-header">🌍 Region-wise Cost</div>',
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

with col1:
    fig_region = px.bar(
        region_df,
        x='region',
        y='total_cost',
        color='region',
        text='total_cost',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_region.update_traces(
        texttemplate='$%{text:,.2f}',
        textposition='outside'
    )
    fig_region.update_layout(
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(
            title='Cost (USD)',
            color='white',
            gridcolor='#2d3250'
        ),
        xaxis=dict(title='Region', color='white'),
        font=dict(color='white'),
        height=350
    )
    st.plotly_chart(fig_region, use_container_width=True)

with col2:
    st.markdown("**Region Cost Table**")
    st.dataframe(
        region_df,
        use_container_width=True,
        hide_index=True,
        height=330
    )

st.divider()

# FORECAST
st.markdown(
    '<div class="section-header">🔮 Cost Forecast — Next 30 Days</div>',
    unsafe_allow_html=True
)

fc1, fc2, fc3, fc4 = st.columns(4)
fc1.metric("📊 Avg Daily Cost",   f"${forecast['avg_daily_cost']:,}")
fc2.metric("🔮 Base Forecast",    f"${forecast['forecast']:,}")
fc3.metric("✅ Optimistic",       f"${forecast['optimistic']:,}",
           delta="-10%", delta_color="normal")
fc4.metric("⚠️ Pessimistic",      f"${forecast['pessimistic']:,}",
           delta="+20%", delta_color="inverse")

# Forecast bar chart
forecast_data = pd.DataFrame({
    'Scenario':    ['Optimistic', 'Base Forecast', 'Pessimistic'],
    'Cost (USD)':  [
        forecast['optimistic'],
        forecast['forecast'],
        forecast['pessimistic']
    ],
    'Color':       ['#28a745', '#007AFF', '#dc3545']
})

fig_forecast = px.bar(
    forecast_data,
    x='Scenario',
    y='Cost (USD)',
    color='Scenario',
    text='Cost (USD)',
    color_discrete_map={
        'Optimistic':   '#28a745',
        'Base Forecast': '#007AFF',
        'Pessimistic':  '#dc3545'
    }
)
fig_forecast.update_traces(
    texttemplate='$%{text:,.2f}',
    textposition='outside'
)
fig_forecast.update_layout(
    showlegend=False,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    yaxis=dict(
        title='Projected Monthly Cost (USD)',
        color='white',
        gridcolor='#2d3250'
    ),
    xaxis=dict(color='white'),
    font=dict(color='white'),
    height=320
)
st.plotly_chart(fig_forecast, use_container_width=True)
st.divider()

# IDLE RESOURCES
st.markdown(
    '<div class="section-header">⚠️ Idle Resource Details</div>',
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Wasted Cost by Service**")
    waste_by_service = waste['by_service']
    if not waste_by_service.empty:
        fig_waste = px.bar(
            waste_by_service,
            x='service',
            y='wasted_cost',
            color='service',
            text='wasted_cost',
            color_discrete_sequence=px.colors.sequential.Reds_r
        )
        fig_waste.update_traces(
            texttemplate='$%{text:,.2f}',
            textposition='outside'
        )
        fig_waste.update_layout(
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(
                title='Wasted Cost (USD)',
                color='white',
                gridcolor='#2d3250'
            ),
            xaxis=dict(title='Service', color='white'),
            font=dict(color='white'),
            height=320
        )
        st.plotly_chart(fig_waste, use_container_width=True)

with col2:
    st.markdown("**Idle Resource List**")
    st.dataframe(
        idle_df.reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
        height=320
    )

st.divider()

# RECOMMENDATIONS
st.markdown(
    '<div class="section-header">💡 Optimization Recommendations</div>',
    unsafe_allow_html=True
)

r1, r2, r3, r4 = st.columns(4)
r1.metric("📋 Total",        rec_summary['total'])
r2.metric("🔴 High Priority", rec_summary['high'])
r3.metric("🟡 Medium",        rec_summary['medium'])
r4.metric("💰 Monthly Saving", f"${rec_summary['total_saving']:,}")

st.markdown("")

rec_df = rec_summary['recommendations']
if not rec_df.empty:
    for _, row in rec_df.iterrows():
        if 'High' in row['priority']:
            st.error(
                f"**{row['priority']}**  |  `{row['resource_id']}`  "
                f"({row['service']} — {row['region']})  \n"
                f"**Issue:** {row['issue']}  \n"
                f"**Action:** {row['action']}  \n"
                f"**Effort:** {row['effort']}  |  "
                f"**Impact:** {row['impact']}  |  "
                f"**Est. Monthly Saving:** ${row['monthly_saving']:,}"
            )
        elif 'Medium' in row['priority']:
            st.warning(
                f"**{row['priority']}**  |  `{row['resource_id']}`  "
                f"({row['service']} — {row['region']})  \n"
                f"**Issue:** {row['issue']}  \n"
                f"**Action:** {row['action']}  \n"
                f"**Effort:** {row['effort']}  |  "
                f"**Impact:** {row['impact']}  |  "
                f"**Est. Monthly Saving:** ${row['monthly_saving']:,}"
            )
        else:
            st.success(
                f"**{row['priority']}**  |  `{row['resource_id']}`  "
                f"({row['service']} — {row['region']})  \n"
                f"**Issue:** {row['issue']}  \n"
                f"**Action:** {row['action']}  \n"
                f"**Effort:** {row['effort']}  |  "
                f"**Impact:** {row['impact']}  |  "
                f"**Est. Monthly Saving:** ${row['monthly_saving']:,}"
            )
else:
    st.success("✅ No optimization actions needed!")

st.divider()

# SAVINGS SUMMARY
st.markdown(
    '<div class="section-header">💰 Potential Savings Summary</div>',
    unsafe_allow_html=True
)

savings_df = savings['breakdown']
if not savings_df.empty:
    col1, col2 = st.columns(2)

    with col1:
        fig_savings = px.bar(
            savings_df,
            x='strategy',
            y='monthly_saving',
            color='impact',
            text='monthly_saving',
            color_discrete_map={
                'High':   '#28a745',
                'Medium': '#ffc107',
                'Low':    '#6c757d'
            }
        )
        fig_savings.update_traces(
            texttemplate='$%{text:,.2f}',
            textposition='outside'
        )
        fig_savings.update_layout(
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(
                title='Monthly Saving (USD)',
                color='white',
                gridcolor='#2d3250'
            ),
            xaxis=dict(
                title='',
                color='white',
                tickangle=-20
            ),
            font=dict(color='white'),
            legend=dict(
                bgcolor='rgba(0,0,0,0)',
                font=dict(color='white')
            ),
            height=340
        )
        st.plotly_chart(fig_savings, use_container_width=True)

    with col2:
        st.markdown("**Savings Breakdown Table**")
        st.dataframe(
            savings_df[[
                'strategy', 'monthly_saving', 'effort', 'impact'
            ]],
            use_container_width=True,
            hide_index=True,
            height=320
        )
        st.success(
            f"💰 **Total Potential Monthly Saving: "
            f"${savings['total_monthly']:,}**"
        )

st.divider()

# RAW DATA
with st.expander("🗂️ View Raw Billing Data"):
    st.dataframe(df, use_container_width=True, hide_index=True)

st.caption(
    "☁️ Cloud Cost Analyzer v3.0  |  "
    "Built with Python · Pandas · Streamlit · Plotly · FPDF  |  "
    "FinOps Intelligence Dashboard"
)
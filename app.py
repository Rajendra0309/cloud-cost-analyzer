import streamlit as st
import pandas as pd
import plotly.express as px
import analyzer

# Page Configuration
st.set_page_config(
    page_title="Cloud Cost Analyzer",
    page_icon="☁️",
    layout="wide"
)

# Custom css
st.markdown("""
    <style>
        .main { background-color: #0f1117; }
        .metric-card {
            background-color: #1e2130;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }
        .section-title {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 10px;    
        }
    </style>
""", unsafe_allow_html=True)

# Title & Header
st.title("☁️ Cloud Cost Analyzer")
st.caption("FinOps Dashboard - AWS Billing Analysis")
st.divider()

# Sidebar - File Upload
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/commons/9/93/Amazon_Web_Services_Logo.svg",
    width=120
)
st.sidebar.title("⚙️ Settings")
st.sidebar.markdown("---")

uploaded_file = st.sidebar.file_uploader(
    "📁 Upload AWS Billing CSV",
    type=["csv"],
    help="Upload your AWS Cost & Usage CSV file"
)

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df['date'] = pd.to_datetime(df['date'])
    st.sidebar.success("✅ Custom file loaded!")
else:
    df = analyzer.load_data("sample_data.csv")
    st.sidebar.info("ℹ️ Using sample dataset")

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Rows:** " + str(len(df)) + " \n" +
    "**Services:** " + str(df['service'].nunique()) + " \n" +
    "**Regions:** " + str(df['region'].nunique()) + " \n" +
    "**Date Range:** " + str(df['date'].min().date()) +
    " -> " + str(df['date'].max().date())
)

# Key Metrics Row
st.subheader("📌 Key Metrics")

total_cost = analyzer.get_total_cost(df)
top_service = analyzer.get_top_service(df)
waste = analyzer.get_idle_waste_summary(df)
idle_cost = waste['idle_cost']
waste_pct = waste['waste_percentage']
idle_count = waste['idle_count']

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    label="💰 Total Cloud Spend",
    value=f"${total_cost:,}"
)
col2.metric(
    label="🏆 Top Cost Service",
    value=top_service['service'],
    delta=f"${top_service['cost']:,}"
)
col3.metric(
    label="⚠️ Idle Resource Waste",
    value=f"${idle_cost:,}",
    delta=f"{waste_pct}% of total spend",
    delta_color="inverse"
)
col4.metric(
    label="🔍 Idle Resources Found",
    value=f"{idle_count} resources"
)

st.divider()

# Cost Breakdown Charts
st.subheader("📊 Cost Breakdown")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Service-wise Cost (Bar Chart)**")
    service_df = analyzer.get_service_breakdown(df)
    fig_bar = px.bar(
        service_df,
        x='service',
        y='total_cost',
        color='service',
        text='total_cost',
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig_bar.update_traces(texttemplate='$%{text:,.2f}', textposition='outside')
    fig_bar.update_layout(
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        yaxis_title="Cost (USD)",
        xaxis_title="Service"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    st.markdown("**Service-wise Cost (Pie Chart)**")
    pct_df = analyzer.get_service_cost_percentage(df)
    pct_df = pct_df.reset_index(drop=True)

    if not pct_df.empty and 'service' in pct_df.columns and 'total_cost' in pct_df.columns:
        fig_pie = px.pie(
            data_frame=pct_df,
            names='service',
            values='total_cost',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_pie.update_traces(textinfo='percent+label')
        fig_pie.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=True
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("No data available for pie chart.")

st.divider()

# Daily Cost Trend
st.subheader("📈 Daily Cost Trend")

trend_df = analyzer.get_daily_trend(df)
fig_line = px.line(
    trend_df,
    x='date',
    y='daily_cost',
    markers=True,
    color_discrete_sequence=['#00d4ff']
)
fig_line.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    yaxis_title="Daily Cost (USD)",
    xaxis_title="Date"
)
fig_line.update_traces(line_width=2.5)
st.plotly_chart(fig_line, use_container_width=True)

st.divider()

# Region Breakdown
st.subheader("🌍 Region-wise Cost")

region_df = analyzer.get_region_breakdown(df)

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
        yaxis_title="Cost (USD)",
        xaxis_title="Region"
    )
    st.plotly_chart(fig_region, use_container_width=True)

with col2:
    st.markdown("**Region Cost Table**")
    st.dataframe(
        region_df,
        use_container_width=True,
        hide_index=True
    )

st.divider()

# Idle Resource Details
st.subheader("⚠️ Idle Resource Details")

idle_df = analyzer.get_idle_resources(df)
waste_by_service = waste['by_service']

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Wasted Cost by Service**")
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
        yaxis_title="Wasted Cost (USD)",
        xaxis_title="Service"
    )
    st.plotly_chart(fig_waste, use_container_width=True)

with col2:
    st.markdown("**Idle Resource List**")
    st.dataframe(
        idle_df.reset_index(drop=True),
        use_container_width=True,
        hide_index=True
    )

st.divider()

# Recommendations
st.subheader("💡 Optimization Recommendations")

rec_df = analyzer.get_recommendations(df)

if not rec_df.empty:
    for _, row in rec_df.iterrows():
        if "High" in row['priority']:
            st.error(
                f"**{row['priority']} | {row['service']}** - "
                f"{row['action']} - "
                f"Estimated Saving: **{row['estimated_saving']}**"
            )
        elif "Medium" in row['priority']:
            st.warning(
                f"**{row['priority']} | {row['service']}** - "
                f"{row['action']} - "
                f"Estimated Saving: **{row['estimated_saving']}**"
            )
        else:
            st.success(
                f"**{row['priority']} | {row['service']}** - "
                f"{row['action']} - "
                f"Estimated Saving: **{row['estimated_saving']}**"
            )
else:
    st.success("✅ No optimization actions needed!")

st.divider()

# Raw Data Viewer
with st.expander("🗂️ View Raw Billing Data"):
    st.dataframe(df, use_container_width=True, hide_index=True)

st.caption("Built with Python - Pandas - Streamlit - Plotly - Cloud Cost Analyzer v2.0")
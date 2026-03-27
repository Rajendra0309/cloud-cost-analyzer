import pandas as pd
import numpy as np

# Core Analysis
def get_total_cost(df):
    """Total spend across all services and regions."""
    return round(df['cost_usd'].sum(), 2)

def get_service_breakdown(df):
    """Cost and percentage breakdown by service."""
    total = df['cost_usd'].sum()
    breakdown = (
        df.groupby('service')['cost_usd']
        .sum()
        .round(2)
        .reset_index()
        .rename(columns={'cost_usd': 'total_cost'})
    )
    breakdown['percentage'] = (
        (breakdown['total_cost'] / total * 100).round(2)
    )
    return breakdown.sort_values('total_cost', ascending=False)

def get_region_breakdown(df):
    """Cost breakdown by AWS region."""
    breakdown = (
        df.groupby('region')['cost_usd']
        .sum()
        .round(2)
        .reset_index()
        .rename(columns={'cost_usd': 'total_cost'})
        .sort_values('total_cost', ascending=False)
    )
    return breakdown

def get_daily_trend(df):
    """Daily total cost over time."""
    trend = (
        df.groupby('date')['cost_usd']
        .sum()
        .round(2)
        .reset_index()
        .rename(columns={'cost_usd': 'daily_cost'})
    )
    return trend

def get_top_service(df):
    """Returns the single highest cost service."""
    breakdown = get_service_breakdown(df)
    top = breakdown.iloc[0]
    return {
        'service': top['service'],
        'cost': top['total_cost']
    }

def get_idle_resources(df):
    """All rows where status is Idle."""
    idle = df[df['status'] == 'Idle'][[
        'date', 'service', 'region',
        'resource_id', 'cost_usd', 'cpu_utilization'
    ]].copy()
    return idle.sort_values('cost_usd', ascending=False)

def get_idle_waste_summary(df):
    """
    Summary of idle resource waste:
    total idle cost, count, % of total spend,
    and breakdown by service.
    """
    idle_df = get_idle_resources(df)
    total_cost = get_total_cost(df)
    idle_cost = round(idle_df['cost_usd'].sum(), 2)
    waste_pct = round((idle_cost / total_cost) * 100, 2) \
                if total_cost > 0 else 0
    
    by_service = (
        idle_df.groupby('service')['cost_usd']
        .sum()
        .round(2)
        .reset_index()
        .rename(columns={'cost_usd': 'wasted_cost'})
        .sort_values('wasted_cost', ascending=False)
    )

    return {
        'idle_count': len(idle_df),
        'idle_cost': idle_cost,
        'waste_percentage': waste_pct,
        'by_service': by_service
    }

# Anomaly Detection
def detect_anomalies(df, threshold_pct=30):
    """
    Detects daily cost spikes by comparing each day's
    total cost to the rolling 3-day average before it.

    A day is flagged as an anomaly if its cost exceeds
    the rolling average by more than threshold_pct (default 30%).

    Returns a DataFrame of anomaly days with:
    - date
    - daily_cost
    - rolling_avg (3-day average before that day)
    - spike_pct (how much % higher than average)
    - is_anomaly flag
    """

    trend = get_daily_trend(df)

    # Rolling 3-day average (min 1 period so day 1 isn't null)
    trend['rolling_avg'] = (
        trend['daily_cost']
        .shift(1)
        .rolling(window=3, min_periods=1)
        .mean()
        .round(2)
    )

    # Percentage change vs rolling average
    trend['spike_pct'] = (
        ((trend['daily_cost'] - trend['rolling_avg'])
         / trend['rolling_avg'] * 100)
         .round(2)
    )

    # Flag anomalies
    trend['is_anomaly'] = trend['spike_pct'] > threshold_pct

    anomalies = trend[trend['is_anomaly']].copy()
    return trend, anomalies

def get_anomaly_summary(df, threshold_pct=30):
    """
    Returns a clean summary dict for the dashboard:
    - how many anomaly days found
    - the worst spike day and its % increase
    - full anomaly DataFrame
    """
    trend, anomalies = detect_anomalies(df, threshold_pct)

    if anomalies.empty:
        return {
            'count': 0,
            'worst_day': None,
            'worst_spike': None,
            'anomalies': anomalies,
            'trend': trend
        }
    
    worst = anomalies.loc[anomalies['spike_pct'].idxmax()]

    return {
        'count': len(anomalies),
        'worst_day': worst['date'].date(),
        'worst_spike': round(worst['spike_pct'], 2),
        'anomalies': anomalies,
        'trend': trend
    }

# Cost Forecasting
def forecast_next_month(df):
    """
    Simple but effective forecasting using a
    weighted moving average of daily costs.

    Returns a dict with forecast figures.
    """
    trend = get_daily_trend(df)
    daily_costs = trend['daily_cost'].values

    # Weighted average
    n = len(daily_costs)
    weights = np.arange(1, n+1)
    weighted_avg = np.average(daily_costs, weights=weights)

    forecast = round(weighted_avg * 30, 2)
    optimistic = round(forecast * 0.90, 2)
    pessimistic = round(forecast * 1.20, 2)
    current_monthly = round(daily_costs.mean() * 30, 2)

    return {
        'avg_daily_cost': round(weighted_avg, 2),
        'forecast': forecast,
        'optimistic': optimistic,
        'pessimistic': pessimistic,
        'current_monthly': current_monthly,
        'trend_direction': 'up' if daily_costs[-1] > daily_costs[0] else 'down'
    }

# Savings Estimator
def get_savings_estimate(df):
    """
    Estimate potential monthly savings from
    four optimization strategies:

    1. Stopping idle EC2 instances
    2. Stopping idle RDS instances
    3. Moving S3 to cheaper storage tiers
    4. Rightsizing low-CPU EC2 instances

    Returns total potential saving and breakdown.
    """
    savings = []

    # Idle EC2
    idle_ec2 = df[(df['service'] == 'EC2') & (df['status'] == 'Idle')]
    if not idle_ec2.empty:
        saving = round(idle_ec2['cost_usd'].sum() * 30 /
                       max(df['date'].nunique(), 1), 2)
        savings.append({
            'strategy': 'Stop Idle EC2 instances',
            'monthly_saving': saving,
            'effort': 'Low',
            'impact': 'High'
        })

    # Idle RDS
    idle_rds = df[(df['service'] == 'RDS') & (df['status'] == 'Idle')]
    if not idle_rds.empty:
        saving = round(idle_rds['cost_usd'].sum() * 30 /
                       max(df['date'].nunique(), 1), 2)
        savings.append({
            'strategy': 'Stop Idle RDS instances',
            'monthly_saving': saving,
            'effort': 'Low',
            'impact': 'High'
        })

    # S3 storage tier optimization
    s3_df = df[df['service'] == 'S3']
    if not s3_df.empty:
        high_storage = s3_df[s3_df['storage_gb'] > 500]
        if not high_storage.empty:
            saving = round(
                high_storage['cost_usd'].sum() * 0.40 * 30 /
                max(df['date'].nunique(), 1), 2
            )
            savings.append({
                'strategy': 'Move S3 to Infrequent Access / Glacier',
                'monthly_saving': saving,
                'effort': 'Medium',
                'impact': 'Medium'
            })

    # Rightsize low-CPU EC2
    low_cpu_ec2 = df[
        (df['service'] == 'EC2') &
        (df['status'] == 'Active') &
        (df['cpu_utilization'] < 20)
    ]
    if not low_cpu_ec2.empty:
        saving = round(
            low_cpu_ec2['cost_usd'].sum() * 0.30 * 30 /
            max(df['date'].nunique(), 1), 2
        )
        savings.append({
            'strategy': 'Rightsize Low-CPU EC2 Instances',
            'monthly_saving': saving,
            'effort': 'Medium',
            'impact': 'High'
        })

    savings_df = pd.DataFrame(savings)

    total_saving = round(savings_df['monthly_saving'].sum(), 2) \
                    if not savings_df.empty else 0
    
    return {
        'breakdown': savings_df,
        'total_monthly': total_saving
    }

if __name__ == "__main__":
    from data_loader import load_data

    df = load_data("data/sample_data.csv")

    print("--- Total Cost ---")
    print(f"${get_total_cost(df)}")

    print("\n--- Service Breakdown ---")
    print(get_service_breakdown(df))

    print("\n--- Anomaly Detection ---")
    anomaly_summary = get_anomaly_summary(df)
    print(f"Anomalies Found : {anomaly_summary['count']}")
    print(f"Worst Day : {anomaly_summary['worst_day']}")
    print(f"Worst Spike : {anomaly_summary['worst_spike']}%")
    print(anomaly_summary['anomalies'][
        ['date', 'daily_cost', 'rolling_avg', 'spike_pct']
    ])

    print("\n--- Forecast ---")
    forecast = forecast_next_month(df)
    for key, val in forecast.items():
        print(f" {key}: {val}")

    print("\n--- Savings Estimate ---")
    savings = get_savings_estimate(df)
    print(f"Total Monthly Saving: ${savings['total_monthly']}")
    print(savings['breakdown'])
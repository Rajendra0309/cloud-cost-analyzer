import pandas as pd

# Load the CSV data
def load_data(filepath):
    df = pd.read_csv(filepath)
    df['date'] = pd.to_datetime(df['date'])
    return df

# Total cloud cost
def get_total_cost(df):
    return round(df['cost_usd'].sum(), 2)

# Service-wise cost breakdown
def get_service_breakdown(df):
    breakdown = (
        df.groupby('service')['cost_usd']
        .sum()
        .round(2)
        .reset_index()
        .rename(columns={'cost_usd': 'total_cost'})
        .sort_values('total_cost', ascending=False)
    )
    return breakdown

# Region-wise cost breakdown
def get_region_breakdown(df):
    breakdown = (
        df.groupby('region')['cost_usd']
        .sum()
        .round(2)
        .reset_index()
        .rename(columns={'cost_usd': 'total_cost'})
        .sort_values('total_cost', ascending=False)
    )
    return breakdown

# Detect idle resources
def get_idle_resources(df):
    idle = df[df['status'] == 'Idle'][[
        'date', 'service', 'region', 'resource_id', 'cost_usd'
    ]].copy()
    idle = idle.sort_values('cost_usd', ascending=False)
    return idle

# Cost percentage per service
def get_service_cost_percentage(df):
    total = df['cost_usd'].sum()
    breakdown = (
        df.groupby('service')['cost_usd']
        .sum()
        .reset_index()
        .rename(columns={'cost_usd': 'total_cost'})
    )
    breakdown['percentage'] = (
        (breakdown['total_cost'] / total * 100)
        .round(2)
    )
    breakdown = breakdown.sort_values('percentage', ascending=False)
    return breakdown

# Top cost service insight
def get_top_service(df):
    breakdown = get_service_breakdown(df)
    top = breakdown.iloc[0]
    return {
        'service': top['service'],
        'cost': top['total_cost']
    }

# Idle resource waste summary
def get_idle_waste_summary(df):
    idle_df = get_idle_resources(df)
    total_cost = get_total_cost(df)
    idle_cost = round(idle_df['cost_usd'].sum(), 2)
    waste_percentage = round((idle_cost / total_cost) * 100, 2)

    summary = {
        'idle_count': len(idle_df),
        'idle_cost': idle_cost,
        'waste_percentage': waste_percentage,
        'by_service': (
            idle_df.groupby('service')['cost_usd']
            .sum()
            .round(2)
            .reset_index()
            .rename(columns={'cost_usd': 'wasted_cost'})
            .sort_values('wasted_cost', ascending=False)
        )
    }
    return summary

# Daily cost trend
def get_daily_trend(df):
    trend = (
        df.groupby('date')['cost_usd']
        .sum()
        .round(2)
        .reset_index()
        .rename(columns={'cost_usd': 'daily_cost'})
    )
    return trend

# Recommendations engine
def get_recommendations(df):
    recommendations = []
    idle_df = get_idle_resources(df)

    # Stop idle EC2 instances
    idle_ec2 = idle_df[idle_df['service'] == 'EC2']
    if not idle_ec2.empty:
        saving = round(idle_ec2['cost_usd'].sum(), 2)
        count = len(idle_ec2['resource_id'].unique())
        recommendations.append({
            'priority': '🔴 High',
            'service': 'EC2',
            'action': f'Stop or terminate {count} idle EC2 instance(s)',
            'estimated_saving':f'${saving}'
        })

    # Stop idle RDS instances
    idle_rds = idle_df[idle_df['service'] == 'RDS']
    if not idle_rds.empty:
        saving = round(idle_rds['cost_usd'].sum(), 2)
        count = len(idle_rds['resource_id'].unique())
        recommendations.append({
            'priority': '🔴 High',
            'service': 'RDS',
            'action': f'Stop or snapshot {count} idle EC2 instance(s)',
            'estimated_saving':f'${saving}'
        })

    # Review S3 storage tiers
    s3_df = df[df['service'] == 'S3']
    if not s3_df.empty:
        s3_cost = round(s3_df['cost_usd'].sum(), 2)
        potential = round(s3_cost * 0.30, 2)
        recommendations.append({
            'priority': '🟡 Medium',
            'service': 'S3',
            'action': 'Move infrequently accessed data to S3-IA or Glacier',
            'estimated_saving':f'${potential} (est. 30% reduction)'
        })
    
    # Use lambda instead of always-on EC2
    active_ec2 = df[(df['service'] == 'EC2') & (df['status'] == 'Active')]
    if not active_ec2.empty:
        ec2_cost = round(active_ec2['cost_usd'].sum(), 2)
        potential = round(ec2_cost * 0.20, 2)
        recommendations.append({
            'priority': '🟢 Low',
            'service': 'EC2',
            'action': 'Evaluate moving lightweight workloads to Lambda or Fargate',
            'estimated_saving':f'${potential} (est. 20% reduction)'
        })
    
    return pd.DataFrame(recommendations)

if __name__ == "__main__":
    df = load_data("sample_data.csv")

    print(" --- Total Cost --- ")
    print(f"${get_total_cost(df)}")

    print("\n --- Top Service ---")
    print(get_top_service(df))

    print("\n --- Service Cost % ---")
    print(get_service_cost_percentage(df))

    print("\n --- Idle Waste Summary ---")
    waste = get_idle_waste_summary(df)
    print(f"Idle Count : {waste['idle_count']}")
    print(f"Idle Cost : ${waste['idle_cost']}")
    print(f"Waste % : {waste['waste_percentage']}%")
    print(waste['by_service'])

    print("\n --- Daily Trend ---")
    print(get_daily_trend(df))

    print("\n --- Recommendations ---")
    print(get_recommendations(df))
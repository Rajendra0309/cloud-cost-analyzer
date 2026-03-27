import pandas as pd

# Thresholds
CPU_LOW_THRESHOLD = 20 # % — below this = underutilized EC2
STORAGE_HIGH_THRESHOLD = 500 # GB — above this = expensive S3
RDS_LOW_CPU = 15 # % — below this = underutilized RDS

# Idle EC2 recommendations
def _rec_idle_ec2(df):
    rows = []
    idle = df[(df['service'] == 'EC2') & (df['status'] == 'Idle')]

    for resource_id, group in idle.groupby('resource_id'):
        avg_cost = round(group['cost_usd'].mean(), 2)
        region = group['region'].iloc[0]
        rows.append({
            'resource_id': resource_id,
            'service': 'EC2',
            'region': region,
            'issue': 'Instance is Idle (0% utilization)',
            'action': 'Stop or terminate this EC2 instance immediately',
            'priority': '🔴 High',
            'effort': 'Low',
            'impact': 'High',
            'daily_saving': avg_cost,
            'monthly_saving': round(avg_cost * 30, 2)
        })

    return rows

# Low CPU EC2 recommendations
def _rec_low_cpu_ec2(df):
    rows = []
    low_cpu = df[
        (df['service'] == 'EC2') &
        (df['status'] == 'Active') &
        (df['cpu_utilization'] < CPU_LOW_THRESHOLD) &
        (df['cpu_utilization'] > 0)
    ]

    for resource_id, group in low_cpu.groupby('resource_id'):
        avg_cpu = round(group['cpu_utilization'].mean(), 2)
        avg_cost = round(group['cost_usd'].mean(), 2)
        region = group['region'].iloc[0]
        saving = round(avg_cost * 0.40, 2)
        rows.append({
            'resource_id': resource_id,
            'service': 'EC2',
            'region': region,
            'issue': f'Low CPU utilization (avg {avg_cpu}%)',
            'action': 'Downsize to a smaller instance type (e.g. t3.medium -> t3.small)',
            'priority': '🟡 Medium',
            'effort': 'Medium',
            'impact': 'High',
            'daily_saving': saving,
            'monthly_saving': round(avg_cost * 30, 2)
        })

    return rows

# Idle RDS recommendations
def _rec_idle_rds(df):
    rows = []
    idle = df[(df['service'] == 'RDS') & (df['status'] == 'Idle')]

    for resource_id, group in idle.groupby('resource_id'):
        avg_cost = round(group['cost_usd'].mean(), 2)
        region = group['region'].iloc[0]
        rows.append({
            'resource_id':    resource_id,
            'service':        'RDS',
            'region':         region,
            'issue':          'RDS instance is Idle',
            'action':         'Stop instance or take a snapshot and terminate',
            'priority':       '🔴 High',
            'effort':         'Low',
            'impact':         'High',
            'daily_saving':   avg_cost,
            'monthly_saving': round(avg_cost * 30, 2)
        })

    return rows

# Underutilized RDS
def _rec_underutilized_rds(df):
    rows = []
    low = df[
        (df['service'] == 'RDS') &
        (df['status'] == 'Active') &
        (df['cpu_utilization'] < RDS_LOW_CPU) &
        (df['cpu_utilization'] > 0)
    ]

    for resource_id, group in low.groupby('resource_id'):
        avg_cpu = round(group['cpu_utilization'].mean(), 2)
        avg_cost = round(group['cost_usd'].mean(), 2)
        region = group['region'].iloc[0]
        saving = round(avg_cost * 0.35, 2)
        rows.append({
            'resource_id':    resource_id,
            'service':        'RDS',
            'region':         region,
            'issue':          f'Underutilized RDS (avg CPU {avg_cpu}%)',
            'action':         'Downgrade to a smaller RDS instance class',
            'priority':       '🟡 Medium',
            'effort':         'Medium',
            'impact':         'Medium',
            'daily_saving':   saving,
            'monthly_saving': round(saving * 30, 2)
        })

    return rows

# High S3 storage cost
def _rec_s3_storage(df):
    rows = []
    s3 = df[
        (df['service'] == 'S3') &
        (df['storage_gb'] > STORAGE_HIGH_THRESHOLD)
    ]

    for resource_id, group in s3.groupby('resource_id'):
        avg_storage = round(group['storage_gb'].mean(), 2)
        avg_cost = round(group['cost_usd'].mean(), 2)
        region = group['region'].iloc[0]
        saving = round(avg_cost * 0.45, 2)
        rows.append({
            'resource_id':    resource_id,
            'service':        'S3',
            'region':         region,
            'issue':          f'High storage usage ({avg_storage} GB)',
            'action':         'Move to S3 Infrequent Access or Glacier for cold data',
            'priority':       '🟡 Medium',
            'effort':         'Medium',
            'impact':         'Medium',
            'daily_saving':   saving,
            'monthly_saving': round(saving * 30, 2)
        })

    return rows

# Main recommendation engine 
# calls all sub-functions and combines results
def get_all_recommendations(df):
    all_rows = []
    all_rows.extend(_rec_idle_ec2(df))
    all_rows.extend(_rec_low_cpu_ec2(df))
    all_rows.extend(_rec_idle_rds(df))
    all_rows.extend(_rec_underutilized_rds(df))
    all_rows.extend(_rec_s3_storage(df))

    if not all_rows:
        return pd.DataFrame()
    
    rec_df = pd.DataFrame(all_rows)

    # Sort by monthly saving descending
    rec_df = rec_df.sort_values(
        'monthly_saving', ascending=False
    ).reset_index(drop=True)

    return rec_df

# Recommendations summary
# For dashboard metric cards
def get_recommendations_summary(df):
    rec_df = get_all_recommendations(df)

    if rec_df.empty:
        return {
            'total': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'total_saving': 0,
            'recommendations': rec_df
        }
    
    high = len(rec_df[rec_df['priority'].str.contains('High')])
    medium = len(rec_df[rec_df['priority'].str.contains('Medium')])
    low = len(rec_df[rec_df['priority'].str.contains('Low')])

    return {
        'total': len(rec_df),
        'high': high,
        'medium': medium,
        'low': low,
        'total_saving': round(rec_df['monthly_saving'].sum(), 2),
        'recommendations': rec_df
    }

if __name__ == "__main__":
    from data_loader import load_data

    df = load_data("data/sample_data.csv")

    print("--- All Recommendations ---")
    rec_df = get_all_recommendations(df)
    print(rec_df[[
        'resource_id', 'service', 'issue',
        'priority', 'monthly_saving'
    ]].to_string())

    print("\n--- Recommendations Summary ---")
    summary = get_recommendations_summary(df)
    print(f"Total : {summary['total']}")
    print(f"High : {summary['high']}")
    print(f"Medium : {summary['medium']}")
    print(f"Low : {summary['low']}")
    print(f"Total Saving : {summary['total_saving']}")
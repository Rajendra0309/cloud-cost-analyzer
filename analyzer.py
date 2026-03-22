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

if __name__ == "__main__":
    df = load_data("sample_data.csv")

    print(" --- Total Cost --- ")
    print(f"${get_total_cost(df)}")

    print("\n --- Service Breakdown --- ")
    print(get_service_breakdown(df))

    print("\n --- Region Breakdown --- ")
    print(get_region_breakdown(df))

    print("\n --- Idle Resources --- ")
    print(get_idle_resources(df))
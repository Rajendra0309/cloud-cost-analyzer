import pandas as pd
import os

# Required Columns & Their Expected Types
REQUIRED_COLUMNS = {
    'date': 'datetime',
    'service': 'string',
    'region': 'string',
    'cost_usd': 'float',
    'usage_hours': 'float',
    'resource_id': 'string',
    'status': 'string',
    'cpu_utilization': 'float',
    'storage_gb': 'float'
}

# Load + validate CSV
def load_data(filepath):
    """
    Loads a CSV billing file, validates columns,
    cleans types, and returns a clean DataFrame.
    Raises clear errors if something is wrong.
    """

    # Check file exists
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"File not found: {filepath}\n"
            f"Make sure your CSV is inside the /data folder."
        )
    
    # Load CSV
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        raise ValueError(f"Could not read CSV file: {e}")
    
    # Validate required columns
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns: {missing}\n"
            f"Your CSV must have: {list(REQUIRED_COLUMNS.keys())}"
        )
    
    # Clean & cast column types
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['cost_usd'] = pd.to_numeric(df['cost_usd'], errors='coerce')
    df['usage_hours'] = pd.to_numeric(df['usage_hours'], errors='coerce')
    df['cpu_utilization'] = pd.to_numeric(df['cpu_utilization'], errors='coerce')
    df['storage_gb'] = pd.to_numeric(df['storage_gb'], errors='coerce')

    # Drop rows where critical fields are null
    before = len(df)
    df = df.dropna(subset=['date', 'cost_usd', 'resource_id'])
    dropped = before - len(df)
    if dropped > 0:
        print(f"[data_loader] Warning: Dropped {dropped} rows with null values.")

    # Standardize text columns
    df['service'] = df['service'].str.strip()
    df['region'] = df['region'].str.strip()
    df['resource_id'] = df['resource_id'].str.strip()
    df['status'] = df['status'].str.strip().str.capitalize()

    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)

    return df

# Get dataset summary
def get_data_summary(df):
    """
    Returns a dict of key facts about the loaded dataset.
    Used in the dashboard sidebar.
    """
    return {
        'total_rows': len(df),
        'services': sorted(df['service'].unique().tolist()),
        'regions': sorted(df['region'].unique().tolist()),
        'date_min': df['date'].min().date(),
        'date_max': df['date'].max().date(),
        'total_days': df['date'].nunique(),
        'has_idle': (df['status'] == 'Idle').any()
    }

# Filter by date range
def filter_by_date(df, start_date, end_date):
    """
    Filters the DataFrame to a specific date range.
    Used by the dashboard date range slider.
    """
    mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)
    return df[mask].reset_index(drop=True)

# Filter by services
def filter_by_service(df, selected_services):
    """
    Filters the DataFrame to selected services only.
    Used by the dashboard service multiselect.
    """
    if not selected_services:
        return df
    return df[df['service'].isin(selected_services)].reset_index(drop=True)

def filter_by_services(df, selected_services):
    """
    Backward-compatible alias for filter_by_service.
    """
    return filter_by_service(df, selected_services)

if __name__ == "__main__":
    df = load_data('data/sample_data.csv')

    print("--- Data Loaded Successfully ---")
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"Date Range: {df['date'].min().date()} -> {df['date'].max().date()}")
    print(f"Services: {df['service'].unique().tolist()}")
    print(f"Statuses: {df['status'].unique().tolist()}")

    print("\n--- Dataset Summary ---")
    summary = get_data_summary(df)
    for key, val in summary.items():
        print(f" {key}: {val}")

    print("\n--- Sample Rows ---")
    print(df.head(5))
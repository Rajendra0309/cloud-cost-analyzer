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


def _coerce_and_clean(df):
    """Apply type coercion and standard cleanup on canonical schema."""
    df = df.copy()

    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['cost_usd'] = pd.to_numeric(df['cost_usd'], errors='coerce')
    df['usage_hours'] = pd.to_numeric(df['usage_hours'], errors='coerce')
    df['cpu_utilization'] = pd.to_numeric(df['cpu_utilization'], errors='coerce')
    df['storage_gb'] = pd.to_numeric(df['storage_gb'], errors='coerce')

    before = len(df)
    df = df.dropna(subset=['date', 'cost_usd', 'resource_id'])
    dropped = before - len(df)
    if dropped > 0:
        print(f"[data_loader] Warning: Dropped {dropped} rows with null values.")

    df['service'] = df['service'].astype(str).str.strip()
    df['region'] = df['region'].astype(str).str.strip()
    df['resource_id'] = df['resource_id'].astype(str).str.strip()
    df['status'] = df['status'].astype(str).str.strip().str.capitalize()

    return df.sort_values('date').reset_index(drop=True)


def _normalize_native_schema(df):
    """Normalize an already-detailed billing schema to canonical column names."""
    col_map = {c.lower().strip(): c for c in df.columns}
    if not all(col in col_map for col in REQUIRED_COLUMNS):
        return None

    normalized = pd.DataFrame({
        col: df[col_map[col]] for col in REQUIRED_COLUMNS
    })
    return normalized


def _normalize_aws_cost_explorer_schema(df):
    """Convert AWS Cost Explorer monthly export (wide format) into canonical long format."""
    if 'Service' not in df.columns:
        return None

    money_cols = [
        c for c in df.columns
        if c.endswith('($)') and c != 'Total costs($)'
    ]
    if not money_cols:
        return None

    working = df.copy()
    working['date'] = pd.to_datetime(
        working['Service'],
        format='%Y-%m-%d',
        errors='coerce'
    )
    working = working[working['date'].notna()].copy()

    if working.empty:
        return None

    long_df = working.melt(
        id_vars=['date'],
        value_vars=money_cols,
        var_name='service',
        value_name='cost_usd'
    )
    long_df['cost_usd'] = pd.to_numeric(long_df['cost_usd'], errors='coerce').fillna(0.0)

    # Keep only rows that carry spend signal.
    long_df = long_df[long_df['cost_usd'] != 0].copy()
    if long_df.empty:
        # Preserve a valid empty-shaped frame for downstream UI handling.
        long_df = pd.DataFrame(columns=['date', 'service', 'cost_usd'])

    if not long_df.empty:
        long_df['service'] = (
            long_df['service']
            .str.replace('($)', '', regex=False)
            .str.strip()
        )
        long_df['service'] = long_df['service'].replace({
            'EC2-Instances': 'EC2',
            'EC2-Other': 'EC2'
        })

    long_df['region'] = 'global'
    long_df['usage_hours'] = 0.0
    long_df['status'] = 'Active'
    long_df['cpu_utilization'] = 0.0
    long_df['storage_gb'] = 0.0

    if long_df.empty:
        long_df['resource_id'] = pd.Series(dtype='object')
    else:
        long_df['resource_id'] = [
            f"aws-billing-{idx+1}" for idx in range(len(long_df))
        ]

    return long_df[[
        'date', 'service', 'region', 'cost_usd',
        'usage_hours', 'resource_id', 'status',
        'cpu_utilization', 'storage_gb'
    ]]


def normalize_billing_df(df):
    """
    Accepts either canonical app schema or AWS Cost Explorer export,
    and returns canonical schema required by the analyzer.
    """
    native = _normalize_native_schema(df)
    if native is not None:
        return _coerce_and_clean(native)

    aws_export = _normalize_aws_cost_explorer_schema(df)
    if aws_export is not None:
        return _coerce_and_clean(aws_export)

    raise ValueError(
        "Unsupported CSV format. Upload either the app schema with columns "
        f"{list(REQUIRED_COLUMNS.keys())} or an AWS Cost Explorer export "
        "that includes a 'Service' column and service cost columns ending with '($)'."
    )

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
    
    return normalize_billing_df(df)


def load_uploaded_data(uploaded_file):
    """Load and normalize a CSV uploaded through Streamlit file_uploader."""
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        raise ValueError(f"Could not read uploaded CSV: {e}")

    return normalize_billing_df(df)

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
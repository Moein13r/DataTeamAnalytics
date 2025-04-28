import pandas as pd
import numpy as np
from io import BytesIO
import chardet

def load_data(file):
    """
    Load data from uploaded file (CSV or Excel)
    
    Args:
        file: The uploaded file object
    
    Returns:
        pandas.DataFrame: The loaded dataframe
    """
    file_extension = file.name.split('.')[-1].lower()
    
    if file_extension == 'csv':
        # Detect encoding
        file_bytes = file.getvalue()
        result = chardet.detect(file_bytes)
        encoding = result['encoding']
        
        # Read CSV with detected encoding
        try:
            df = pd.read_csv(BytesIO(file_bytes), encoding=encoding)
        except Exception:
            # Fallback to default encoding
            df = pd.read_csv(BytesIO(file_bytes))
            
    elif file_extension in ['xlsx', 'xls']:
        df = pd.read_excel(file)
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")
    
    return df

def get_data_info(df):
    """
    Get basic information about the dataframe
    
    Args:
        df: pandas.DataFrame
    
    Returns:
        dict: Dictionary containing information about the dataframe
    """
    # Get basic information
    rows = df.shape[0]
    columns = df.shape[1]
    missing_values = df.isna().sum().sum()
    duplicate_rows = df.duplicated().sum()
    
    # Get column information
    column_info = pd.DataFrame({
        'Column': df.columns,
        'Type': df.dtypes.astype(str),
        'Non-Null Count': df.count().values,
        'Missing Values': df.isna().sum().values,
        'Missing %': (df.isna().sum().values / rows * 100).round(2),
        'Unique Values': [df[col].nunique() for col in df.columns]
    })
    
    return {
        'rows': rows,
        'columns': columns,
        'missing_values': missing_values,
        'duplicate_rows': duplicate_rows,
        'column_info': column_info
    }

def get_summary_statistics(df):
    """
    Get summary statistics for numeric columns in the dataframe
    
    Args:
        df: pandas.DataFrame with numeric columns
    
    Returns:
        pandas.DataFrame: Summary statistics
    """
    # Get basic statistics
    summary = df.describe().T
    
    # Add more statistics
    summary['median'] = df.median()
    summary['skew'] = df.skew()
    summary['kurtosis'] = df.kurtosis()
    
    # Reorder columns
    column_order = ['count', 'mean', 'median', 'std', 'min', '25%', '50%', '75%', 'max', 'skew', 'kurtosis']
    summary = summary[column_order]
    
    return summary.round(2)

def clean_data(df, columns, strategy, fill_value=None):
    """
    Clean data based on specified strategy
    
    Args:
        df: pandas.DataFrame
        columns: List of column names to clean
        strategy: Strategy to handle missing values
        fill_value: Value to fill missing data with (if strategy is 'Fill with value')
    
    Returns:
        pandas.DataFrame: Cleaned dataframe
    """
    df_cleaned = df.copy()
    
    for col in columns:
        if strategy == "Drop rows":
            df_cleaned = df_cleaned.dropna(subset=[col])
        elif strategy == "Fill with mean":
            if pd.api.types.is_numeric_dtype(df_cleaned[col]):
                df_cleaned[col] = df_cleaned[col].fillna(df_cleaned[col].mean())
        elif strategy == "Fill with median":
            if pd.api.types.is_numeric_dtype(df_cleaned[col]):
                df_cleaned[col] = df_cleaned[col].fillna(df_cleaned[col].median())
        elif strategy == "Fill with mode":
            df_cleaned[col] = df_cleaned[col].fillna(df_cleaned[col].mode()[0])
        elif strategy == "Fill with value":
            # Try to convert the fill value to the appropriate type
            column_type = df_cleaned[col].dtype
            try:
                if pd.api.types.is_numeric_dtype(column_type):
                    typed_fill_value = float(fill_value) if '.' in fill_value else int(fill_value)
                else:
                    typed_fill_value = fill_value
                df_cleaned[col] = df_cleaned[col].fillna(typed_fill_value)
            except (ValueError, TypeError):
                # If conversion fails, use the string value
                df_cleaned[col] = df_cleaned[col].fillna(fill_value)
    
    return df_cleaned

def get_correlation_matrix(df):
    """
    Calculate correlation matrix for numeric columns
    
    Args:
        df: pandas.DataFrame with numeric columns
    
    Returns:
        pandas.DataFrame: Correlation matrix
    """
    # Calculate Pearson correlation
    corr_matrix = df.corr(method='pearson').round(2)
    return corr_matrix

def sample_data(df, n=1000):
    """
    Sample data from a large dataframe
    
    Args:
        df: pandas.DataFrame
        n: Number of rows to sample
    
    Returns:
        pandas.DataFrame: Sampled dataframe
    """
    if len(df) > n:
        return df.sample(n=n, random_state=42)
    return df

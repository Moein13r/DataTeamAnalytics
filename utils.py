import base64
import pandas as pd
import io
import uuid
import json
import streamlit as st

def get_download_link(df, filename="data.csv", text="Download CSV"):
    """
    Generate a download link for a dataframe
    
    Args:
        df: pandas.DataFrame to download
        filename: Name of the file to download
        text: Text to display for the download link
        
    Returns:
        str: HTML link for downloading the data
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href

def generate_share_code():
    """
    Generate a unique code for sharing visualizations
    
    Returns:
        str: Unique share code
    """
    return str(uuid.uuid4())[:8]

def export_image(fig, format="png"):
    """
    Export a plotly figure as an image
    
    Args:
        fig: plotly.graph_objects.Figure
        format: Image format (png, jpg, svg)
        
    Returns:
        bytes: Image data
    """
    try:
        img_bytes = fig.to_image(format=format)
        return img_bytes
    except Exception as e:
        st.error(f"Failed to export image: {str(e)}")
        return None

def convert_df_to_json(df):
    """
    Convert a dataframe to a JSON string
    
    Args:
        df: pandas.DataFrame
        
    Returns:
        str: JSON string
    """
    return df.to_json(orient="records", date_format="iso")

def filter_dataframe(df, filters):
    """
    Filter a dataframe based on specified filters
    
    Args:
        df: pandas.DataFrame
        filters: Dictionary of column:value pairs
        
    Returns:
        pandas.DataFrame: Filtered dataframe
    """
    filtered_df = df.copy()
    
    for column, value in filters.items():
        if column in filtered_df.columns:
            if pd.api.types.is_numeric_dtype(filtered_df[column]):
                if isinstance(value, list) and len(value) == 2:
                    filtered_df = filtered_df[(filtered_df[column] >= value[0]) & 
                                            (filtered_df[column] <= value[1])]
            elif pd.api.types.is_categorical_dtype(filtered_df[column]) or pd.api.types.is_object_dtype(filtered_df[column]):
                if isinstance(value, list):
                    filtered_df = filtered_df[filtered_df[column].isin(value)]
                else:
                    filtered_df = filtered_df[filtered_df[column] == value]
    
    return filtered_df

def encode_dataframe(df):
    """
    Encode a dataframe for passing between pages
    
    Args:
        df: pandas.DataFrame
        
    Returns:
        str: Base64 encoded dataframe
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return b64

def decode_dataframe(encoded_df):
    """
    Decode a previously encoded dataframe
    
    Args:
        encoded_df: Base64 encoded dataframe
        
    Returns:
        pandas.DataFrame: Decoded dataframe
    """
    csv = base64.b64decode(encoded_df.encode()).decode()
    df = pd.read_csv(io.StringIO(csv))
    return df

import os
import json
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI

# Import visualization functions
from visualization import (
    plot_histogram, 
    plot_scatter, 
    plot_bar, 
    plot_line, 
    plot_correlation_heatmap, 
    plot_box, 
    plot_pie
)

# Get OpenAI API key from environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
MODEL = "gpt-4o"

def process_nlp_query(query, df):
    """
    Process a natural language query about the data
    
    Args:
        query: The user's query as string
        df: pandas DataFrame
    
    Returns:
        tuple: (response text, visualization if applicable)
    """
    if OPENAI_API_KEY is None:
        return "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.", None
    
    # Get dataframe info
    df_info = {
        "columns": list(df.columns),
        "dtypes": {col: str(df[col].dtype) for col in df.columns},
        "shape": df.shape,
        "head": df.head(5).to_dict(orient="records"),
        "summary": df.describe().to_dict() if len(df.select_dtypes(include=[np.number]).columns) > 0 else {}
    }
    
    # Create a system message with context about the data
    system_message = (
        "You are a data analysis assistant that helps users understand their data. "
        "You're connected to a Streamlit app that can create visualizations and perform data analysis. "
        "When a user asks about their data, provide a clear, helpful response. "
        "If they request a visualization, determine the appropriate chart type and return "
        "instructions in JSON format that the app can use to create the visualization.\n\n"
        f"The user has the following dataframe loaded:\n"
        f"- Shape: {df_info['shape'][0]} rows, {df_info['shape'][1]} columns\n"
        f"- Columns: {', '.join(df_info['columns'])}\n"
        f"- Data types: {json.dumps(df_info['dtypes'])}\n"
        f"- Sample data: {json.dumps(df_info['head'])}\n\n"
        "For visualization requests, return a JSON object with the following structure:\n"
        "{\n"
        "  'response': 'Your text response to the user',\n"
        "  'visualization': {\n"
        "    'type': 'One of: histogram, scatter, bar, line, box, pie, correlation',\n"
        "    'parameters': {\n"
        "      'column': 'column_name' or 'x_column', 'y_column', etc. based on chart type\n"
        "    }\n"
        "  }\n"
        "}\n\n"
        "If no visualization is needed, just return:\n"
        "{\n"
        "  'response': 'Your text response to the user'\n"
        "}\n\n"
        "Always ensure your response is accurate, helpful, and relevant to the data."
    )
    
    try:
        # Make the API call
        response = openai.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": query}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        
        # Extract the response
        response_content = response.choices[0].message.content
        response_json = json.loads(response_content)
        
        # Extract the text response
        text_response = response_json.get('response', 'I could not generate a response.')
        
        # Check if visualization is requested
        visualization_data = response_json.get('visualization', None)
        visualization = None
        
        if visualization_data:
            viz_type = visualization_data.get('type', '').lower()
            params = visualization_data.get('parameters', {})
            
            if viz_type == 'histogram':
                column = params.get('column')
                bins = params.get('bins', 20)
                visualization = plot_histogram(df, column, bins)
                
            elif viz_type == 'scatter':
                x_column = params.get('x_column')
                y_column = params.get('y_column')
                color_column = params.get('color_column')
                visualization = plot_scatter(df, x_column, y_column, color_column)
                
            elif viz_type == 'bar':
                x_column = params.get('x_column')
                y_column = params.get('y_column', 'Count')
                title = params.get('title', f'{y_column} by {x_column}')
                
                if y_column == 'Count':
                    # Create count data
                    count_data = df[x_column].value_counts().reset_index()
                    count_data.columns = [x_column, 'Count']
                    visualization = plot_bar(count_data, x_column, 'Count', title)
                else:
                    visualization = plot_bar(df, x_column, y_column, title)
                
            elif viz_type == 'line':
                x_column = params.get('x_column')
                y_column = params.get('y_column')
                group_column = params.get('group_column')
                visualization = plot_line(df, x_column, y_column, group_column)
                
            elif viz_type == 'box':
                y_column = params.get('y_column')
                x_column = params.get('x_column')
                visualization = plot_box(df, y_column, x_column)
                
            elif viz_type == 'pie':
                column = params.get('column')
                visualization = plot_pie(df, column)
                
            elif viz_type == 'correlation':
                columns = params.get('columns', df.select_dtypes(include=[np.number]).columns.tolist())
                corr_matrix = df[columns].corr()
                visualization = plot_correlation_heatmap(corr_matrix)
                
        return text_response, visualization
        
    except Exception as e:
        return f"Error processing your query: {str(e)}", None

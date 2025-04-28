import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def plot_histogram(df, column, bins=20):
    """
    Create a histogram for the given column
    
    Args:
        df: pandas.DataFrame
        column: Column name to plot
        bins: Number of bins for the histogram
    
    Returns:
        plotly.graph_objects.Figure: Histogram figure
    """
    # Check if the column is numeric
    if not pd.api.types.is_numeric_dtype(df[column]):
        raise ValueError(f"Column '{column}' is not numeric")
    
    fig = px.histogram(
        df, 
        x=column, 
        nbins=bins,
        marginal="box",
        title=f"Distribution of {column}",
        labels={column: column},
        template="plotly_white"
    )
    
    # Add mean line
    mean_value = df[column].mean()
    fig.add_vline(
        x=mean_value, 
        line_dash="dash", 
        line_color="red", 
        annotation_text=f"Mean: {mean_value:.2f}",
        annotation_position="top right"
    )
    
    # Add median line
    median_value = df[column].median()
    fig.add_vline(
        x=median_value, 
        line_dash="dash", 
        line_color="green", 
        annotation_text=f"Median: {median_value:.2f}",
        annotation_position="top left"
    )
    
    fig.update_layout(bargap=0.1)
    
    return fig

def plot_scatter(df, x_column, y_column, color_column=None):
    """
    Create a scatter plot with two numeric columns
    
    Args:
        df: pandas.DataFrame
        x_column: Column name for x-axis
        y_column: Column name for y-axis
        color_column: Optional column name for color encoding
    
    Returns:
        plotly.graph_objects.Figure: Scatter plot figure
    """
    # Check if x and y columns are numeric
    if not pd.api.types.is_numeric_dtype(df[x_column]):
        raise ValueError(f"Column '{x_column}' is not numeric")
    if not pd.api.types.is_numeric_dtype(df[y_column]):
        raise ValueError(f"Column '{y_column}' is not numeric")
    
    # Basic scatter plot
    if color_column is None:
        fig = px.scatter(
            df, 
            x=x_column, 
            y=y_column,
            opacity=0.7,
            title=f"{y_column} vs {x_column}",
            template="plotly_white"
        )
    else:
        fig = px.scatter(
            df, 
            x=x_column, 
            y=y_column, 
            color=color_column,
            opacity=0.7,
            title=f"{y_column} vs {x_column} (colored by {color_column})",
            template="plotly_white"
        )
    
    # Add trendline
    if color_column is None:
        fig.update_layout(
            shapes=[{
                'type': 'line',
                'line': {
                    'color': 'rgba(255, 0, 0, 0.5)',
                    'dash': 'dot',
                },
                'x0': df[x_column].min(),
                'y0': df[y_column].min(),
                'x1': df[x_column].max(),
                'y1': df[y_column].max()
            }]
        )
    
    return fig

def plot_bar(data, x, y, title):
    """
    Create a bar chart
    
    Args:
        data: pandas.DataFrame
        x: Column name for x-axis (categories)
        y: Column name for y-axis (values)
        title: Plot title
    
    Returns:
        plotly.graph_objects.Figure: Bar chart figure
    """
    # Limit to 50 categories max for readability
    if data[x].nunique() > 50:
        top_categories = data.groupby(x)[y].sum().nlargest(50).index.tolist()
        filtered_data = data[data[x].isin(top_categories)]
        title = f"{title} (Top 50 shown)"
    else:
        filtered_data = data
    
    fig = px.bar(
        filtered_data, 
        x=x, 
        y=y,
        title=title,
        labels={x: x, y: y},
        template="plotly_white",
        color_discrete_sequence=['#636EFA']
    )
    
    # Rotate x-axis labels if too many categories
    if filtered_data[x].nunique() > 10:
        fig.update_layout(
            xaxis_tickangle=-45,
            xaxis_title=x,
            yaxis_title=y
        )
    
    return fig

def plot_line(df, x_column, y_column, group_column=None):
    """
    Create a line chart
    
    Args:
        df: pandas.DataFrame
        x_column: Column name for x-axis
        y_column: Column name for y-axis
        group_column: Optional column name for grouping lines
    
    Returns:
        plotly.graph_objects.Figure: Line chart figure
    """
    if group_column:
        # Group data
        fig = px.line(
            df, 
            x=x_column, 
            y=y_column, 
            color=group_column,
            markers=True,
            title=f"{y_column} over {x_column} by {group_column}",
            template="plotly_white"
        )
    else:
        # Simple line chart
        fig = px.line(
            df, 
            x=x_column, 
            y=y_column,
            markers=True,
            title=f"{y_column} over {x_column}",
            template="plotly_white"
        )
    
    fig.update_layout(
        xaxis_title=x_column,
        yaxis_title=y_column
    )
    
    return fig

def plot_correlation_heatmap(corr_matrix):
    """
    Create a correlation heatmap
    
    Args:
        corr_matrix: pandas.DataFrame with correlation values
    
    Returns:
        plotly.graph_objects.Figure: Heatmap figure
    """
    fig = px.imshow(
        corr_matrix,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title="Correlation Matrix",
        template="plotly_white"
    )
    
    fig.update_layout(
        coloraxis_colorbar=dict(
            title="Correlation",
            titleside="right"
        )
    )
    
    return fig

def plot_box(df, y_column, x_column=None):
    """
    Create a box plot
    
    Args:
        df: pandas.DataFrame
        y_column: Column name for y-axis (values)
        x_column: Optional column name for x-axis (grouping)
    
    Returns:
        plotly.graph_objects.Figure: Box plot figure
    """
    # Check if y-column is numeric
    if not pd.api.types.is_numeric_dtype(df[y_column]):
        raise ValueError(f"Column '{y_column}' is not numeric")
    
    if x_column:
        title = f"Box Plot of {y_column} by {x_column}"
        # Limit number of categories for better visualization
        if df[x_column].nunique() > 20:
            counts = df[x_column].value_counts().nlargest(20)
            df_filtered = df[df[x_column].isin(counts.index)]
            title += " (Top 20 categories)"
        else:
            df_filtered = df
            
        fig = px.box(
            df_filtered, 
            x=x_column, 
            y=y_column,
            title=title,
            template="plotly_white",
            points="outliers"
        )
    else:
        fig = px.box(
            df, 
            y=y_column,
            title=f"Box Plot of {y_column}",
            template="plotly_white",
            points="outliers"
        )
    
    return fig

def plot_pie(df, column):
    """
    Create a pie chart for a categorical column
    
    Args:
        df: pandas.DataFrame
        column: Column name to visualize
    
    Returns:
        plotly.graph_objects.Figure: Pie chart figure
    """
    value_counts = df[column].value_counts()
    
    # If too many categories, group smaller ones as "Other"
    if len(value_counts) > 10:
        top_n = value_counts.nlargest(9)
        other_sum = value_counts[~value_counts.index.isin(top_n.index)].sum()
        
        labels = list(top_n.index) + ['Other']
        values = list(top_n.values) + [other_sum]
        
        title = f"Distribution of {column} (Top 9 + Other)"
    else:
        labels = value_counts.index
        values = value_counts.values
        
        title = f"Distribution of {column}"
    
    fig = px.pie(
        names=labels,
        values=values,
        title=title,
        template="plotly_white",
        hole=0.3
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    return fig

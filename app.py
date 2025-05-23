import streamlit as st
import pandas as pd
import io
import base64
import os
import json
import time

# Import custom modules
from data_processor import (
    load_data,
    get_data_info,
    get_summary_statistics,
    clean_data,
    get_correlation_matrix
)
from visualization import (
    plot_histogram,
    plot_scatter,
    plot_bar,
    plot_line,
    plot_correlation_heatmap,
    plot_box,
    plot_pie
)
from ai_assistant import process_nlp_query
from utils import get_download_link, generate_share_code

# Import SQL Server UML diagram modules
from sql_server_connection import (
    create_connection_string,
    create_sqlalchemy_engine,
    test_connection,
    get_available_databases,
    save_uploaded_bak,
    restore_database_from_backup
)
from db_schema_extractor import get_full_schema, create_dependency_graph, format_sql
from uml_generator import generate_database_uml, display_uml_in_streamlit, get_uml_legend
from db_analyzer import analyze_database, display_recommendations, get_database_metrics, display_database_metrics
from ef_code_generator import generate_ef_code, display_code_preview

# Set page config
st.set_page_config(
    page_title="Data Analysis Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if 'data' not in st.session_state:
    st.session_state.data = None
if 'file_name' not in st.session_state:
    st.session_state.file_name = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'processing_status' not in st.session_state:
    st.session_state.processing_status = None
    
# SQL Server specific session state variables
if 'sql_connection' not in st.session_state:
    st.session_state.sql_connection = None
if 'sql_engine' not in st.session_state:
    st.session_state.sql_engine = None
if 'db_schema' not in st.session_state:
    st.session_state.db_schema = None
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = None
if 'code_files' not in st.session_state:
    st.session_state.code_files = None

def main():
    st.title("📊 Interactive Data Analysis Tool")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select a page:",
        ["📥 Data Upload", "🧹 Data Cleaning", "📈 Data Analysis", "📊 Visualization", "🤖 Data Chat", 
         "🔄 SQL Server UML"]
    )
    
    # Show the selected page
    if page == "📥 Data Upload":
        show_data_upload_page()
    elif page == "🧹 Data Cleaning":
        show_data_cleaning_page()
    elif page == "📈 Data Analysis":
        show_data_analysis_page()
    elif page == "📊 Visualization":
        show_visualization_page()
    elif page == "🤖 Data Chat":
        show_chat_page()
    elif page == "🔄 SQL Server UML":
        show_sql_server_uml_page()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.info(
        "This tool helps data teams analyze data, create visualizations, "
        "and interact with their data using natural language."
    )

def show_data_upload_page():
    st.header("📥 Data Upload")
    
    st.write("""
    Upload your data file (CSV or Excel) to get started with analysis and visualization.
    """)
    
    # File uploader
    uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls"])
    
    if uploaded_file is not None:
        try:
            # Save the file name
            st.session_state.file_name = uploaded_file.name
            
            # Display loading message
            with st.spinner("Loading data..."):
                # Load the data
                df = load_data(uploaded_file)
                
                # Store in session state
                st.session_state.data = df
                
                # Show success message
                st.success(f"Successfully loaded: {uploaded_file.name}")
                
                # Show data preview
                st.subheader("Data Preview")
                st.dataframe(df.head(10))
                
                # Show basic data info
                st.subheader("Data Information")
                info = get_data_info(df)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Rows:** {info['rows']}")
                    st.write(f"**Columns:** {info['columns']}")
                    
                with col2:
                    st.write(f"**Missing Values:** {info['missing_values']}")
                    st.write(f"**Duplicate Rows:** {info['duplicate_rows']}")
                
                # Display column info
                st.subheader("Column Information")
                st.dataframe(info['column_info'])
        
        except Exception as e:
            st.error(f"Error loading the file: {str(e)}")

def show_data_cleaning_page():
    st.header("🧹 Data Cleaning")
    
    if st.session_state.data is None:
        st.warning("Please upload a data file first.")
        return
    
    st.write("Use the options below to clean and preprocess your data.")
    
    df = st.session_state.data.copy()
    
    # Cleaning options
    st.subheader("Cleaning Options")
    
    # Handle missing values
    st.write("### Handle Missing Values")
    missing_cols = df.columns[df.isnull().any()].tolist()
    
    if missing_cols:
        col1, col2 = st.columns(2)
        
        with col1:
            selected_cols = st.multiselect(
                "Select columns with missing values to handle:",
                options=missing_cols,
                default=missing_cols
            )
        
        with col2:
            missing_strategy = st.selectbox(
                "How to handle missing values?",
                options=["Drop rows", "Fill with mean", "Fill with median", "Fill with mode", "Fill with value"]
            )
        
        fill_value = None
        if missing_strategy == "Fill with value":
            fill_value = st.text_input("Value to fill:")
        
        if selected_cols and st.button("Apply Missing Value Handling"):
            with st.spinner("Processing..."):
                df = clean_data(df, selected_cols, missing_strategy, fill_value)
                st.session_state.data = df
                st.success("Missing values handled successfully!")
                st.rerun()
    else:
        st.info("No missing values detected in the data.")
    
    # Drop duplicate rows
    st.write("### Handle Duplicate Rows")
    if st.button("Drop Duplicate Rows"):
        with st.spinner("Removing duplicates..."):
            original_shape = df.shape[0]
            df = df.drop_duplicates()
            st.session_state.data = df
            new_shape = df.shape[0]
            removed = original_shape - new_shape
            st.success(f"Removed {removed} duplicate rows.")
    
    # Drop columns
    st.write("### Remove Columns")
    cols_to_drop = st.multiselect("Select columns to drop:", options=df.columns.tolist())
    if cols_to_drop and st.button("Drop Selected Columns"):
        with st.spinner("Removing columns..."):
            df = df.drop(columns=cols_to_drop)
            st.session_state.data = df
            st.success(f"Removed columns: {', '.join(cols_to_drop)}")
    
    # Data preview after cleaning
    st.subheader("Data Preview After Cleaning")
    st.dataframe(st.session_state.data.head(10))
    
    # Data info after cleaning
    st.subheader("Data Information After Cleaning")
    info = get_data_info(st.session_state.data)
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Rows:** {info['rows']}")
        st.write(f"**Columns:** {info['columns']}")
        
    with col2:
        st.write(f"**Missing Values:** {info['missing_values']}")
        st.write(f"**Duplicate Rows:** {info['duplicate_rows']}")

def show_data_analysis_page():
    st.header("📈 Data Analysis")
    
    if st.session_state.data is None:
        st.warning("Please upload a data file first.")
        return
    
    df = st.session_state.data
    
    # Summary statistics
    st.subheader("Summary Statistics")
    
    # Only include numeric columns for summary statistics
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    if numeric_cols:
        summary = get_summary_statistics(df[numeric_cols])
        st.dataframe(summary)
    else:
        st.info("No numeric columns found for summary statistics.")
    
    # Correlation analysis
    st.subheader("Correlation Analysis")
    
    if len(numeric_cols) > 1:
        corr_matrix = get_correlation_matrix(df[numeric_cols])
        
        # Plot the correlation heatmap
        st.write("### Correlation Heatmap")
        fig = plot_correlation_heatmap(corr_matrix)
        st.plotly_chart(fig, use_container_width=True)
        
        # Show correlation values
        st.write("### Correlation Values")
        st.dataframe(corr_matrix)
    else:
        st.info("At least two numeric columns are required for correlation analysis.")
    
    # Data distribution
    st.subheader("Data Distribution")
    
    selected_col = st.selectbox(
        "Select column to view distribution:",
        options=df.columns.tolist()
    )
    
    if selected_col in numeric_cols:
        fig = plot_histogram(df, selected_col)
        st.plotly_chart(fig, use_container_width=True)
        
        # Box plot for the selected column
        fig_box = plot_box(df, selected_col)
        st.plotly_chart(fig_box, use_container_width=True)
    else:
        # For categorical columns
        value_counts = df[selected_col].value_counts().reset_index()
        value_counts.columns = [selected_col, 'Count']
        
        fig = plot_bar(
            data=value_counts,
            x=selected_col,
            y='Count',
            title=f'Distribution of {selected_col}'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Pie chart for categorical data
        fig_pie = plot_pie(df, selected_col)
        st.plotly_chart(fig_pie, use_container_width=True)

def show_visualization_page():
    st.header("📊 Visualization")
    
    if st.session_state.data is None:
        st.warning("Please upload a data file first.")
        return
    
    df = st.session_state.data
    
    # Visualization type selector
    viz_type = st.selectbox(
        "Select visualization type:",
        options=["Scatter Plot", "Bar Chart", "Line Chart", "Histogram", "Box Plot", "Pie Chart"]
    )
    
    # Get numeric and categorical columns
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=['number']).columns.tolist()
    
    # Configure and show the selected visualization
    if viz_type == "Scatter Plot":
        st.subheader("Scatter Plot")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            x_col = st.selectbox("X-axis:", options=numeric_cols, key="scatter_x")
        with col2:
            y_col = st.selectbox("Y-axis:", options=numeric_cols, key="scatter_y")
        with col3:
            color_col = st.selectbox(
                "Color by (optional):",
                options=["None"] + df.columns.tolist(),
                key="scatter_color"
            )
        
        color = None if color_col == "None" else color_col
        fig = plot_scatter(df, x_col, y_col, color)
        st.plotly_chart(fig, use_container_width=True)
        
    elif viz_type == "Bar Chart":
        st.subheader("Bar Chart")
        
        col1, col2 = st.columns(2)
        
        with col1:
            x_col = st.selectbox("X-axis (categorical):", options=df.columns.tolist(), key="bar_x")
        with col2:
            y_col = st.selectbox("Y-axis (numeric):", options=["Count"] + numeric_cols, key="bar_y")
        
        if y_col == "Count":
            # Create count data
            count_data = df[x_col].value_counts().reset_index()
            count_data.columns = [x_col, 'Count']
            fig = plot_bar(count_data, x_col, 'Count', f'Count of {x_col}')
        else:
            fig = plot_bar(df, x_col, y_col, f'{y_col} by {x_col}')
        
        st.plotly_chart(fig, use_container_width=True)
        
    elif viz_type == "Line Chart":
        st.subheader("Line Chart")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            x_col = st.selectbox("X-axis:", options=df.columns.tolist(), key="line_x")
        with col2:
            y_col = st.selectbox("Y-axis:", options=numeric_cols, key="line_y")
        with col3:
            group_col = st.selectbox(
                "Group by (optional):",
                options=["None"] + categorical_cols,
                key="line_group"
            )
        
        group = None if group_col == "None" else group_col
        fig = plot_line(df, x_col, y_col, group)
        st.plotly_chart(fig, use_container_width=True)
        
    elif viz_type == "Histogram":
        st.subheader("Histogram")
        
        col1, col2 = st.columns(2)
        
        with col1:
            hist_col = st.selectbox("Select column:", options=numeric_cols, key="hist_col")
        with col2:
            bin_count = st.slider("Number of bins:", min_value=5, max_value=100, value=20)
        
        fig = plot_histogram(df, hist_col, bin_count)
        st.plotly_chart(fig, use_container_width=True)
        
    elif viz_type == "Box Plot":
        st.subheader("Box Plot")
        
        col1, col2 = st.columns(2)
        
        with col1:
            y_col = st.selectbox("Y-axis (numeric):", options=numeric_cols, key="box_y")
        with col2:
            x_col = st.selectbox(
                "X-axis (categorical, optional):",
                options=["None"] + categorical_cols,
                key="box_x"
            )
        
        x = None if x_col == "None" else x_col
        fig = plot_box(df, y_col, x)
        st.plotly_chart(fig, use_container_width=True)
        
    elif viz_type == "Pie Chart":
        st.subheader("Pie Chart")
        
        pie_col = st.selectbox("Select column:", options=df.columns.tolist(), key="pie_col")
        fig = plot_pie(df, pie_col)
        st.plotly_chart(fig, use_container_width=True)
    
    # Share visualization
    st.subheader("Share Visualization")
    
    # Generate a share code for the current state
    if st.button("Generate Shareable Link"):
        share_code = generate_share_code()
        share_link = f"http://localhost:5000/?share_code={share_code}"
        st.success("Share the following link:")
        st.code(share_link)
    
    # Download visualization
    st.download_button(
        label="Download Visualization",
        data=json.dumps({"type": "visualization_data"}),  # This would be replaced with actual plot data
        file_name=f"{viz_type.lower().replace(' ', '_')}.json",
        mime="application/json"
    )

def show_chat_page():
    st.header("🤖 Data Chat")
    
    if st.session_state.data is None:
        st.warning("Please upload a data file first.")
        return
    
    df = st.session_state.data
    
    st.write("""
    Ask questions about your data in natural language. Examples:
    - "What's the average value of column X?"
    - "Show me the correlation between X and Y"
    - "Plot a histogram of column Z"
    - "Which rows have the highest values in column A?"
    """)
    
    # Display chat history
    chat_container = st.container()
    
    with chat_container:
        for chat in st.session_state.chat_history:
            if chat["role"] == "user":
                st.write(f"**You:** {chat['content']}")
            else:
                st.write(f"**Assistant:** {chat['content']}")
                if "chart" in chat:
                    st.plotly_chart(chat["chart"])
    
    # Query input
    user_query = st.text_input("Ask a question about your data:", key="nlp_query")
    
    if st.button("Submit") and user_query:
        with st.spinner("Processing your question..."):
            # Add user query to chat history
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_query
            })
            
            # Process the NLP query using OpenAI
            try:
                response, chart = process_nlp_query(user_query, df)
                
                # Add assistant response to chat history
                chat_response = {
                    "role": "assistant",
                    "content": response
                }
                
                if chart is not None:
                    chat_response["chart"] = chart
                
                st.session_state.chat_history.append(chat_response)
                
                # Rerun to update the chat display
                st.rerun()
                
            except Exception as e:
                error_message = f"Error processing your question: {str(e)}"
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": error_message
                })
                st.error(error_message)
                st.rerun()

def show_sql_server_uml_page():
    st.header("🔄 SQL Server UML Diagram Generator")
    
    st.write("""
    This tool helps you connect to SQL Server databases, visualize their structure, 
    analyze database design, and generate Entity Framework code.
    """)
    
    # Create tabs for the different steps
    connection_tab, diagram_tab, analysis_tab, code_tab = st.tabs([
        "1. Connect to Database", 
        "2. Generate UML Diagram", 
        "3. Database Analysis", 
        "4. Entity Framework Code"
    ])
    
    # 1. Connection Tab
    with connection_tab:
        st.subheader("Connect to SQL Server Database")
        
        # Connection methods
        connection_method = st.radio(
            "Select connection method:",
            ["Connect to existing database", "Import from .bak file"]
        )
        
        if connection_method == "Connect to existing database":
            # Server connection details
            col1, col2 = st.columns(2)
            
            with col1:
                server = st.text_input("Server:", value="localhost")
                auth_type = st.radio(
                    "Authentication:",
                    ["SQL Server Authentication", "Windows Authentication"]
                )
            
            with col2:
                if auth_type == "SQL Server Authentication":
                    username = st.text_input("Username:")
                    password = st.text_input("Password:", type="password")
                    trusted_connection = False
                else:
                    trusted_connection = True
                    username = None
                    password = None
            
            # Test connection
            if st.button("Test Connection"):
                try:
                    if trusted_connection:
                        connection_string = create_connection_string(server, "master", trusted_connection=True)
                    else:
                        connection_string = create_connection_string(server, "master", username, password)
                    
                    success, error = test_connection(connection_string)
                    
                    if success:
                        st.success("Connection successful!")
                        
                        # Get available databases
                        databases = get_available_databases(server, username, password, trusted_connection)
                        
                        if databases:
                            st.write("Available databases:")
                            selected_db = st.selectbox("Select a database:", databases)
                            
                            if st.button("Connect to Database"):
                                with st.spinner("Connecting to database..."):
                                    # Create connection string and engine
                                    if trusted_connection:
                                        conn_string = create_connection_string(server, selected_db, trusted_connection=True)
                                        engine = create_sqlalchemy_engine(server, selected_db, trusted_connection=True)
                                    else:
                                        conn_string = create_connection_string(server, selected_db, username, password)
                                        engine = create_sqlalchemy_engine(server, selected_db, username, password)
                                    
                                    # Store in session state
                                    st.session_state.sql_connection = conn_string
                                    st.session_state.sql_engine = engine
                                    
                                    # Extract schema
                                    with st.spinner("Extracting database schema..."):
                                        try:
                                            schema = get_full_schema(engine)
                                            st.session_state.db_schema = schema
                                            
                                            # Generate recommendations
                                            recommendations = analyze_database(schema)
                                            st.session_state.recommendations = recommendations
                                            
                                            # Generate Entity Framework code
                                            code_files = generate_ef_code(schema)
                                            st.session_state.code_files = code_files
                                            
                                            st.success(f"Successfully connected to {selected_db} and extracted schema!")
                                            st.info("Now go to the 'Generate UML Diagram' tab to visualize the database structure.")
                                        except Exception as e:
                                            st.error(f"Error extracting schema: {str(e)}")
                        else:
                            st.warning("No user databases found on the server.")
                    else:
                        st.error(f"Connection failed: {error}")
                except Exception as e:
                    st.error(f"Error connecting to SQL Server: {str(e)}")
        
        elif connection_method == "Import from .bak file":
            st.write("Upload a SQL Server backup (.bak) file:")
            
            # Server connection details for restore
            col1, col2 = st.columns(2)
            
            with col1:
                restore_server = st.text_input("Server for restore:", value="localhost")
                auth_type = st.radio(
                    "Authentication for restore:",
                    ["SQL Server Authentication", "Windows Authentication"]
                )
            
            with col2:
                if auth_type == "SQL Server Authentication":
                    restore_username = st.text_input("Username for restore:")
                    restore_password = st.text_input("Password for restore:", type="password")
                    restore_trusted = False
                else:
                    restore_trusted = True
                    restore_username = None
                    restore_password = None
            
            # New database name
            restore_db_name = st.text_input("New database name:", value="RestoredDB")
            
            # Upload backup file
            bak_file = st.file_uploader("Upload .bak file:", type=["bak"])
            
            if bak_file is not None and st.button("Restore Database"):
                with st.spinner("Saving and restoring backup file..."):
                    try:
                        # Save the uploaded .bak file
                        backup_path = save_uploaded_bak(bak_file)
                        
                        if backup_path:
                            # Restore the database
                            success = restore_database_from_backup(
                                restore_server, 
                                restore_db_name, 
                                backup_path, 
                                restore_username, 
                                restore_password, 
                                restore_trusted
                            )
                            
                            if success:
                                st.success(f"Database restored successfully as {restore_db_name}!")
                                
                                # Connect to the restored database
                                with st.spinner("Connecting to restored database..."):
                                    try:
                                        # Create connection string and engine
                                        if restore_trusted:
                                            conn_string = create_connection_string(restore_server, restore_db_name, trusted_connection=True)
                                            engine = create_sqlalchemy_engine(restore_server, restore_db_name, trusted_connection=True)
                                        else:
                                            conn_string = create_connection_string(restore_server, restore_db_name, restore_username, restore_password)
                                            engine = create_sqlalchemy_engine(restore_server, restore_db_name, restore_username, restore_password)
                                        
                                        # Store in session state
                                        st.session_state.sql_connection = conn_string
                                        st.session_state.sql_engine = engine
                                        
                                        # Extract schema
                                        with st.spinner("Extracting database schema..."):
                                            try:
                                                schema = get_full_schema(engine)
                                                st.session_state.db_schema = schema
                                                
                                                # Generate recommendations
                                                recommendations = analyze_database(schema)
                                                st.session_state.recommendations = recommendations
                                                
                                                # Generate Entity Framework code
                                                code_files = generate_ef_code(schema)
                                                st.session_state.code_files = code_files
                                                
                                                st.success(f"Successfully connected to restored database and extracted schema!")
                                                st.info("Now go to the 'Generate UML Diagram' tab to visualize the database structure.")
                                            except Exception as e:
                                                st.error(f"Error extracting schema: {str(e)}")
                                    except Exception as e:
                                        st.error(f"Error connecting to restored database: {str(e)}")
                            else:
                                st.error("Failed to restore database. Check the error message above.")
                        else:
                            st.error("Failed to save the uploaded .bak file.")
                    except Exception as e:
                        st.error(f"Error restoring database: {str(e)}")
    
    # 2. UML Diagram Tab
    with diagram_tab:
        st.subheader("Generate UML Diagram")
        
        if st.session_state.db_schema is None:
            st.warning("Please connect to a database in the 'Connect to Database' tab first.")
        else:
            schema = st.session_state.db_schema
            
            # Diagram options
            st.write("### Diagram Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                include_tables = st.checkbox("Include Tables", value=True)
                include_views = st.checkbox("Include Views", value=True)
            
            with col2:
                include_procedures = st.checkbox("Include Stored Procedures", value=False)
                include_functions = st.checkbox("Include Functions", value=False)
            
            if st.button("Generate Diagram"):
                with st.spinner("Generating UML diagram..."):
                    try:
                        # Display the diagram
                        display_uml_in_streamlit(
                            schema, 
                            include_tables, 
                            include_views, 
                            include_procedures, 
                            include_functions
                        )
                        
                        # Display legend
                        st.markdown(get_uml_legend(), unsafe_allow_html=True)
                        
                    except Exception as e:
                        st.error(f"Error generating UML diagram: {str(e)}")
    
    # 3. Database Analysis Tab
    with analysis_tab:
        st.subheader("Database Analysis and Recommendations")
        
        if st.session_state.db_schema is None:
            st.warning("Please connect to a database in the 'Connect to Database' tab first.")
        else:
            schema = st.session_state.db_schema
            
            # Display database metrics
            metrics = get_database_metrics(schema)
            display_database_metrics(metrics)
            
            # Display recommendations
            if st.session_state.recommendations:
                display_recommendations(st.session_state.recommendations)
            else:
                with st.spinner("Analyzing database..."):
                    recommendations = analyze_database(schema)
                    st.session_state.recommendations = recommendations
                    display_recommendations(recommendations)
    
    # 4. Entity Framework Code Tab
    with code_tab:
        st.subheader("Entity Framework Code Generation")
        
        if st.session_state.db_schema is None:
            st.warning("Please connect to a database in the 'Connect to Database' tab first.")
        else:
            schema = st.session_state.db_schema
            
            # EF options
            st.write("### Entity Framework Options")
            
            ef_version = st.radio(
                "Entity Framework Version:",
                ["Entity Framework Core (.NET Core / .NET 5+)", "Entity Framework 6 (.NET Framework)"]
            )
            
            namespace = st.text_input("Namespace:", value="YourNamespace")
            context_name = st.text_input("DbContext Name:", value="ApplicationDbContext")
            
            if st.button("Generate Code"):
                with st.spinner("Generating Entity Framework code..."):
                    try:
                        # Generate EF code
                        if st.session_state.code_files is None:
                            code_files = generate_ef_code(schema)
                            st.session_state.code_files = code_files
                        
                        # Display code preview
                        display_code_preview(st.session_state.code_files)
                        
                    except Exception as e:
                        st.error(f"Error generating Entity Framework code: {str(e)}")

if __name__ == "__main__":
    main()

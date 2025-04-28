import streamlit as st
import pandas as pd
import io
import base64
import os
import json
import time

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
    page_title="SQL Server UML Diagram Generator",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
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
    st.title("🔄 SQL Server UML Diagram Generator")
    
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
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.info(
        "This tool helps database developers visualize database structure, analyze design, "
        "and generate Entity Framework code."
    )

if __name__ == "__main__":
    main()
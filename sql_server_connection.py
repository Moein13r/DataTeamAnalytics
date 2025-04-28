"""
SQL Server Connection Module

This module provides functionality to connect to SQL Server databases,
import backups, and manage database connections.
"""

import os
import tempfile
import pyodbc
import pymssql
import sqlalchemy as sa
from sqlalchemy.engine import URL
import streamlit as st

def create_connection_string(server, database, username=None, password=None, trusted_connection=False, driver=None):
    """
    Create a connection string for SQL Server

    Args:
        server: SQL Server instance name
        database: Database name
        username: SQL Server username (if using SQL authentication)
        password: SQL Server password (if using SQL authentication)
        trusted_connection: Whether to use Windows authentication
        driver: Optional ODBC driver name (will try to auto-detect if not specified)

    Returns:
        str: Connection string
    """
    # Try to find available SQL Server drivers if not specified
    if driver is None:
        try:
            available_drivers = pyodbc.drivers()
            sql_server_drivers = [d for d in available_drivers if 'SQL Server' in d]
            if sql_server_drivers:
                # Prefer newer drivers if available
                for preferred_driver in ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server Native Client 11.0"]:
                    if preferred_driver in sql_server_drivers:
                        driver = preferred_driver
                        break
                if driver is None:
                    # Just use the first one found
                    driver = sql_server_drivers[0]
            else:
                # Default if no SQL Server drivers are found
                driver = "ODBC Driver 17 for SQL Server"
        except:
            # Default if pyodbc.drivers() fails
            driver = "ODBC Driver 17 for SQL Server"
    
    if trusted_connection:
        return f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};Trusted_Connection=yes;"
    else:
        return f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={username};PWD={password};"

def create_sqlalchemy_engine(server, database, username=None, password=None, trusted_connection=False):
    """
    Create a SQLAlchemy engine for SQL Server

    Args:
        server: SQL Server instance name
        database: Database name
        username: SQL Server username (if using SQL authentication)
        password: SQL Server password (if using SQL authentication)
        trusted_connection: Whether to use Windows authentication

    Returns:
        sqlalchemy.engine.Engine: SQLAlchemy engine
    """
    # Get a connection string with auto-detected driver
    conn_str = create_connection_string(server, database, username, password, trusted_connection)
    
    # First attempt: Try using the connection string directly
    try:
        connection_url = URL.create(
            "mssql+pyodbc",
            query={"odbc_connect": conn_str}
        )
        return sa.create_engine(connection_url)
    except:
        # Second attempt: Try using pymssql instead of pyodbc if first attempt fails
        try:
            # pymssql doesn't use ODBC, so we can try this as a fallback
            if trusted_connection:
                connection_url = URL.create(
                    "mssql+pymssql",
                    host=server,
                    database=database,
                    query={"trusted_connection": "yes"}
                )
            else:
                connection_url = URL.create(
                    "mssql+pymssql",
                    username=username,
                    password=password,
                    host=server,
                    database=database
                )
            return sa.create_engine(connection_url)
        except:
            # Last attempt: Fall back to original method with ODBC Driver 18
            if trusted_connection:
                connection_url = URL.create(
                    "mssql+pyodbc",
                    query={"odbc_connect": f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;"}
                )
            else:
                connection_url = URL.create(
                    "mssql+pyodbc",
                    username=username,
                    password=password,
                    host=server,
                    database=database,
                    query={"driver": "ODBC Driver 18 for SQL Server"}
                )
            return sa.create_engine(connection_url)

def test_connection(connection_string):
    """
    Test a SQL Server connection

    Args:
        connection_string: Connection string to test

    Returns:
        bool: True if connection successful, False otherwise
        str: Error message if connection failed
    """
    # First try with pyodbc
    try:
        conn = pyodbc.connect(connection_string)
        conn.close()
        return True, None
    except Exception as pyodbc_error:
        # If pyodbc fails, try to extract server, database, username, password from connection string
        try:
            import re
            server_match = re.search(r"SERVER=([^;]+)", connection_string)
            db_match = re.search(r"DATABASE=([^;]+)", connection_string)
            uid_match = re.search(r"UID=([^;]+)", connection_string)
            pwd_match = re.search(r"PWD=([^;]+)", connection_string)
            trusted_match = re.search(r"Trusted_Connection=yes", connection_string, re.IGNORECASE)
            
            if server_match and db_match:
                server = server_match.group(1)
                database = db_match.group(1)
                
                # Second attempt with pymssql
                try:
                    if trusted_match:
                        conn = pymssql.connect(server=server, database=database, trusted=True)
                    elif uid_match and pwd_match:
                        username = uid_match.group(1)
                        password = pwd_match.group(1)
                        conn = pymssql.connect(server=server, database=database, user=username, password=password)
                    else:
                        raise Exception("Could not extract authentication details from connection string")
                    
                    conn.close()
                    return True, None
                except Exception as pymssql_error:
                    return False, f"Connection failed with both ODBC and pymssql drivers. Errors: {str(pyodbc_error)} and {str(pymssql_error)}"
            else:
                return False, f"Could not parse connection string. Error: {str(pyodbc_error)}"
        except Exception as parse_error:
            return False, f"Connection failed and error parsing connection string. Error: {str(pyodbc_error)}, {str(parse_error)}"

def get_available_databases(server, username=None, password=None, trusted_connection=False):
    """
    Get a list of available databases on the server

    Args:
        server: SQL Server instance name
        username: SQL Server username (if using SQL authentication)
        password: SQL Server password (if using SQL authentication)
        trusted_connection: Whether to use Windows authentication

    Returns:
        list: List of database names
    """
    try:
        if trusted_connection:
            conn = pymssql.connect(server=server, trusted=True)
        else:
            conn = pymssql.connect(server=server, user=username, password=password)
            
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sys.databases WHERE name NOT IN ('master', 'tempdb', 'model', 'msdb')")
        databases = [row[0] for row in cursor.fetchall()]
        conn.close()
        return databases
    except Exception as e:
        st.error(f"Error connecting to SQL Server: {str(e)}")
        return []

def save_uploaded_bak(uploaded_file):
    """
    Save an uploaded .bak file to a temporary location

    Args:
        uploaded_file: The uploaded .bak file

    Returns:
        str: Path to the saved .bak file
    """
    try:
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.bak')
        temp_file.write(uploaded_file.getvalue())
        temp_file.close()
        return temp_file.name
    except Exception as e:
        st.error(f"Error saving backup file: {str(e)}")
        return None

def restore_database_from_backup(server, database_name, backup_path, username=None, password=None, trusted_connection=False):
    """
    Restore a database from a .bak file

    Args:
        server: SQL Server instance name
        database_name: Name for the restored database
        backup_path: Path to the .bak file
        username: SQL Server username (if using SQL authentication)
        password: SQL Server password (if using SQL authentication)
        trusted_connection: Whether to use Windows authentication

    Returns:
        bool: True if restore successful, False otherwise
    """
    try:
        # Create connection
        if trusted_connection:
            conn = pymssql.connect(server=server, trusted=True)
        else:
            conn = pymssql.connect(server=server, user=username, password=password)
            
        cursor = conn.cursor()
        
        # Check if database exists and drop if it does
        cursor.execute(f"IF DB_ID('{database_name}') IS NOT NULL DROP DATABASE [{database_name}]")
        conn.commit()
        
        # Create new database
        cursor.execute(f"CREATE DATABASE [{database_name}]")
        conn.commit()
        
        # Restore database from backup
        restore_query = f"""
        USE [master]
        RESTORE DATABASE [{database_name}] FROM DISK = '{backup_path}'
        WITH REPLACE, RECOVERY
        """
        cursor.execute(restore_query)
        conn.commit()
        conn.close()
        
        # Clean up temporary file
        if os.path.exists(backup_path):
            os.remove(backup_path)
            
        return True
    except Exception as e:
        st.error(f"Error restoring database: {str(e)}")
        return False
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

def create_connection_string(server, database, username=None, password=None, trusted_connection=False):
    """
    Create a connection string for SQL Server

    Args:
        server: SQL Server instance name
        database: Database name
        username: SQL Server username (if using SQL authentication)
        password: SQL Server password (if using SQL authentication)
        trusted_connection: Whether to use Windows authentication

    Returns:
        str: Connection string
    """
    if trusted_connection:
        return f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;"
    else:
        return f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};"

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
    if trusted_connection:
        connection_url = URL.create(
            "mssql+pyodbc",
            query={"odbc_connect": f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;"}
        )
    else:
        connection_url = URL.create(
            "mssql+pyodbc",
            username=username,
            password=password,
            host=server,
            database=database,
            query={"driver": "ODBC Driver 17 for SQL Server"}
        )
    
    return sa.create_engine(connection_url)

def test_connection(connection_string):
    """
    Test a SQL Server connection

    Args:
        connection_string: Connection string to test

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        conn = pyodbc.connect(connection_string)
        conn.close()
        return True
    except Exception as e:
        return False, str(e)

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
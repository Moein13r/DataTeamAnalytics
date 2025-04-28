"""
Database Schema Extractor Module

This module extracts database schema information from SQL Server databases,
including tables, relationships, stored procedures, functions, and views.
"""

import sqlalchemy as sa
from sqlalchemy import inspect
import pandas as pd
import sqlparse
import networkx as nx

def get_tables(engine):
    """
    Get all tables in the database
    
    Args:
        engine: SQLAlchemy engine connected to the database
        
    Returns:
        list: List of table names
    """
    inspector = inspect(engine)
    return inspector.get_table_names()

def get_views(engine):
    """
    Get all views in the database
    
    Args:
        engine: SQLAlchemy engine connected to the database
        
    Returns:
        list: List of view names
    """
    inspector = inspect(engine)
    return inspector.get_view_names()

def get_table_columns(engine, table_name):
    """
    Get columns for a specific table
    
    Args:
        engine: SQLAlchemy engine connected to the database
        table_name: Name of the table
        
    Returns:
        list: List of column details
    """
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)
    return columns

def get_primary_keys(engine, table_name):
    """
    Get primary keys for a specific table
    
    Args:
        engine: SQLAlchemy engine connected to the database
        table_name: Name of the table
        
    Returns:
        list: List of primary key column names
    """
    inspector = inspect(engine)
    pk_constraint = inspector.get_pk_constraint(table_name)
    return pk_constraint.get('constrained_columns', [])

def get_foreign_keys(engine, table_name):
    """
    Get foreign keys for a specific table
    
    Args:
        engine: SQLAlchemy engine connected to the database
        table_name: Name of the table
        
    Returns:
        list: List of foreign key details
    """
    inspector = inspect(engine)
    foreign_keys = inspector.get_foreign_keys(table_name)
    return foreign_keys

def get_relationships(engine):
    """
    Get all relationships between tables in the database
    
    Args:
        engine: SQLAlchemy engine connected to the database
        
    Returns:
        list: List of relationships
    """
    inspector = inspect(engine)
    relationships = []
    
    for table_name in inspector.get_table_names():
        for fk in inspector.get_foreign_keys(table_name):
            relationships.append({
                'source_table': table_name,
                'source_columns': fk['constrained_columns'],
                'target_table': fk['referred_table'],
                'target_columns': fk['referred_columns'],
                'name': fk.get('name', '')
            })
    
    return relationships

def get_stored_procedures(engine):
    """
    Get all stored procedures in the database
    
    Args:
        engine: SQLAlchemy engine connected to the database
        
    Returns:
        dict: Dictionary of procedure names and their definitions
    """
    query = """
    SELECT ROUTINE_NAME, ROUTINE_DEFINITION
    FROM INFORMATION_SCHEMA.ROUTINES
    WHERE ROUTINE_TYPE = 'PROCEDURE'
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(sa.text(query))
            procedures = {row[0]: row[1] for row in result}
        return procedures
    except Exception as e:
        print(f"Error getting stored procedures: {str(e)}")
        return {}

def get_functions(engine):
    """
    Get all functions in the database
    
    Args:
        engine: SQLAlchemy engine connected to the database
        
    Returns:
        dict: Dictionary of function names and their definitions
    """
    query = """
    SELECT ROUTINE_NAME, ROUTINE_DEFINITION
    FROM INFORMATION_SCHEMA.ROUTINES
    WHERE ROUTINE_TYPE = 'FUNCTION'
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(sa.text(query))
            functions = {row[0]: row[1] for row in result}
        return functions
    except Exception as e:
        print(f"Error getting functions: {str(e)}")
        return {}

def get_view_definitions(engine):
    """
    Get definitions for all views in the database
    
    Args:
        engine: SQLAlchemy engine connected to the database
        
    Returns:
        dict: Dictionary of view names and their definitions
    """
    query = """
    SELECT TABLE_NAME, VIEW_DEFINITION
    FROM INFORMATION_SCHEMA.VIEWS
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(sa.text(query))
            views = {row[0]: row[1] for row in result}
        return views
    except Exception as e:
        print(f"Error getting view definitions: {str(e)}")
        return {}

def get_full_schema(engine):
    """
    Get the full database schema
    
    Args:
        engine: SQLAlchemy engine connected to the database
        
    Returns:
        dict: Dictionary containing the full database schema
    """
    schema = {
        'tables': {},
        'views': {},
        'relationships': [],
        'stored_procedures': {},
        'functions': {}
    }
    
    inspector = inspect(engine)
    
    # Get tables and their columns
    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        primary_keys = inspector.get_pk_constraint(table_name).get('constrained_columns', [])
        foreign_keys = inspector.get_foreign_keys(table_name)
        
        schema['tables'][table_name] = {
            'columns': columns,
            'primary_keys': primary_keys,
            'foreign_keys': foreign_keys
        }
    
    # Get relationships
    schema['relationships'] = get_relationships(engine)
    
    # Get views
    views = get_view_definitions(engine)
    schema['views'] = views
    
    # Get stored procedures
    schema['stored_procedures'] = get_stored_procedures(engine)
    
    # Get functions
    schema['functions'] = get_functions(engine)
    
    return schema

def create_dependency_graph(schema):
    """
    Create a dependency graph of tables, views, stored procedures, and functions
    
    Args:
        schema: Full database schema
        
    Returns:
        networkx.DiGraph: Directed graph representing dependencies
    """
    G = nx.DiGraph()
    
    # Add tables and views as nodes
    for table_name in schema['tables'].keys():
        G.add_node(table_name, type='table')
    
    for view_name in schema['views'].keys():
        G.add_node(view_name, type='view')
    
    # Add relationships as edges
    for relationship in schema['relationships']:
        source = relationship['source_table']
        target = relationship['target_table']
        G.add_edge(source, target, type='foreign_key')
    
    # Analyze view dependencies (this is a simplified approach)
    for view_name, view_def in schema['views'].items():
        if view_def:
            # Find referenced tables in the view definition
            for table_name in schema['tables'].keys():
                if f" {table_name} " in view_def or f"[{table_name}]" in view_def:
                    G.add_edge(view_name, table_name, type='view_dependency')
    
    # Analyze stored procedure and function dependencies (simplified)
    for sp_name, sp_def in schema['stored_procedures'].items():
        if sp_def:
            G.add_node(sp_name, type='stored_procedure')
            # Find referenced tables in the stored procedure
            for table_name in schema['tables'].keys():
                if f" {table_name} " in sp_def or f"[{table_name}]" in sp_def:
                    G.add_edge(sp_name, table_name, type='proc_dependency')
    
    for func_name, func_def in schema['functions'].items():
        if func_def:
            G.add_node(func_name, type='function')
            # Find referenced tables in the function
            for table_name in schema['tables'].keys():
                if f" {table_name} " in func_def or f"[{table_name}]" in func_def:
                    G.add_edge(func_name, table_name, type='func_dependency')
    
    return G

def format_sql(sql_text):
    """
    Format SQL text to be more readable
    
    Args:
        sql_text: SQL text to format
        
    Returns:
        str: Formatted SQL text
    """
    if sql_text:
        try:
            return sqlparse.format(
                sql_text,
                reindent=True,
                keyword_case='upper',
                strip_comments=False
            )
        except Exception:
            return sql_text
    return ""
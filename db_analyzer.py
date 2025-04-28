"""
Database Analyzer Module

This module analyzes database schema and provides recommendations for improvements.
"""

import networkx as nx
import pandas as pd
import sqlalchemy as sa
from sqlalchemy import inspect
import streamlit as st

def analyze_table_structure(schema):
    """
    Analyze table structure and provide recommendations
    
    Args:
        schema: Full database schema
        
    Returns:
        list: List of recommendations
    """
    recommendations = []
    
    for table_name, table_info in schema['tables'].items():
        columns = table_info['columns']
        primary_keys = table_info['primary_keys']
        foreign_keys = table_info['foreign_keys']
        
        # Check if table has a primary key
        if not primary_keys:
            recommendations.append({
                'type': 'primary_key',
                'severity': 'high',
                'object': table_name,
                'message': f"Table '{table_name}' does not have a primary key. Consider adding one for better data integrity and performance."
            })
        
        # Check if there are any non-nullable columns without default values
        for column in columns:
            if not column.get('nullable', True) and 'default' not in column:
                recommendations.append({
                    'type': 'column_default',
                    'severity': 'medium',
                    'object': f"{table_name}.{column['name']}",
                    'message': f"Non-nullable column '{column['name']}' in table '{table_name}' has no default value. Consider adding a default value for easier data insertion."
                })
        
        # Check for potential composite keys
        if len(primary_keys) > 2:
            recommendations.append({
                'type': 'composite_key',
                'severity': 'low',
                'object': table_name,
                'message': f"Table '{table_name}' has a complex composite key with {len(primary_keys)} columns. Consider simplifying by using a surrogate key if appropriate."
            })
        
        # Check for potential naming issues
        column_names = [col['name'] for col in columns]
        if 'id' in column_names and 'id' not in primary_keys:
            recommendations.append({
                'type': 'naming_convention',
                'severity': 'low',
                'object': f"{table_name}.id",
                'message': f"Column 'id' in table '{table_name}' is not a primary key. Consider renaming to avoid confusion."
            })
        
        # Check for potential indexing needs
        for fk in foreign_keys:
            for col in fk['constrained_columns']:
                if col not in primary_keys:  # Foreign keys that aren't part of the primary key should be indexed
                    recommendations.append({
                        'type': 'index',
                        'severity': 'medium',
                        'object': f"{table_name}.{col}",
                        'message': f"Consider adding an index on foreign key column '{col}' in table '{table_name}' for better query performance."
                    })
    
    return recommendations

def analyze_relationships(schema):
    """
    Analyze table relationships and provide recommendations
    
    Args:
        schema: Full database schema
        
    Returns:
        list: List of recommendations
    """
    recommendations = []
    
    # Find tables without relationships
    table_names = set(schema['tables'].keys())
    tables_with_relationships = set()
    
    for rel in schema['relationships']:
        tables_with_relationships.add(rel['source_table'])
        tables_with_relationships.add(rel['target_table'])
    
    isolated_tables = table_names - tables_with_relationships
    for table in isolated_tables:
        recommendations.append({
            'type': 'isolated_table',
            'severity': 'medium',
            'object': table,
            'message': f"Table '{table}' has no relationships with other tables. This might indicate a design issue or an orphaned table."
        })
    
    # Check for potential many-to-many relationships without junction tables
    relationship_counts = {}
    for rel in schema['relationships']:
        source = rel['source_table']
        target = rel['target_table']
        
        key = (source, target)
        if key in relationship_counts:
            relationship_counts[key] += 1
        else:
            relationship_counts[key] = 1
        
        # If two tables have multiple relationships, it might indicate a missing junction table
        if relationship_counts[key] > 1:
            recommendations.append({
                'type': 'junction_table',
                'severity': 'medium',
                'object': f"{source} - {target}",
                'message': f"Tables '{source}' and '{target}' have multiple relationships. Consider using a junction table for cleaner many-to-many relationship modeling."
            })
    
    return recommendations

def analyze_dependency_cycles(schema):
    """
    Analyze dependency cycles in the database
    
    Args:
        schema: Full database schema
        
    Returns:
        list: List of recommendations
    """
    recommendations = []
    
    # Create a directed graph of table relationships
    G = nx.DiGraph()
    
    # Add tables as nodes
    for table_name in schema['tables'].keys():
        G.add_node(table_name)
    
    # Add relationships as edges
    for rel in schema['relationships']:
        source = rel['source_table']
        target = rel['target_table']
        G.add_edge(source, target)
    
    # Check for cycles
    try:
        cycles = list(nx.simple_cycles(G))
        for cycle in cycles:
            cycle_str = " → ".join(cycle)
            recommendations.append({
                'type': 'dependency_cycle',
                'severity': 'high',
                'object': cycle_str,
                'message': f"Detected a dependency cycle: {cycle_str}. This may cause issues with referential integrity and data insertion. Consider redesigning the schema to eliminate this cycle."
            })
    except nx.NetworkXNoCycle:
        pass  # No cycles detected
    
    return recommendations

def analyze_stored_procedures(schema):
    """
    Analyze stored procedures and provide recommendations
    
    Args:
        schema: Full database schema
        
    Returns:
        list: List of recommendations
    """
    recommendations = []
    
    for proc_name, proc_def in schema['stored_procedures'].items():
        if not proc_def:
            continue
            
        # Check for potential SQL injection vulnerabilities
        if "EXEC(" in proc_def or "EXECUTE(" in proc_def or "sp_executesql" in proc_def:
            recommendations.append({
                'type': 'security',
                'severity': 'high',
                'object': proc_name,
                'message': f"Stored procedure '{proc_name}' uses dynamic SQL execution, which could be vulnerable to SQL injection. Consider using parameterized queries."
            })
        
        # Check for potentially inefficient queries
        if "SELECT *" in proc_def:
            recommendations.append({
                'type': 'performance',
                'severity': 'medium',
                'object': proc_name,
                'message': f"Stored procedure '{proc_name}' uses 'SELECT *', which may retrieve unnecessary columns. Consider specifying only needed columns."
            })
            
        # Check for cursors (potential performance issue)
        if "DECLARE CURSOR" in proc_def or "CURSOR FOR" in proc_def:
            recommendations.append({
                'type': 'performance',
                'severity': 'medium',
                'object': proc_name,
                'message': f"Stored procedure '{proc_name}' uses cursors, which can be inefficient. Consider using set-based operations instead."
            })
            
        # Check for transaction handling
        if "BEGIN TRANSACTION" in proc_def and ("COMMIT" not in proc_def or "ROLLBACK" not in proc_def):
            recommendations.append({
                'type': 'reliability',
                'severity': 'high',
                'object': proc_name,
                'message': f"Stored procedure '{proc_name}' begins a transaction but may not properly commit or rollback in all code paths. This could lead to open transactions or deadlocks."
            })
    
    return recommendations

def analyze_functions(schema):
    """
    Analyze functions and provide recommendations
    
    Args:
        schema: Full database schema
        
    Returns:
        list: List of recommendations
    """
    recommendations = []
    
    for func_name, func_def in schema['functions'].items():
        if not func_def:
            continue
            
        # Check for potentially inefficient queries
        if "SELECT *" in func_def:
            recommendations.append({
                'type': 'performance',
                'severity': 'medium',
                'object': func_name,
                'message': f"Function '{func_name}' uses 'SELECT *', which may retrieve unnecessary columns. Consider specifying only needed columns."
            })
            
        # Check for cursors (potential performance issue)
        if "DECLARE CURSOR" in func_def or "CURSOR FOR" in func_def:
            recommendations.append({
                'type': 'performance',
                'severity': 'medium',
                'object': func_name,
                'message': f"Function '{func_name}' uses cursors, which can be inefficient. Consider using set-based operations instead."
            })
            
        # Check if function might modify data (anti-pattern)
        if "INSERT" in func_def or "UPDATE" in func_def or "DELETE" in func_def:
            recommendations.append({
                'type': 'design',
                'severity': 'high',
                'object': func_name,
                'message': f"Function '{func_name}' appears to modify data. This is generally considered an anti-pattern. Consider using a stored procedure instead."
            })
    
    return recommendations

def analyze_views(schema):
    """
    Analyze views and provide recommendations
    
    Args:
        schema: Full database schema
        
    Returns:
        list: List of recommendations
    """
    recommendations = []
    
    for view_name, view_def in schema['views'].items():
        if not view_def:
            continue
            
        # Check for potentially inefficient queries
        if "SELECT *" in view_def:
            recommendations.append({
                'type': 'performance',
                'severity': 'medium',
                'object': view_name,
                'message': f"View '{view_name}' uses 'SELECT *', which may retrieve unnecessary columns. Consider specifying only needed columns."
            })
            
        # Check for subqueries in the SELECT clause (potential performance issue)
        if "SELECT " in view_def and "(" in view_def and "SELECT" in view_def.split("FROM")[0]:
            recommendations.append({
                'type': 'performance',
                'severity': 'low',
                'object': view_name,
                'message': f"View '{view_name}' may contain subqueries in the SELECT clause, which can impact performance. Consider restructuring if possible."
            })
    
    return recommendations

def analyze_database(schema):
    """
    Analyze the entire database schema and provide comprehensive recommendations
    
    Args:
        schema: Full database schema
        
    Returns:
        list: List of recommendations
    """
    all_recommendations = []
    
    # Table structure analysis
    all_recommendations.extend(analyze_table_structure(schema))
    
    # Relationship analysis
    all_recommendations.extend(analyze_relationships(schema))
    
    # Dependency cycle analysis
    all_recommendations.extend(analyze_dependency_cycles(schema))
    
    # Stored procedure analysis
    all_recommendations.extend(analyze_stored_procedures(schema))
    
    # Function analysis
    all_recommendations.extend(analyze_functions(schema))
    
    # View analysis
    all_recommendations.extend(analyze_views(schema))
    
    # Sort recommendations by severity
    severity_order = {'high': 0, 'medium': 1, 'low': 2}
    all_recommendations.sort(key=lambda x: severity_order[x['severity']])
    
    return all_recommendations

def display_recommendations(recommendations):
    """
    Display recommendations in Streamlit
    
    Args:
        recommendations: List of recommendations
    """
    if not recommendations:
        st.info("No recommendations found. Your database schema looks good!")
        return
    
    st.subheader("Database Recommendations")
    
    # Group recommendations by severity
    high_severity = [r for r in recommendations if r['severity'] == 'high']
    medium_severity = [r for r in recommendations if r['severity'] == 'medium']
    low_severity = [r for r in recommendations if r['severity'] == 'low']
    
    # Display high severity recommendations
    if high_severity:
        st.markdown("### 🚨 High Priority Recommendations")
        for rec in high_severity:
            with st.expander(f"{rec['object']} - {rec['type']}"):
                st.markdown(f"**Object:** {rec['object']}")
                st.markdown(f"**Issue Type:** {rec['type']}")
                st.markdown(f"**Recommendation:** {rec['message']}")
    
    # Display medium severity recommendations
    if medium_severity:
        st.markdown("### ⚠️ Medium Priority Recommendations")
        for rec in medium_severity:
            with st.expander(f"{rec['object']} - {rec['type']}"):
                st.markdown(f"**Object:** {rec['object']}")
                st.markdown(f"**Issue Type:** {rec['type']}")
                st.markdown(f"**Recommendation:** {rec['message']}")
    
    # Display low severity recommendations
    if low_severity:
        st.markdown("### ℹ️ Low Priority Recommendations")
        for rec in low_severity:
            with st.expander(f"{rec['object']} - {rec['type']}"):
                st.markdown(f"**Object:** {rec['object']}")
                st.markdown(f"**Issue Type:** {rec['type']}")
                st.markdown(f"**Recommendation:** {rec['message']}")

def get_database_metrics(schema):
    """
    Calculate database metrics
    
    Args:
        schema: Full database schema
        
    Returns:
        dict: Dictionary of database metrics
    """
    metrics = {}
    
    # Basic counts
    metrics['table_count'] = len(schema['tables'])
    metrics['view_count'] = len(schema['views'])
    metrics['stored_procedure_count'] = len(schema['stored_procedures'])
    metrics['function_count'] = len(schema['functions'])
    metrics['relationship_count'] = len(schema['relationships'])
    
    # Column metrics
    total_columns = 0
    primary_key_count = 0
    foreign_key_count = 0
    nullable_column_count = 0
    
    for table_name, table_info in schema['tables'].items():
        total_columns += len(table_info['columns'])
        primary_key_count += len(table_info['primary_keys'])
        
        # Count foreign key columns
        for fk in table_info['foreign_keys']:
            foreign_key_count += len(fk['constrained_columns'])
        
        # Count nullable columns
        for column in table_info['columns']:
            if column.get('nullable', True):
                nullable_column_count += 1
    
    metrics['total_columns'] = total_columns
    metrics['primary_key_count'] = primary_key_count
    metrics['foreign_key_count'] = foreign_key_count
    metrics['nullable_column_count'] = nullable_column_count
    
    # Calculate dependency metrics using NetworkX
    G = nx.DiGraph()
    
    # Add tables as nodes
    for table_name in schema['tables'].keys():
        G.add_node(table_name)
    
    # Add relationships as edges
    for rel in schema['relationships']:
        source = rel['source_table']
        target = rel['target_table']
        G.add_edge(source, target)
    
    # Calculate metrics
    try:
        metrics['avg_in_degree'] = sum(dict(G.in_degree()).values()) / (len(G) or 1)
        metrics['avg_out_degree'] = sum(dict(G.out_degree()).values()) / (len(G) or 1)
        metrics['density'] = nx.density(G)
        
        # Check if the graph is connected
        if len(G) > 0:
            UG = G.to_undirected()
            metrics['connected_components'] = nx.number_connected_components(UG)
        else:
            metrics['connected_components'] = 0
            
    except Exception as e:
        print(f"Error calculating graph metrics: {str(e)}")
        metrics['avg_in_degree'] = 0
        metrics['avg_out_degree'] = 0
        metrics['density'] = 0
        metrics['connected_components'] = 0
    
    return metrics

def display_database_metrics(metrics):
    """
    Display database metrics in Streamlit
    
    Args:
        metrics: Dictionary of database metrics
    """
    st.subheader("Database Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Tables", metrics['table_count'])
        st.metric("Stored Procedures", metrics['stored_procedure_count'])
        st.metric("Total Columns", metrics['total_columns'])
    
    with col2:
        st.metric("Views", metrics['view_count'])
        st.metric("Functions", metrics['function_count'])
        st.metric("Primary Keys", metrics['primary_key_count'])
    
    with col3:
        st.metric("Relationships", metrics['relationship_count'])
        st.metric("Foreign Keys", metrics['foreign_key_count'])
        st.metric("Nullable Columns", metrics['nullable_column_count'])
    
    # Display graph metrics
    st.subheader("Relationship Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Avg. Incoming References", round(metrics['avg_in_degree'], 2))
    
    with col2:
        st.metric("Avg. Outgoing References", round(metrics['avg_out_degree'], 2))
    
    with col3:
        st.metric("Connected Components", metrics['connected_components'])
        
    st.metric("Graph Density", round(metrics['density'], 4), 
              help="Density closer to 1 indicates a highly interconnected database")
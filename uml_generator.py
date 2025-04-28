"""
UML Diagram Generator Module

This module generates UML diagrams from database schema information.
"""

import pydot
import networkx as nx
import base64
from io import BytesIO
import random
import json
import streamlit as st

# Define colors for different database objects
COLORS = {
    'table': {
        'header': '#3498db',  # Blue
        'body': '#d6eaf8'
    },
    'view': {
        'header': '#2ecc71',  # Green
        'body': '#d5f5e3'
    },
    'stored_procedure': {
        'header': '#9b59b6',  # Purple
        'body': '#e8daef'
    },
    'function': {
        'header': '#f1c40f',  # Yellow
        'body': '#fcf3cf'
    }
}

# Define relationship colors and styles
RELATIONSHIP_STYLES = {
    'foreign_key': {
        'color': '#e74c3c',  # Red
        'style': 'solid',
        'arrowhead': 'normal'
    },
    'view_dependency': {
        'color': '#16a085',  # Teal
        'style': 'dashed',
        'arrowhead': 'vee'
    },
    'proc_dependency': {
        'color': '#8e44ad',  # Dark Purple
        'style': 'dotted',
        'arrowhead': 'diamond'
    },
    'func_dependency': {
        'color': '#d35400',  # Orange
        'style': 'dotted',
        'arrowhead': 'odiamond'
    }
}

def random_position():
    """Generate random position for graph nodes"""
    return (random.uniform(0, 1000), random.uniform(0, 1000))

def create_table_uml(table_name, columns, primary_keys, foreign_keys):
    """
    Create UML representation of a table
    
    Args:
        table_name: Name of the table
        columns: List of column details
        primary_keys: List of primary key column names
        foreign_keys: List of foreign key details
        
    Returns:
        str: HTML/UML representation of the table
    """
    html = f"""<
    <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="{COLORS['table']['body']}">
    <TR><TD COLSPAN="3" BGCOLOR="{COLORS['table']['header']}"><FONT COLOR="white"><B>{table_name}</B></FONT></TD></TR>
    <TR><TD><B>Column</B></TD><TD><B>Type</B></TD><TD><B>Attributes</B></TD></TR>
    """
    
    for column in columns:
        col_name = column['name']
        col_type = str(column['type'])
        
        # Determine column attributes (PK, FK, nullable)
        attributes = []
        if col_name in primary_keys:
            attributes.append('PK')
        
        # Check if column is part of any foreign key
        for fk in foreign_keys:
            if col_name in fk['constrained_columns']:
                attributes.append(f"FK → {fk['referred_table']}")
        
        if not column.get('nullable', True):
            attributes.append('NOT NULL')
            
        attr_text = ', '.join(attributes)
        
        html += f"""<TR><TD>{col_name}</TD><TD>{col_type}</TD><TD>{attr_text}</TD></TR>"""
    
    html += '</TABLE>>'
    return html

def create_view_uml(view_name):
    """
    Create UML representation of a view
    
    Args:
        view_name: Name of the view
        
    Returns:
        str: HTML/UML representation of the view
    """
    html = f"""<
    <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="{COLORS['view']['body']}">
    <TR><TD BGCOLOR="{COLORS['view']['header']}"><FONT COLOR="white"><B>{view_name}</B></FONT></TD></TR>
    <TR><TD>View</TD></TR>
    </TABLE>
    >>"""
    return html

def create_procedure_uml(proc_name):
    """
    Create UML representation of a stored procedure
    
    Args:
        proc_name: Name of the stored procedure
        
    Returns:
        str: HTML/UML representation of the stored procedure
    """
    html = f"""<
    <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="{COLORS['stored_procedure']['body']}">
    <TR><TD BGCOLOR="{COLORS['stored_procedure']['header']}"><FONT COLOR="white"><B>{proc_name}</B></FONT></TD></TR>
    <TR><TD>Stored Procedure</TD></TR>
    </TABLE>
    >>"""
    return html

def create_function_uml(func_name):
    """
    Create UML representation of a function
    
    Args:
        func_name: Name of the function
        
    Returns:
        str: HTML/UML representation of the function
    """
    html = f"""<
    <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="{COLORS['function']['body']}">
    <TR><TD BGCOLOR="{COLORS['function']['header']}"><FONT COLOR="white"><B>{func_name}</B></FONT></TD></TR>
    <TR><TD>Function</TD></TR>
    </TABLE>
    >>"""
    return html

def generate_database_uml(schema, include_tables=True, include_views=True, 
                          include_procedures=False, include_functions=False):
    """
    Generate a UML diagram of the database schema
    
    Args:
        schema: Full database schema
        include_tables: Whether to include tables in the diagram
        include_views: Whether to include views in the diagram
        include_procedures: Whether to include stored procedures in the diagram
        include_functions: Whether to include functions in the diagram
        
    Returns:
        pydot.Dot: UML diagram as a Dot graph
    """
    graph = pydot.Dot(graph_type='digraph', rankdir='LR', splines='ortho')
    graph.set_node_defaults(shape='plaintext')
    
    # Add tables
    if include_tables:
        for table_name, table_info in schema['tables'].items():
            node = pydot.Node(
                table_name, 
                label=create_table_uml(
                    table_name, 
                    table_info['columns'], 
                    table_info['primary_keys'], 
                    table_info['foreign_keys']
                )
            )
            graph.add_node(node)
    
    # Add views
    if include_views:
        for view_name in schema['views'].keys():
            node = pydot.Node(view_name, label=create_view_uml(view_name))
            graph.add_node(node)
    
    # Add stored procedures
    if include_procedures:
        for proc_name in schema['stored_procedures'].keys():
            node = pydot.Node(proc_name, label=create_procedure_uml(proc_name))
            graph.add_node(node)
    
    # Add functions
    if include_functions:
        for func_name in schema['functions'].keys():
            node = pydot.Node(func_name, label=create_function_uml(func_name))
            graph.add_node(node)
    
    # Add relationships
    for rel in schema['relationships']:
        if include_tables:
            source = rel['source_table']
            target = rel['target_table']
            
            # Use the first column as the label if there are multiple columns
            label = f"{rel['source_columns'][0]} → {rel['target_columns'][0]}"
            
            edge = pydot.Edge(
                source, 
                target, 
                label=label,
                color=RELATIONSHIP_STYLES['foreign_key']['color'],
                style=RELATIONSHIP_STYLES['foreign_key']['style'],
                arrowhead=RELATIONSHIP_STYLES['foreign_key']['arrowhead']
            )
            graph.add_edge(edge)
    
    # Add dependencies
    dependency_graph = nx.DiGraph()
    
    # Build dependency graph from schema
    for view_name, view_def in schema['views'].items():
        if include_views and view_def:
            for table_name in schema['tables'].keys():
                if include_tables and (f" {table_name} " in view_def or f"[{table_name}]" in view_def):
                    edge = pydot.Edge(
                        view_name,
                        table_name,
                        color=RELATIONSHIP_STYLES['view_dependency']['color'],
                        style=RELATIONSHIP_STYLES['view_dependency']['style'],
                        arrowhead=RELATIONSHIP_STYLES['view_dependency']['arrowhead']
                    )
                    graph.add_edge(edge)
    
    for proc_name, proc_def in schema['stored_procedures'].items():
        if include_procedures and proc_def:
            for table_name in schema['tables'].keys():
                if include_tables and (f" {table_name} " in proc_def or f"[{table_name}]" in proc_def):
                    edge = pydot.Edge(
                        proc_name,
                        table_name,
                        color=RELATIONSHIP_STYLES['proc_dependency']['color'],
                        style=RELATIONSHIP_STYLES['proc_dependency']['style'],
                        arrowhead=RELATIONSHIP_STYLES['proc_dependency']['arrowhead']
                    )
                    graph.add_edge(edge)
    
    for func_name, func_def in schema['functions'].items():
        if include_functions and func_def:
            for table_name in schema['tables'].keys():
                if include_tables and (f" {table_name} " in func_def or f"[{table_name}]" in func_def):
                    edge = pydot.Edge(
                        func_name,
                        table_name,
                        color=RELATIONSHIP_STYLES['func_dependency']['color'],
                        style=RELATIONSHIP_STYLES['func_dependency']['style'],
                        arrowhead=RELATIONSHIP_STYLES['func_dependency']['arrowhead']
                    )
                    graph.add_edge(edge)
    
    return graph

def save_uml_as_image(graph, format='png'):
    """
    Save the UML diagram as an image
    
    Args:
        graph: pydot.Dot graph
        format: Image format (png, svg, pdf)
        
    Returns:
        bytes: Image data
    """
    if format == 'png':
        return graph.create_png()
    elif format == 'svg':
        return graph.create_svg()
    elif format == 'pdf':
        return graph.create_pdf()
    else:
        return graph.create_png()

def generate_uml_html(schema, include_tables=True, include_views=True, 
                      include_procedures=False, include_functions=False):
    """
    Generate an interactive HTML representation of the UML diagram
    
    Args:
        schema: Full database schema
        include_tables: Whether to include tables in the diagram
        include_views: Whether to include views in the diagram
        include_procedures: Whether to include stored procedures in the diagram
        include_functions: Whether to include functions in the diagram
        
    Returns:
        str: HTML code for the interactive diagram
    """
    # Generate a SVG image of the UML diagram
    graph = generate_database_uml(schema, include_tables, include_views, 
                                  include_procedures, include_functions)
    svg_data = graph.create_svg()
    
    # Base HTML template with CSS for interactivity
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .diagram-container {
                width: 100%;
                height: 600px;
                overflow: auto;
                border: 1px solid #ccc;
                position: relative;
            }
            .uml-node {
                cursor: move;
            }
            .uml-node:hover {
                filter: brightness(1.1);
            }
            .controls {
                margin-bottom: 10px;
            }
            .legend {
                margin-top: 10px;
                border: 1px solid #ccc;
                padding: 10px;
            }
            .legend-item {
                display: flex;
                align-items: center;
                margin-bottom: 5px;
            }
            .legend-color {
                width: 20px;
                height: 20px;
                margin-right: 10px;
            }
        </style>
    </head>
    <body>
        <div class="controls">
            <button id="zoom-in">Zoom In</button>
            <button id="zoom-out">Zoom Out</button>
            <button id="reset">Reset</button>
        </div>
        <div class="diagram-container" id="diagram">
    """
    
    # Insert the SVG data
    html += svg_data.decode('utf-8')
    
    # Add legend
    html += """
        </div>
        <div class="legend">
            <h3>Legend</h3>
            <div class="legend-items">
    """
    
    # Add legend items for node types
    for node_type, colors in COLORS.items():
        if ((node_type == 'table' and include_tables) or 
            (node_type == 'view' and include_views) or 
            (node_type == 'stored_procedure' and include_procedures) or 
            (node_type == 'function' and include_functions)):
            html += f"""
                <div class="legend-item">
                    <div class="legend-color" style="background-color: {colors['header']}"></div>
                    <span>{node_type.replace('_', ' ').title()}</span>
                </div>
            """
    
    # Add legend items for relationship types
    for rel_type, style in RELATIONSHIP_STYLES.items():
        html += f"""
            <div class="legend-item">
                <svg width="50" height="20">
                    <line x1="0" y1="10" x2="40" y2="10" stroke="{style['color']}" 
                          stroke-width="2" stroke-dasharray="{style['style'] == 'dashed' and '5,5' or style['style'] == 'dotted' and '2,2' or 'none'}" />
                    <polygon points="40,10 35,5 35,15" fill="{style['color']}" />
                </svg>
                <span>{rel_type.replace('_', ' ').title()}</span>
            </div>
        """
    
    # Add JavaScript for interactivity
    html += """
            </div>
        </div>
        
        <script>
            // Make nodes draggable
            document.addEventListener('DOMContentLoaded', function() {
                // Get all nodes
                const nodes = document.querySelectorAll('.node');
                let scale = 1;
                let panEnabled = false;
                let startX, startY;
                const diagram = document.getElementById('diagram');
                
                // Function to make nodes draggable
                nodes.forEach(node => {
                    let isDragging = false;
                    let offsetX, offsetY;
                    
                    node.classList.add('uml-node');
                    
                    node.addEventListener('mousedown', function(e) {
                        isDragging = true;
                        offsetX = e.clientX - parseFloat(node.getAttribute('x') || 0);
                        offsetY = e.clientY - parseFloat(node.getAttribute('y') || 0);
                        e.preventDefault();
                    });
                    
                    document.addEventListener('mousemove', function(e) {
                        if (isDragging) {
                            node.setAttribute('x', e.clientX - offsetX);
                            node.setAttribute('y', e.clientY - offsetY);
                            
                            // Update connected edges
                            // This is a simplified approach and may need more complex logic
                            // for production use
                        }
                    });
                    
                    document.addEventListener('mouseup', function() {
                        isDragging = false;
                    });
                });
                
                // Zoom controls
                document.getElementById('zoom-in').addEventListener('click', function() {
                    scale *= 1.2;
                    diagram.style.transform = `scale(${scale})`;
                });
                
                document.getElementById('zoom-out').addEventListener('click', function() {
                    scale /= 1.2;
                    diagram.style.transform = `scale(${scale})`;
                });
                
                document.getElementById('reset').addEventListener('click', function() {
                    scale = 1;
                    diagram.style.transform = `scale(${scale})`;
                });
                
                // Enable panning
                diagram.addEventListener('mousedown', function(e) {
                    if (e.target === diagram) {
                        panEnabled = true;
                        startX = e.clientX;
                        startY = e.clientY;
                        diagram.style.cursor = 'grabbing';
                    }
                });
                
                document.addEventListener('mousemove', function(e) {
                    if (panEnabled) {
                        diagram.scrollLeft += startX - e.clientX;
                        diagram.scrollTop += startY - e.clientY;
                        startX = e.clientX;
                        startY = e.clientY;
                    }
                });
                
                document.addEventListener('mouseup', function() {
                    panEnabled = false;
                    diagram.style.cursor = 'default';
                });
            });
        </script>
    </body>
    </html>
    """
    
    return html

def display_uml_in_streamlit(schema, include_tables=True, include_views=True, 
                           include_procedures=False, include_functions=False):
    """
    Display the UML diagram in Streamlit
    
    Args:
        schema: Full database schema
        include_tables: Whether to include tables in the diagram
        include_views: Whether to include views in the diagram
        include_procedures: Whether to include stored procedures in the diagram
        include_functions: Whether to include functions in the diagram
    """
    # Generate the UML diagram
    graph = generate_database_uml(schema, include_tables, include_views, 
                                include_procedures, include_functions)
    
    # Create PNG image
    png_data = graph.create_png()
    
    # Display the diagram
    st.image(png_data, caption="Database UML Diagram", use_column_width=True)
    
    # Provide download links
    col1, col2, col3 = st.columns(3)
    
    with col1:
        png_bytes = BytesIO(png_data)
        st.download_button(
            label="Download PNG",
            data=png_bytes,
            file_name="database_diagram.png",
            mime="image/png"
        )
    
    with col2:
        svg_data = graph.create_svg()
        st.download_button(
            label="Download SVG",
            data=svg_data,
            file_name="database_diagram.svg",
            mime="image/svg+xml"
        )
    
    with col3:
        html_content = generate_uml_html(schema, include_tables, include_views, 
                                       include_procedures, include_functions)
        st.download_button(
            label="Download Interactive HTML",
            data=html_content,
            file_name="database_diagram.html",
            mime="text/html"
        )

def get_uml_legend():
    """
    Generate a legend for the UML diagram
    
    Returns:
        str: HTML for the diagram legend
    """
    html = """
    <div style="border: 1px solid #ccc; padding: 10px; margin-top: 20px;">
        <h4>Legend</h4>
        <div>
    """
    
    # Node types
    for node_type, colors in COLORS.items():
        html += f"""
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <div style="width: 20px; height: 20px; background-color: {colors['header']}; margin-right: 10px;"></div>
                <span>{node_type.replace('_', ' ').title()}</span>
            </div>
        """
    
    # Relationship types
    for rel_type, style in RELATIONSHIP_STYLES.items():
        dash_style = ""
        if style['style'] == 'dashed':
            dash_style = "stroke-dasharray: 5,5"
        elif style['style'] == 'dotted':
            dash_style = "stroke-dasharray: 2,2"
        
        html += f"""
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <svg width="50" height="20">
                    <line x1="0" y1="10" x2="40" y2="10" stroke="{style['color']}" 
                        stroke-width="2" {dash_style} />
                    <polygon points="40,10 35,5 35,15" fill="{style['color']}" />
                </svg>
                <span>{rel_type.replace('_', ' ').title()}</span>
            </div>
        """
    
    html += """
        </div>
    </div>
    """
    
    return html
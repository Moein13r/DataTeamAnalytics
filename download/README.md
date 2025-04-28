# SQL Server UML Diagram Generator

A tool that generates UML diagrams from SQL Server databases, analyzes database design, and generates Entity Framework code.

## Features

- Connect to SQL Server databases or import from backup (.bak) files
- Generate UML diagrams for tables, views, stored procedures, and functions
- Analyze database design with metrics and recommendations
- Generate Entity Framework code (models, DbContext, repositories, and services)

## Setup Instructions

1. Install dependencies:
   ```
   pip install -r dependencies_list.txt
   ```

2. For SQL Server connectivity, you'll also need:
   - SQL Server drivers (ODBC Driver for SQL Server)
   - For Linux: `unixodbc-dev` and `freetds-dev` packages

3. Run the application:
   ```
   streamlit run sql_uml_app.py
   ```

## App Structure

- `sql_uml_app.py` - Main Streamlit application
- `sql_server_connection.py` - SQL Server connection module
- `db_schema_extractor.py` - Database schema extraction
- `uml_generator.py` - UML diagram generation
- `db_analyzer.py` - Database analysis and recommendations
- `ef_code_generator.py` - Entity Framework code generation

## Notes

- The app uses Streamlit for the web interface
- UML diagrams are generated with pydot and Graphviz
- Entity Framework code generation creates C# code for both EF Core and EF6

## System Requirements

- Python 3.8+
- SQL Server instance accessible from the host running the application
- Graphviz (for UML diagram generation)

## Docker Deployment

You can also run this application using Docker:

1. Build and start the container:
   ```
   docker-compose up -d
   ```

2. The application will be available at http://localhost:5000

3. To stop the container:
   ```
   docker-compose down
   ```

### Manual Docker Build

If you prefer to build the Docker image manually:

1. Build the image:
   ```
   docker build -t sql-uml-generator .
   ```

2. Run the container:
   ```
   docker run -p 5000:5000 sql-uml-generator
   ```

Note: When using Docker, make sure your SQL Server instance is accessible from the container. You may need to use the host IP address instead of localhost when connecting to SQL Server.
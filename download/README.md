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

### Alternative Docker Builds

We provide multiple Dockerfile options for different environments:

#### Standard Build (Dockerfile)
- Uses Debian slim with Microsoft SQL Server drivers
- Full functionality including SQL Server connectivity
```
docker build -t sql-uml-generator .
docker run -p 5000:5000 sql-uml-generator
```

#### Ubuntu Build (Dockerfile.ubuntu)
- Uses Ubuntu 22.04 with Microsoft SQL Server drivers
- Try this if the standard build has issues with SQL Server drivers
```
docker build -t sql-uml-generator-ubuntu -f Dockerfile.ubuntu .
docker run -p 5000:5000 sql-uml-generator-ubuntu
```

#### Minimal Build (Dockerfile.minimal)
- Minimal build without SQL Server drivers
- Use for demo purposes only when SQL Server connectivity is not needed
```
docker build -t sql-uml-generator-minimal -f Dockerfile.minimal .
docker run -p 5000:5000 sql-uml-generator-minimal
```

Note: When using Docker, make sure your SQL Server instance is accessible from the container. You may need to use the host IP address (not localhost) when connecting to SQL Server from inside the container.
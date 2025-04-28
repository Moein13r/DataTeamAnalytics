FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    unixodbc-dev \
    gnupg \
    curl \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft SQL Server ODBC driver
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY dependencies_list.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r dependencies_list.txt

# Copy application files
COPY *.py .
COPY .streamlit/ .streamlit/

# Expose port
EXPOSE 5000

# Set the entrypoint
ENTRYPOINT ["streamlit", "run", "sql_uml_app.py", "--server.port=5000", "--server.address=0.0.0.0"]
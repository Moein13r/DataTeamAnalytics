FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    unixodbc-dev \
    gnupg2 \
    curl \
    graphviz \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft SQL Server ODBC driver using the updated method
# Note: The application code now auto-detects available SQL Server drivers
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl -fsSL https://packages.microsoft.com/config/debian/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
    && apt-get install -y --no-install-recommends unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pymssql dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    freetds-dev \
    freetds-bin \
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
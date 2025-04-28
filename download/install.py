#!/usr/bin/env python3
"""
SQL Server UML Diagram Generator - Installation Script
This script helps set up the environment for running the application.
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Check if Python version is 3.8 or greater"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or greater is required.")
        return False
    return True

def install_dependencies():
    """Install Python dependencies from the list"""
    try:
        # Check if pip is available
        subprocess.check_call([sys.executable, "-m", "pip", "--version"])
        
        # Install dependencies
        if os.path.exists("dependencies_list.txt"):
            print("Installing dependencies...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "dependencies_list.txt"])
            print("Dependencies installed successfully.")
        else:
            print("Error: dependencies_list.txt not found.")
            return False
        
        return True
    except subprocess.CalledProcessError:
        print("Error: Failed to install dependencies.")
        return False

def check_graphviz():
    """Check if Graphviz is installed"""
    try:
        # Try to import pydot to see if it can find Graphviz
        import pydot
        graphs = pydot.graph_from_dot_data("digraph { a -> b }")
        if graphs:
            print("Graphviz appears to be installed correctly.")
            return True
    except ImportError:
        print("Warning: pydot module not found. Will be installed with dependencies.")
    except Exception:
        system = platform.system()
        if system == "Windows":
            print("Warning: Graphviz may not be installed. Please download and install from: https://graphviz.org/download/")
        elif system == "Linux":
            print("Warning: Graphviz may not be installed. Try: sudo apt-get install graphviz")
        elif system == "Darwin":  # macOS
            print("Warning: Graphviz may not be installed. Try: brew install graphviz")
        else:
            print("Warning: Graphviz may not be installed. Please install from: https://graphviz.org/download/")
        print("After installing Graphviz, run this script again.")
        return False
    
    return True

def check_sql_server_drivers():
    """Check if SQL Server drivers are available"""
    try:
        import pyodbc
        drivers = pyodbc.drivers()
        sql_drivers = [d for d in drivers if 'SQL Server' in d]
        
        if sql_drivers:
            print(f"SQL Server drivers found: {', '.join(sql_drivers)}")
            return True
        else:
            system = platform.system()
            if system == "Windows":
                print("Warning: No SQL Server drivers found. Download ODBC Driver for SQL Server from: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server")
            elif system == "Linux":
                print("Warning: No SQL Server drivers found. Install unixodbc-dev and ODBC Driver for SQL Server.")
                print("See: https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server")
            elif system == "Darwin":  # macOS
                print("Warning: No SQL Server drivers found. Install ODBC Driver for SQL Server for macOS.")
                print("See: https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/install-microsoft-odbc-driver-sql-server-macos")
            
            return False
    except ImportError:
        print("Warning: pyodbc module not found. Will be installed with dependencies.")
    
    return True

def setup_streamlit_config():
    """Create streamlit config directory and configuration file if not exists"""
    config_dir = os.path.join(os.path.expanduser("~"), ".streamlit")
    config_file = os.path.join(config_dir, "config.toml")
    
    # Create .streamlit directory if it doesn't exist
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        print(f"Created Streamlit config directory: {config_dir}")
    
    # Create config.toml if it doesn't exist
    if not os.path.exists(config_file):
        with open(config_file, "w") as f:
            f.write("[server]\n")
            f.write("headless = true\n")
            f.write("address = \"0.0.0.0\"\n")
            f.write("port = 5000\n")
        print(f"Created Streamlit config file: {config_file}")
    
    # If .streamlit exists in current directory, use that
    local_config_dir = os.path.join(os.getcwd(), ".streamlit")
    if not os.path.exists(local_config_dir):
        os.makedirs(local_config_dir)
        with open(os.path.join(local_config_dir, "config.toml"), "w") as f:
            f.write("[server]\n")
            f.write("headless = true\n")
            f.write("address = \"0.0.0.0\"\n")
            f.write("port = 5000\n")
        print(f"Created local Streamlit config file in: {local_config_dir}")
    
    return True

def main():
    """Main installation function"""
    print("SQL Server UML Diagram Generator - Installation")
    print("=" * 50)
    
    if not check_python_version():
        return 1
    
    setup_streamlit_config()
    
    if not install_dependencies():
        return 1
    
    check_graphviz()
    check_sql_server_drivers()
    
    print("\nInstallation completed.")
    print("\nTo run the application:")
    print("    streamlit run sql_uml_app.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
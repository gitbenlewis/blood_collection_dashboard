#!/bin/bash

# Blood Collection Dashboard - Dash App PyInstaller Build
# Creates a single executable from the Dash web version

set -e

echo "🏗️  Building Blood Collection Dashboard (Dash Web Version)..."
echo "=============================================================="

# Clean previous builds
rm -rf build/ dist/ __pycache__/

# Install PyInstaller if not already installed
if ! python3 -m pyinstaller --version &> /dev/null; then
    echo "Installing PyInstaller..."
    python3 -m pip install pyinstaller
fi

# Check if required dependencies are installed
echo "Checking dependencies..."
python3 -m pip install -q dash dash-bootstrap-components
python3 -m pip install -q plotly pandas pyyaml

# Verify data files exist
echo "Checking data files..."
if [ ! -f "config/config.yaml" ]; then
    echo "❌ Error: config/config.yaml not found!"
    exit 1
fi

if [ ! -d "output_files" ]; then
    echo "⚠️  Warning: output_files directory not found"
    echo "   Generating sample data first..."
    cd scripts
    python3 generate_data.py
    cd ..
fi

# Build with PyInstaller for Dash
echo "Running PyInstaller..."
pyinstaller \
    --onefile \
    --windowed \
    --name "Blood_Collection_Dashboard_Web" \
    --add-data "config:config" \
    --add-data "output_files:output_files" \
    --add-data "app_dash.py:." \
    --add-data "run_dash_app.py:." \
    --clean \
    --log-level=INFO \
    run_dash_app.py

echo ""
echo "✅ Build complete!"
echo ""
echo "📦 Output: dist/Blood_Collection_Dashboard_Web"
echo "📦 Size: $(du -sh dist/Blood_Collection_Dashboard_Web | cut -f1)"
echo ""
echo "🧪 To test on this machine:"
echo "   ./dist/Blood_Collection_Dashboard_Web"
echo ""
echo "📦 To create distribution package:"
echo "   zip -r Blood_Collection_Dashboard_Web_Dist.zip dist/Blood_Collection_Dashboard_Web"
echo ""
echo "🎉 Ready for distribution!"
echo ""
echo "The executable will:"
echo "  • Open in a native desktop window (windowed mode)"
echo "  • Automatically launch your default browser"
echo "  • Load the dashboard at http://127.0.0.1:8050"
echo "  • Include all dependencies (Python, dash, plotly, pandas, etc.)"
echo "  • Include your data files (config + CSVs)"
echo "  • Run completely offline"

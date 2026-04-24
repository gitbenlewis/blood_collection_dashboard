#!/bin/bash

# Blood Collection Dashboard - Flask-WebGUI PyInstaller Build
# Creates a single executable from the Flask-WebGUI desktop app

set -e

echo "🏗️  Building Blood Collection Dashboard (Flask-WebGUI)..."
echo "===================================================="

# Clean previous builds
rm -rf build/ dist/ __pycache__/

# Install PyInstaller if not already installed
if ! python3 -m pyinstaller --version &> /dev/null; then
    echo "Installing PyInstaller..."
    python3 -m pip install pyinstaller
fi

# Verify data files exist
echo "Checking data files..."
if [ ! -f "config/config.yaml" ]; then
    echo "❌ Error: config/config.yaml not found!"
    exit 1
fi

if [ ! -d "output_files" ]; then
    echo "⚠️  Warning: output_files directory not found"
    echo "   Generating sample data first..."
    python scripts/generate_data.py
fi

# Build with PyInstaller for Flask-WebGUI
echo "Running PyInstaller..."
pyinstaller \
    --onefile \
    --windowed \
    --name "Blood_Collection_Dashboard" \
    --add-data "config:config" \
    --add-data "output_files:output_files" \
    --clean \
    --log-level=INFO \
    flask_app.py

echo ""
echo "✅ Build complete!"
echo ""
echo "📦 Output: dist/Blood_Collection_Dashboard"
echo "📦 Size: $(du -sh dist/Blood_Collection_Dashboard | cut -f1)"
echo ""
echo "🧪 To test on this machine:"
echo "   ./dist/Blood_Collection_Dashboard"
echo ""
echo "📦 To create distribution package:"
echo "   zip -r Blood_Collection_Dashboard_Dist.zip dist/Blood_Collection_Dashboard"
echo ""
echo "🎉 Ready for distribution!"
echo ""
echo "The executable will:"
echo "  • Open as a native desktop window (not a browser)"
echo "  • Include all dependencies (Python, pandas, plotly, pywebview, etc.)"
echo "  • Include your data files (config + CSVs)"
echo "  • Launch automatically when double-clicked"

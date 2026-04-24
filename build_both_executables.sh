#!/bin/bash

# Blood Collection Dashboard - Build Both Executables
# Builds both Flask-WebGUI (Option 1) and Dash (Option 2) versions

set -e

echo "🏗️  Building Blood Collection Dashboard - Both Versions"
echo "========================================================="
echo ""

cd "$(dirname "$0")"

# Clean previous builds
rm -rf build/ dist/

echo "📦 Option 1: Flask-WebGUI (Native Desktop Window)"
echo "   ================================================="

# Build Flask-WebGUI version
python3 -m PyInstaller \
    --onefile \
    --windowed \
    --name "Blood_Collection_Dashboard" \
    --add-data "config:config" \
    --add-data "output_files:output_files" \
    --clean \
    --log-level=INFO \
    flask_app.py

FLASK_SIZE=$(du -sh dist/Blood_Collection_Dashboard | cut -f1)
echo "✅ Flask-WebGUI version built: dist/Blood_Collection_Dashboard"
echo "   Size: $FLASK_SIZE"
echo ""

echo "📦 Option 2: Dash Web Version (Browser-based)"
echo "   ==========================================="

# Build Dash version
python3 -m PyInstaller \
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

DASH_SIZE=$(du -sh dist/Blood_Collection_Dashboard_Web | cut -f1)
echo "✅ Dash version built: dist/Blood_Collection_Dashboard_Web"
echo "   Size: $DASH_SIZE"
echo ""

echo "📊 Build Summary:"
echo "   ==================="
echo "   Option 1 (Flask-WebGUI): dist/Blood_Collection_Dashboard ($FLASK_SIZE)"
echo "   - Native desktop window"
echo "   - No browser needed"
echo "   - ~80-120 MB"
echo ""
echo "   Option 2 (Dash): dist/Blood_Collection_Dashboard_Web ($DASH_SIZE)"
echo "   - Opens system browser automatically"
echo "   - Web-based interface"
echo "   - ~100-200 MB"
echo ""

echo "🎉 Both versions built successfully!"
echo ""
echo "📦 Next Steps:"
echo "   1. Test both executables"
echo "   2. Choose preferred version"
echo "   3. Create distribution package"
echo "   4. Ship to your boss!"
echo ""

echo "🧪 To test:"
echo "   ./dist/Blood_Collection_Dashboard           # Option 1"
echo "   ./dist/Blood_Collection_Dashboard_Web       # Option 2"
echo ""
echo "📦 To create distribution package:"
echo "   zip -r Blood_Collection_Dashboard_Dist.zip dist/Blood_Collection_Dashboard"
echo "   zip -r Blood_Collection_Dashboard_Web_Dist.zip dist/Blood_Collection_Dashboard_Web"

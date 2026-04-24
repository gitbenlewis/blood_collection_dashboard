"""
Entry point for Dash app with auto-browser launch.
This script opens a system browser automatically when run.
"""
import os
import sys
import time
import threading
import webbrowser

# Ensure we can import the Dash app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def open_browser():
    """Open the dashboard in the default browser"""
    time.sleep(1)  # Wait for the app to initialize
    webbrowser.open("http://127.0.0.1:8050")

def main():
    # Start browser in background thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Import and run the Dash app
    from app_dash import app
    
    print("Launching Blood Collection Dashboard...")
    print("Opening dashboard in your default browser...")
    
    app.run(host="0.0.0.0", port=8050, debug=False)

if __name__ == "__main__":
    main()

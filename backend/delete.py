import os
import sys

# --- Configuration ---
# You need to define APP_DATA_PATH based on your application's actual data storage location.
# Examples for common OS:
# Windows: C:\Users\<username>\AppData\Roaming\<YourAppName>
# macOS: /Users/<username>/Library/Application Support/<YourAppName>
# Linux: /home/<username>/.config/<YourAppName> or /home/<username>/.local/share/<YourAppName>

# For demonstration, let's use a temporary directory or a specific path.
# In a real Electron app, APP_DATA_PATH would often be provided by Electron's app.getPath() API
# For a backend script, you might derive it from the executable location or a known config.

# Example 1: Use a temporary directory for safe testing (comment out for production)
# import tempfile
# APP_DATA_PATH = os.path.join(tempfile.gettempdir(), "your_app_name_test")
# os.makedirs(APP_DATA_PATH, exist_ok=True) # Ensure it exists for testing

# Example 2: More realistic placeholder (YOU MUST ADJUST THIS!)
if sys.platform == "win32":
    APP_DATA_PATH = os.path.join(os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA"), "WA_BOMB_App")
elif sys.platform == "darwin": # macOS
    APP_DATA_PATH = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "WA_BOMB_App")
else: # Linux
    APP_DATA_PATH = os.path.join(os.path.expanduser("~"), ".config", "WA_BOMB_App")

# Ensure the directory exists if this script is meant to run standalone before the app creates it
os.makedirs(APP_DATA_PATH, exist_ok=True)

# The path to the activation file
ACTIVATION_FILE = os.path.join(APP_DATA_PATH, "whatsapp-activation.txt")

# --- Script to delete the file ---

print(f"Attempting to delete activation file at: {ACTIVATION_FILE}")

if os.path.exists(ACTIVATION_FILE):
    try:
        os.remove(ACTIVATION_FILE)
        print(f"Successfully deleted: {ACTIVATION_FILE}")
    except OSError as e:
        print(f"Error deleting file {ACTIVATION_FILE}: {e}")
        print(f"Please check permissions for the directory and file: {os.path.dirname(ACTIVATION_FILE)}")
    except Exception as e:
        print(f"An unexpected error occurred while deleting {ACTIVATION_FILE}: {e}")
else:
    print(f"File not found: {ACTIVATION_FILE}. No action needed.")
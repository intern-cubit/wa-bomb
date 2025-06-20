import os
import shutil
import tempfile
import json
import pandas as pd
import subprocess
import hashlib
import asyncio
import sys
import requests

from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import logging
from appdirs import user_data_dir

APP_AUTHOR = "YourCompany"
APP_NAME = "CampaignFlow"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # Set default level for this module's logger

# --- Global Shutdown Event ---
shutdown_event = asyncio.Event()
SHUTDOWN_GRACE_PERIOD = 5

ACTIVATION_API_URL = "https://api-keygen.obzentechnolabs.com/api/sadmin/check-activation"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown events.
    """
    logger.info("FastAPI app starting up...")
    yield # Application is ready to receive requests
    logger.info("FastAPI app received shutdown signal. Waiting for graceful termination...")

    try:
        # Wait for the shutdown event with a timeout
        await asyncio.wait_for(shutdown_event.wait(), timeout=SHUTDOWN_GRACE_PERIOD)
        logger.info("FastAPI app received shutdown signal and completed graceful wait.")
    except asyncio.TimeoutError:
        logger.warning(f"FastAPI app did not complete graceful shutdown within {SHUTDOWN_GRACE_PERIOD} seconds. Forcing exit.")
    except Exception as e:
        logger.error(f"Error during graceful shutdown wait: {e}", exc_info=True)

    # Any specific cleanup tasks that MUST run before the process exits
    # For example, closing database connections, flushing logs, etc.
    # Add them here if you have any.
    logger.info("FastAPI app proceeding with final cleanup and exit.")
    sys.exit(0) # Explicitly exit the process after graceful attempts

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.name == 'nt': # Check if the operating system is Windows
    app_data_dir = os.getenv('LOCALAPPDATA')
    if app_data_dir is None: # Fallback in case LOCALAPPDATA env var is not set (unlikely on modern Windows)
        app_data_dir = os.path.join(os.path.expanduser('~'), 'AppData', 'Local')
else: # For other OS (Linux/macOS), use XDG_DATA_HOME or a fallback in user home
    app_data_dir = os.getenv('XDG_DATA_HOME', os.path.join(os.path.expanduser('~'), '.local', 'share'))

APP_NAME_DIR = "mailstorm" 
APP_DATA_PATH = os.path.join(app_data_dir, APP_NAME_DIR)

try:
    os.makedirs(APP_DATA_PATH, exist_ok=True)
    logger.info(f"Ensured application data directory exists: {APP_DATA_PATH}")
except OSError as e:
    logger.critical(f"CRITICAL ERROR: Could not create application data directory {APP_DATA_PATH}: {e}")
    sys.exit(1) 

ACTIVATION_FILE = os.path.join(APP_DATA_PATH, "whatsapp-activation.txt")


class ActivationRequest(BaseModel):
    motherboardSerial: str
    processorId: str
    activationKey: str

def get_motherboard_serial():
    try:
        try:
            result = subprocess.check_output(
                ["powershell.exe", "-Command", "(Get-WmiObject Win32_BaseBoard).SerialNumber"],
                text=True,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            serial = result.strip()
            if serial:
                return serial
            else:
                logger.warning("Powershell returned empty motherboard serial. Falling back to wmic.")
        except (subprocess.CalledProcessError, FileNotFoundError, Exception) as e:
            logger.warning(f"Powershell WMI query for motherboard serial failed ({e}). Falling back to wmic.")

        result = subprocess.check_output("wmic baseboard get serialnumber", shell=True, text=True)
        serial = result.split('\n')[1].strip()
        return serial
    except Exception as e:
        logger.error(f"Failed to get motherboard serial: {e}")
        return f"Error getting motherboard serial: {e}"

def get_processor_id():
    try:
        try:
            result = subprocess.check_output(
                ["powershell.exe", "-Command", "(Get-WmiObject Win32_Processor).ProcessorId"],
                text=True,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            processor_id = result.strip()
            if processor_id:
                return processor_id
            else:
                logger.warning("Powershell returned empty processor ID. Falling back to wmic.")
        except (subprocess.CalledProcessError, FileNotFoundError, Exception) as e:
            logger.warning(f"Powershell WMI query for processor ID failed ({e}). Falling back to wmic.")

        result = subprocess.check_output("wmic cpu get processorId", shell=True, text=True)
        processor_id = result.split('\n')[1].strip()
        return processor_id
    except Exception as e:
        logger.error(f"Failed to get processor ID: {e}")
        return f"Error getting processor ID: {e}"

def generate_activation_key(processorId: str, motherboardSerial: str) -> str:
    """
    Generates an activation key similar to the provided JavaScript function.
    """
    input_string = f"{processorId}:{motherboardSerial}".upper()

    hash_object = hashlib.sha256()
    hash_object.update(input_string.encode('utf-8'))
    hex_hash = hash_object.hexdigest().upper()

    big_int_value = int(hex_hash, 16)

    base36_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    base36_result = ""
    while big_int_value > 0:
        big_int_value, remainder = divmod(big_int_value, 36)
        base36_result = base36_chars[remainder] + base36_result

    if not base36_result:
        base36_result = "0"

    base36 = base36_result.upper()

    raw_key = base36.zfill(16)[:16]

    formatted_key = "-".join([raw_key[i:i+4] for i in range(0, len(raw_key), 4)])

    return formatted_key

@app.get("/system-info")
async def get_system_info_endpoint():
    motherboard_serial = get_motherboard_serial()
    processor_id = get_processor_id()

    if "Error" in motherboard_serial or "Error" in processor_id:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve complete system information. Motherboard: {motherboard_serial}, Processor: {processor_id}"
        )

    return {"motherboardSerial": motherboard_serial, "processorId": processor_id}


@app.post("/activate")
async def activate_system_endpoint(request: ActivationRequest):
    logger.info(f"Activation request received for Motherboard: '{request.motherboardSerial}', Processor: '{request.processorId}'")

    appName = "WA BOMB" 
    api_payload = {
        "processorId": request.processorId,
        "motherboardSerial": request.motherboardSerial,
        "appName": appName
    }

    try:
        logger.info(f"Pre-checking activation status with API: {ACTIVATION_API_URL}")
        response = requests.post(ACTIVATION_API_URL, json=api_payload)
        response.raise_for_status() 
        api_response_data = response.json()
        logger.info(f"API Pre-check Response: {api_response_data}")

        api_activation_status = api_response_data.get("activationStatus")
        api_success = api_response_data.get("success", False)

        if not api_success or api_activation_status != "active":
            message = api_response_data.get("activationStatus", "Please activate your device on the website first.")
            if api_activation_status == "inactive":
                message = "Your device license has expired. Please renew it on the website."
            elif api_activation_status == "Device not found":
                 message = "Device not registered. Please register and activate it on the website."

            logger.warning(f"Activation pre-check failed. Server status: {api_activation_status}. Message: {message}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, # Forbidden
                detail={"success": False, "message": message}
            )

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error during API pre-check: {http_err} - {response.text}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail={"success": False, "message": f"Failed to connect to activation server for pre-check: {http_err}"}
        )
    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"Connection error during API pre-check: {conn_err}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"success": False, "message": "Could not connect to activation server for pre-check. Please check your internet connection."}
        )
    except requests.exceptions.Timeout as timeout_err:
        logger.error(f"Timeout error during API pre-check: {timeout_err}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"success": False, "message": "Activation server took too long to respond during pre-check."}
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred during API pre-check: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": f"An unexpected error occurred during activation pre-check: {e}"}
        )
    
    generated_key = generate_activation_key(request.processorId, request.motherboardSerial)
    logger.info(f"Generated Activation Key locally: {generated_key}")

    if generated_key == request.activationKey.strip().upper():
        try:
            os.makedirs(os.path.dirname(ACTIVATION_FILE), exist_ok=True)
            with open(ACTIVATION_FILE, "w") as f:
                f.write(generated_key)
            logger.info(f"Activation successful. Key saved to {ACTIVATION_FILE}")
            return {"success": True, "message": "Activation successful!"}
        except IOError as e:
            logger.error(f"IOError saving activation file {ACTIVATION_FILE}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"success": False, "message": f"Failed to save activation data due to file system error: {e}"})
        except Exception as e:
            logger.error(f"Unexpected error saving activation file {ACTIVATION_FILE}: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"success": False, "message": f"An unexpected error occurred while saving activation data: {e}"})
    else:
        logger.warning(f"Local activation failed: Provided key '{request.activationKey}' does not match generated key '{generated_key}'.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "Activation failed: Invalid key provided by client."}
        )
    
@app.get("/check-activation")
async def check_activation_endpoint():
    motherboard_serial = get_motherboard_serial()
    processor_id = get_processor_id()
    appName = "WA BOMB"

    # Initialize variables for the response
    api_device_status = "unknown" # Default for API status
    api_message = "Could not verify activation status with server." # Default message from API
    local_key_status = False # Default for local key check
    local_key_message = "Local activation file not found or invalid." # Default for local key message
    is_activated_overall = False # Overall activation status, default to False

    if "Error" in motherboard_serial or "Error" in processor_id:
        error_message = (
            f"Failed to retrieve system information for activation check. "
            f"Motherboard: {motherboard_serial}, Processor: {processor_id}"
        )
        logger.error(error_message)
        if os.path.exists(ACTIVATION_FILE):
            try:
                os.remove(ACTIVATION_FILE)
                logger.info(f"Deleted local activation file due to system info error: {ACTIVATION_FILE}")
            except OSError as e:
                logger.error(f"Error deleting activation file {ACTIVATION_FILE} during system info cleanup: {e}")
        
        return {
            "isActivated": is_activated_overall, # False
            "apiStatus": api_device_status, # "unknown"
            "apiMessage": error_message,
            "localKeyStatus": False,
            "localKeyMessage": "System information could not be retrieved."
        }

    payload = {
        "processorId": processor_id,
        "motherboardSerial": motherboard_serial,
        "appName": appName
    }

    try:
        logger.info(f"Sending activation check request to: {ACTIVATION_API_URL} with payload: {payload}")
        response = requests.post(ACTIVATION_API_URL, json=payload, timeout=10) # Added timeout

        api_response_data = {}
        try:
            api_response_data = response.json()
        except requests.exceptions.JSONDecodeError:
            logger.warning(f"API response not JSON for status {response.status_code}: {response.text}")
            api_message = f"Invalid response format from activation server (Status: {response.status_code})."

        logger.info(f"API Response (Status: {response.status_code}): {api_response_data}")

        # Extract API status and message
        api_device_status = api_response_data.get("activationStatus", "unknown")
        # Prioritize 'message' if it exists, otherwise use activationStatus or default
        api_message = api_response_data.get("message", api_response_data.get("activationStatus", api_message))


        # --- Start API Response Handling (your specific logic) ---

        # If API indicates an error status (4xx, 5xx)
        if response.status_code >= 400:
            logger.warning(f"External API reported error status {response.status_code}: {api_message}")
            if os.path.exists(ACTIVATION_FILE):
                try:
                    os.remove(ACTIVATION_FILE)
                    logger.info(f"Local activation file {ACTIVATION_FILE} deleted due to external API error.")
                except OSError as e:
                    logger.error(f"Error deleting activation file {ACTIVATION_FILE} during external error cleanup: {e}")
            
            is_activated_overall = False # API error means not activated
            local_key_status = False # Local key cannot be validated against a failing API
            local_key_message = "API validation failed (server error), local key status is not relevant."
            
            return {
                "isActivated": is_activated_overall,
                "apiStatus": api_device_status,
                "apiMessage": api_message,
                "localKeyStatus": local_key_status,
                "localKeyMessage": local_key_message
            }
        
        # If API response is 2xx, but "success" is false or "activationStatus" is not "active"
        is_activated_from_api = api_response_data.get("success", False) and api_device_status == "active"

        if is_activated_from_api:
            # API says active, now check local key
            generated_key = generate_activation_key(processor_id, motherboard_serial)
            stored_key = None

            if os.path.exists(ACTIVATION_FILE):
                try:
                    with open(ACTIVATION_FILE, "r") as f:
                        stored_key = f.read().strip()
                except IOError as e:
                    logger.error(f"IOError reading activation file {ACTIVATION_FILE}: {e}")
                    # If file is unreadable, treat as not matching, and delete it.
                    if os.path.exists(ACTIVATION_FILE):
                        try:
                            os.remove(ACTIVATION_FILE)
                            logger.info(f"Deleted unreadable activation file: {ACTIVATION_FILE}")
                        except OSError as e_del:
                            logger.error(f"Error deleting unreadable activation file {ACTIVATION_FILE}: {e_del}")
                    
                    is_activated_overall = False # Local file unreadable, so not fully activated
                    local_key_status = False
                    local_key_message = "Local activation file corrupted or unreadable. Please reactivate."

                    return { # Return immediately based on unreadable file
                        "isActivated": is_activated_overall,
                        "apiStatus": api_device_status, # still "active" from API
                        "apiMessage": api_message,
                        "localKeyStatus": local_key_status,
                        "localKeyMessage": local_key_message
                    }

            # Check if generated key matches stored key (if stored_key is not None)
            if generated_key == stored_key:
                logger.info("Local activation file matches API status. System is fully activated.")
                is_activated_overall = True # Both API and local key match
                local_key_status = True
                local_key_message = "Local activation key matches."
            else:
                # File exists but doesn't match, or file didn't exist (stored_key is None)
                logger.warning("Local activation key mismatch or not found, despite API reporting active.")
                is_activated_overall = False # API says active, but local doesn't match, so not fully activated
                local_key_status = False
                local_key_message = "Local activation key mismatch or not found. Please reactivate."
                
                # Delete the local file if it exists but is incorrect/missing
                if os.path.exists(ACTIVATION_FILE):
                    try:
                        os.remove(ACTIVATION_FILE)
                        logger.info(f"Deleted mismatched local activation file: {ACTIVATION_FILE}")
                    except OSError as e:
                        logger.error(f"Error deleting mismatched activation file {ACTIVATION_FILE}: {e}")
            
            return {
                "isActivated": is_activated_overall,
                "apiStatus": api_device_status, # Still "active" from API
                "apiMessage": api_message,
                "localKeyStatus": local_key_status,
                "localKeyMessage": local_key_message
            }

        else: # External API returned 200 OK, but not 'active' (e.g., inactive, Device not found)
            logger.info(f"API reported activation status: {api_device_status}. Device is not active from API perspective.")
            if os.path.exists(ACTIVATION_FILE):
                try:
                    os.remove(ACTIVATION_FILE)
                    logger.info(f"Local activation file {ACTIVATION_FILE} deleted successfully as API indicates inactive status.")
                except OSError as e:
                    logger.error(f"Error deleting activation file {ACTIVATION_FILE}: {e}")

            # Update api_message based on the actual status from API
            if api_device_status == "inactive":
                api_message = "Device license has expired. Please renew it on the website."
            elif api_device_status == "Device not found":
                api_message = "Device not registered. Please register and activate it on the website."
            elif not api_response_data.get("success", False): # Explicitly check for success: false
                api_message = api_response_data.get("message", "System is not activated based on API response.")
            
            is_activated_overall = False # API says not active
            local_key_status = False # Local key is irrelevant/should be removed

            return {
                "isActivated": is_activated_overall,
                "apiStatus": api_device_status,
                "apiMessage": api_message,
                "localKeyStatus": local_key_status,
                "localKeyMessage": "Local activation file removed as API indicates inactive status."
            }

    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"Connection error occurred: {conn_err}")
        if os.path.exists(ACTIVATION_FILE):
            try:
                os.remove(ACTIVATION_FILE)
                logger.info(f"Local activation file {ACTIVATION_FILE} deleted due to connection error.")
            except OSError as e:
                logger.error(f"Error deleting activation file {ACTIVATION_FILE} during connection error cleanup: {e}")
        
        is_activated_overall = False
        api_device_status = "error"
        api_message = "Could not connect to activation server. Please check your internet connection."
        local_key_status = False
        local_key_message = "Connection to activation server failed."
        
        return {
            "isActivated": is_activated_overall,
            "apiStatus": api_device_status,
            "apiMessage": api_message,
            "localKeyStatus": local_key_status,
            "localKeyMessage": local_key_message
        }
    except requests.exceptions.Timeout as timeout_err:
        logger.error(f"Timeout error occurred: {timeout_err}")
        if os.path.exists(ACTIVATION_FILE):
            try:
                os.remove(ACTIVATION_FILE)
                logger.info(f"Local activation file {ACTIVATION_FILE} deleted due to timeout error.")
            except OSError as e:
                logger.error(f"Error deleting activation file {ACTIVATION_FILE} during timeout error cleanup: {e}")
        
        is_activated_overall = False
        api_device_status = "error"
        api_message = "Activation server took too long to respond."
        local_key_status = False
        local_key_message = "Connection to activation server timed out."
        
        return {
            "isActivated": is_activated_overall,
            "apiStatus": api_device_status,
            "apiMessage": api_message,
            "localKeyStatus": local_key_status,
            "localKeyMessage": local_key_message
        }
    except Exception as e:
        logger.error(f"An unexpected error occurred during API call: {e}", exc_info=True)
        if os.path.exists(ACTIVATION_FILE):
            try:
                os.remove(ACTIVATION_FILE)
                logger.info(f"Local activation file {ACTIVATION_FILE} deleted due to unexpected error.")
            except OSError as e:
                logger.error(f"Error deleting activation file {ACTIVATION_FILE} during unexpected error cleanup: {e}")
        
        is_activated_overall = False
        api_device_status = "error"
        api_message = f"An unexpected error occurred: {e}"
        local_key_status = False
        local_key_message = "An unexpected error occurred during local key check."
        
        return {
            "isActivated": is_activated_overall,
            "apiStatus": api_device_status,
            "apiMessage": api_message,
            "localKeyStatus": local_key_status,
            "localKeyMessage": local_key_message
        }
        
USER_DATA_DIR = os.path.join(user_data_dir(APP_NAME, APP_AUTHOR), "selenium_profile")

@app.post("/logout")
async def logout_endpoint():
    if os.path.exists(ACTIVATION_FILE):
        try:
            os.remove(ACTIVATION_FILE)
            logger.info(f"Activation file '{ACTIVATION_FILE}' deleted successfully for logout.")
        except OSError as e:
            logger.error(f"Error deleting activation file '{ACTIVATION_FILE}' during logout: {e}")
    else:
        logger.info("Logout requested, but no activation file found.")

    if os.path.exists(USER_DATA_DIR):
        try:
            shutil.rmtree(USER_DATA_DIR)
            logger.info(f"Selenium user data directory '{USER_DATA_DIR}' cleared successfully.")
        except OSError as e:
            logger.error(f"Error clearing Selenium user data directory '{USER_DATA_DIR}': {e}")
            raise HTTPException(status_code=500, detail=f"Failed to clear WhatsApp session data: {e}")
    else:
        logger.info(f"Selenium user data directory '{USER_DATA_DIR}' not found, no WhatsApp session to clear.")

    return JSONResponse(content={"success": True, "message": "Logged out successfully. WhatsApp session data cleared."})

@app.post("/preview-csv")
async def preview_csv_endpoint(
    csv_file: UploadFile = File(..., description="CSV file to preview")
):
    """
    Preview the uploaded CSV file and return column names and first few rows
    """
    if not csv_file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Uploaded file is not a CSV.")
    
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp()
        csv_path = os.path.join(temp_dir, "preview.csv")
        
        with open(csv_path, "wb") as f:
            f.write(await csv_file.read())

        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(csv_path, encoding='latin1')
            except Exception as e:
                raise HTTPException(status_code=422, detail=f"Failed to parse CSV with fallback encoding: {e}")
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Failed to parse CSV: {e}")

        columns = df.columns.tolist()
        preview_data = df.head(10).fillna("").to_dict('records')
        
        return JSONResponse({
            "status": "success",
            "columns": columns,
            "preview": preview_data,
            "total_rows": len(df)
        })

    except HTTPException:
        raise
    except Exception as e:
        print(f"DEBUG: Unexpected error in /preview-csv: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
    finally:
        if temp_dir and os.path.exists(temp_dir): # Only try to remove if it exists
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except OSError as e:
                print(f"DEBUG: Error cleaning up temp directory {temp_dir}: {e}")

@app.post("/send-messages")
async def send_messages_endpoint(
    message: str = Form(..., description="Message template with variables like {name}"),
    csv_file: UploadFile = File(..., description="CSV with contact data"),
    variables: str = Form(..., description="JSON list of variable names used in template"),
    media_file: UploadFile = File(None, description="Optional media file to send to all contacts.")
):
    try:
        variable_list = json.loads(variables)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid variables format")

    if not csv_file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Uploaded file is not a CSV.")
    
    temp_dir = None 
    try:
        temp_dir = tempfile.mkdtemp()
        
        csv_path = os.path.join(temp_dir, "contacts.csv")
        with open(csv_path, "wb") as f: 
            f.write(await csv_file.read())

        # Read and validate CSV, explicitly setting encoding to UTF-8
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
        except UnicodeDecodeError:
            # Fallback to 'latin1' or 'cp1252' if UTF-8 fails
            try:
                df = pd.read_csv(csv_path, encoding='latin1')
            except Exception as e:
                raise HTTPException(status_code=422, detail=f"Failed to parse CSV with fallback encoding: {e}")
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Failed to parse CSV: {e}")

        # Check if required variables exist in CSV columns
        missing_vars = [var for var in variable_list if var not in df.columns] # Use variable_list here
        if missing_vars:
            raise HTTPException(
                status_code=422,
                detail=f"Variables not found in CSV: {', '.join(missing_vars)}"
            )

        # Ensure we have at least a phone column (required for WhatsApp)
        if 'phone' not in df.columns:
            raise HTTPException(
                status_code=422,
                detail="CSV must contain a 'phone' column for WhatsApp messaging"
            )

        # Save media file if provided
        media_path = None
        if media_file:
            media_path = os.path.join(temp_dir, media_file.filename)
            with open(media_path, "wb") as f:
                f.write(await media_file.read())

        from whatsapp_sender import send_messages_with_variables
        print(f"DEBUG: data frame: {df} Sending messages with template: {message}, variables: {variable_list}, media: {media_path}")
        send_messages_with_variables(df, message, variable_list, media_path)

        return JSONResponse({
            "status": "success", 
            "detail": f"Successfully sent {len(df)} personalized messages"
        })

    except HTTPException:
        raise
    except Exception as e:
        print(f"DEBUG: Unexpected error in /send-messages: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected server error: {e}")
    finally:
        if temp_dir and os.path.exists(temp_dir): # Only try to remove if it exists
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except OSError as e:
                print(f"DEBUG: Error cleaning up temp directory {temp_dir}: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "WhatsApp Message Dashboard API is running"}

@app.post("/shutdown")
async def shutdown_backend_endpoint():
    logger.info("Received shutdown request for backend. Signaling graceful exit...")
    shutdown_event.set() # Set the event to unblock the lifespan shutdown
    return {"message": "Backend received shutdown request. Attempting graceful exit."}
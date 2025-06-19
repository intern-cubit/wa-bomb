import os
import shutil
import tempfile
import json
import pandas as pd
import subprocess
import hashlib
import asyncio
import sys

from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
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

    generated_key = generate_activation_key(request.processorId, request.motherboardSerial)
    logger.info(f"Generated Activation Key: {generated_key}")

    if generated_key == request.activationKey.upper():
        try:
            os.makedirs(os.path.dirname(ACTIVATION_FILE), exist_ok=True)
            with open(ACTIVATION_FILE, "w") as f:
                f.write(generated_key)
            logger.info(f"Activation successful. Key saved to {ACTIVATION_FILE}")
            return {"success": True, "message": "Activation successful!"}
        except IOError as e:
            logger.error(f"IOError saving activation file {ACTIVATION_FILE}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save activation data due to file system error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving activation file {ACTIVATION_FILE}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred while saving activation data: {e}")
    else:
        logger.warning(f"Activation failed: Provided key '{request.activationKey}' does not match generated key '{generated_key}'.")
        return {"success": False, "message": "Activation failed: Invalid key."}

@app.get("/check-activation")
async def check_activation_endpoint():
    motherboard_serial = get_motherboard_serial()
    processor_id = get_processor_id()

    if "Error" in motherboard_serial or "Error" in processor_id:
        error_message = f"Failed to retrieve system information for activation check. Motherboard: {motherboard_serial}, Processor: {processor_id}"
        logger.error(error_message)
        if os.path.exists(ACTIVATION_FILE):
            try:
                os.remove(ACTIVATION_FILE)
            except OSError as e:
                logger.error(f"Error deleting activation file {ACTIVATION_FILE} during cleanup: {e}")
        return {"isActivated": False, "message": error_message}

    generated_key = generate_activation_key(processor_id, motherboard_serial)
    logger.info(f"Check Activation: Generated Key: {generated_key}")

    is_activated = False
    stored_key = None
    try:
        if os.path.exists(ACTIVATION_FILE):
            try:
                with open(ACTIVATION_FILE, "r") as f:
                    stored_key = f.read().strip()
                logger.info(f"Check Activation: Stored Key: {stored_key}")

                if generated_key == stored_key:
                    is_activated = True
                    logger.info("Check Activation: System is activated.")
                else:
                    logger.warning("Check Activation: Generated key does not match stored key. Deleting activation file.")
                    try:
                        os.remove(ACTIVATION_FILE)
                    except OSError as e:
                        logger.error(f"Error deleting activation file {ACTIVATION_FILE} during mismatch: {e}")
            except IOError as e:
                logger.error(f"IOError reading activation file {ACTIVATION_FILE}: {e}")
                if os.path.exists(ACTIVATION_FILE):
                    try:
                        os.remove(ACTIVATION_FILE)
                    except OSError as e_del:
                        logger.error(f"Error deleting unreadable activation file {ACTIVATION_FILE}: {e_del}")
                is_activated = False
        else:
            logger.info("Check Activation: Activation file not found.")

    except Exception as e:
        logger.error(f"Unhandled error during activation check: {e}", exc_info=True)
        if os.path.exists(ACTIVATION_FILE):
            try:
                os.remove(ACTIVATION_FILE)
            except OSError as e_del:
                logger.error(f"Error deleting activation file {ACTIVATION_FILE} due to error during check: {e_del}")
        is_activated = False

    return {"isActivated": is_activated, "message": "System is activated." if is_activated else "System is not activated."}

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
    
    temp_dir = None # Initialize temp_dir outside try to ensure finally always has it
    try:
        temp_dir = tempfile.mkdtemp()
        csv_path = os.path.join(temp_dir, "preview.csv")
        
        # Ensure file handle is explicitly closed after writing
        with open(csv_path, "wb") as f:
            f.write(await csv_file.read())

        # Read the CSV into a DataFrame, explicitly setting encoding to UTF-8
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
        except UnicodeDecodeError:
            # Fallback to 'latin1' or 'cp1252' if UTF-8 fails (common for messy CSVs)
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
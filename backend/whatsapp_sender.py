import os
import time
import random
import pandas as pd
from typing import List

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC

import sys
import appdirs
import logging
from logging.handlers import RotatingFileHandler

# Import ChromeDriverManager
from webdriver_manager.chrome import ChromeDriverManager # You'll need to install this: pip install webdriver-manager

# --- Configure logging to ensure UTF-8 output ---
# (Rest of your logging configuration remains the same)
APP_AUTHOR = "YourCompany"
APP_NAME = "CampaignFlow"

LOG_FILE_PATH = os.path.join(appdirs.user_data_dir(APP_NAME, APP_AUTHOR), "app.log")
os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=1024*1024*5, backupCount=5, encoding='utf-8')
file_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
try:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        console_handler.setFormatter(formatter)
    else:
        console_handler.setFormatter(formatter)
except Exception:
    console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

def safe_print(message):
    logger.info(message)

WHATSAPP_WEB_URL = "https://web.whatsapp.com"
TYPING_SPEED_RANGE = (0.01, 0.05)
DELAY_BETWEEN_MESSAGES = (5, 15)

MEDIA_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
    ".mp4", ".mov", ".avi", ".mkv", ".3gp"
}

USER_DATA_DIR = os.path.join(appdirs.user_data_dir(APP_NAME, APP_AUTHOR), "selenium_profile")

if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR)
# -----------------------------------------------

def human_typing(element, text: str):
    """
    Simulates human-like typing, including line breaks.
    """
    for char in text:
        if char == "\n":
            element.send_keys(Keys.SHIFT, Keys.ENTER)
        else:
            element.send_keys(char)
        time.sleep(random.uniform(*TYPING_SPEED_RANGE))


def replace_variables_in_message(message_template: str, row_data: dict, variables: List[str]) -> str:
    """
    Replace variables in message template with actual data from CSV row
    """
    personalized_message = message_template

    for variable in variables:
        placeholder = f"{{{variable}}}"
        if variable in row_data:
            value = str(row_data[variable]) if pd.notna(row_data[variable]) else ""
            personalized_message = personalized_message.replace(placeholder, value)
        else:
            personalized_message = personalized_message.replace(placeholder, "")

    return personalized_message


def send_whatsapp_message_enhanced(
    driver: webdriver.Chrome,
    phone: str,
    personalized_message: str,
    contact_name: str,
    media_path: str = None
):
    """
    Enhanced version that sends a fully personalized message
    """
    url = f"https://web.whatsapp.com/send?phone={phone}&text&app_absent=0"
    driver.get(url)
    safe_print(f"📱 Opening chat with {phone} ({contact_name})...")

    try:
        message_box_xpath = '//div[@title="Type a message"] | //div[@data-tab="10"]'
        message_box = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, message_box_xpath))
        )

        human_typing(message_box, personalized_message)

        if media_path and os.path.exists(media_path):
            ext = os.path.splitext(media_path)[1].lower()
            safe_print(f"📎 Attaching media: {media_path}")

            attach_button = None
            for xpath in [
                '//button[@title="Attach"]',
                '//div[@title="Attach"]',
                '//span[@data-icon="clip"]'
            ]:
                try:
                    attach_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    break
                except:
                    continue

            if not attach_button:
                safe_print("❌ Could not find attach button. Sending message without media.")
                message_box.send_keys(Keys.ENTER)
                return

            attach_button.click()
            time.sleep(1)

            if ext in MEDIA_EXTENSIONS:
                file_input_xpath = '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]'
            else:
                file_input_xpath = '//input[@accept="*"]'

            file_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, file_input_xpath))
            )
            file_input.send_keys(media_path)
            time.sleep(2)

            send_button_xpath = '//div[@role="button" and @aria-label="Send"]'
            send_btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, send_button_xpath))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", send_btn)
            time.sleep(0.5)
            send_btn.click()
        else:
            message_box.send_keys(Keys.ENTER)

        safe_print(f"✅ Message sent to {contact_name} ({phone})")

    except Exception as e:
        safe_print(f"❌ Error sending to {phone}: {e}")
        # Optionally, you might want to log the full traceback for debugging
        # logger.exception(f"Error sending to {phone}:") # This logs the full traceback
        pass # Continue to next contact even if one fails


def send_messages_with_variables(
    df: pd.DataFrame,
    message_template: str,
    variables: List[str],
    media_path: str = None
):
    """
    Send personalized messages using dynamic variables from CSV
    """
    options = Options()
    options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--remote-debugging-port=9222")

    try:
        # Use ChromeDriverManager to get the path to the ChromeDriver executable
        # This will download it if it's not present or outdated
        driver_service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(
            service=driver_service,
            options=options
        )

        safe_print("🔓 Opening WhatsApp Web. Please scan QR code if not already logged in…")
        driver.get(WHATSAPP_WEB_URL)

        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"]'))
        )
        safe_print("✅ Logged into WhatsApp Web.")

        for index, row in df.iterrows():
            phone_raw = str(row.get("phone", "")).strip().replace(" ", "").replace("+", "")
            if not phone_raw.isdigit():
                safe_print(f"⚠️ Skipping invalid phone number: {phone_raw}")
                continue

            contact_name = "Friend"
            for name_field in ["name", "fullName", "full_name", "firstName", "first_name"]:
                if name_field in row and pd.notna(row[name_field]):
                    contact_name = str(row[name_field])
                    break

            row_dict = row.to_dict()
            personalized_message = replace_variables_in_message(
                message_template, row_dict, variables
            )

            send_whatsapp_message_enhanced(
                driver, phone_raw, personalized_message, contact_name, media_path
            )

            sleep_time = random.randint(*DELAY_BETWEEN_MESSAGES)
            safe_print(f"⏱️ Sleeping {sleep_time}s before next message...\n")
            time.sleep(sleep_time)

        safe_print("🎉 All messages sent successfully!")

    except Exception as e:
        safe_print(f"❌ Error in message sending process: {e}")
        logger.exception("Full traceback for error:") # This will log the detailed exception
    finally:
        if 'driver' in locals() and driver: # Ensure driver object exists before quitting
            driver.quit()


def send_messages_from_dataframe(df: pd.DataFrame, message_template: str, media_path: str = None):
    import re
    variables = re.findall(r'\{([^}]+)\}', message_template)
    send_messages_with_variables(df, message_template, variables, media_path)
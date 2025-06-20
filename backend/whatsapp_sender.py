import os
import time
import random
import pandas as pd
from typing import List
import sys
import appdirs
import logging
from logging.handlers import RotatingFileHandler
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# App config
APP_AUTHOR = "YourCompany"
APP_NAME = "CampaignFlow"
WHATSAPP_WEB_URL = "https://web.whatsapp.com"
TYPING_SPEED_RANGE = (0.01, 0.05)
DELAY_BETWEEN_MESSAGES = (5, 15)
MEDIA_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".mp4", ".mov", ".avi", ".mkv", ".3gp"}

# Logging setup
LOG_FILE_PATH = os.path.join(appdirs.user_data_dir(APP_NAME, APP_AUTHOR), "app.log")
os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=1024*1024*5, backupCount=5, encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

def safe_print(message):
    logger.info(message)

USER_DATA_DIR = os.path.join(appdirs.user_data_dir(APP_NAME, APP_AUTHOR), "selenium_profile")
os.makedirs(USER_DATA_DIR, exist_ok=True)

def human_typing(element, text: str):
    for char in text:
        if char == "\n":
            element.send_keys(Keys.SHIFT, Keys.ENTER)
        else:
            element.send_keys(char)
        time.sleep(random.uniform(*TYPING_SPEED_RANGE))

def replace_variables_in_message(message_template: str, row_data: dict, variables: List[str]) -> str:
    personalized_message = message_template
    for variable in variables:
        placeholder = f"{{{variable}}}"
        value = str(row_data.get(variable, "")) if pd.notna(row_data.get(variable, "")) else ""
        personalized_message = personalized_message.replace(placeholder, value)
    return personalized_message

def send_whatsapp_message_enhanced(driver, phone: str, personalized_message: str, contact_name: str, media_path: str = None):
    url = f"https://web.whatsapp.com/send?phone={phone}&text&app_absent=0"
    driver.get(url)
    safe_print(f"📱 Opening chat with {phone} ({contact_name})...")

    try:
        message_box_xpath = '//div[@title="Type a message"] | //div[@data-tab="10"]'
        message_box = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, message_box_xpath)))

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
                    attach_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    break
                except:
                    continue

            if not attach_button:
                safe_print("❌ Could not find attach button. Sending message without media.")
                message_box.send_keys(Keys.ENTER)
                return

            attach_button.click()
            time.sleep(1)

            file_input_xpath = '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]' if ext in MEDIA_EXTENSIONS else '//input[@accept="*"]'
            file_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, file_input_xpath)))
            file_input.send_keys(media_path)
            time.sleep(2)

            send_button_xpath = '//div[@role="button" and @aria-label="Send"]'
            send_btn = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, send_button_xpath)))
            driver.execute_script("arguments[0].scrollIntoView(true);", send_btn)
            time.sleep(0.5)
            send_btn.click()
        else:
            message_box.send_keys(Keys.ENTER)

        safe_print(f"✅ Message sent to {contact_name} ({phone})")

    except Exception as e:
        safe_print(f"❌ Error sending to {phone}: {e}")

def send_messages_with_variables(df: pd.DataFrame, message_template: str, variables: List[str], media_path: str = None):
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--remote-debugging-port=9222")

    try:
        driver = uc.Chrome(options=options, user_data_dir=USER_DATA_DIR)

        safe_print("🔓 Opening WhatsApp Web. Please scan QR code if not already logged in…")
        driver.get(WHATSAPP_WEB_URL)

        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"]')))
        safe_print("✅ Logged into WhatsApp Web.")

        for index, row in df.iterrows():
            phone_raw = str(row.get("phone", "")).strip().replace(" ", "").replace("+", "")
            if not phone_raw.isdigit():
                safe_print(f"⚠️ Skipping invalid phone number: {phone_raw}")
                continue

            contact_name = next((str(row[field]) for field in ["name", "fullName", "full_name", "firstName", "first_name"]
                                 if field in row and pd.notna(row[field])), "Friend")

            row_dict = row.to_dict()
            personalized_message = replace_variables_in_message(message_template, row_dict, variables)

            send_whatsapp_message_enhanced(driver, phone_raw, personalized_message, contact_name, media_path)

            sleep_time = random.randint(*DELAY_BETWEEN_MESSAGES)
            safe_print(f"⏱️ Sleeping {sleep_time}s before next message...\n")
            time.sleep(sleep_time)

        safe_print("🎉 All messages sent successfully!")

    except Exception as e:
        safe_print(f"❌ Error in message sending process: {e}")
        logger.exception("Full traceback for error:")
    finally:
        if 'driver' in locals() and driver:
            driver.quit()

def send_messages_from_dataframe(df: pd.DataFrame, message_template: str, media_path: str = None):
    import re
    variables = re.findall(r'\{([^}]+)\}', message_template)
    send_messages_with_variables(df, message_template, variables, media_path)

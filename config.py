import os
import time

# DOCKER ENVIRONMENT VARIABLES
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "abc")
TELEGRAM_ADMIN = os.environ.get("TELEGRAM_ADMIN", "abc")
TELEGRAM_GROUP = os.environ.get("TELEGRAM_GROUP", "abc")
TELEGRAM_THREAD = os.environ.get("TELEGRAM_THREAD", "1")
LANGUAGE = os.environ.get("LANGUAGE", "ES")
TZ = os.environ.get("TZ", "UTC")

# Aplica la zona horaria para las marcas de tiempo
os.environ["TZ"] = TZ
time.tzset()

# CONSTANTS
ANONYMOUS_USER_ID = "1087968824"
DATA_PATH = "/app/data"
DEVICES_FILE = "devices"
DEVICES_FILE_PATH = f'{DATA_PATH}/{DEVICES_FILE}'
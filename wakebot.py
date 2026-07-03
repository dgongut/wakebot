import re
import os
import telebot
from telebot import util
from telebot.types import InlineKeyboardMarkup
from telebot.types import InlineKeyboardButton
from wakeonlan import send_magic_packet
from datetime import datetime
from config import *
import time
import threading
import json
import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor
import device_store

VERSION = "1.1.0"
MAX_NAME_LENGTH = 46
MAC_REGEX = re.compile(r'^([0-9a-fA-F]{2}[:\-.]){5}[0-9a-fA-F]{2}$')

def debug(message):
	print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - DEBUG: {message}')

def error(message):
	print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - ERROR: {message}')

def warning(message):
	print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - WARNING: {message}')

if LANGUAGE.lower() not in ("es", "en"):
	error("LANGUAGE only can be ES/EN")
	sys.exit(1)

device_data = {}

# MODULO DE TRADUCCIONES
def load_locale(locale):
	with open(f"/app/locale/{locale}.json", "r", encoding="utf-8") as file:
		return json.load(file)

# Se carga una única vez en memoria al arrancar
MESSAGES = load_locale(LANGUAGE.lower())

def get_text(key, *args):
	if key in MESSAGES:
		translated_text = MESSAGES[key]
		for i, arg in enumerate(args, start=1):
			placeholder = f"${i}"
			translated_text = translated_text.replace(placeholder, str(arg))
		return translated_text
	else:
		warning(f"key ['{key}'] is not in locale {LANGUAGE}")
		return f"key ['{key}'] is not in locale {LANGUAGE}"


# Comprobación inicial de variables
if "abc" == TELEGRAM_TOKEN:
	error(get_text("error_bot_token"))
	sys.exit(1)

if ":" not in TELEGRAM_TOKEN:
	error(get_text("error_bot_token_invalid"))
	sys.exit(1)

if "abc" == TELEGRAM_ADMIN:
	error(get_text("error_bot_telegram_admin"))
	sys.exit(1)

if str(ANONYMOUS_USER_ID) in str(TELEGRAM_ADMIN).split(','):
	error(get_text("error_bot_telegram_admin_anonymous"))
	sys.exit(1)

if "abc" == TELEGRAM_GROUP:
	if len(str(TELEGRAM_ADMIN).split(',')) > 1:
		error(get_text("error_multiple_admin_only_with_group"))
		sys.exit(1)
	TELEGRAM_GROUP = TELEGRAM_ADMIN

try:
	TELEGRAM_THREAD = int(TELEGRAM_THREAD)
except:
	error(get_text("error_bot_telegram_thread", TELEGRAM_THREAD))
	sys.exit(1)

if not os.path.exists(DATA_PATH):
	os.makedirs(DATA_PATH)

# Instanciamos el bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)
BOT_INFO = bot.get_me()
BOT_USERNAME = BOT_INFO.username
BOT_ID = BOT_INFO.id

@bot.message_handler(commands=["start", "wake", "list", "add", "remove", "rename", "version", "donate"])
def command_controller(message):
	userId = message.from_user.id
	comando = message.text.split(' ', 1)[0]
	messageId = message.id

	debug(f"COMMAND: {comando}")
	debug(f"USER: {userId}")
	debug(f"CHAT/GROUP: {message.chat.id}")
	message_thread_id = message.message_thread_id
	if not message_thread_id:
		message_thread_id = 1
	debug(f"THREAD ID: {message_thread_id}")

	if message_thread_id != TELEGRAM_THREAD and (not message.reply_to_message or message.reply_to_message.from_user.id != BOT_ID):
		return

	if not is_admin(userId):
		warning(get_text("warning_not_admin", userId, message.from_user.username))
		send_message(chat_id=userId, message=get_text("user_not_admin"))
		return

	if comando not in ('/start', f'/start@{BOT_USERNAME}'):
		delete_message(messageId)

	if comando in ('/start', f'/start@{BOT_USERNAME}'):
		texto_inicial = get_text("menu")
		send_message(message=texto_inicial)

	elif comando in ('/wake', f'/wake@{BOT_USERNAME}'):
		send_device_list(action_prefix="wake", emoji="⚡️", prompt_key="wake_message", show_status=True)

	elif comando in ('/list', f'/list@{BOT_USERNAME}'):
		send_device_details()

	elif comando in ('/add', f'/add@{BOT_USERNAME}'):
		if device_data.pop(userId, None) is not None:
			delayed_delete_in_thread(message=get_text("cancel_input"), seconds=10)
		device_data[userId] = {'state': 'asking_name'}
		markup = InlineKeyboardMarkup(row_width = 1)
		markup.add(InlineKeyboardButton(get_text("button_cancel"), callback_data="cancelAdd"))
		send_message(message=get_text("input_name"), reply_markup=markup)

	elif comando in ('/remove', f'/remove@{BOT_USERNAME}'):
		send_device_list(action_prefix="remove", emoji="🗑️", prompt_key="remove_message")

	elif comando in ('/rename', f'/rename@{BOT_USERNAME}'):
		send_device_list(action_prefix="rename", emoji="✏️", prompt_key="rename_message")

	elif comando in ('/version', f'/version@{BOT_USERNAME}'):
		delayed_delete_in_thread(message=get_text("version", VERSION), seconds=15)

	elif comando in ('/donate', f'/donate@{BOT_USERNAME}'):
		delayed_delete_in_thread(message=get_text("donate"), seconds=45)

@bot.callback_query_handler(func=lambda mensaje: True)
def button_controller(call):
	messageId = call.message.id
	userId = call.from_user.id

	if not is_admin(userId):
		warning(get_text("warning_not_admin", userId, call.from_user.username))
		send_message(chat_id=userId, message=get_text("user_not_admin"))
		return

	delete_message(messageId)
	if call.data == "cerrar":
		return
	
	if call.data in ("cancelAdd", "cancelRename"):
		device_data.pop(userId, None)
		return

	parts = call.data.split("|", 1)
	if len(parts) != 2:
		return
	command, mac = parts
	device = get_device_by_mac(mac=mac)
	if not device:
		send_message(message=get_text("device_not_found"))
		return
	name = device[0]['name']
	ip = device[0]['ip']

	if command == "wake":
		debug(message=get_text("debug_sending_wol", name, mac, ip))
		try:
			send_magic_packet(mac)
		except Exception as e:
			error(get_text("error_sending_wol", name, e))
		send_message(message=get_text("device_awoke", name))

	if command == "remove":
		remove_device(name)
		send_message(message=get_text("device_removed", name, mac, ip))

	if command == "rename":
		if device_data.pop(userId, None) is not None:
			delayed_delete_in_thread(message=get_text("cancel_input"), seconds=10)
		device_data[userId] = {'state': 'asking_new_name', 'mac': mac, 'old_name': name}
		markup = InlineKeyboardMarkup(row_width = 1)
		markup.add(InlineKeyboardButton(get_text("button_cancel"), callback_data="cancelRename"))
		send_message(message=get_text("input_new_name", name), reply_markup=markup)


# Manejar respuestas de texto
@bot.message_handler(func=lambda message: True)
def handle_message(message):
	userId = message.from_user.id
	text = message.text

	debug(f"USER: {userId}")
	debug(f"CHAT/GROUP: {message.chat.id}")
	message_thread_id = message.message_thread_id
	if not message_thread_id:
		message_thread_id = 1
	debug(f"THREAD ID: {message_thread_id}")

	if message_thread_id != TELEGRAM_THREAD and (not message.reply_to_message or message.reply_to_message.from_user.id != BOT_ID):
		return

	if not is_admin(userId):
		warning(get_text("warning_not_admin", userId, message.from_user.username))
		send_message(chat_id=userId, message=get_text("user_not_admin"))
		return

	if userId not in device_data:
		return

	state = device_data[userId]['state']

	if state == 'asking_name':
		if len(text) > MAX_NAME_LENGTH or '|' in text or '`' in text or exist_device(text):
			send_message(message=get_text("input_name_invalid"))
			return
		device_data[userId]['name'] = text
		markup = InlineKeyboardMarkup(row_width = 1)
		markup.add(InlineKeyboardButton(get_text("button_cancel"), callback_data="cancelAdd"))
		send_message(message=get_text("input_mac"), reply_markup=markup)
		device_data[userId]['state'] = 'asking_mac'

	elif state == 'asking_mac':
		if not MAC_REGEX.match(text):
			send_message(message=get_text("input_mac_invalid"))
			return
		mac = normalize_mac(text)
		if get_device_by_mac(mac):
			send_message(message=get_text("input_mac_duplicated"))
			return
		device_data[userId]['mac'] = mac
		markup = InlineKeyboardMarkup(row_width = 1)
		markup.add(InlineKeyboardButton(get_text("button_cancel"), callback_data="cancelAdd"))
		send_message(message=get_text("input_ip"), reply_markup=markup)
		device_data[userId]['state'] = 'asking_ip'

	elif state == 'asking_ip':
		patron = r'^(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]?|0)' \
					r'\.(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]?|0)' \
					r'\.(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]?|0)' \
					r'\.(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]?|0)$'

		if not re.match(patron, text):
			send_message(message=get_text("input_ip_invalid"))
			return
		device_data[userId]['ip'] = text
		name = device_data[userId]['name']
		mac = device_data[userId]['mac']
		ip = device_data[userId]['ip']
		add_device(name, mac, ip)
		send_message(message=get_text("device_added", name, mac, ip))
		device_data.pop(userId, None)

	elif state == 'asking_new_name':
		old_name = device_data[userId]['old_name']
		if len(text) > MAX_NAME_LENGTH or '|' in text or '`' in text or (text != old_name and exist_device(text)):
			send_message(message=get_text("input_name_invalid"))
			return
		rename_device(old_name, text)
		send_message(message=get_text("device_renamed", old_name, text))
		device_data.pop(userId, None)

def delayed_delete(message, seconds):
	x = send_message(message=message)
	if x is None:
		return
	time.sleep(seconds)
	delete_message(x.message_id)

def delayed_delete_in_thread(message, seconds):
	hilo = threading.Thread(target=delayed_delete, args=(message, seconds))
	hilo.start()

def store_device_json(devices):
	device_store.store_devices(DEVICES_FILE_PATH, devices)

def read_devices_json():
	return device_store.read_devices(DEVICES_FILE_PATH)

def add_device(name, mac, ip):
	device_store.add_device(DEVICES_FILE_PATH, name, mac, ip)

def remove_device(name):
	device_store.remove_device(DEVICES_FILE_PATH, name)

def rename_device(name, new_name):
	device_store.rename_device(DEVICES_FILE_PATH, name, new_name)

def exist_device(name):
	return device_store.exist_device(DEVICES_FILE_PATH, name)

def get_device_by_mac(mac):
	return device_store.get_device_by_mac(DEVICES_FILE_PATH, mac)

def normalize_mac(mac):
	return device_store.normalize_mac(mac)

def is_device_online(ip):
	try:
		result = subprocess.run(
			["ping", "-c", "1", "-W", "1", ip],
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL,
		)
		return result.returncode == 0
	except Exception:
		return False

def send_device_list(action_prefix, emoji, prompt_key, show_status=False):
	try:
		devices = read_devices_json()
	except Exception as e:
		error(get_text("error_reading_devices_file", e))
		devices = []

	if not devices:
		send_message(message=get_text("empty_file"), parse_mode="html")
		return

	statuses = {}
	if show_status:
		with ThreadPoolExecutor(max_workers=10) as executor:
			statuses = dict(executor.map(lambda d: (d['mac'], is_device_online(d['ip'])), devices))

	markup = InlineKeyboardMarkup(row_width = 1)
	for device in devices:
		if show_status:
			label_emoji = "🟢" if statuses.get(device['mac']) else "🔴"
		else:
			label_emoji = emoji
		markup.add(InlineKeyboardButton(f"{label_emoji} {device['name']}", callback_data=f"{action_prefix}|{device['mac']}"))
	markup.add(InlineKeyboardButton(get_text("button_close"), callback_data="cerrar"))
	send_message(message=get_text(prompt_key), reply_markup=markup)

def send_device_details():
	try:
		devices = read_devices_json()
	except Exception as e:
		error(get_text("error_reading_devices_file", e))
		devices = []

	if not devices:
		send_message(message=get_text("empty_file"), parse_mode="html")
		return

	mac_counts = {}
	for device in devices:
		mac_counts[device['mac']] = mac_counts.get(device['mac'], 0) + 1

	has_duplicates = False
	lines = [get_text("list_header"), ""]
	for i, device in enumerate(devices, start=1):
		duplicated = mac_counts[device['mac']] > 1
		has_duplicates = has_duplicates or duplicated
		warn = " ⚠️" if duplicated else ""
		lines.append(get_text("list_item", i, device['name'], warn, device['mac'], device['ip']))

	if has_duplicates:
		lines.append("")
		lines.append(get_text("list_duplicate_note"))

	markup = InlineKeyboardMarkup(row_width = 1)
	markup.add(InlineKeyboardButton(get_text("button_close"), callback_data="cerrar"))
	send_message(message="\n".join(lines), reply_markup=markup)

def delete_message(message_id):
	try:
		bot.delete_message(TELEGRAM_GROUP, message_id)
	except:
		pass

def send_message(chat_id=TELEGRAM_GROUP, message=None, reply_markup=None, parse_mode="markdown", disable_web_page_preview=True):
	try:
		if TELEGRAM_THREAD == 1:
			return bot.send_message(chat_id, message, parse_mode=parse_mode, reply_markup=reply_markup, disable_web_page_preview=disable_web_page_preview)
		else:
			return bot.send_message(chat_id, message, parse_mode=parse_mode, reply_markup=reply_markup, disable_web_page_preview=disable_web_page_preview, message_thread_id=TELEGRAM_THREAD)
	except Exception as e:
		error(get_text("error_sending_message", chat_id, message, e))
		pass

def is_admin(userId):
	return str(userId) in str(TELEGRAM_ADMIN).split(',')

if __name__ == '__main__':
	debug(get_text("debug_starting_bot", VERSION))
	bot.set_my_commands([
		telebot.types.BotCommand("/start", get_text("menu_start")),
		telebot.types.BotCommand("/wake", get_text("menu_wake")),
		telebot.types.BotCommand("/list", get_text("menu_list")),
		telebot.types.BotCommand("/add", get_text("menu_add")),
		telebot.types.BotCommand("/remove", get_text("menu_remove")),
		telebot.types.BotCommand("/rename", get_text("menu_rename")),
		telebot.types.BotCommand("/version", get_text("menu_version")),
		telebot.types.BotCommand("/donate", get_text("menu_donate"))
		])
	starting_message = f"🫡 *WakeBot \n{get_text('active')}*"
	starting_message += f"\n_⚙️ v{VERSION}_"
	send_message(message=starting_message)
	bot.infinity_polling(timeout=60)

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

VERSION = "0.9.0"

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

def get_text(key, *args):
	messages = load_locale(LANGUAGE.lower())
	if key in messages:
		translated_text = messages[key]
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

if not os.path.exists(SCHEDULE_PATH):
	os.makedirs(SCHEDULE_PATH)

# Instanciamos el bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=["start", "wake", "add", "remove", "version", "donate"])
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

	if message_thread_id != TELEGRAM_THREAD and (not message.reply_to_message or message.reply_to_message.from_user.id != bot.get_me().id):
		return

	if not is_admin(userId):
		warning(get_text("warning_not_admin", userId, message.from_user.username))
		send_message(chat_id=userId, message=get_text("user_not_admin"))
		return
	
	if comando not in ('/start', f'/start@{bot.get_me().username}'):
		delete_message(messageId)

	if comando in ('/start', f'/start@{bot.get_me().username}'):
		texto_inicial = get_text("menu")
		send_message(message=texto_inicial)

	elif comando in ('/wake', f'/wake@{bot.get_me().username}'):
		markup = InlineKeyboardMarkup(row_width = 1)
		empty = True
		botones = []
		try:
			devices = read_devices_json()
			for device in devices:
				empty = False
				botones.append(InlineKeyboardButton(f"⚡️ {device['name']}", callback_data=f"wake|{device['mac']}"))
		except Exception as e:
			error(get_text("error_reading_devices_file", e))

		if empty:
			send_message(message=get_text("empty_file"), parse_mode="html")
		else:
			markup.add(*botones)
			markup.add(InlineKeyboardButton(get_text("button_close"), callback_data="cerrar"))
			send_message(message=get_text("wake_message"), reply_markup=markup)

	elif comando in ('/add', f'/add@{bot.get_me().username}'):
		try:
			del device_data[userId]
			delayed_delete_in_thread(message=get_text("cancel_input"), seconds=10)
		except:
			pass
		device_data[userId] = {'state': 'asking_name'}
		markup = InlineKeyboardMarkup(row_width = 1)
		markup.add(InlineKeyboardButton(get_text("button_cancel"), callback_data="cancelAdd"))
		x = send_message(message=get_text("input_name"), reply_markup=markup)

	elif comando in ('/remove', f'/remove@{bot.get_me().username}'):
		markup = InlineKeyboardMarkup(row_width = 1)
		empty = True
		botones = []
		try:
			devices = read_devices_json()
			for device in devices:
				empty = False
				botones.append(InlineKeyboardButton(f"🗑️ {device['name']}", callback_data=f"remove|{device['mac']}"))
		except Exception as e:
			error(get_text("error_reading_devices_file", e))

		if empty:
			send_message(message=get_text("empty_file"), parse_mode="html")
		else:
			markup.add(*botones)
			markup.add(InlineKeyboardButton(get_text("button_close"), callback_data="cerrar"))
			send_message(message=get_text("remove_message"), reply_markup=markup)
	
	elif comando in ('/version', f'/version@{bot.get_me().username}'):
		delayed_delete_in_thread(message=get_text("version", VERSION), seconds=15)

	elif comando in ('/donate', f'/donate@{bot.get_me().username}'):
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
	
	if call.data == "cancelAdd":
		try:
			del device_data[userId]
		except:
			pass
		return

	command, mac = call.data.split("|")
	device = get_device_by_mac(mac=mac)
	name = device[0]['name']
	ip = device[0]['ip']
	
	if command == "wake":
		debug(message=get_text("debug_sending_wol", name, mac, ip))
		try:
			send_magic_packet(mac, interface=ip)
		except:
			send_magic_packet(mac)
		send_message(message=get_text("device_awoke", name))

	if command == "remove":
		remove_device(name)
		send_message(message=get_text("device_removed", name, mac, ip))


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

	if message_thread_id != TELEGRAM_THREAD and (not message.reply_to_message or message.reply_to_message.from_user.id != bot.get_me().id):
		return

	if not is_admin(userId):
		warning(get_text("warning_not_admin", userId, message.from_user.username))
		send_message(chat_id=userId, message=get_text("user_not_admin"))
		return

	state = device_data[userId]['state']
	
	if state == 'asking_name':
		if len(text) >= 46 or '|' in text or exist_device(text):
			send_message(message=get_text("input_name_invalid"))
			return
		device_data[userId]['name'] = text
		markup = InlineKeyboardMarkup(row_width = 1)
		markup.add(InlineKeyboardButton(get_text("button_cancel"), callback_data="cancelAdd"))
		send_message(message=get_text("input_mac"), reply_markup=markup)
		device_data[userId]['state'] = 'asking_mac'

	elif state == 'asking_mac':
		patron = r'^([a-zA-Z0-9]{2}\.){5}[a-zA-Z0-9]{2}$'

		if not re.match(patron, text):
			send_message(message=get_text("input_mac_invalid"))
			return
		device_data[userId]['mac'] = text
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
		send_message(message=get_text("device_added", name, mac, ip))
		add_device(name, mac, ip)
		del device_data[userId]

def delayed_delete(message, seconds):
	x = send_message(message=message)
	time.sleep(seconds)
	delete_message(x.message_id)

def delayed_delete_in_thread(message, seconds):
	hilo = threading.Thread(target=delayed_delete, args=(message, seconds))
	hilo.start()

def store_device_json(devices):
	with open(FULL_SCHEDULE_PATH, 'w') as archivo:
		json.dump(devices, archivo, indent=4)

def read_devices_json():
	try:
		with open(FULL_SCHEDULE_PATH, 'r') as archivo:
			return json.load(archivo)
	except FileNotFoundError:
		return []

def add_device(name, mac, ip):
	devices = read_devices_json()
	devices.append({'name': name, 'mac': mac, 'ip': ip})
	store_device_json(devices)

def remove_device(name):
	devices = read_devices_json()
	devices = [device for device in devices if device['name'] != name]
	store_device_json(devices)

def exist_device(name):
	devices = read_devices_json()
	devices = [device for device in devices if device['name'] == name]
	return len(devices) > 0

def get_device_by_mac(mac):
	devices = read_devices_json()
	device = [device for device in devices if device['mac'] == mac]
	return device

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

def delete_line_from_file(file_path, line_to_delete):
	try:
		with open(file_path, "r") as file:
			lines = file.readlines()

		with open(file_path, "w") as file:
			for line in lines:
				if line.strip() != line_to_delete.strip():
					file.write(line)
	except Exception as e:
		error(get_text("error_deleting_from_file_with_error", e))

def is_admin(userId):
	return str(userId) in str(TELEGRAM_ADMIN).split(',')

if __name__ == '__main__':
	debug(get_text("debug_starting_bot", VERSION))
	bot.set_my_commands([
		telebot.types.BotCommand("/start", get_text("menu_start")),
		telebot.types.BotCommand("/wake", get_text("menu_wake")),
		telebot.types.BotCommand("/add", get_text("menu_add")),
		telebot.types.BotCommand("/remove", get_text("menu_remove")),
		telebot.types.BotCommand("/version", get_text("menu_version")),
		telebot.types.BotCommand("/donate", get_text("menu_donate"))
		])
	starting_message = f"🫡 *WakeBot \n{get_text('active')}*"
	starting_message += f"\n_⚙️ v{VERSION}_"
	send_message(message=starting_message)
	bot.infinity_polling(timeout=60)

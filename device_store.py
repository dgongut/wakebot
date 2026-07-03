import json
import re

# Lógica pura de almacenamiento y consulta de dispositivos.
# Sin efectos secundarios ni dependencias del bot: la ruta del fichero se
# recibe como parámetro para poder reutilizarla y testearla con facilidad.

def normalize_mac(mac):
	hex_only = re.sub(r'[:\-.]', '', mac)
	return ':'.join(hex_only[i:i + 2] for i in range(0, 12, 2)).lower()

def read_devices(path):
	try:
		with open(path, 'r') as archivo:
			return json.load(archivo)
	except FileNotFoundError:
		return []

def store_devices(path, devices):
	with open(path, 'w') as archivo:
		json.dump(devices, archivo, indent=4)

def add_device(path, name, mac, ip):
	devices = read_devices(path)
	devices.append({'name': name, 'mac': mac, 'ip': ip})
	store_devices(path, devices)

def remove_device(path, name):
	devices = read_devices(path)
	devices = [device for device in devices if device['name'] != name]
	store_devices(path, devices)

def rename_device(path, name, new_name):
	devices = read_devices(path)
	for device in devices:
		if device['name'] == name:
			device['name'] = new_name
	store_devices(path, devices)

def exist_device(path, name):
	devices = read_devices(path)
	return any(device['name'] == name for device in devices)

def get_device_by_mac(path, mac):
	devices = read_devices(path)
	return [device for device in devices if device['mac'] == mac]

import os
import tempfile
import unittest

import device_store


class NormalizeMacTest(unittest.TestCase):
	def test_accepts_colon_dash_dot_and_uppercase(self):
		expected = "aa:bb:cc:dd:ee:ff"
		self.assertEqual(device_store.normalize_mac("AA:BB:CC:DD:EE:FF"), expected)
		self.assertEqual(device_store.normalize_mac("aa-bb-cc-dd-ee-ff"), expected)
		self.assertEqual(device_store.normalize_mac("aa.bb.cc.dd.ee.ff"), expected)
		self.assertEqual(device_store.normalize_mac("Aa:bB:cc:DD:ee:Ff"), expected)

	def test_all_separators_produce_same_result(self):
		self.assertEqual(
			device_store.normalize_mac("01:23:45:67:89:ab"),
			device_store.normalize_mac("01-23-45-67-89-ab"),
		)


class DeviceStoreTest(unittest.TestCase):
	def setUp(self):
		fd, self.path = tempfile.mkstemp()
		os.close(fd)
		os.remove(self.path)  # empezamos sin fichero, como el bot en el primer arranque

	def tearDown(self):
		if os.path.exists(self.path):
			os.remove(self.path)

	def test_read_missing_file_returns_empty_list(self):
		self.assertEqual(device_store.read_devices(self.path), [])

	def test_add_and_read_device(self):
		device_store.add_device(self.path, "pc", "aa:bb:cc:dd:ee:ff", "192.168.1.10")
		devices = device_store.read_devices(self.path)
		self.assertEqual(devices, [{"name": "pc", "mac": "aa:bb:cc:dd:ee:ff", "ip": "192.168.1.10"}])

	def test_add_multiple_devices_preserves_all(self):
		device_store.add_device(self.path, "pc", "aa:bb:cc:dd:ee:01", "192.168.1.10")
		device_store.add_device(self.path, "nas", "aa:bb:cc:dd:ee:02", "192.168.1.11")
		self.assertEqual(len(device_store.read_devices(self.path)), 2)

	def test_exist_device(self):
		device_store.add_device(self.path, "pc", "aa:bb:cc:dd:ee:01", "192.168.1.10")
		self.assertTrue(device_store.exist_device(self.path, "pc"))
		self.assertFalse(device_store.exist_device(self.path, "unknown"))

	def test_get_device_by_mac(self):
		device_store.add_device(self.path, "pc", "aa:bb:cc:dd:ee:01", "192.168.1.10")
		found = device_store.get_device_by_mac(self.path, "aa:bb:cc:dd:ee:01")
		self.assertEqual(len(found), 1)
		self.assertEqual(found[0]["name"], "pc")

	def test_get_device_by_mac_not_found_returns_empty_list(self):
		device_store.add_device(self.path, "pc", "aa:bb:cc:dd:ee:01", "192.168.1.10")
		self.assertEqual(device_store.get_device_by_mac(self.path, "00:00:00:00:00:00"), [])

	def test_remove_device_by_name(self):
		device_store.add_device(self.path, "pc", "aa:bb:cc:dd:ee:01", "192.168.1.10")
		device_store.add_device(self.path, "nas", "aa:bb:cc:dd:ee:02", "192.168.1.11")
		device_store.remove_device(self.path, "pc")
		remaining = device_store.read_devices(self.path)
		self.assertEqual(len(remaining), 1)
		self.assertEqual(remaining[0]["name"], "nas")

	def test_rename_device_by_name(self):
		device_store.add_device(self.path, "pc", "aa:bb:cc:dd:ee:01", "192.168.1.10")
		device_store.rename_device(self.path, "pc", "workstation")
		devices = device_store.read_devices(self.path)
		self.assertEqual(devices[0]["name"], "workstation")
		self.assertEqual(devices[0]["mac"], "aa:bb:cc:dd:ee:01")

	def test_rename_device_unknown_name_is_noop(self):
		device_store.add_device(self.path, "pc", "aa:bb:cc:dd:ee:01", "192.168.1.10")
		device_store.rename_device(self.path, "unknown", "workstation")
		self.assertEqual(device_store.read_devices(self.path)[0]["name"], "pc")

	def test_rename_by_name_does_not_touch_devices_sharing_mac(self):
		device_store.add_device(self.path, "pc", "aa:bb:cc:dd:ee:01", "192.168.1.10")
		device_store.add_device(self.path, "pc-dup", "aa:bb:cc:dd:ee:01", "192.168.1.11")
		device_store.rename_device(self.path, "pc", "workstation")
		names = [d["name"] for d in device_store.read_devices(self.path)]
		self.assertEqual(names, ["workstation", "pc-dup"])


if __name__ == "__main__":
	unittest.main()

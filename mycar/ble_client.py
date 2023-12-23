from bluepy.btle import Peripheral, UUID
from bluepy.btle import Scanner, DefaultDelegate
import time
import global_state

new_distance = None  # Variable to store the new distance value
isScanning = False  # Flag to indicate if scanning is in progress

class ScanDelegate(DefaultDelegate):
	# Custom delegate class for handling scan results
	def __init__(self):
		DefaultDelegate.__init__(self)

	def handleDiscovery(self, dev, isNewDev, isNewData):
		# Called when a new device is discovered
		global isScanning
		if isNewDev:
			if isScanning:
				print("NOTE: Scanning Device...")
				isScanning = False  # Reset scanning flag after first device discovery
			# Uncomment to See Discovered Device and Address List
			#print("Discovered device", dev.addr)
			#print("Received new data from", dev.addr)

class MyDelegate(DefaultDelegate):
	# Custom delegate class for handling BLE notifications
	def __init__(self):
		DefaultDelegate.__init__(self)

	def handleNotification(self, cHandle, data):
		# Called when a BLE notification is received
		global new_distance
		if cHandle == 0:
			# Handle specific data for a certain characteristic
			ia = [int.from_bytes(data[i : i + 2], "little", signed="True") for i in range(0, len(data), 2)]
			# print(f"Magnometer Notification: {ia[0]} {ia[1]} {ia[2]} from Handle {cHandle}")
		else:
			# Update global distance variable based on the notification data
			new_distance = int.from_bytes(data, "little")
			global_state.global_state.update_tof_distance(new_distance)  # Update global state
			# print(f"ToF Notification: {new_distance}")

def get_tof_distance():
	# Function to get the latest Time of Flight (ToF) distance
	return new_distance

def continuous_scan():
	# Function to continuously scan for BLE devices
	global isScanning
	isScanning = True
	scanner = Scanner().withDelegate(ScanDelegate())
	devices = scanner.scan(10.0)  # Scan for devices for 10 seconds

	n = 0
	addr = []  # List to store device addresses
	for dev in devices:
		# Print details of each discovered device
		print("%d: Device %s (%s), RSSI=%d dB" % (n, dev.addr, dev.addrType, dev.rssi))
		addr.append(dev.addr)
		if dev.addr == 'e3:9f:46:c7:39:e1':
			print("Device MATCH #########################")
		n += 1
		for (adtype, desc, value) in dev.getScanData():
			print(" %s = %s" % (desc, value))
	# Uncomment if you want to choose your own device
	#number = input('Enter your device number: ')
	#print('Device', number)
	#num = int(number)
	#print(addr[num])

	print("Connecting...")
	dev = Peripheral('e3:9f:46:c7:39:e1', 'random')  # Connect to a specific device
	print("CONNECTED")
	dev.setDelegate(MyDelegate())  # Set the delegate for handling notifications

	try:
		# Setup and handling of specific BLE services and characteristics
		hrc = dev.getCharacteristics(uuid=UUID(0x2A15))[0]
		print(f"Heartrate cHandle: {hrc.getHandle()}")
		cccd_descriptor = hrc.getDescriptors(forUUID=0x2902)[0]
		new_cccd_value = bytearray([0x01, 0x00])
		cccd_descriptor.write(new_cccd_value)

		magnetoService = dev.getServiceByUUID(UUID(0x1815))
		mg = dev.getCharacteristics(uuid=UUID(0x2A55))[0]
		print(f"Magnetometer cHandle: {mg.getHandle()}")
		cccd_descriptor = mg.getDescriptors(forUUID=0x2902)[0]
		new_cccd_value = bytearray([0x01, 0x00])
		cccd_descriptor.write(new_cccd_value)

		while True:
			# Waiting for notifications
			if dev.waitForNotifications(1.0):
				continue
			print("waiting")
	finally:
		dev.disconnect()  # Ensure disconnection in the end
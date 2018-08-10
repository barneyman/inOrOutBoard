#!/usr/bin/python

# sudo python3 -m pip install pybluez smbus2
import bluetooth
import time
import sys
import http.client
import smbus2
import json

btaddrsWeCareAbout=[{ '5C:51:81:A2:D6:AE': "Barney"}]

lightActions={ "homeAlone":[
				# kitchen
				"sonoff_a799d7.local"
				],
		"full":[
				# kitchen
				"sonoff_a799d7.local",
				"sonoff_68ecd4.local",
				"sonoff_2dacf4.local"

				]
		}

currentConfig=json.load(open('/home/pi/bluetooth/config.json'))
currentState=json.load(open('/home/pi/bluetooth/state.json'))


btaddrsWeCareAbout=currentConfig["BTaddresses"]
lightActions=currentConfig["Actions"]

print(btaddrsWeCareAbout,lightActions)


if currentState['current']==sys.argv[1]:
	print("bailed")
	sys.exit(0)

print ("In/Out Board")

# first - get the lux

i2cbus=smbus2.SMBus(1)
luxAddress=0x4a
minLuxValue=250

msb=i2cbus.read_byte_data(luxAddress,0x3)
lsb=i2cbus.read_byte_data(luxAddress,0x4)

exponent=(msb&0xf0) >> 4
mantissa=(lsb&0x0f) | ((msb&0x0f) << 4)

luxValue=mantissa * 2**exponent

print ("Checking " + time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime()))
print ("lux is ", luxValue)

isanyonein=False
for line in btaddrsWeCareAbout:
	for key, val in line.items():
		result = bluetooth.lookup_name(key, timeout=5)
		print(val," ",)
		if(result!=None):
			print("in")
			isanyonein=True
		else:
			print("out")
thingsToPing=[]

if luxValue < minLuxValue:
	if isanyonein==False:
		thingsToPing=lightActions['homeAlone']
	else:
		# we don't want it turning things OFF when we're here
		if sys.argv[1]=="ON":
			thingsToPing=lightActions['full']

	for each in thingsToPing:
		print (each)
		conn=http.client.HTTPConnection(each)
		if sys.argv[1]=='ON':
			# http://sonoff_a799d7.local/button?action=on&port=0
			conn.request(url="/button?action=on&port=0", method="GET")

		if sys.argv[1]=='OFF':
			# http://sonoff_a799d7.local/button?action=on&port=0
			conn.request(url="/button?action=off&port=0", method="GET")

		r=conn.getresponse()

	currentState['current']=sys.argv[1]
	with open('/home/pi/bluetooth/state.json', 'w') as outfile:
	    json.dump(currentState, outfile)

else:
	print("too bright!")


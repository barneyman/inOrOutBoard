#!/usr/bin/python

# sudo python3 -m pip install pybluez smbus2
import bluetooth
import time
import sys
import http.client
import smbus2
import json



def sendOut(list, command):	
	for each in list:
		try:
			print (each)
			conn=http.client.HTTPConnection(each)
			if command=='ON':
				conn.request(url="/button?action=on&port=0", method="GET")

			if command=='OFF':
				conn.request(url="/button?action=off&port=0", method="GET")

			r=conn.getresponse()
		except:
			print("Exception in http request")








currentConfig=json.load(open('/home/pi/bluetooth/config.json'))
currentState=json.load(open('/home/pi/bluetooth/state.json'))

btaddrsWeCareAbout=currentConfig["BTaddresses"]
lightActions=currentConfig["Actions"]


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
			break
		else:
			print("out")

# if we're the same as last time - bail
if currentState['current']==sys.argv[1] and currentState['occupied']==isanyonein:
	print("bailed")
	sys.exit(0)


thingsToPing=[]


# now, we do some working out ...

if currentState['current']=="OFF" and sys.argv[1]=="ON":
	print ("from OFF to ON check")
	if luxValue < minLuxValue:
		# it's got dark enough to care ...
		if isanyonein==False:
			print ("vacant ON")
			sendOut(lightActions['vacant'], "ON")
			currentState['current']="ON"
		else:
			print ("occupied ON")
			sendOut(lightActions['occupied'], "ON")
			currentState['current']="ON"
	else:
		print ("too bright ", luxValue)
	



if currentState['current']=="ON":
	if sys.argv[1]=="OFF":
		print ("from ON to OFF")
		if isanyonein==False:
			sendOut(lightActions['vacant'], "OFF")
			print ("vacant OFF")
			currentState['current']="OFF"

	elif sys.argv[1]=="FORCE_OFF":
			sendOut(lightActions['vacant'], "OFF")
			sendOut(lightActions['occupied'], "OFF")
			currentState['current']="OFF"

	else:
		if isanyonein!=currentState['occupied']:
			print ("vacancy transition")
			if isanyonein==True:
				print ("to occupied")
				sendOut(lightActions['vacant'],"OFF")
				sendOut(lightActions['occupied'],"ON")
			else:
				print ("to vacant")
				sendOut(lightActions['occupied'],"OFF")
				sendOut(lightActions['vacant'],"ON")

			currentState['current']="ON"


currentState['occupied']=isanyonein

with open('/home/pi/bluetooth/state.json', 'w') as outfile:
    json.dump(currentState, outfile)








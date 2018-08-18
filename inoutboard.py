#!/usr/bin/python

# sudo python3 -m pip install pybluez smbus2
import bluetooth
import time
import sys
import http.client
import smbus2
import json


#lightActions['vacant'],lightActions['occupied'])
def sendOutOffOn(offlist, onlist): 
	aggregateList={}
	for each in offlist:
		aggregateList[each]="OFF"
	# rely on replacements/overrides
	for each in onlist:
		aggregateList[each]="ON"

	print (aggregateList)

	for key, value in aggregateList.items():
		print(key,":",value)
		sendOutOne(key,value)


def sendOut(list, command):	
	for each in list:
		sendOutOne(each,command)



def sendOutOne(each, command):	
	try:
		print (each,command)
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
minLuxValue=1000

msb=i2cbus.read_byte_data(luxAddress,0x3)
lsb=i2cbus.read_byte_data(luxAddress,0x4)

exponent=(msb&0xf0) >> 4
mantissa=(lsb&0x0f) | ((msb&0x0f) << 4)

luxValue=mantissa * 2**exponent

print ("Checking " + time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime()))
print ("lux is ", luxValue)

# check all the BT addresse we care about
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

# DEBUG - hmm - python ternery!
# isanyonein= False if currentState['occupied']==True else True


# if we're the same as last time - bail
if currentState['current']==sys.argv[1] and currentState['occupied']==isanyonein:
	print("bailed")
	sys.exit(0)


thingsToPing=[]


# now, we do some working out ...

# 'normal' use case - OFF turning to ON
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



# if we think we're on ...
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

	# sys.argv==ON by elimination
	elif sys.argv[1]=="ON":
		if isanyonein!=currentState['occupied']:
			print ("vacancy transition")
			if isanyonein==True:
				print ("to occupied")
				sendOutOffOn(lightActions['vacant'],lightActions['occupied'])
#				sendOut(lightActions['vacant'],"OFF")
#				sendOut(lightActions['occupied'],"ON")
			else:
				print ("to vacant")
				sendOutOffOn(lightActions['occupied'],lightActions['vacant'])
#				sendOut(lightActions['occupied'],"OFF")
#				sendOut(lightActions['vacant'],"ON")
			currentState['current']="ON"

	else:
		print (currentState)

currentState['occupied']=isanyonein

with open('/home/pi/bluetooth/state.json', 'w') as outfile:
    json.dump(currentState, outfile)








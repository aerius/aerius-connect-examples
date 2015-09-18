#!/usr/bin/python3
"""
Dit script is als voorbeeld om het gebruik van AERIUS connect te demonstreren.

Dit voorbeeld script vertuurt de invoer naar AERIUS connect om berekend te worden.
Indien de invoer niet valide is wordt dit teruggegeven. Als de invoer wel goed was,
wordt de berekening gestart en het resultaat in delen terug ontvangen als een
rpc method vanaf de server naar de client.

Een volledige implementatie zou de json-rpc aanroep vanaf de server moeten interpreteren
als een echte json-rpc methode. Dit voorbeeld print alleen de ontvangen data vanaf de server.
"""
import json
import time
import os
import pprint
import sys
import getopt
import websocket

AERIUS_SERVER = "ws://connect.aerius.nl"
debug = False

def calculate(inputfile):
	compare = ""
	f = open(inputfile,'r')
	data = f.read()
	f.close
	# create json text object
	json_text = """
	{
		"jsonrpc":"2.0",
		"id":0,
		"method":"calculation.calculate",
		"params":{
			"options":{
				"calculationType":"NBWET",
				"year":2015,
				"substances":["NOX","NH3"]
			},
			"data":[{
				"dataType":"GML",
				"contentType":"TEXT",
				"data":""}],
			"callback":"callback"
		}
	}
	"""
	# replace paramaters
	json_data = json.loads(json_text)
	json_data["id"] = int(time.time() * 1000) #create unique id
	json_data["params"]["data"][0]["data"] = data
	print(json_text)

	#print(json.dumps(json_data))

	try:
		ws = websocket.create_connection(AERIUS_SERVER + "/connect/2/services")
	except Exception as e:
		print ("Unexpected connection error:", e)
		return

	try:
		#sending data
		ws.send(json.dumps(json_data))
		while True:
			result = ws.recv()
			if result == None:
				print ("nothing")
			else:
				print (json.loads(result))
		ws.close()
		if debug:
			print ("(DEBUG json data send:)")
			print (json.dumps(json_data))
			print ("(DEBUG json data recieved:)")
			print (result)
		# write result part
		if result.find("successful") > -1:
			json_output = json.loads(result)
			if (result.find("errors") > -1):
				for error in json_output["result"]["errors"]:
					print (error["errorCode"] + " - " + error["description"])
			else:
				print ("gml calculation added to the queue")
		else: 
			# we have JSON-RPC error
			json_output = json.loads(result)
			error = json_output["error"]
			print ("error: " + str(error["code"]) + " - " + error["message"])

	except Exception as e:
		print ("Unexpected result error:", e)

	finally:
		ws.close()

	return

def main(argv):
	opts, args = getopt.getopt(argv,"hdi:e:",["ifile="])
	for opt, arg in opts:
		if opt == '-h':
			print('AERIUS_calculate.py [-d] -i <gml file>')
			sys.exit()
		elif opt == '-d':
			global debug
			debug = True
		elif opt in ("-i", "--ifile"):
			inputfile = arg

	print("reading ", inputfile)

	calculate(inputfile)

if __name__ == "__main__":
	main(sys.argv[1:])

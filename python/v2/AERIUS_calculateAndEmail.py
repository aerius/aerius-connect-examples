#!/usr/bin/python3
"""
Dit script is als voorbeeld om het gebruik van AERIUS connect te demonstreren.

Dit voorbeeld script vertuurt de invoer naar AERIUS connect om berekend te worden.
Indien de invoer niet valide is wordt dit teruggegeven. Als de invoer wel goed was,
wordt de berekening gestart en het resultaat verstuurt naar het opgegeven e-mailadres.
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

def calculateAndEmail(inputfile, email):
	compare = ""
	f = open(inputfile,'r')
	data = f.read()
	f.close
	# create json text object
	json_text = """
	{
		"jsonrpc":"2.0",
		"id":0,
		"method":"calculation.calculateAndEmail",
		"params":{
			"email":"",
			"options":{
				"calculationType":"NBWET",
				"year":2015,
				"substances":["NOX","NH3"]
			},
			"data":[{
				"dataType":"GML",
				"contentType":"TEXT",
				"data":""}]
		}
	}
	"""
	# replace paramaters
	json_data = json.loads(json_text)
	json_data["id"] = int(time.time() * 1000) #create unique id
	json_data["params"]["data"][0]["data"] = data
	json_data["params"]["email"] = email
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
		result = ws.recv()
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
	opts, args = getopt.getopt(argv,"hdi:e:",["ifile=","eemail="])
	for opt, arg in opts:
		if opt == '-h':
			print('AERIUS_calculateAndEmail.py [-d] -i <gml file> -e <email address>')
			sys.exit()
		elif opt == '-d':
			global debug
			debug = True
		elif opt in ("-i", "--ifile"):
			inputfile = arg
		elif opt in ("-e", "--eemail"):
			email = arg

	print("reading ", inputfile)

	calculateAndEmail(inputfile,email)

if __name__ == "__main__":
	main(sys.argv[1:])

#!/usr/bin/python3
import json
import time
import os
import pprint
import sys
import getopt
import websocket

AERIUS_SERVER = "connect.aerius.nl"
debug = False

"""
Open the file, create json object send this json to AERIUS connect endpoint
Process the result test on successful and write the result to a result file
"""
def gml_calculateAndEmail(inputfile,comparefile):
    compare = ""
    f = open(inputfile,'r')
    data = f.read()
    f.close
    if comparefile != "":
        f = open(comparefile,'r')
        compare = f.read()
        f.close
    # create json text object
    json_text = """
    {
        "jsonrpc":"2.0",
        "id":0,
        "method":"calculation.calculateAndEmail",
        "params":{
			"email":"aeriusmail+connect@gmail.com",
			"options":{
				"calculationType":"NBWET",
				"year":2020,
				"substances":["NOX","NH3"],
				"maximumRange":10000,
				"tempProject":0,
				"tempProjectYears":1
			},
			"data":[{
				"dataType":"GML",
				"contentType":"TEXT",
				"data":""}]
        }
    }
    """
    # replace paramaters
    print(json_text)
    json_data = json.loads(json_text)
    json_data["id"] = int(time.time() * 1000) #create unique id
    json_data["params"]["data"][0]["data"] = data
    if compare != "":
        row = json_data["params"]["data"][0]
        json_data["params"]["data"].append(row)
        json_data["params"]["data"][1]["data"] = compare
	
    print(json.dumps(json_data))
	
    try:
        ws = websocket.create_connection("ws://" + AERIUS_SERVER + "/connect/2/services")
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
                print ("gml calculation added to the qui")
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
    comparefile = ""
    opts, args = getopt.getopt(argv,"hdi:c:",["ifile=","cfile="])
    for opt, arg in opts:
        if opt == '-h':
            print('AERIUS_calculateAndEmail.py [-d] -i <gml file current situation> -c <gml file compare with new situation')
            sys.exit()
        elif opt == '-d':
            global debug
            debug = True
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-c", "--cfile"):
            comparefile = arg

    print("reading ", inputfile)
    if comparefile != "":
        print("reading", comparefile)
		
    gml_calculateAndEmail(inputfile,comparefile)

if __name__ == "__main__":
   main(sys.argv[1:])

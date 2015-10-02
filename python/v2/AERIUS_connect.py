#!/usr/bin/python3
"""
Dit script is als voorbeeld om het gebruik van AERIUS connect te demonstreren.

Deze module bevat het generiek deel om de data via websocket naar AERIUS connect te sturen.
"""
import json
import time
import sys
import getopt
import websocket

AERIUS_SERVER = "ws://connect.aerius.nl"
AERIUS_PATH = "/connect/2/services"

def processResults(debug, json_data):
    json_output = False
    if debug:
        print ("(DEBUG json data send:)")
        print (json.dumps(json_data))
        print ("(DEBUG json data received:)")
    # write result part
    json_output = json.loads(json_data)
    if json_data.find("successful") > -1:
        if (json_data.find("errors") > -1):
            for error in json_output["result"]["errors"]:
                print (error["code"] + " - " + error["message"])
        else:
            print ("Call successful")
    else: 
        # we have JSON-RPC error
        error = json_output["error"]
        print ("error: " + str(error["code"]) + " - " + error["message"])
    return json_output

def callConnect(debug, json_data):
    ws = websocket.create_connection(AERIUS_SERVER + AERIUS_PATH)
    try:
        #sending data
        ws.send(json.dumps(json_data))
        result = ws.recv()
        return processResults(debug, result)
    except Exception as e:
        print ("Unexpected connection error:", e)
        return False     
    finally:
        ws.close()

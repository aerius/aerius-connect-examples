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
# import os
# import pprint
import sys
import getopt
import websocket

AERIUS_SERVER = "ws://connect.aerius.nl"
AERIUS_PATH = "/connect/2/services"
debug = False


def calculate(inputfile):
    f = open(inputfile, 'r')
    data = f.read()
    f.close()
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
    # replace parameters
    json_data = json.loads(json_text)
    json_data["id"] = int(time.time() * 1000)  # create unique id
    json_data["params"]["data"][0]["data"] = data
    print(json_text)

    # print(json.dumps(json_data))

    try:
        ws = websocket.create_connection(AERIUS_SERVER + AERIUS_PATH)
    except Exception as e:
        print ("Unexpected connection error:", e)
        return

    try:
        result = ""
        # sending data
        ws.send(json.dumps(json_data))
        while True:
            result = ws.recv()
            if not result:
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
            if result.find("errors") > -1:
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


def usage(errorlevel=0):
    # Neat helptext to display by user request or in case of errors
    print "Usage: ", __file__, " [-d] -i <gml file>\n"
    print "-d   - Run in debug mode"
    print "-i   - Specify input file -i <gml file> or --ifile=<gml file>"
    print "-h   - Show this help text"
    sys.exit(errorlevel)


def main(argv):
    # Initialize inputfile here to prevent unassigned variable errors later on
    inputfile = ""

    # Try parsing arguments and catch any exceptions that getopt can throw at us
    try:
        opts, args = getopt.getopt(argv, 'hdi:e:', ['help', 'debug', "ifile="])
    except getopt.GetoptError as err:
        print(err)
        usage(2)

    # We expect at least 1 option so let's check for one
    if not opts:
        print("At least 1 option is required to run")
        usage()

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
        elif opt in ("-d", "--debug"):
            global debug
            debug = True
        elif opt in ("-i", "--ifile"):
            inputfile = arg

    # If still empty here no inputfile was specified
    if not inputfile:
        print("No input file specified!")
        usage()
    else:
        print("Reading ", inputfile)

    calculate(inputfile)


if __name__ == "__main__":
    main(sys.argv[1:])

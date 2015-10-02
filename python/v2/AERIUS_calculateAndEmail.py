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
from AERIUS_connect import processResults, callConnect

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
    callConnect(debug, json_data)

def usage():
    print('AERIUS_calculateAndEmail.py [-d] -i <gml file> -e <email address>')
    sys.exit()

def main(argv):
    inputfile = ''
    email = ''
    opts, args = getopt.getopt(argv,"hdi:e:",["ifile=","eemail="])
    for opt, arg in opts:
        if opt == '-h':
            usage()
        elif opt == '-d':
            global debug
            debug = True
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-e", "--eemail"):
            email = arg

    if not inputfile:
        print("No input file specified!")
        usage()
    if not email:
        print("No email specified!")
        usage()
    else:
        calculateAndEmail(inputfile,email)

if __name__ == "__main__":
    main(sys.argv[1:])

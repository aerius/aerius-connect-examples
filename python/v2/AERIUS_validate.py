#!/usr/bin/python3
"""
Dit script is als voorbeeld om het gebruik van AERIUS connect te demonstreren.

Dit voorbeeld script verstuurt de GML naar AERIUS connect en geeft terug of validatie goed was of de fouten.
"""
import json
import time
import os
import pprint
import sys
import getopt
from AERIUS_connect import processResults, callConnect

debug = False

def validate(inputfile):
    f = open(inputfile,'r')
    data = f.read()
    f.close
    # create json text object
    json_text = """
    {
        "jsonrpc":"2.0",
        "id":0,
        "method":"validation.validate",
        "params":{
            "dataType":"GML",
            "contentType":"TEXT",
            "data":""
        }
    }
    """
    # replace paramaters
    json_data = json.loads(json_text)
    json_data["id"] = int(time.time() * 1000) #create unique id
    json_data["params"]["data"] = data
    callConnect(debug, json_data)

def usage():
    print('AERIUS_validate.py [-d] -i <gml file>')
    sys.exit()

def main(argv):
    inputfile = ''
    opts, args = getopt.getopt(argv,"hdi:o:",["ifile=","ofile="])
    for opt, arg in opts:
        if opt == '-h':
            usage()
        elif opt == '-d':
            global debug
            debug = True
        elif opt in ("-i", "--ifile"):
            inputfile = arg
    
    if not inputfile:
        print("No input file specified!")
        usage()
    else:
        print("reading ", inputfile)
        validate(inputfile)

if __name__ == "__main__":
   main(sys.argv[1:])

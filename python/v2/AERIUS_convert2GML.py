#!/usr/bin/python3
"""
Dit script is als voorbeeld om het gebruik van AERIUS connect te demonstreren.

Dit voorbeeld script verstuurt de GML naar AERIUS connect en geeft een naar
de laatste versie van IMAER GML geconverteerd document terug of indien er
fouten waren deze terug gegeven.
"""
import json
import time
import os
import pprint
import sys
import getopt
from AERIUS_connect import processResults, callConnect

debug = False

def convert2GML(inputfile,outputfile):
    f = open(inputfile,'r')
    data = f.read()
    f.close
    # create json text object
    json_text = """
    {
        "jsonrpc":"2.0",
        "id":0,
        "method":"conversion.convert2GML",
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
    json_output = callConnect(debug, json_data)
    if json_output:
        print ("writing converted content to ", outputfile)
        fileOut = open(outputfile, "w+")
        fileOut.write(json_output["result"]["dataObject"]["data"])

def usage():
    print('AERIUS_convert2GML.py [-d] -i <gml file> -o <gml file>')
    sys.exit()

def main(argv):
    inputfile = ''
    outputfile = ''
    opts, args = getopt.getopt(argv,"hdi:o:",["ifile=","ofile="])
    for opt, arg in opts:
        if opt == '-h':
            usage()
        elif opt == '-d':
            global debug
            debug = True
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg

    if not inputfile:
        print("No input file specified!")
        usage()
    if not outputfile:
        print("No output file specified!")
        usage()
    else:
        print("reading ", inputfile)
        convert2GML(inputfile, outputfile)

if __name__ == "__main__":
   main(sys.argv[1:])

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
import sys
import getopt
import websocket

# AERIUS_SERVER = "ws://connect.aerius.nl"
AERIUS_SERVER = "ws://192.168.1.17:6060"
AERIUS_PATH = "/connect/2/services"
debug = False
DUMPFILE_JSON_REQUEST = "dump_json_request.log"
DUMPFILE_JSON_RESULTS = "dump_json_resultx.log"


def calculate(inputfile):
    # Open and read content of the input file
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

    try:
        ws = websocket.create_connection(AERIUS_SERVER + AERIUS_PATH)
    except Exception as e:
        print("Unexpected connection error:", e)
        return

    try:
        # Initialize result variables and send the prepared JSON request
        received_data = ""
        ws.send(json.dumps(json_data))
        while True:
            result = ws.recv()
            if not result:
                print("## Received nothing!?")
            else:
                if debug:
                    # Gather all responses received so we can dump them to a file
                    received_data += str(json.loads(result)) + "\n"
                if "'successful': True" in result:
                    print("## Received confirmation from server: started processing data")
                if "callback.onResults" in result:
                    print("## Received (partial) result")
                # Check result and break out of the loop if any errors occurred
                if "error" in result:
                    # print("Received errors from server:", str(result))
                    json_output = json.loads(result)
                    for error in json_output["result"]["errors"]:
                        print("error: " + str(error["code"]) + " - " + str(error["message"]))
                    break
                # Break out of the loop when the onFinish event is received
                if "callback.onFinish" in result:
                    print("## Received confirmation from server: finished processing data")
                    break
        if debug:
            # When the debug (-d) option is set we dump sent and received data to files for further inspection
            with open(DUMPFILE_JSON_REQUEST, "w") as file:
                file.write(str(json.dumps(json_data)))
                print("DEBUG json request written to file: ", file.name)
                file.close()
            with open(DUMPFILE_JSON_RESULTS, "w") as file:
                file.write(received_data)
                print("DEBUG json results written to file: ", file.name)
                file.close()
    except IOError as e:
        print("Unexpected result error:", str(e))
    except Exception:
        print("Unexpected result error:", sys.exc_info()[:3])
    finally:
        ws.close()
    return


def usage(errorlevel=0):
    # Neat help text to display by user request or in case of errors
    print("Usage: ", __file__, " [-d] -i <gml file>")
    print()
    print("-d , --debug  : Run in debug mode")
    print("-i , --ifile  : Specify input file -i <gml file> or --ifile=<gml file>")
    print("-h , --help   : Show this help text")
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

    # If all prerequisites are satisfied we can start the actual calculation
    calculate(inputfile)


if __name__ == "__main__":
    main(sys.argv[1:])

#!/usr/bin/python3
"""
Dit script is bedoeld als voorbeeld om het gebruik van AERIUS connect te demonstreren.
"""
from __future__ import print_function  # Consistent print methods across various Python versions
from __future__ import unicode_literals  # Unicode literal fixes

import base64
import binascii
import datetime
import getopt
import json
import numbers
import os
import sys
import time
import websocket

if not hasattr(websocket, 'create_connection'):
    print("Incompatible websocket module found.")
    print("- Please make sure that you have 'websocket-client' installed.")
    print("- Remove other websocket implementations if needed.")
    sys.exit()


DEBUG_ENABLED = False
DEBUG_INPUT_FILE = 'debug.input.json'
DEBUG_RESULT_FILE = 'debug.result.json'
CONNECT_HOST = 'ws://connect.aerius.nl'
CONNECT_SERVICE_URL = '/connect/2/services'
CONNECT_SERVICE_FULL = CONNECT_HOST + CONNECT_SERVICE_URL

COMMAND_VALIDATE = "validate"
COMMAND_CONVERT = "convert"
COMMAND_CALCULATEANDEMAIL = "calculateAndEmail"
COMMAND_CALCULATEREPORTANDEMAIL = "calculateReportAndEmail"
COMMAND_MERGE = "merge"
COMMAND_STATUS = "status"

ALL_COMMANDS = [
    COMMAND_VALIDATE,
    COMMAND_CONVERT,
    COMMAND_CALCULATEANDEMAIL,
    COMMAND_CALCULATEREPORTANDEMAIL,
    COMMAND_MERGE,
    COMMAND_STATUS
]

# JSON BASE will be filled based on the chosen action
JSON_BASE = """
{
    "jsonrpc":"2.0",
    "id":0,
    "method":""
}
"""


def debug(args):
    if DEBUG_ENABLED:
        print("DEBUG:" + args)


def get_json(method, params):
    json_data = json.loads(JSON_BASE)
    json_data["method"] = method
    # Create an unique id
    json_data["id"] = int(time.time() * 1000)
    json_data["params"] = params

    return json_data


def service_convert2gml(inputfile, outputfile):
    call_connect(
        get_json(
            'conversion.convert2GML', inputfile
        ),
        outputfile
    )


def service_validate(inputfile):
    call_connect(
        get_json(
            'validation.validate', inputfile
        )
    )


def service_calculate_and_email(inputfile, emailaddress):
    json_data = get_json(
        'calculation.calculateAndEmail',
        {
            "email": emailaddress,
            "options": {
                "calculationType": "NBWET",
                "year": 2016,
                "substances": [
                    "NOX",
                    "NH3"
                ]
            },
            "data": [inputfile]
        }
    )

    call_connect(json_data)


def service_calculate_report_and_email(inputfile, emailaddress):
    json_data = get_json(
        'report.calculateReportAndEmail',
        {
            "email": emailaddress,
            "options": {
                "calculationType": "NBWET",
                "year": 2016,
                "substances": [
                    "NOX",
                    "NH3"
                ]
            },
            "proposed": [inputfile]
        }
    )

    call_connect(json_data)


def service_merge(inputfile, inputfile2, outputfile):
    call_connect(
        get_json(
            'util.merge',
            {
                "data": [inputfile, inputfile2]
            }
        ),
        outputfile
    )


def service_status(emailaddress):
    json_output = call_connect(
        get_json(
            'status.jobs',
            {
                "email": emailaddress
            }
        )
    )

    if not json_output:
        return

    print("Job", '\t', "Type", '\t\t', "State", '\t\t', "Start time", '\t\t', "End time", '\t\t', "Hectare calculated")
    print("------------------------------------------------------------------------------------------------------------")
    if not json_output["result"]["progresses"]:
        print("No jobs found")
    for progress in json_output["result"]["progresses"]:
        print(progress.get('jobId', '-'), '\t',
              progress.get('type', '-'), '\t',
              progress.get('state', '-'), '\t',
              pretty_format_unixtime(progress.get('startDateTime', '-\t\t')), '\t',
              pretty_format_unixtime(progress.get('endDateTime', '-\t\t')), '\t',
              progress.get('hectareCalculated', '-'))


def process_results(json_data):
    # write result part
    json_output = json.loads(json_data)
    if json_data.find("successful") > -1:
        if json_data.find("errors") > -1:
            for error in json_output["result"]["errors"]:
                print('ERROR:', error["code"], "-", error["message"])
                sys.exit(1)
        elif json_data.find("warnings") > -1 and len(json_output["result"]["warnings"]) > 0:
            print("Call succeeded without errors, but with following warnings:")
            for warning in json_output["result"]["warnings"]:
                print('WARNING:', warning["code"], "-", warning["message"])
        else:
            debug("Call succeeded without errors")

    return json_output


def read_file_content(filepath):
    try:
        if filepath.lower().endswith('.zip'):
            debug('Identified a zip file. Reading binary data using implicit base64 conversion')
            with open(filepath, 'rb') as f:
                file_info = {"dataType": "ZIP", "contentType": "BASE64", "data": binascii.b2a_base64(f.read()).decode()}
                return file_info
        else:
            with open(filepath, 'r') as f:
                file_info = {"dataType": "GML", "contentType": "TEXT", "data": f.read()}
                return file_info
    except IOError as e:
        print("Error reading file:", e)
        sys.exit(1)


def call_connect(json_data, outputfile=None):
    try:
        debug("Connecting using websocket...")
        ws = websocket.create_connection(CONNECT_HOST + CONNECT_SERVICE_URL)
    except Exception as e:
        print("Unexpected connection error while trying to establish connection:", e)
        return

    try:
        debug("Trying to send data to service..")
        if DEBUG_ENABLED:
            debug("Writing input data send to service to:" + DEBUG_INPUT_FILE)
            fileout = open(DEBUG_INPUT_FILE, "w+")
            fileout.write(json.dumps(json_data))

        ws.send(json.dumps(json_data))
        debug("Send! Trying to receive data from service..")
        result = ws.recv()
        debug("Done receiving!")

        if DEBUG_ENABLED:
            debug("Writing full result from service to:" + DEBUG_RESULT_FILE)
            fileout = open(DEBUG_RESULT_FILE, "w+")
            fileout.write(str(result))

        json_output = process_results(result)
    except Exception as e:
        print("Unexpected connection error:", e)
        return False
    finally:
        debug("Closing connection")
        ws.close()

    if json_output and outputfile:
        outputdata = json_output["result"]["data"].encode("UTF-8")
        if json_output["result"]["contentType"]:
            debug("Result has contentType: " + json_output["result"]["contentType"])
            if json_output["result"]["contentType"] == 'BASE64':
                outputdata = base64.standard_b64decode(outputdata)

        if json_output["result"]["dataType"] \
                and not outputfile.lower().endswith("." + json_output["result"]["dataType"].lower()):
            print("Warning: The supplied output filename does not have the expected extension. Expected extension: ." +
                  json_output["result"]["dataType"].lower() + ".")

        print("Writing content to:", outputfile)
        fileout = open(outputfile, "wb+")
        fileout.write(outputdata)

    return json_output


def pretty_format_unixtime(value):
    if isinstance(value, numbers.Number):
        return datetime.datetime.fromtimestamp(value / 1000).strftime('%Y-%m-%d %H:%M:%S')

    return value


def usage(errormessage=None):
    if errormessage:
        print("ERROR:", errormessage)
        print()

    print("Usage:")
    print("\t", os.path.basename(__file__), "[-d] " + COMMAND_VALIDATE + " <input file>")
    print("\t", os.path.basename(__file__), "[-d] " + COMMAND_CONVERT + " <input file> <output file>")
    print("\t", os.path.basename(__file__), "[-d] " + COMMAND_STATUS + " <email address>")
    print("\t", os.path.basename(__file__), "[-d] " + COMMAND_CALCULATEANDEMAIL + " <input file> <email address>")
    print("\t", os.path.basename(__file__), "[-d] " + COMMAND_CALCULATEREPORTANDEMAIL +
          " <input file> <email address>")
    print("\t", os.path.basename(__file__), "[-d] " + COMMAND_MERGE +
          " <input file 1> <inputL file 2> <output file>")
    print()
    print()
    print("-d, --debug")
    print("\trun in debug mode. Writes debug lines and the full result JSON.")
    print("-h, --help")
    print("\tshow this help text.")
    print()
    print()
    print("Actions:")
    print("- " + COMMAND_VALIDATE + ":", '\t\t\t', "Validate the file.")
    print("- " + COMMAND_CONVERT + ":", '\t\t\t', "Convert file to the latest version.")
    print("- " + COMMAND_STATUS + ":", '\t\t\t', "Get status information about the jobs running for you.")
    print("- " + COMMAND_CALCULATEANDEMAIL + ":", '\t\t', "Import and calculate the file and email the results.")
    print("- " + COMMAND_CALCULATEREPORTANDEMAIL + ":", '\t', "Import and produce a NBWET PDF and email the results.")
    print("- " + COMMAND_MERGE + ":", '\t\t\t',
          "Merge given input files and return single file containing the highest depositions of the two.")

    if errormessage:
        sys.exit(1)
    else:
        sys.exit(0)


def main(argv):
    try:
        opts, remainder = getopt.getopt(argv, 'hd', ['help', 'debug'])
    except getopt.GetoptError as err:
        print("Invalid argument(s):", str(err))
        usage(1)

    inputfile = None
    inputfile2 = None
    email_address = None
    outputfile = None

    needs_input_file = False
    needs_input_file2 = False
    needs_output_file = False
    needs_email_address = False

    for opt, arg in opts:
        if opt == '-d':
            global DEBUG_ENABLED
            DEBUG_ENABLED = True
        else:
            usage()

    if len(remainder) > 0:
        command_to_execute = remainder[0]
        # By default we expect nothing, only the command to execute
        amount_of_args_expected = 0

        # Check if the command given is valid
        if not command_to_execute in ALL_COMMANDS:
            usage("Command not recognized")

        # Let's determine which and how much arguments we expect, default is specified above
        if command_to_execute == COMMAND_CONVERT:
            needs_input_file = True
            needs_output_file = True
        elif command_to_execute == COMMAND_VALIDATE:
            needs_input_file = True
        elif command_to_execute == COMMAND_CALCULATEANDEMAIL:
            needs_input_file = True
            needs_email_address = True
        elif command_to_execute == COMMAND_CALCULATEREPORTANDEMAIL:
            needs_input_file = True
            needs_email_address = True
        elif command_to_execute == COMMAND_MERGE:
            needs_input_file = True
            needs_input_file2 = True
            needs_output_file = True
        elif command_to_execute == COMMAND_STATUS:
            needs_email_address = True

        if needs_input_file:
            amount_of_args_expected += 1
        if needs_input_file2:
            amount_of_args_expected += 1
        if needs_output_file:
            amount_of_args_expected += 1
        if needs_email_address:
            amount_of_args_expected += 1

        if len(remainder) != (amount_of_args_expected + 1):
            usage("Unexpected amount of args received")

        argument_position = 1
        if needs_input_file:
            inputfile = read_file_content(remainder[argument_position])
            argument_position += 1
        if needs_input_file2:
            inputfile2 = read_file_content(remainder[argument_position])
            argument_position += 1
        if needs_output_file:
            outputfile = remainder[argument_position]
            argument_position += 1
        if needs_email_address:
            email_address = remainder[argument_position]
            argument_position += 1

        if command_to_execute == COMMAND_CONVERT:
            service_convert2gml(inputfile, outputfile)
        elif command_to_execute == COMMAND_VALIDATE:
            service_validate(inputfile)
        elif command_to_execute == COMMAND_CALCULATEANDEMAIL:
            service_calculate_and_email(inputfile, email_address)
        elif command_to_execute == COMMAND_CALCULATEREPORTANDEMAIL:
            service_calculate_report_and_email(inputfile, email_address)
        elif command_to_execute == COMMAND_MERGE:
            service_merge(inputfile, inputfile2, outputfile)
        elif command_to_execute == COMMAND_STATUS:
            service_status(email_address)

    else:
        usage("No command specified")


if __name__ == '__main__':
    main(sys.argv[1:])

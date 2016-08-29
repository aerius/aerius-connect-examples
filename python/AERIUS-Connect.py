#!/usr/bin/python3
"""
Dit script is bedoeld als voorbeeld om het gebruik van AERIUS connect te demonstreren.
"""
from __future__ import print_function  # Consistent print methods across various Python versions
from __future__ import unicode_literals  # Unicode literal fixes

from bravado.client import SwaggerClient
from bravado.exception import HTTPError

import arrow
import base64
import binascii
import getopt
import os
import sys

DEBUG_ENABLED = False
DEBUG_REQUEST_FILE = 'debug.request.txt'
DEBUG_RESPONSE_FILE = 'debug.response.txt'
DEBUG_RESPONSE_RAW_FILE = 'debug.response.raw.txt'
CONNECT_HOST = 'https://connect.aerius.nl'
CONNECT_SERVICE_URL = '/api/3/swagger.yaml'
CONNECT_SERVICE_FULL = CONNECT_HOST + CONNECT_SERVICE_URL

COMMAND_VALIDATE = "validate"
COMMAND_CONVERT = "convert"
COMMAND_CALCULATE = "calculate"
COMMAND_REPORT = "report"
COMMAND_HIGHESTVALUEPERHEXAGON = "highestValuePerHexagon"
COMMAND_STATUS = "status"
COMMAND_GENERATE_API_KEY = "generateAPIKey"

ALL_COMMANDS = [
    COMMAND_VALIDATE,
    COMMAND_CONVERT,
    COMMAND_CALCULATE,
    COMMAND_REPORT,
    COMMAND_HIGHESTVALUEPERHEXAGON,
    COMMAND_STATUS,
    COMMAND_GENERATE_API_KEY
]


def debug(args):
    if DEBUG_ENABLED:
        print("DEBUG: " + args)


def get_connect_client():
    try:
        return SwaggerClient.from_url(CONNECT_SERVICE_FULL, config={
            # Determines what is returned by the service call.
            'also_return_response': True,

            #  validate incoming responses
            'validate_responses': False,

            # validate outgoing requests
            'validate_requests': True,

            # validate the swagger spec
            'validate_swagger_spec': True,

            # Use models (Python classes) instead of dicts for #/definitions/{models}
            'use_models': True,
        })
    except Exception as e:
        print("Error communicating with API.")
        print(e)
        sys.exit(1)


def log_request_if_needed(swagger_request):
    if DEBUG_ENABLED and swagger_request:
        debug("Writing request object to: " + DEBUG_REQUEST_FILE)
        fileout = open(DEBUG_REQUEST_FILE, "w+")
        fileout.write(str(swagger_request))


def log_response_if_needed(response, http_response):
    if DEBUG_ENABLED and http_response:
        debug("Writing object response from service to: " + DEBUG_RESPONSE_FILE)
        fileout = open(DEBUG_RESPONSE_FILE, "w+")
        fileout.write(str(response))

        debug("Writing object response from service to: " + DEBUG_RESPONSE_RAW_FILE)
        fileout = open(DEBUG_RESPONSE_RAW_FILE, "w+")
        fileout.write(http_response.text)


def process_http_error(exception):
    if exception.swagger_result:
        result = exception.swagger_result
        if hasattr(result, 'code') and hasattr(result, 'message'):
            print("An API validation error has been received:")
            print("- {}: {}".format(result.code, result.message))
    else:
        print("An unexpected error has occurred while communicating with the API:")
        print("- {}".format(str(exception)))


def process_response_validate(type_string, result, http_response):
    log_response_if_needed(result, http_response)

    print("{} successful: {}".format(type_string, str(result.successful)))

    if result.warnings and len(result.warnings) > 0:
        print()
        print('Warnings reported:')
        for warning in result.warnings:
            print("- {}: {}".format(warning.code, warning.message))

    if result.errors and len(result.errors) > 0:
        print()
        print('Errors reported:')
        for error in result.errors:
            print("- {}: {}".format(error.code, error.message))


def process_response_convert(result, http_response, output_file):
    process_response_validate("Conversion", result, http_response)

    if result.successful:
        write_dataobject_to_disk(result.dataObject, output_file)


def service_validate(input_file):
    client = get_connect_client()

    # Required models for this call
    ValidateRequest = client.get_model('ValidateRequest')
    DataObject = client.get_model('DataObject')

    request = ValidateRequest(
        dataObject=read_file_content(DataObject(), input_file),
        strict=False)

    log_request_if_needed(request)
    try:
        result, http_response = client.util.postValidate(body=request).result()
    except HTTPError as e:
        process_http_error(e)
        return
    process_response_validate("Validate", result, http_response)


def service_convert(input_file, output_file):
    client = get_connect_client()

    # Required models for this call
    ConvertRequest = client.get_model('ConvertRequest')
    DataObject = client.get_model('DataObject')

    request = ConvertRequest(
        dataObject=read_file_content(DataObject(), input_file)
    )

    log_request_if_needed(request)
    try:
        result, http_response = client.util.postConvert(body=request).result()
    except HTTPError as e:
        process_http_error(e)
        return
    process_response_convert(result, http_response, output_file)


def service_calculate(input_file, api_key):
    client = get_connect_client()

    # Required models for this call
    CalculateRequest = client.get_model('CalculateRequest')
    CalculateDataObject = client.get_model('CalculateDataObject')
    CalculationOptions = client.get_model('CalculationOptions')

    calculate_data_object = CalculateDataObject()
    request = CalculateRequest(
        apiKey=api_key,
        options=CalculationOptions(
            calculationType='NBWET',
            year=2016,
            substances=['NOX', 'NH3']
        ),
        calculateDataObjects=[
            read_file_content(calculate_data_object, input_file)
        ]
    )

    log_request_if_needed(request)
    try:
        result, http_response = client.calculation.postCalculate(body=request).result()
    except HTTPError as e:
        process_http_error(e)
        return
    # The response is also a ValidationResponse, so treat it as such.
    process_response_validate("Calculation start", result, http_response)


def service_report(input_file, api_key):
    client = get_connect_client()

    # Required models for this call
    ReportRequest = client.get_model('ReportRequest')
    ReportDataObject = client.get_model('ReportDataObject')
    CalculationOptions = client.get_model('CalculationOptions')

    report_data_object = ReportDataObject()
    report_data_object.situationType = 'PROPOSED'
    request = ReportRequest(
        apiKey=api_key,
        options=CalculationOptions(
            calculationType='NBWET',
            year=2016,
            substances=['NOX', 'NH3'],
        ),
        reportDataObjects=[
            read_file_content(report_data_object, input_file)
        ]
    )

    log_request_if_needed(request)
    try:
        result, http_response = client.calculation.postReport(body=request).result()
    except HTTPError as e:
        process_http_error(e)
        return
    # The response is also a ValidationResponse, so treat it as such.
    process_response_validate("Report start", result, http_response)


def service_highest_value_per_hexagon(input_file, input_file2, output_file):
    client = get_connect_client()

    # Required models for this call
    HighestValuePerHexagonRequest = client.get_model('HighestValuePerHexagonRequest')
    DataObject = client.get_model('DataObject')

    request = HighestValuePerHexagonRequest(
        dataObjects=[
            read_file_content(DataObject(), input_file),
            read_file_content(DataObject(), input_file2)
        ]
    )

    log_request_if_needed(request)
    try:
        result, http_response = client.util.postHighestValuePerHexagon(body=request).result()
    except HTTPError as e:
        process_http_error(e)
        return
    # The response is also a ConvertResponse, so treat it as such.
    process_response_convert(result, http_response, output_file)


def service_generate_api_key(email):
    client = get_connect_client()

    # Required models for this call
    GenerateAPIKeyRequest = client.get_model('GenerateAPIKeyRequest')
    request = GenerateAPIKeyRequest(email=email)

    log_request_if_needed(request)
    try:
        result, http_response = client.user.postGenerateAPIKey(body=request).result()
    except HTTPError as e:
        process_http_error(e)
        return
    process_response_validate("Generate API key", result, http_response)


def service_status(api_key):
    try:
        result, http_response = get_connect_client().user.getStatusJobs(apiKey=api_key).result()
    except HTTPError as e:
        process_http_error(e)
        return

    log_response_if_needed(result, http_response)

    if not result.entries:
        print("No jobs found")
        return

    print("Job", '\t', "Type", '\t\t', "State", '\t\t', "Start time", '\t\t', "End time", '\t\t', "Hectare calculated")
    print("-----------------------------------------------------------------------------------------------------------")
    for entry in result.entries:
        print(str(entry.jobId) or '-', '\t',
              entry.jobType or '-', '\t',
              entry.jobState or '-', '\t',
              pretty_format_datetime(entry.startDateTime, '-\t\t'), '\t',
              pretty_format_datetime(entry.endDateTime, '-\t\t'), '\t',
              str(entry.hectareCalculated) or '-')


def read_file_content(data_object, file_path):
    try:
        if file_path.lower().endswith('.zip'):
            with open(file_path, 'rb') as f:
                setattr(data_object, 'dataType', 'ZIP')
                setattr(data_object, 'contentType', 'BASE64')
                setattr(data_object, 'data', binascii.b2a_base64(f.read()).decode())
        else:
            with open(file_path, 'r') as f:
                setattr(data_object, 'dataType', 'GML')
                setattr(data_object, 'contentType', 'TEXT')
                setattr(data_object, 'data', f.read())
    except IOError as e:
        print("Error reading file:", e)
        sys.exit(1)
    return data_object


def write_dataobject_to_disk(dataobject, outputfile):
    if not dataobject:
        print("No file received from the API while one is expected")
        return

    outputdata = dataobject.data.encode("UTF-8")
    if dataobject.contentType:
        debug("Result has contentType: " + dataobject.contentType)
        if dataobject.contentType == 'BASE64':
            outputdata = base64.standard_b64decode(outputdata)

    if dataobject.dataType \
            and not outputfile.lower().endswith("." + dataobject.dataType.lower()):
        print("Warning: The supplied output filename does not have the expected extension. Expected extension: .{}"
              .format(dataobject.dataType.lower()))

    print("Writing file to: {}".format(outputfile))
    fileout = open(outputfile, "wb+")
    fileout.write(outputdata)


def pretty_format_datetime(value, default):
    if not value:
        return default

    return arrow.get(value).to('Europe/Amsterdam').format('YYYY-MM-DD HH:mm:ss')


def usage(error_message=None):
    if error_message:
        print("ERROR:", error_message)
        print()

    usage_line_format = "\t" + os.path.basename(__file__) + " [-d] {} {}"
    action_line_short_format = "- {}:\t\t\t{}"
    action_line_medium_format = "- {}:\t\t{}"
    action_line_long_format = "- {}:\t{}"

    print("Usage:")
    print(usage_line_format.format(COMMAND_VALIDATE, "<input file>"))
    print(usage_line_format.format(COMMAND_CONVERT, "<input file> <output file>"))
    print(usage_line_format.format(COMMAND_STATUS, "<email address>"))
    print(usage_line_format.format(COMMAND_CALCULATE, "<input file> <API key>"))
    print(usage_line_format.format(COMMAND_REPORT, "<input file> <API key>"))
    print(usage_line_format.format(COMMAND_HIGHESTVALUEPERHEXAGON, "<input file 1> <input file 2> <output file>"))
    print(usage_line_format.format(COMMAND_GENERATE_API_KEY, "<email address>"))
    print()
    print()
    print("-d, --debug")
    print("\trun in debug mode. Will print debug lines and write the request and response to files.")
    print("-h, --help")
    print("\tshow this help text.")
    print()
    print()
    print("Actions:")
    print(action_line_short_format.format(COMMAND_VALIDATE, "Validate the file."))
    print(action_line_short_format.format(COMMAND_CONVERT, "Convert file to the latest version."))
    print(action_line_short_format.format(COMMAND_STATUS, "Get status information about the jobs running for you."))
    print(action_line_short_format.format(COMMAND_CALCULATE, "Import and calculate the file and email the results."))
    print(action_line_short_format.format(COMMAND_REPORT, "Import and produce a NBWET PDF and email the results."))
    print(action_line_long_format.format(COMMAND_HIGHESTVALUEPERHEXAGON,
                                         "Merge given input files and return single file containing"
                                         " the highest deposition value per hexagon."))
    print(action_line_medium_format.format(COMMAND_GENERATE_API_KEY, "Generate an API key."))

    if error_message:
        sys.exit(1)
    else:
        sys.exit(0)


def main(argv):
    try:
        opts, remainder = getopt.getopt(argv, 'hd', ['help', 'debug'])
    except getopt.GetoptError as err:
        print("Invalid argument(s):", str(err))
        usage(1)

    input_file = None
    input_file2 = None
    email_address = None
    output_file = None

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
        if command_to_execute not in ALL_COMMANDS:
            usage("Command not recognized")

        # Let's determine which and how much arguments we expect, default is specified above
        if command_to_execute == COMMAND_CONVERT:
            needs_input_file = True
            needs_output_file = True
        elif command_to_execute == COMMAND_VALIDATE:
            needs_input_file = True
        elif command_to_execute == COMMAND_CALCULATE:
            needs_input_file = True
            needs_email_address = True
        elif command_to_execute == COMMAND_REPORT:
            needs_input_file = True
            needs_email_address = True
        elif command_to_execute == COMMAND_HIGHESTVALUEPERHEXAGON:
            needs_input_file = True
            needs_input_file2 = True
            needs_output_file = True
        elif command_to_execute == COMMAND_STATUS:
            needs_email_address = True
        elif command_to_execute == COMMAND_GENERATE_API_KEY:
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
            input_file = remainder[argument_position]
            argument_position += 1
        if needs_input_file2:
            input_file2 = remainder[argument_position]
            argument_position += 1
        if needs_output_file:
            output_file = remainder[argument_position]
            argument_position += 1
        if needs_email_address:
            email_address = remainder[argument_position]
            argument_position += 1

        if command_to_execute == COMMAND_CONVERT:
            service_convert(input_file, output_file)
        elif command_to_execute == COMMAND_VALIDATE:
            service_validate(input_file)
        elif command_to_execute == COMMAND_CALCULATE:
            service_calculate(input_file, email_address)
        elif command_to_execute == COMMAND_REPORT:
            service_report(input_file, email_address)
        elif command_to_execute == COMMAND_HIGHESTVALUEPERHEXAGON:
            service_highest_value_per_hexagon(input_file, input_file2, output_file)
        elif command_to_execute == COMMAND_STATUS:
            service_status(email_address)
        elif command_to_execute == COMMAND_GENERATE_API_KEY:
            service_generate_api_key(email_address)

    else:
        usage("No command specified")


if __name__ == '__main__':
    main(sys.argv[1:])

import time
import sys
import signal
import json
import argparse
import datetime
from colorama import init
import dateutil.parser

import modules
import utils

com = None


def signal_handler(sig, frame):
    com.disconnect()
    print("Exiting test")
    sys.exit(0)


if __name__ == "__main__":

    # Init Colorama
    init()

    # Register Signal handler for graceful exit
    signal.signal(signal.SIGINT, signal_handler)

    # Argument parser
    ap = argparse.ArgumentParser()
    ap.add_argument("-b", "--baud", required=False, metavar="", help="Baudrate")

    reqArgs = ap.add_argument_group("required arguments")
    reqArgs.add_argument(
        "-p", "--port", required=True, metavar="", help="COM port (example: COM10)"
    )

    args = vars(ap.parse_args())

    # Connect to EVE
    com = utils.com_class()
    if args["baud"]:
        com.connect(args["port"], args["baud"], 1)
    else:
        com.connect(args["port"], 115200, 1)

    # Start test
    rtcObj = modules.module_class(com)
    rtcObj.rtcSetCalendar(
        datetime.datetime.now().replace(microsecond=0).isoformat()
    )  # Set RTC to PC time

    while True:
        # Read System time
        pcDateTime = datetime.datetime.now().replace(microsecond=0).isoformat()

        # Read EVE time
        eveDateTime = rtcObj.rtcGetCalendar()
        if eveDateTime == None:
            utils.formatPrint.red("Failed to read Calendar...")
            continue

        # Measure time deviation
        delta = dateutil.parser.parse(pcDateTime) - dateutil.parser.parse(eveDateTime)
        utils.formatPrint.bright("PC Time: " + pcDateTime)
        utils.formatPrint.bright("EVE Time: " + eveDateTime)
        utils.formatPrint.cyan("Time deviation: " + str(abs(delta)) + "\r\n")
        time.sleep(10)

    com.disconnect()
    print("Exiting test")

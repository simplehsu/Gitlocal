# System imports
import json
import time
import sys
import signal
import argparse
from colorama import init

# Local imports
import utils
import modules


class lte_pwr_test_class(modules.module_class):

    # Private variables
    __com = None

    def __init__(self, arg):
        self.__com = arg
        modules.module_class.__init__(self, arg)


if __name__ == "__main__":

    # Init Colorama
    init()

    # Argument parser
    ap = argparse.ArgumentParser()
    ap.add_argument("-b", "--baud", required=False, metavar="", help="Baudrate")
    ap.add_argument(
        "-act",
        "--action",
        required=True,
        metavar="",
        help="continuous_tx, stop or onoff",
    )

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

    # Run tests
    lteTest = lte_pwr_test_class(com)

    # check lte init
    Info = lteTest.lteAt("")
    if Info.find("OK") != -1:
        print("LTE module is up")
    else:
        utils.formatPrint.red("Please turn ON LTE before starting the test")
        com.disconnect()
        exit(1)

    if args["action"] == "continuous_tx":
        lteInfo = lteTest.lteAt("+UTEST=1")
        if lteInfo.find("OK") == -1:
            utils.formatPrint.red("Failed to enter test mode")
            com.disconnect()
            exit(1)
        # run test forever till stop is called.
        lteInfo = lteTest.lteAt("+UTEST=3,118900,24,,,0")
        if lteInfo.find("OK") == -1:
            utils.formatPrint.red("Failed start Tx")
            com.disconnect()
            exit(1)

        print("LTE TX TEST STARTED")

    elif args["action"] == "stop":
        lteInfo = lteTest.lteAt("+UTEST=0")
        if lteInfo.find("OK") == -1:
            utils.formatPrint.red("Failed to stop test")
        else:
            print("TX TEST STOPPED")
    elif args["action"] == "onoff":
        while True:
            lteInfo = lteTest.lteAt("+UTEST=1")
            if lteInfo.find("OK") == -1:
                utils.formatPrint.red("Failed to enter test mode")
                com.disconnect()
                exit(1)
            # run TX test for 1 second
            lteInfo = lteTest.lteAt("+UTEST=3,118900,24,,,1000")
            if lteInfo.find("OK") == -1:
                utils.formatPrint.red("Failed start Tx")
    else:
        utils.formatPrint.red("Err: Inval args")

    # Clean-up and exit
    com.disconnect()

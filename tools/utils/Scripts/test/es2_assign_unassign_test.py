""" This script is a tool for testing assignment and unassignment from an AG-55.
    Pre-requisites:
        * Python2
        * AG-55 running factory CLI
        * AG-55 serial port connected to the computer running this script

    Command Line Syntax:
        * Run `python2 es2_assign_unassign_test.py --help`

"""

import sys
import signal
import argparse
import os
from time import time, sleep

import utils
import modules

import json
import shutil


def signal_handler(sig, frame):
    com.disconnect()
    print ("Exiting Script")
    sys.exit(0)


class EsBle(modules.module_class):
    """" Class for testing BLE sensor devices attached to AG-55 running factory cli"""

    def __init__(self, com):
        """ constructor initializes cli modules"""
        self.available_sensors = {}
        self.connected_sensors = {}
        modules.module_class.__init__(self, com)

    def scan(self):
        """Scan for all ble devices"""

        resp = self.bleScan()
        result = self.parse_response(resp, "BLE", True)
        print ("\nBLE SCAN : " + result)

        self.available_sensors = self.bleEsDevices()

        # scan a few times
        for _ in range(5):
            self.available_sensors.update(self.bleEsDevices())

        return self.available_sensors

    def get_connected_sensors(self):
        """Get a list of connected devices"""
        self.connected_sensors = self.bleConnectedDevices()
        return self.connected_sensors

    def parse_response(self, response, module, display):
        """ Parse the Response and on error terminates program if terminate flag is Set """
        try:
            result = json.loads(response)
            return result[module]["RESULT"]
        except:
            return "INVALID"


if __name__ == "__main__":
    """ main """
    # Signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Argument parser
    ap = argparse.ArgumentParser()
    ap.add_argument("-b", "--baud", required=False, metavar="", help="Baudrate")

    reqArgs = ap.add_argument_group("required arguments")
    reqArgs.add_argument(
        "-p", "--port", required=True, metavar="", help="COM port (example: COM10)"
    )

    ap.add_argument(
        "-r",
        "--repeat",
        required=False,
        metavar="",
        type=int,
        default=0,
        help="Repeat count",
    )

    args = vars(ap.parse_args())
    es2_dut = "ACCE21BC160133"

    # Connect to AG-55
    com = utils.com_class()
    # create object for dfu class
    ble = EsBle(com)
    if args["baud"]:
        com.connect(args["port"], args["baud"], 1)
    else:
        com.connect(args["port"], 115200, 1)

    reps = args["repeat"]

    print ("reps = %s" % reps)

    for i in range(reps + 1):
        result = ble.bleSetSensorList()
        sleep(1)

        result = filter(lambda l: es2_dut in l, ble.bleDumpDb())
        while result:
            print "\n".join(result)
            sleep(1)
            result = filter(lambda l: es2_dut in l, ble.bleDumpDb())

        print "ES-2 db after unassignment", "\n".join(
            filter(lambda l: "ACCE" in l, ble.bleDumpDb())
        )
        print "\n"

        try:
            input("Reset the ES-2 then press enter")
        except:
            pass

        result = ble.bleSetSensorList([es2_dut])
        sleep(1)

        result = filter(lambda l: es2_dut in l, ble.bleDumpDb())
        while result and not filter(lambda l: " CONNECTED" in l, result):
            print "\n".join(result)
            sleep(1)
            result = filter(lambda l: es2_dut in l, ble.bleDumpDb())

        print "ES-2 db after assignment\n", "\n".join(
            filter(lambda l: "ACCE" in l, ble.bleDumpDb())
        )
        print "\n"

    # Exit the script
    com.disconnect()
    sys.exit(0)

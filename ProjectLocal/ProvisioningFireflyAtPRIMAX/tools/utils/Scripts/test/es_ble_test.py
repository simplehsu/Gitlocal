""" This script is a tool for testing BLE sensor devices from an AG-55.
    Pre-requisites:
        * Python2
        * AG-55 running factory CLI
        * AG-55 serial port connected to the computer running this script

    Command Line Syntax:
        * Run `python2 es_ble_test.py --help`

    TODO:
        This is a starting point with lots of room for additions and enhancements. Have at it.
        * Convert the whole thing to Python3 (including the modules)
        * Use Python logging module throughout and improve logging of errors that may be
          printed from the AG CLI rather than just eating them.
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
    print("Exiting Script")
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
        print("\nBLE SCAN : " + result)

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

    ap.add_argument(
        "-m",
        "--monitor_seconds",
        required=False,
        metavar="",
        type=int,
        default=30,
        help="Duration to monitor connections before deleting and reconnecting",
    )

    args = vars(ap.parse_args())

    # Connect to AG-55
    com = utils.com_class()
    # create object for dfu class
    ble = EsBle(com)
    if args["baud"]:
        com.connect(args["port"], args["baud"], 1)
    else:
        com.connect(args["port"], 115200, 1)

    reps = args["repeat"]

    print("reps = %s" % reps)

    for i in range(reps + 1):
        start_time = time()

        # Get the sw version
        result = ble.bleGetSwVer()
        reset_attempts = 0
        while result and result["RESULT"] != "PASS" and reset_attempts < 10:
            print("Failed to read BLE App Version. Resetting BLE Chip...")
            result = ble.bleChipReset()
            print("Chip Reset: %s" % result["RESULT"])
            sleep(5)
            result = ble.bleGetSwVer()
            print(result)
            reset_attempts += 1
        if not result or result["RESULT"] != "PASS":
            print("Failed to reset BLE chip after 10 attempts.")
            sys.exit(1)

        print("BLE App Version: %s" % result["MSG"]["FW_VER"])

        # Scan for ES devices
        resp = ble.scan()

        # Connect to ES devices
        for name, es in resp.iteritems():
            print("Connecting to %s" % es["name"])
            ble.bleConnect(es["mac"])

        # Show connected devices
        if len(resp) > 0:
            for _ in range(args["monitor_seconds"] / 5):
                sleep(5)
                resp = ble.get_connected_sensors()
                print("Connected to:")
                for mac in resp:
                    print(
                        "\t%s: RSSI %d"
                        % (
                            ble.available_sensors[mac]["name"],
                            ble.available_sensors[mac]["rssi"],
                        )
                    )

            # Read temp / humidity a few times

            # Disconnect
            for mac in ble.available_sensors:
                ble.bleDisconnect(mac)

            print("After disconnect, connected to:")
            resp = ble.get_connected_sensors()
            for mac in resp:
                print(
                    "\t%s: RSSI %d"
                    % (
                        ble.available_sensors[mac]["name"],
                        ble.available_sensors[mac]["rssi"],
                    )
                )

        sleep(1)

        print("iter %d took %.0f seconds" % (i, time() - start_time))

    # Exit the script
    com.disconnect()
    sys.exit(0)

# -*- coding: UTF-8 -*-
"""
/** @file  reboot.py
 *  @date  December 14, 2021
 *  @brief Quick script to reboot an AG connected to a serial port
 *
 *  @copyright  2021, KeepTruckin, Inc. All rights reserved.
 *  @author Paras
 *  @bug No known bugs.
 */
"""

import os
import sys
import signal
import argparse
import time
import json
import datetime
import serial


class Rebooter:
    """ To reboot an AG-55 """

    # TimeOuts in seconds
    DEFAULT_RD_TIMEOUT = 1  # To wait for response from EVE
    SET_UPDATE_FLAG_TIMEOUT = 3  # To wait for firmware update flag to be set
    TG_APP_HANDSHAKE_TIMEOUT = (
        3 * 60
    )  # To establish handshake with TG Application (3 mins)
    TG_APP_ENTER_CLI_TIMEOUT = 5  # To wait for TG Application to enter CLI mode

    SYS_MODULE_NAME = "SYS"
    CMD_REBOOT = "REBOOT"

    TG_APP_HANDSHAKE_STRING = "UpdateAvailable?"
    TG_APP_HANDSHAKE_RESP = "Yes|EnterCLI"

    # Response
    RESP_KEY = "RESULT"
    RESP_VALUES = ["PASS", "FAIL", "TIMEOUT", "INVALID"]

    def __init__(self):
        self.com = None
        self.time_now = None

    def connect(self, com_port, baud):
        """ To establish connection between EVE and the PC """

        # Connect to serial COM port with specified configuration
        try:
            self.com = serial.Serial(
                port=com_port, baudrate=baud, timeout=self.DEFAULT_RD_TIMEOUT
            )
            # Print Connection Info to user
            self.time_now = datetime.datetime.now()
            print("\nConnected to AG-55 at: {}".format(time.ctime()))

            # Clear serial port
            self.com.flushInput()
            self.com.flushOutput()

        except:
            print("\nFailed to establish connection with AG-55.  Verify COM Port.")
            sys.exit()

    def disconnect(self):
        """ Disconnects the connection between EVE and the PC """
        if self.com:
            self.com.close()
            print(
                "\nDisconnected after {}".format(
                    str(datetime.datetime.now() - self.time_now)
                )
            )

    def send_cmd(self, cmd):
        """ Send command """
        # Clear serial port
        self.com.flushInput()
        self.com.flushOutput()
        self.com.timeout = self.DEFAULT_RD_TIMEOUT  # Configure Serial timeout
        cmd = cmd + "\n"  # Add LF to complete the cmd
        for wdata in cmd:  # Read Byte from String
            wdata = wdata.encode("charmap")  # Encode Byte
            self.com.write(wdata)  # Send Byte
            rdata = self.com.read(1)  # Read back the byte
            if rdata != wdata:  # Check EVE is responding ?
                print("\nAG-55 is not responding!")  # Print error message
                self.disconnect()  # Disconnect from EVE
                sys.exit()  # Terminate

        # Read new line printed on ending the cmd
        self.com.readline()

    def send_data(self, string):
        """ Send raw data """
        for data in string:  # Read Byte from String
            data = data.encode("charmap")  # Encode Byte
            self.com.write(data)  # Send Data Byte
            self.com.flushOutput()  # Flush Data

    def reboot_eve(self):
        """ Reboot EVE  """
        # Send Reboot cmd
        print("\nSending Reboot command.")
        self.send_cmd(self.SYS_MODULE_NAME + " " + self.CMD_REBOOT)

    def reboot_eve_with_handshake(self):
        """ Handshake with TG Application """
        print("Waiting for handshake.")
        left_time = self.TG_APP_HANDSHAKE_TIMEOUT
        self.com.flushInput()
        self.com.flushOutput()

        while left_time > 0:
            self.com.timeout = left_time  # Configure Serial timeout
            start_time = time.time()  # To check for timeout
            line = self.com.readline()  # Try to read expected handshake string
            line.decode("charmap")
            if self.TG_APP_HANDSHAKE_STRING in line:
                self.send_data(
                    self.TG_APP_HANDSHAKE_RESP
                )  # Send Response to Handshake string
                resp = self.read_response(self.TG_APP_ENTER_CLI_TIMEOUT)
                if "Welcome" in resp:  # Check whether TG Application entered CLI
                    print("Handshake successful")
                    self.reboot_eve()
                    return self.RESP_VALUES[0]

            # Calculate Time left to establish handshake
            left_time = left_time - (time.time() - start_time)

        print("\nHandshake failed")
        return self.RESP_VALUES[2]

    def read_response(self, timeout):
        """ Read Response """
        output = ""
        self.com.timeout = timeout  # Configure Serial timeout
        line = self.com.readline()  # Read 1st line of Response
        self.com.timeout = (
            self.DEFAULT_RD_TIMEOUT
        )  # Configure Serial timeout to default

        while True:
            if line == b"{\r\n":  # This is the start of response
                output = ""  # Clear output
            elif len(line) == 1 and line == b"$":  # Previous line was end of response
                try:
                    return json.loads(output)  # Convert to JSON object
                except:
                    return output  # Return Response
            elif not line:  # No response
                return output  # Timeout error

            output += line.decode("charmap")  # Part of response, store it
            line = self.com.readline()  # Read next line of Response

    def parse_response(self, response, module, display, terminate):
        """ Parse the Response and on error terminates program if terminate flag is Set """
        if isinstance(response, dict):  # Is valid Response
            try:
                return_value = (response[module])[
                    self.RESP_KEY
                ]  # Try to Parse Response
            except KeyError:
                return_value = self.RESP_VALUES[3]  # Return INVALID
        elif not response:  # Response is empty
            return_value = self.RESP_VALUES[2]  # Return Timeout
        else:  # Response is not empty
            return_value = self.RESP_VALUES[3]  # Return INVALID

        # Display Flag Set
        if display:
            # Display the response
            if isinstance(response, dict):
                print(json.dumps(response))
            else:
                print(response)

        # In case of error and Terminate Flag is set
        if return_value != self.RESP_VALUES[0] and terminate:
            self.disconnect()  # Disconnect from EVE
            sys.exit()  # Terminate

        return return_value


def signal_handler(sig, frame):
    """ Signal handler for keyboard interrupt """
    rebooter.disconnect()
    print("Exiting...")
    sys.exit(0)


if __name__ == "__main__":

    # Argument parser
    ap = argparse.ArgumentParser()
    reqArgs = ap.add_argument_group("required arguments")
    reqArgs.add_argument(
        "-p", "--port", required=True, metavar="", help="COM port (Ex: COM10)"
    )

    args = vars(ap.parse_args())

    # Registering signal handle
    signal.signal(signal.SIGINT, signal_handler)

    rebooter = Rebooter()

    rebooter.connect(args["port"], 115200)

    rebooter.reboot_eve_with_handshake()

    rebooter.disconnect()

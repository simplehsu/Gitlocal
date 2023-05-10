# -*- coding: UTF-8 -*-

import sys
import os
import json
import time
import serial


class Qsn:

    DEFAULT_RD_TIMEOUT = 1
    QSN_ADDRESS = "0x00000400"

    def __init__(self):
        self.ser = None

    def connect(self, *args):
        """ To establish connection between EVE and the PC """

        # Connect to serial COM port with specified configuration
        try:
            self.ser = serial.Serial(
                port=str(args[0]), baudrate=args[1], timeout=self.DEFAULT_RD_TIMEOUT
            )

            # Print Connection Info to user
            # print('\nConnected to EVE')

            # Clear serial port
            self.ser.flushInput()
            self.ser.flushOutput()

        except:
            print("Failed to establish connection with EVE")
            sys.exit()

    def disconnect(self):
        """ Disconnects the connection between EVE and the PC """
        self.ser.close()
        # print('\nDisconnected')

    def send_cmd(self, cmd):
        """ Send String """
        self.ser.timeout = self.DEFAULT_RD_TIMEOUT  # Configure Serial timeout
        cmd = cmd + "\n"  # Add LF to complete the cmd
        for wdata in cmd:  # Read Byte from String
            wdata = wdata.encode("charmap")  # Encode Byte
            self.ser.write(wdata)  # Send Byte
            rdata = self.ser.read(1)  # Read back the byte
            if rdata != wdata:  # Check EVE is responding ?
                print("\nEVE is not responding..!!")  # Print error message
                self.disconnect()  # Disconnect from EVE
                sys.exit()  # Terminate
        self.ser.readline()  # Read new line printed on ending the cmd

    def read_response(self, timeout):
        """ Read Response """
        output = ""
        self.ser.timeout = timeout  # Configure Serial timeout
        line = self.ser.readline()  # Read 1st line of Response
        self.ser.timeout = (
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
            line = self.ser.readline()  # Read next line of Response

    def write(self, data):
        self.send_cmd("EEPROM WRITE" + " " + self.QSN_ADDRESS + " " + data)

        # Read and Parse the Response
        resp = self.read_response(self.DEFAULT_RD_TIMEOUT)
        qsn = (resp["EEPROM"])["RESULT"]

        # Display the response
        if isinstance(resp, dict):
            if (resp["EEPROM"])["RESULT"] == "PASS":
                print("QSN write successful")
                return
        print(resp.encode("ascii"))

    def read(
        self,
    ):
        self.send_cmd("EEPROM READ" + " " + self.QSN_ADDRESS + " " + "16")

        # Read and Parse the Response
        resp = self.read_response(self.DEFAULT_RD_TIMEOUT)

        # Display the response
        if isinstance(resp, dict):
            qsn = ((resp["EEPROM"])["MSG"])[self.QSN_ADDRESS]
            print("QSN: " + "".join([chr(int(x, 16)) for x in qsn.split()]))
        else:
            print(resp.encode("ascii"))


if __name__ == "__main__":

    # Check for Arguments
    if len(sys.argv) < 3:
        # Print Error Message
        print("\nError: Insufficient Arguments")
        # Print Usage Information
        print("Expected  Arguments")
        print("1. COM Port to which EVE is connected")
        print("2. RD_QSN/WR_QSN [QSN]")
        sys.exit()

    module = Qsn()

    # Connect to EVE
    module.connect(sys.argv[1], 115200)

    if sys.argv[2] == "RD_QSN":
        module.read()
    elif sys.argv[2] == "WR_QSN":
        if len(sys.argv) < 4:
            print("\nError: QSN missing")
        else:
            module.write(sys.argv[3])
    else:
        print("\nError: Invalid command")

    # Disconnect from EVE
    module.disconnect()

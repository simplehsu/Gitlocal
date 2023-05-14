# -*- coding: UTF-8 -*-
"""
/** @file  dcl_ship_mode.py
 *  @date  August 21, 2020
 *  @brief This is a tool for DCL to return a charged AG-55 to ship mode.
 *
 *         The tool works best if the script is started, the AG port has
 *         power and then is plugged in.  This will time out if a cell OTA
 *         starts.  Hopefully that will happen during the charge cycle or
 *         not at all.  Only supports AG versions 5602 and higher.
 *
 *         This relies on Python 2.7 and the serial libraries.  If you have
 *         a version of pip for Python 3.x pip will not be able to install
 *         serial and pyserial properly.
 *         Setup on Windows machine:
 *         Install python 2.7 to C:\Python27
 *         pip uninstall pip
 *         Download get-pip.py at https://bootstrap.pypa.io/get-pip.py
 *         python get-pip
 *         python get-pip install
 *         C:\Python27\Scripts
 *         pip install serial
 *         pip install pyserial
 *
 *  @copyright  2020, KeepTruckin, Inc. All rights reserved.
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
import logging


class EveModeSwitch:
    """ To switch between FACTORY and SHIPMENT mode of EVE """

    # TimeOuts in seconds
    DEFAULT_RD_TIMEOUT = 1  # To wait for response from EVE
    SET_UPDATE_FLAG_TIMEOUT = 3  # To wait for firmware update flag to be set
    TG_APP_BATTERY_CHECK_TIMEOUT = (
        7 * 60
    )  # To fetch the battery level with TG Application (7 mins) This can take a long time without GNSS signal.
    TG_APP_HANDSHAKE_TIMEOUT = (
        3 * 60
    )  # To establish handshake with TG Application (3 mins)
    TG_APP_ENTER_CLI_TIMEOUT = 5  # To wait for TG Application to enter CLI mode
    ENTER_SHIP_MODE_TIMEOUT = 60  # To wait for EVE to enter shipment mode
    ENTER_SHIP_MODE_VERIFY_TIMEOUT = 3  # To verify EVE really entered shipment mode
    ENTER_FACT_MODE_TIMEOUT = 2 * 60  # To wait for EVE to switch to factory mode

    # Modules/CMDs and Arguments
    FW_UP_MODULE_NAME = "FW_UPDATE"
    CMD_WR_MCU_FW_INFO = "WR_MCU_FW_INFO"
    CMD_SET_UPDATE_FLAG = "SET_MCU_FW_UPDATE_FLAG"

    SYS_MODULE_NAME = "SYS"
    CMD_REBOOT = "REBOOT"
    CMD_WR_RR = "WR_RR"

    AGM_MODULE_NAME = "AGM"
    CMD_AGM_DIS = "DIS"

    TEMP_MODULE_NAME = "TEMP"
    CMD_TEMP_DIS = "DIS_DEV"

    TG_APP_BATTERY_CHARGE_STRING = "batteryModel.RemChargePercent"
    TG_APP_SERIAL_NUMBER_STRING = "Serial Number"

    # Key to switch to FACT from TG_APP(SHIP)
    TG_APP_HANDSHAKE_STRING = "UpdateAvailable?"
    TG_APP_HANDSHAKE_RESP = "Yes|EnterCLI"

    # Response
    RESP_KEY = "RESULT"
    RESP_VALUES = ["PASS", "FAIL", "TIMEOUT", "INVALID"]

    # EVE Mode
    EVE_MODES = ["FACT", "SHIP", "F_SHIP"]

    # Max Firmware Size
    MAX_APP_FW_SIZE = 1280 * 1024  # 1280 KB

    # Reset Reason
    RR_VALUE = 3

    # Firmware Info
    EXMEM_RAW_MSG_ID = 0xFF01  # OTA Region ID in External Memory
    APP_FW_INT_FLASH_REGION = 2  # APP firmware Region ID in Internal FLASH
    FACT_FW_EXMEM_REG_START_OFFSET = 0x18000  # Start Offset of FACT firmware
    SHIP_FW_EXMEM_REG_START_OFFSET = 0x158000  # Start Offset of SHIP firmware

    def __init__(self):
        self.com = None
        self.time_now = None
        self.debug = False

    def connect(self, com_port, baud):
        """ To establish connection between EVE and the PC """

        # Connect to serial COM port with specified configuration
        try:
            self.com = serial.Serial(
                port=com_port, baudrate=baud, timeout=self.DEFAULT_RD_TIMEOUT
            )
            # Print Connection Info to user
            self.time_now = datetime.datetime.now()
            logging.info("\nConnected to AG-55 at: {}".format(time.ctime()))

            # Clear serial port
            self.com.flushInput()
            self.com.flushOutput()

        except:
            logging.info(
                "\nFailed to establish connection with AG-55.  Verify COM Port, then contact KT."
            )
            sys.exit()

    def disconnect(self):
        """ Disconnects the connection between EVE and the PC """
        if self.com:
            self.com.close()
            logging.info(
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
                logging.info("\nAG-55 is not responding!")  # Print error message
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
        logging.info("\nSending Reboot command.")
        self.send_cmd(self.SYS_MODULE_NAME + " " + self.CMD_REBOOT)

    def reboot_eve_with_handshake(self):
        """ Handshake with TG Application """
        logging.info("Waiting for handshake.")
        left_time = self.TG_APP_HANDSHAKE_TIMEOUT
        self.com.flushInput()
        self.com.flushOutput()

        while left_time > 0:
            self.com.timeout = left_time  # Configure Serial timeout
            start_time = time.time()  # To check for timeout
            line = self.com.readline()  # Try to read expected handshake string
            line.decode("charmap")
            if self.debug == True:
                logging.debug(line)  # Ignore, for debug only
            if self.TG_APP_SERIAL_NUMBER_STRING in line:
                logging.info(line)
            if self.TG_APP_HANDSHAKE_STRING in line:
                self.send_data(
                    self.TG_APP_HANDSHAKE_RESP
                )  # Send Response to Handshake string
                resp = self.read_response(self.TG_APP_ENTER_CLI_TIMEOUT)
                if "Welcome" in resp:  # Check whether TG Application entered CLI
                    logging.info("Handshake successful")
                    self.reboot_eve()
                    return self.RESP_VALUES[0]

            # Calculate Time left to establish handshake
            left_time = left_time - (time.time() - start_time)

        logging.info("\nHandshake failed")
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
                logging.info(json.dumps(response))
            else:
                logging.info(response)

        # In case of error and Terminate Flag is set
        if return_value != self.RESP_VALUES[0] and terminate:
            self.disconnect()  # Disconnect from EVE
            sys.exit()  # Terminate

        return return_value

    def set_reset_reason(self, rr_value):
        """ Set reset reason """
        logging.info("\nSetting Reset Reason")
        self.send_cmd("{} {} {}".format(self.SYS_MODULE_NAME, self.CMD_WR_RR, rr_value))
        resp = self.read_response(self.DEFAULT_RD_TIMEOUT)
        self.parse_response(resp, self.SYS_MODULE_NAME, True, True)
        logging.info("Done")

    def set_update_flag(self):
        """ Initiate application Firmware update """
        # Send Initiate Update CMD
        logging.info("\nSet Firmware update flag.")
        self.send_cmd(self.FW_UP_MODULE_NAME + " " + self.CMD_SET_UPDATE_FLAG)

        # Read and Parse the Response
        resp = self.read_response(self.SET_UPDATE_FLAG_TIMEOUT)
        self.parse_response(resp, self.FW_UP_MODULE_NAME, True, True)
        logging.info("Done")

    def tg_app_charge_check(self):
        """ Checking Battery Charge """
        logging.info("Waiting for Battery Charge Level.")
        left_time = self.TG_APP_BATTERY_CHECK_TIMEOUT
        self.com.flushInput()
        self.com.flushOutput()

        while left_time > 0:
            self.com.timeout = left_time  # Configure Serial timeout
            start_time = time.time()  # To check for timeout
            line = self.com.readline()  # Try to read expected handshake string
            line.decode("charmap")
            if self.debug == True:
                logging.debug(line)  # Ignore, for debug only
            if self.TG_APP_SERIAL_NUMBER_STRING in line:
                logging.info(line)
            if self.TG_APP_BATTERY_CHARGE_STRING in line:
                index = line.find(self.TG_APP_BATTERY_CHARGE_STRING)
                index = index + len(self.TG_APP_BATTERY_CHARGE_STRING) + 1
                percent = int(line[index:])
                if percent > 70:
                    logging.info("Charge is good at " + str(percent))
                    return self.RESP_VALUES[0]
                else:
                    logging.info("Charge is LOW at " + str(percent))
                    return self.RESP_VALUES[1]

            # Calculate Time left to establish handshake
            left_time = left_time - (time.time() - start_time)

        return self.RESP_VALUES[2]

    def tg_app_handshake(self):
        """ Handshake with TG Application """
        logging.info("Waiting for handshake.")
        left_time = self.TG_APP_HANDSHAKE_TIMEOUT
        self.com.flushInput()
        self.com.flushOutput()

        while left_time > 0:
            self.com.timeout = left_time  # Configure Serial timeout
            start_time = time.time()  # To check for timeout
            line = self.com.readline()  # Try to read expected handshake string
            line.decode("charmap")
            if self.debug == True:
                logging.debug(line)  # Ignore, for debug only
            if self.TG_APP_SERIAL_NUMBER_STRING in line:
                logging.info(line)
            if self.TG_APP_HANDSHAKE_STRING in line:
                self.send_data(
                    self.TG_APP_HANDSHAKE_RESP
                )  # Send Response to Handshake string
                resp = self.read_response(self.TG_APP_ENTER_CLI_TIMEOUT)
                if "Welcome" in resp:  # Check whether TG Application entered CLI
                    logging.info("Handshake successful")
                    return self.RESP_VALUES[0]

            # Calculate Time left to establish handshake
            left_time = left_time - (time.time() - start_time)

        logging.info("\nHandshake failed")
        return self.RESP_VALUES[2]

    def verify_switch_operation(self, switch_to):
        """ Function to verify whether switch operation is successful or not """
        if switch_to == self.EVE_MODES[1]:
            left_time = self.ENTER_SHIP_MODE_TIMEOUT
            found_shipment_mode = False
            enter_shipment_mode_success = True
            while left_time > 0:
                self.com.timeout = left_time  # Configure Serial timeout
                start_time = time.time()  # To check for timeout

                line = self.com.readline().decode("utf8")

                if found_shipment_mode:
                    if "Failed to enter SHIPMENT MODE" in line:
                        enter_shipment_mode_success = False

                if "Entering SHIPMENT MODE" in line:
                    found_shipment_mode = True
                    left_time = self.ENTER_SHIP_MODE_VERIFY_TIMEOUT
                else:
                    left_time = left_time - (time.time() - start_time)

            if enter_shipment_mode_success and found_shipment_mode:
                logging.info("\nEntered SHIPMENT MODE successfully!")
            else:
                logging.info("\nError: Failed to enter SHIPMENT MODE")
        else:
            left_time = self.ENTER_FACT_MODE_TIMEOUT
            while left_time > 0:
                self.com.timeout = left_time  # Configure Serial timeout
                start_time = time.time()  # To check for timeout
                line = self.com.readline()
                line.decode("charmap")
                if "Welcome" in line:
                    logging.info("\nSwitched back to FACTORY MODE successfully...!!")
                    return

                left_time = left_time - (time.time() - start_time)

    def force_enter_ship_mode(self):
        result = self.reboot_eve_with_handshake()  # Get the device to a known state
        if result != self.RESP_VALUES[0]:
            logging.info("\n*********************************************")
            logging.info("* ERROR REBOOTING.  CONTACT KT.             *")
            logging.info("*********************************************")
            logging.info("\nFinished At: {}".format(time.ctime()))
            return

        result = self.tg_app_charge_check()
        if result == self.RESP_VALUES[2]:
            logging.info("\n*********************************************")
            logging.info("* ERROR GETTING BATTERY LEVEL.  CONTACT KT. *")
            logging.info("*********************************************")
            logging.info("\nFinished At: {}".format(time.ctime()))
            return

        if result == self.RESP_VALUES[1]:
            logging.info("\n*******************************************")
            logging.info("* DEVICE NEEDS MORE CHARGE, TRY AGAIN *")
            logging.info("*******************************************")
            logging.info("\nFinished At: {}".format(time.ctime()))
            return

        if self.tg_app_handshake() != self.RESP_VALUES[0]:
            logging.info("\n*******************************************")
            logging.info("* FAILED TO SET SHIP MODE, TRY AGAIN  *")
            logging.info("*******************************************")
            logging.info("\nFinished At: {}".format(time.ctime()))
            return

        self.set_reset_reason(self.RR_VALUE)
        self.reboot_eve()
        self.verify_switch_operation(self.EVE_MODES[1])

        logging.info("\n*******************************************")
        logging.info("* DEVICE IN SHIPMENT MODE.  RETURN TO BOX *")
        logging.info("*******************************************")
        logging.info("\nFinished At: {}".format(time.ctime()))


def signal_handler(sig, frame):
    """ Signal handler for keyboard interrupt """
    switch_mode.disconnect()
    logging.info("Exiting...")
    sys.exit(0)


if __name__ == "__main__":

    # Argument parser
    ap = argparse.ArgumentParser()
    ap.add_argument("PORT", help="COM port (Ex: COM10)")
    ap.add_argument("--debug", help="print debug info", required=False)

    args = vars(ap.parse_args())

    # Registering signal handle
    signal.signal(signal.SIGINT, signal_handler)

    switch_mode = EveModeSwitch()

    if not os.path.exists(".\\Logs"):
        os.makedirs(".\\Logs")

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
        datefmt="%m-%d %H:%M",
        filename=".\\Logs\\shipment_mode.log",
        filemode="a",
    )

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)

    formatter = logging.Formatter("%(name)-12s: %(levelname)-8s %(message)s")
    logging.getLogger().addHandler(console)

    if args["debug"] == "True":
        logging.info("Debug Printing Enabled")
        console.setLevel(logging.DEBUG)
        switch_mode.debug = True

    switch_mode.connect(args["PORT"], 115200)

    switch_mode.force_enter_ship_mode()

    switch_mode.disconnect()

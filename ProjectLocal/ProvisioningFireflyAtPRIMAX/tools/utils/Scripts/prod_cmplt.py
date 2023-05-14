# -*- coding: UTF-8 -*-
"""
/**===========================================================================
 * @file   prod_cmplt.py
 * @date   08-April-2019
 * @author malikrihan.r@pathpartnertech.com
 *
 * @brief  Python script to put the device in shipment mode
 *
 *============================================================================
 *
 * Copyright � 2019, KeepTruckin, Inc.
 * All rights reserved.
 *
 * All information contained herein is the property of KeepTruckin Inc. The
 * intellectual and technical concepts contained herein are proprietary to
 * KeepTruckin. Dissemination of this information or reproduction of this
 * material is strictly forbidden unless prior written permission is obtained
 * from KeepTruckin.
 *
 *===========================================================================
 */
"""

import sys
import signal
import argparse
import time
import json
import datetime
import serial


class EveModeSwitch:
    """ To switch between FACTORY and SHIPMENT mode of EVE """

    # TimeOuts in seconds
    DEFAULT_RD_TIMEOUT = 1  # To wait for response from EVE
    SET_UPDATE_FLAG_TIMEOUT = 3  # To wait for firmware update flag to be set
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

    def connect(self, com_port, baud):
        """ To establish connection between EVE and the PC """

        # Connect to serial COM port with specified configuration
        try:
            self.com = serial.Serial(
                port=com_port, baudrate=baud, timeout=self.DEFAULT_RD_TIMEOUT
            )
            # Print Connection Info to user
            self.time_now = datetime.datetime.now()
            print("\n{} Connected to EVE".format(time.ctime()))
            print(self.com)

            # Clear serial port
            self.com.flushInput()
            self.com.flushOutput()

        except:
            print("\nFailed to establish connection with EVE")
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
                print("\nEVE is not responding..!!")  # Print error message
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
        print("\nSending Re-boot command....")
        self.send_cmd(self.SYS_MODULE_NAME + " " + self.CMD_REBOOT)

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

    def send_fw_info(self, offset, checksum, size):
        """ Send firmware Information required to switch mode """
        # Form CMD string
        cmd = "{} {} {} {:x} {:x} {:x} {}".format(
            self.FW_UP_MODULE_NAME,
            self.CMD_WR_MCU_FW_INFO,
            size,
            checksum,
            self.EXMEM_RAW_MSG_ID,
            offset,
            self.APP_FW_INT_FLASH_REGION,
        )

        # Send Firmware Info
        print("\nSending Firmware Information..........")
        self.send_cmd(cmd)

        # Read and Parse the Response
        resp = self.read_response(self.DEFAULT_RD_TIMEOUT)
        self.parse_response(resp, self.FW_UP_MODULE_NAME, True, True)

        print("Done")

    def set_reset_reason(self, rr_value):
        """ Set reset reason """
        print("\nSetting Reset Reason")
        self.send_cmd("{} {} {}".format(self.SYS_MODULE_NAME, self.CMD_WR_RR, rr_value))
        resp = self.read_response(self.DEFAULT_RD_TIMEOUT)
        self.parse_response(resp, self.SYS_MODULE_NAME, True, True)
        print("Done")

    def set_update_flag(self):
        """ Initiate application Firmware update """
        # Send Initiate Update CMD
        print("\nSet Firmware update flag.........")
        self.send_cmd(self.FW_UP_MODULE_NAME + " " + self.CMD_SET_UPDATE_FLAG)

        # Read and Parse the Response
        resp = self.read_response(self.SET_UPDATE_FLAG_TIMEOUT)
        self.parse_response(resp, self.FW_UP_MODULE_NAME, True, True)
        print("Done")

    def tg_app_handshake(self):
        """ Handshake with TG Application """
        print("Waiting for handshake........")
        left_time = self.TG_APP_HANDSHAKE_TIMEOUT
        self.com.flushInput()
        self.com.flushOutput()

        while left_time > 0:
            self.com.timeout = left_time  # Configure Serial timeout
            start_time = time.time()  # To check for timeout
            line = self.com.readline()  # Try to read expected handshake string
            line.decode("charmap")
            print(line)  # Ignore, for debug only
            if self.TG_APP_HANDSHAKE_STRING in line:
                self.send_data(
                    self.TG_APP_HANDSHAKE_RESP
                )  # Send Response to Handshake string
                resp = self.read_response(self.TG_APP_ENTER_CLI_TIMEOUT)
                if "Welcome" in resp:  # Check whether TG Application entered CLI
                    print("Handshake successful")
                    return self.RESP_VALUES[0]

            # Calculate Time left to establish handshake
            left_time = left_time - (time.time() - start_time)

        print("\nHandshake failed")
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
                print("\nEntered SHIPMENT MODE successfully...!!")
            else:
                print("\nError: Failed to enter SHIPMENT MODE")
        else:
            left_time = self.ENTER_FACT_MODE_TIMEOUT
            while left_time > 0:
                self.com.timeout = left_time  # Configure Serial timeout
                start_time = time.time()  # To check for timeout
                line = self.com.readline()
                line.decode("charmap")
                if "Welcome" in line:
                    print("\nSwitched back to FACTORY MODE successfully...!!")
                    return

                left_time = left_time - (time.time() - start_time)

    def disable_agm_and_temp_sens(self):
        print("\nDisabling AGM Sensor")
        self.send_cmd("{} {}".format(self.AGM_MODULE_NAME, self.CMD_AGM_DIS))
        resp = self.read_response(self.DEFAULT_RD_TIMEOUT)
        self.parse_response(resp, self.AGM_MODULE_NAME, True, True)
        print("Done")

        print("\nDisabling TEMP Sensor")
        self.send_cmd("{} {}".format(self.TEMP_MODULE_NAME, self.CMD_TEMP_DIS))
        resp = self.read_response(self.DEFAULT_RD_TIMEOUT)
        self.parse_response(resp, self.TEMP_MODULE_NAME, True, True)
        print("Done")

    def switch_to_ship_mode(self, checksum, size):
        """ Function to enter shipment mode """
        print(
            "\nRequested to enter SHIPMENT mode. It means that "
            "all testing is done and unit is ready for shipment."
        )
        print("Note: After successful execution of this command")
        print("\t1. Console will no longer be available")
        print("\t2. Device will enter SHIPMENT mode")

        # Read user choice
        try:
            choice = raw_input("\nContinue... ? [y/n]: ")
        except NameError:
            choice = input("\nContinue... ? [y/n]: ")

        # Terminate if opted
        if choice != "y":
            return

        self.send_fw_info(self.SHIP_FW_EXMEM_REG_START_OFFSET, checksum, size)
        self.set_reset_reason(self.RR_VALUE)
        self.disable_agm_and_temp_sens()  # This is just a workaround, proper fix is required in AG_APP
        self.set_update_flag()
        self.reboot_eve()
        print("\nLook for LED indications..")
        self.verify_switch_operation(self.EVE_MODES[1])

    def switch_to_fact_mode(self, checksum, size):
        """ Function to enter shipment mode """
        print("\nRequested to switch back to FACTORY mode.")
        print("Note: After successful execution of this command")
        print(
            "\t1. Device will enter FACTORY mode leaving SHIPMENT"
            " mode and will not be suitable for shipment"
        )
        print(
            "\t2. Have to re-do the production complete process"
            " to make this unit eligible for shipment"
        )

        # Read user choice
        try:
            choice = raw_input("\nContinue... ? [y/n]: ")
        except NameError:
            choice = input("\nContinue... ? [y/n]: ")

        # Terminate if opted
        if choice != "y":
            return

        if self.tg_app_handshake() != self.RESP_VALUES[0]:
            return
        self.send_fw_info(self.FACT_FW_EXMEM_REG_START_OFFSET, checksum, size)
        self.set_update_flag()
        self.reboot_eve()
        print("\nLook for LED indications..")
        self.verify_switch_operation(self.EVE_MODES[0])

    def force_enter_ship_mode(self):
        print("\nRequested force entry to SHIPMENT mode. ")
        print("Note: After successful execution of this command")
        print("\t1. Device will enter SHIPMENT mode")
        print("\t2. Need to do standard wake-up activity to make unit up again")

        # Read user choice
        try:
            choice = raw_input("\nContinue... ? [y/n]: ")
        except NameError:
            choice = input("\nContinue... ? [y/n]: ")

        # Terminate if opted
        if choice != "y":
            return

        if self.tg_app_handshake() != self.RESP_VALUES[0]:
            return
        self.set_reset_reason(self.RR_VALUE)
        self.reboot_eve()
        self.verify_switch_operation(self.EVE_MODES[1])


def signal_handler(sig, frame):
    """ Signal handler for keyboard interrupt """
    switch_mode.disconnect()
    print("Exiting...")
    sys.exit(0)


if __name__ == "__main__":

    # Argument parser
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "SWITCH-TO",
        default=EveModeSwitch.EVE_MODES[1],
        choices=EveModeSwitch.EVE_MODES,
        nargs="?",
        help="Switch to requested mode.(Default choice is SHIP)",
    )
    ap.add_argument("PORT", help="COM port (Ex: COM10)")
    ap.add_argument(
        "CHECKSUM",
        type=lambda x: int(x, 16),
        help="Checksum of the factory firmware to switch to FACT "
        "mode or checksum of the tg_app(shipment) firmware "
        "to switch to SHIP mode. Value in Hex (Ex: 0x1d513d1)",
    )
    ap.add_argument(
        "SIZE",
        type=lambda x: int(x, 16),
        help="Size of the factory firmware to switch to FACT "
        "mode or size of the tg_app(shipment) firmware to "
        "switch to SHIP mode. Value in Hex (Ex: 0x4a0fc)",
    )

    args = vars(ap.parse_args())

    # Registering signal handle
    signal.signal(signal.SIGINT, signal_handler)

    switch_mode = EveModeSwitch()

    switch_mode.connect(args["PORT"], 115200)

    if args["SWITCH-TO"] == switch_mode.EVE_MODES[0]:
        switch_mode.switch_to_fact_mode(args["CHECKSUM"], args["SIZE"])
    elif args["SWITCH-TO"] == switch_mode.EVE_MODES[1]:
        switch_mode.switch_to_ship_mode(args["CHECKSUM"], args["SIZE"])
    else:
        switch_mode.force_enter_ship_mode()

    switch_mode.disconnect()

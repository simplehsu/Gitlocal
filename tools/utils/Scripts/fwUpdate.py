#! /usr/bin/env nix-shell
#! nix-shell --pure -i python2 -p "python2.withPackages(ps: with ps; [ pyserial ])"
"""
/**===========================================================================
 * @file   fwUpdate.py
 * @date   08-Mar-2019
 * @author vinay.r@pathpartnertech.com
 *
 * @brief  Python Script for firmware upgrade
 * Note:
 * This script also supports placing the FIRMWWARE IMGAE to QSPI flash
 * As per the factory process, shipment image should be placed in QSPI before
 * SMT. Factory should follow QSPI gang programming. However, SW need to
 * simulate and Verify the  implementation, before factory process.
 * This script helps to place the user specified image in QSPI.
 *
 * Note: Please refer the user guide for detailed usage
 *
 *============================================================================
 *
 * Copyright (c) 2019, KeepTruckin, Inc.
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
import os
import json
import time
import argparse
import re
import datetime
import serial


class EveFwUpdate:
    """ To update EVE Firmware """

    # Number of bytes to send in one shot
    CHUNK_SIZE = 16 * 1024  # Must be <= fw_updateCliBUFF_SIZE

    # Number of retries
    RE_TRY_COUNT = 3

    # TimeOuts in seconds
    SEC_ERASE_TIMEOUT = 2  # To wait for sector erase to get complete
    WR_FW_TIMEOUT = 30  # To transfer CHUNK_SIZE bytes
    WR_FW_INITIAL_DELAY = 0.01  # To wait for EVE to be ready to read firmware
    SET_UPDATE_FLAG_TIMEOUT = 3  # To wait for firmware update flag to be set
    VER_FW_CHECKSUM_TIMEOUT = 3  # To wait for firmware checksum validation to get over
    BTL_UPDATE_TIMEOUT = 15  # To wait for Boot-loader update to get complete
    DEFAULT_RD_TIMEOUT = 1  # To wait for response from EVE
    TG_APP_HANDSHAKE_TIMEOUT = (
        6 * 60
    )  # To establish handshake with TG Application (6 mins)
    TG_APP_ENTER_CLI_TIMEOUT = 5  # To wait for TG Application to enter CLI mode
    APP_FW_UPDATE_TIMEOUT = 20  # To wait for App firmware update to get complete
    TG_APP_BOOT_TIMEOUT = 3 * 60  # To wait for TG_APP to boot
    FAC_APP_BOOT_TIMEOUT = 50  # To wait for FAC APP to boot
    EXMEM_FORMAT_TIMEOUT = 5 * 60  # To wait for EXMEM format to get complete (5 mins)

    # Max Firmware Size
    MAX_APP_FW_SIZE = 1280 * 1024  # 1280 KB
    MAX_BTL_FW_SIZE = 64 * 1024  # 64 KB

    # Internal Flash Information
    APP_FW_INT_FLASH_REGION = 2  # APP firmware Region ID in Internal FLASH
    BTL_FW_INT_FLASH_REGION = 0  # Boot-loader firmware Region ID in Internal FLASH

    # Modules/CMDs and Arguments
    FW_UP_MODULE_NAME = "FW_UPDATE"
    CMD_WR_MCU_FW_INFO = "WR_MCU_FW_INFO"
    CMD_WR_BTL_FW_INFO = "WR_BTL_FW_INFO"
    CMD_SET_UPDATE_FLAG = "SET_MCU_FW_UPDATE_FLAG"
    CMD_UPDATE_BTL = "UPDATE_BTL"
    CMD_WR_FW = "WR_FW"
    CMD_VER_MCU_CHKSM = "VER_MCU_CHECKSUM"

    QSPI_MODULE_NAME = "QSPI"
    CMD_QSPI_SEC_ERASE = "SEC_ER"
    QSPI_SEC_SIZE = 64 * 1024  # 64 KB Sector
    QSPI_SEC_ARG = 2  # Argument to be passed to erase QSPI_SEC_SIZE sector

    EXMEM_MODULE_NAME = "EXMEM"
    CMD_EXMEM_FORMAT = "FORMAT"

    SYS_MODULE_NAME = "SYS"
    CMD_REBOOT = "REBOOT"
    CMD_FW_VER = "FW_VER"

    # Key to switch to CLI from TG_APP
    TG_APP_HANDSHAKE_STRING = "UpdateAvailable?"
    TG_APP_HANDSHAKE_RESP = "Yes|EnterCLI"

    # Response
    RESP_KEY = "RESULT"
    RESP_VALUES = ["PASS", "FAIL", "TIMEOUT", "INVALID"]

    # EVE Mode
    EVE_MODES = ["FACT", "TG_APP"]

    # Firmware Types
    FW_TYPES = ["bootloader", "factory", "tg_app"]

    # Operations
    OP_SMT_SIMULATE = "SMT_SIMULATE"
    OP_FW_UPDATE = "FW_UPDATE"

    # Dependency:[Version, ExmemID, ExmemOffset, EraseAddress, BTL update support]
    DEP_DET = [
        [4011, 0xFF01, 0x8000, 0x10000, True],
        [4005, 0xFF05, 0x0, 0x2C00000, False],
    ]

    # Assuming we finalize the boot-loader by V6000
    FINAL_BTL_VER = 9000

    def __init__(self, mode, operation):
        self.com = None
        self.time_now = None
        self.cur_ver = []
        self.mem_det = []
        self.bin_info = []
        self.mode = mode
        self.operation = operation
        if operation == self.OP_SMT_SIMULATE:
            self.mode = self.EVE_MODES[0]

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

            # Perform handshake if EVE is in TG_AP mode
            if self.mode == self.EVE_MODES[1]:
                if self.tg_app_handshake() != self.RESP_VALUES[0]:
                    print(
                        "\nHandshake failed after {}".format(
                            str(datetime.datetime.now() - time_start)
                        )
                    )
                    self.disconnect()
                    sys.exit()
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

    def reboot_eve(self):
        """ Reboot EVE  """
        # Send Reboot cmd
        print("\nSending Re-boot command....")
        self.send_cmd(self.SYS_MODULE_NAME + " " + self.CMD_REBOOT)
        print(
            "\n{} Done after {}".format(
                time.ctime(), str(datetime.datetime.now() - self.time_now)
            )
        )

    def get_dependency_det(self, ver):
        """ Get dependency details of required version """
        for det in self.DEP_DET:
            if det[0] <= ver:
                return det
        # Will never happen
        return []

    def extract_bin_info(self, files, checksum):
        """ Extract information from given binary files """

        for file in files:
            file_name = os.path.basename(file)
            inf = re.findall(
                r"^((lbb_mcu)((_)(bootloader|factory))?)((_)([0-9]{4,6}))?(\.bin)$",
                file_name,
            )

            info = [inf[0][4], inf[0][7], file, os.path.getsize(file)]
            if info[0] == "":
                info[0] = "tg_app"

            if info[1] == "":
                info[1] = int("4005")
            else:
                info[1] = int(info[1])

            if info[0] == self.FW_TYPES[0] and info[1] > self.FINAL_BTL_VER:
                print(
                    "\nError: V{} is the final boot-loader version. Hence Boot-loader "
                    "update to V{} is not possible".format(self.FINAL_BTL_VER, info[1])
                )
                return False

            # Check whether firmware size is within the limit
            if info[0] == self.FW_TYPES[0] and info[3] > self.MAX_BTL_FW_SIZE:
                print(
                    "\nError: Boot-loader firmware size should be less than"
                    " {} bytes".format(self.MAX_BTL_FW_SIZE)
                )
                return False

            if (info[0] == self.FW_TYPES[1] or info[0] == self.FW_TYPES[2]) and info[
                3
            ] > self.MAX_APP_FW_SIZE:
                print(
                    "\nError: Application firmware size should be less than"
                    " {} bytes".format(self.MAX_APP_FW_SIZE)
                )
                return False

            self.bin_info.append(info)

        if len(self.bin_info) == 2 and self.operation == self.OP_FW_UPDATE:
            if self.bin_info[0][0] == self.FW_TYPES[0]:
                self.bin_info.reverse()

            if self.bin_info[0][0] == self.bin_info[1][0]:
                print("\nERROR: Encountered multiple files of same firmware type")
                return False

            if (
                self.bin_info[0][0] != self.FW_TYPES[0]
                and self.bin_info[1][0] != self.FW_TYPES[0]
            ):
                print(
                    "\nERROR: Update to both TG_APP and FACTORY firmware is not possible"
                )
                return False

        if self.operation == self.OP_SMT_SIMULATE:
            if (
                self.bin_info[0][0] == self.FW_TYPES[0]
                or self.bin_info[1][0] == self.FW_TYPES[0]
            ):
                print("\nError: SMT simulation for boot-loader is not supported")
                return False

            if self.bin_info[0][0] == self.bin_info[1][0]:
                print(
                    "\nERROR: Encountered multiple files of same firmware type. Provide"
                    " both factory and TG application firmware files"
                )
                return False

            self.bin_info[0].append(checksum[0])
            self.bin_info[1].append(checksum[1])

            if self.bin_info[0][0] == self.FW_TYPES[2]:
                self.bin_info.reverse()

        return True

    def get_cur_fw_ver(self):
        print("\nFetching Firmware version....")
        # Get firmware version
        self.send_cmd(self.SYS_MODULE_NAME + " " + self.CMD_FW_VER)
        resp = self.read_response(2)
        if not isinstance(resp, dict):
            print(
                "\nError: Unable to fetch the current firmware version. Make sure"
                " EVE is running on Version 4.5 or above"
            )
            return False

        # Read Boot-loader version
        try:
            self.cur_ver.append(int(((resp[self.SYS_MODULE_NAME])["MSG"])["BTL"]))
            if self.cur_ver[0] > self.FINAL_BTL_VER:
                # This can happen if boot-loader is still <= V4005 and app is not
                self.cur_ver[0] = int("4005")
        except KeyError:
            self.cur_ver.append(int("4005"))
            self.cur_ver.append(self.cur_ver[0])
            print(
                "\nCurrent firmware Information: [{} - <= V{}] [BTL - <= V{}]".format(
                    self.mode, self.cur_ver[1], self.cur_ver[0]
                )
            )
            return True

        # Read application version
        if self.mode == self.EVE_MODES[1]:
            # If TG_APP
            try:
                self.cur_ver.append(
                    int(((resp[self.SYS_MODULE_NAME])["MSG"])["TG_APP"])
                )
            except KeyError:
                self.cur_ver.append(self.get_tg_app_ver())
                if not self.cur_ver[1]:
                    print("\nError: Unable to fetch the current firmware version")
                    return False
        else:
            self.cur_ver.append(int(((resp[self.SYS_MODULE_NAME])["MSG"])["CLI"]))

        print(
            "\nCurrent firmware Information: [{} - V{}] [BTL - V{}]".format(
                self.mode, self.cur_ver[1], self.cur_ver[0]
            )
        )
        return True

    def get_tg_app_ver(self):
        """ Work around to get TG_APP version in version below 4013 """
        magic_num = int("DEFEC8ED", 16)
        max_count = int("FFFFFFFF", 16)
        min_count = 0
        self.send_cmd("EEPROM READ 180 16")
        resp1 = self.read_response(2)
        if not isinstance(resp1, dict):
            return None
        self.send_cmd("EEPROM READ 2180 16")
        resp2 = self.read_response(2)
        if not isinstance(resp1, dict):
            return None
        try:
            value1 = ((resp1["EEPROM"])["MSG"])["0x00000180"]
            value1 = list(value1.split())
            value1.reverse()
            value1 = [
                int("".join(x), 16)
                for x in [value1[0:4], value1[4:8], value1[8:12], value1[12:16]]
            ]
            value2 = ((resp2["EEPROM"])["MSG"])["0x00002180"]
            value2 = list(value2.split())
            value2.reverse()
            value2 = [
                int("".join(x), 16)
                for x in [value2[0:4], value2[4:8], value2[8:12], value2[12:16]]
            ]

            pos = 0
            if value1[2] == magic_num and value2[2] != magic_num:
                return value1[0]
            if value2[2] == magic_num and value1[2] != magic_num:
                return value2[0]
            if value1[2] != magic_num and value2[2] != magic_num:
                pos = 2

            if value1[3] == max_count and value2[3] == min_count:
                return value2[pos]
            if value2[3] == max_count and value1[3] == min_count:
                return value1[pos]
            if value1[3] > value2[3]:
                return value1[pos]
            return value2[pos]
        except KeyError:
            return None

    def check_dependencies(self):
        """ Check for dependencies involved in requested update operation """

        # Read current firmware version
        if not self.get_cur_fw_ver():
            return False

        print("\nChecking dependency........")

        if self.bin_info[0][0] == self.FW_TYPES[0]:
            # Request for boot-loader update
            return self.is_btl_update_possible(self.bin_info[0])

        # Request for Application update
        if not self.is_app_update_possible():
            return False

        # Is requested application update possible ?

        new_dep_det = self.get_dependency_det(self.bin_info[0][1])
        cur_dep_det = self.get_dependency_det(self.cur_ver[1])

        if new_dep_det[0] < cur_dep_det[0]:
            print(
                "\nError: Downgrade to {} below V{} is not supported".format(
                    self.bin_info[0][0], cur_dep_det[0]
                )
            )

        elif new_dep_det[0] > cur_dep_det[0]:
            # Critical change from existing version to requested version. Requires boot-loader update
            if len(self.bin_info) == 1:
                # No request for boot-loader update. Throw error
                print(
                    "\nError: Updating to {} V{} from {} V{} or below alone is not "
                    "allowed. Consider updating both boot-loader and application to V{}".format(
                        self.bin_info[0][0],
                        self.bin_info[0][1],
                        self.mode,
                        self.cur_ver[1],
                        self.bin_info[0][1],
                    )
                )
            elif self.bin_info[1][1] < new_dep_det[0]:
                print(
                    "\nError: Updating boot-loader to V{} from V{} or below and {} to V{} "
                    "from V{} or below is not allowed. Consider updating both"
                    " boot-loader and application to V{} or above".format(
                        self.bin_info[1][1],
                        self.cur_ver[0],
                        self.bin_info[0][0],
                        self.bin_info[0][1],
                        self.cur_ver[1],
                        new_dep_det[0],
                    )
                )
            else:
                self.mem_det.append(cur_dep_det)
                self.mem_det.append(new_dep_det)
                return True

        else:
            # Request for dummy app update
            self.mem_det.append(cur_dep_det)
            # If boot-loader update is not requested
            if len(self.bin_info) == 1:
                return True

            if self.is_btl_update_possible(self.bin_info[1]):
                # Can update boot-loader first and then application in this case
                self.mem_det.reverse()
                self.bin_info.reverse()
                return True

        return False

    def is_app_update_possible(self):
        """ Function to check whether application update is possible or not """

        btl_dep_det = self.get_dependency_det(self.cur_ver[0])
        app_dep_det = self.get_dependency_det(self.cur_ver[1])

        if btl_dep_det[0] == app_dep_det[0]:
            return True

        if btl_dep_det[0] > app_dep_det[0]:
            print(
                "\nError: Existing boot-loader and application are not compatible "
                "to do any application update. First downgrade the boot-loader to "
                "V{} or below".format(app_dep_det[0])
            )
        else:
            if len(self.bin_info) == 2:
                return True
            print(
                "\nError: Existing boot-loader and application are not compatible "
                "to do any application update. First update the boot-loader to "
                "V{} or above".format(app_dep_det[0])
            )
        return False

    def is_btl_update_possible(self, new_bin_info):
        """ Function to check whether boot-loader update is possible or not"""
        # Get version details
        new_dep_det = self.get_dependency_det(new_bin_info[1])
        cur_dep_det = self.get_dependency_det(self.cur_ver[1])

        # TG_APP: Check whether it is supported or not
        if self.mode == self.EVE_MODES[1] and not cur_dep_det[4]:
            print(
                "\nError: Boot-loader update is not supported in "
                "TG_APP V{}".format(self.cur_ver[1])
            )
        elif cur_dep_det[0] < new_dep_det[0]:
            print(
                "\nError: Updating boot-loader alone to V{} in {} V{} or below is "
                "not allowed".format(new_bin_info[1], self.mode, self.cur_ver[1])
            )
        elif cur_dep_det[0] > new_dep_det[0]:
            print(
                "\nError: Downgrading boot-loader alone to V{} in {} V{} or below is "
                "not allowed".format(new_bin_info[1], self.mode, self.cur_ver[1])
            )
        else:
            self.mem_det.append(cur_dep_det)
            return True

        return False

    def update_fw(self):
        """ Function to update firmwares in required order """

        # Boot-loader [ + Application] update
        if self.bin_info[0][0] == self.FW_TYPES[0]:
            if len(self.bin_info) == 2:  # Is there a request for app update also
                self.btl_fw_update(
                    0, True, False
                )  # Update boot-loader. No need for reboot
                self.app_fw_update(1)  # Update Application
            else:
                self.btl_fw_update(0, True, True)  # Update boot-loader and reboot
            return

        # Application [ + Boot-loader] update
        if len(self.bin_info) == 2:
            self.warn_user()  # Warn user if request is to update both
        self.app_fw_update(0)  # Update Application

        # Request for boot-loader update ?
        if len(self.bin_info) == 2:
            # Print waiting message for user
            print("\nWaiting for Application update to get over....Please wait....")
            time.sleep(self.APP_FW_UPDATE_TIMEOUT)
            # Was it update to TG_APP ?
            if self.bin_info[0][0] == self.FW_TYPES[2]:
                self.mode = self.EVE_MODES[1]
                # Wait for TG_APP to boot
                if (
                    self.is_eve_ready(
                        "TG APP CLI console Task", self.TG_APP_BOOT_TIMEOUT
                    )
                    != self.RESP_VALUES[0]
                ):
                    print(
                        "\nError:Looks like the set-up is disturbed. Unable to communicate with EVE"
                    )
                    return
                # Perform handshake
                if self.tg_app_handshake() != self.RESP_VALUES[0]:
                    return
            else:
                self.mode = self.EVE_MODES[0]
                # Wait for factory application to boot
                if (
                    self.is_eve_ready("Welcome", self.FAC_APP_BOOT_TIMEOUT)
                    != self.RESP_VALUES[0]
                ):
                    print(
                        "\nError:Looks like the set-up is disturbed. Unable to communicate with EVE"
                    )
                    return
            # Update boot-loader and reboot
            self.btl_fw_update(1, False, True)

    def app_fw_update(self, inf_pos):
        """ Function to update application firmware  """

        # Calculate Write and erase offset based on firmware type
        write_offset = self.mem_det[inf_pos][2] + self.MAX_BTL_FW_SIZE
        erase_offset = self.mem_det[inf_pos][3] + self.MAX_BTL_FW_SIZE
        if self.bin_info[inf_pos][0] == self.FW_TYPES[2]:
            write_offset += self.MAX_APP_FW_SIZE
            erase_offset += self.MAX_APP_FW_SIZE

        # Send Firmware Information
        self.send_fw_info(
            self.bin_info[inf_pos],
            self.CMD_WR_MCU_FW_INFO,
            self.mem_det[inf_pos][1],
            write_offset,
            self.APP_FW_INT_FLASH_REGION,
        )

        # Erase Memory
        self.erase_exmemory(erase_offset, self.bin_info[inf_pos][3])

        # Send Firmware
        self.send_binary(self.bin_info[inf_pos][2], write_offset)

        # Initiate Update
        self.set_update_flag()

        # Re-Boot EVE
        self.reboot_eve()

    def btl_fw_update(self, inf_pos, warn, reboot):
        """ Function to update Boot-loader firmware  """

        # Send Firmware Information
        self.send_fw_info(
            self.bin_info[inf_pos],
            self.CMD_WR_BTL_FW_INFO,
            self.mem_det[inf_pos][1],
            self.mem_det[inf_pos][2],
            self.BTL_FW_INT_FLASH_REGION,
        )

        # Erase Memory
        self.erase_exmemory(self.mem_det[inf_pos][3], self.bin_info[inf_pos][3])

        # Send Firmware
        self.send_binary(self.bin_info[inf_pos][2], self.mem_det[inf_pos][2])

        # Warn use if required
        if warn:
            self.warn_user()

        # Update Boot-loader
        print("\nUpdating Boot-loader....... ")
        self.send_cmd(self.FW_UP_MODULE_NAME + " " + self.CMD_UPDATE_BTL)

        # Read and Parse the Response
        resp = self.read_response(self.BTL_UPDATE_TIMEOUT)
        self.parse_response(resp, self.FW_UP_MODULE_NAME, True, True)

        print("Done")

        # Re-Boot EVE if required
        if reboot:
            self.reboot_eve()

    def warn_user(self):
        """ Function to warn user in critical cases and get user confirmation """
        # Print warning message
        print(
            "\nWarning: EVE may not boot or won't be able to support further updates "
            "if this operation becomes incomplete\n"
        )
        print("\t1.Ensure that power source to EVE is reliable")
        print("\t2.Do not power off EVE manually")
        print("\t2.Do not terminate the script execution")
        print("\t3.Wait until the update is complete")

        # Read user choice
        try:
            choice = raw_input("\nContinue... ? [y/n]: ")
        except NameError:
            choice = input("\nContinue... ? [y/n]: ")

        # Terminate if opted
        if choice != "y":
            self.disconnect()
            sys.exit()

    def tg_app_handshake(self):
        """ Handshake with TG Application """
        print("Waiting for handshake........")
        left_time = self.TG_APP_HANDSHAKE_TIMEOUT
        while left_time > 0:
            self.com.timeout = left_time  # Configure Serial timeout
            start_time = time.time()  # To check for timeout
            line = self.com.readline().decode(
                "utf-8"
            )  # Try to read expected handshake string
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

    def is_eve_ready(self, look_for, timeout):
        """ Function to check whether application is in position to communicate or not"""
        left_time = timeout
        while left_time > 0:
            self.com.timeout = left_time  # Configure Serial timeout
            start_time = time.time()  # To check for timeout
            line = self.com.readline()
            line.decode("charmap")
            if look_for in line:
                return self.RESP_VALUES[0]

            # Calculate Time left to establish handshake
            left_time = left_time - (time.time() - start_time)
        return self.RESP_VALUES[1]

    def process_request(self):
        """ Process operation requested from user """
        if self.operation == self.OP_FW_UPDATE:
            # Verify all dependencies are met or not
            if update.check_dependencies():
                # Update firmware/s as requested
                update.update_fw()
            return

        # Read current firmware version
        if self.get_cur_fw_ver():
            self.eve_smt_simulate()

    def eve_smt_simulate(self):
        """ EVE SMT SIMULATION """

        fac_dep_det = self.get_dependency_det(self.bin_info[0][1])
        tgapp_dep_det = self.get_dependency_det(self.bin_info[1][1])
        cur_dep_det = self.get_dependency_det(self.cur_ver[1])

        if fac_dep_det[0] != tgapp_dep_det[0]:
            print(
                "\nError: TG application firmware V{} and Factory firmware V{} are"
                " not compatible".format(self.bin_info[1][1], self.bin_info[0][1])
            )

        elif fac_dep_det[0] != cur_dep_det[0]:
            print(
                "\nError: Required minimum factory firmware V{} to perform SMT simulate"
                " operation for TG application firmware V{} and Factory firmware V{}".format(
                    cur_dep_det[0], self.bin_info[1][1], self.bin_info[0][1]
                )
            )

        elif self.bin_info[0][4] != self.calculate_checksum(
            self.bin_info[0][2]
        ) or self.bin_info[1][4] != self.calculate_checksum(self.bin_info[1][2]):
            print("\nError: Checksum mismatch")

        else:
            # Prepare Memory for SMT simulation
            print("\nPreparing external memory for SMT.......")
            self.send_cmd(self.EXMEM_MODULE_NAME + " " + self.CMD_EXMEM_FORMAT)
            resp = self.read_response(self.EXMEM_FORMAT_TIMEOUT)
            self.parse_response(resp, self.EXMEM_MODULE_NAME, True, True)
            print("Done")

            # Send Firmware Information
            self.send_fw_info(
                self.bin_info[0],
                self.CMD_WR_MCU_FW_INFO,
                cur_dep_det[1],
                cur_dep_det[2] + self.MAX_BTL_FW_SIZE,
                self.APP_FW_INT_FLASH_REGION,
            )

            # Send Firmware
            self.send_binary(self.bin_info[0][2], cur_dep_det[2] + self.MAX_BTL_FW_SIZE)

            # Verify checksum
            print("\nVerifying checksum")
            self.send_cmd(self.FW_UP_MODULE_NAME + " " + self.CMD_VER_MCU_CHKSM)
            resp = self.read_response(self.VER_FW_CHECKSUM_TIMEOUT)
            self.parse_response(resp, self.FW_UP_MODULE_NAME, True, True)
            print("Done")

            # Send Firmware Information
            self.send_fw_info(
                self.bin_info[1],
                self.CMD_WR_MCU_FW_INFO,
                cur_dep_det[1],
                cur_dep_det[2] + self.MAX_BTL_FW_SIZE + self.MAX_APP_FW_SIZE,
                self.APP_FW_INT_FLASH_REGION,
            )

            # Send Firmware
            self.send_binary(
                self.bin_info[1][2],
                cur_dep_det[2] + self.MAX_BTL_FW_SIZE + self.MAX_APP_FW_SIZE,
            )

            # Verify checksum
            print("\nVerifying checksum")
            self.send_cmd(self.FW_UP_MODULE_NAME + " " + self.CMD_VER_MCU_CHKSM)
            resp = self.read_response(self.VER_FW_CHECKSUM_TIMEOUT)
            self.parse_response(resp, self.FW_UP_MODULE_NAME, True, True)
            print("Done")

            print("\nTransfer complete")
            print("\nNow, QSPI FLASH has the specified Images")

    def calculate_checksum(self, bin_file):
        """ Function to calculate checksum of given binary file """
        # Open Binary file
        binary = open(bin_file, "rb")
        checksum = 0
        while True:  # Calculate CheckSum
            binary_data = binary.read(self.CHUNK_SIZE)  # Try reading 'CHUNK_SIZE' bytes
            if not binary_data:  # Break if nothing is read
                break
            binary_data = binary_data.decode("charmap")

            checksum += sum(map(ord, binary_data))  # Update CheckSum

        # Close bin file
        binary.close()

        return checksum

    def send_fw_info(
        self, bin_info, info_cmd, exmem_region, exmem_offset, intflash_region
    ):
        """ Send firmware Information to EVE's EEPROM """
        self.send_cmd("EEPROM WRITE 0 2234")
        resp = self.read_response(2)
        self.parse_response(resp, "EEPROM", False, True)

        self.send_cmd("EEPROM WRITE 2000 1234")
        resp = self.read_response(2)
        self.parse_response(resp, "EEPROM", False, True)

        # Get checksum of binary file
        if self.operation == self.OP_FW_UPDATE:
            checksum = self.calculate_checksum(bin_info[2])
        else:
            checksum = bin_info[4]

        # Get size of binary file
        size = bin_info[3]

        # Print Firmware Information
        print("\nFirmware Information")
        print("\tSize               : " + hex(size))
        print("\tChecksum           : " + hex(checksum))
        print("\tExMem Region       : " + hex(exmem_region))
        print("\tExMem StartOffset  : " + hex(exmem_offset))
        print("\tIntFlash Region    : " + hex(intflash_region))

        # Form CMD string
        cmd = (
            self.FW_UP_MODULE_NAME
            + " "
            + info_cmd
            + " "
            + str(size)
            + " "
            + ("%x" % checksum)
            + " "
            + ("%x" % exmem_region)
            + " "
            + ("%x" % exmem_offset)
            + " "
            + str(intflash_region)
        )

        # Send Firmware Info
        print("\nSending Firmware Information..........")
        self.send_cmd(cmd)

        # Read and Parse the Response
        resp = self.read_response(self.DEFAULT_RD_TIMEOUT)
        self.parse_response(resp, self.FW_UP_MODULE_NAME, True, True)

        print("Done")

    def erase_exmemory(self, start_address, size):
        """ Erase the memory required to store firmware """
        print("\nErasing Memory.................")

        for sector in range(start_address, start_address + size, self.QSPI_SEC_SIZE):
            # Erase Sector
            self.send_cmd(
                self.QSPI_MODULE_NAME
                + " "
                + self.CMD_QSPI_SEC_ERASE
                + " "
                + str(self.QSPI_SEC_ARG)
                + " "
                + ("%x" % sector)
            )

            # Read and Parse the Response
            resp = self.read_response(self.SEC_ERASE_TIMEOUT)
            self.parse_response(resp, self.QSPI_MODULE_NAME, True, True)

        print("Done")

    def send_binary(self, bin_file, offset):
        """ Send firmware to EVE's External Memory """

        # Open Binary file
        binary = open(bin_file, "rb")

        print("\nSending Firmware.............")
        # Send Binary to EVE in chunks of 'CHUNK_SIZE' bytes
        while True:
            binary_data = binary.read(self.CHUNK_SIZE)  # Try reading 'CHUNK_SIZE' bytes
            if not binary_data:  # Break if nothing is read
                break

            # Calculate checksum of the chunk
            binary_data = binary_data.decode("charmap")
            checksum = sum(map(ord, binary_data))

            # Form command to be sent
            cmd = (
                self.FW_UP_MODULE_NAME
                + " "
                + self.CMD_WR_FW
                + " "
                + ("%x" % checksum)
                + " "
                + ("%x" % offset)
                + " "
                + str(len(binary_data))
            )

            # Update Offset Value
            offset += len(binary_data)

            for retry in range(1, self.RE_TRY_COUNT + 1, 1):
                # Send CMD
                self.send_cmd(cmd)

                # Send Binary read
                self.send_data(binary_data)

                # Read and Parse the Response
                resp = self.read_response(self.WR_FW_TIMEOUT)

                if retry == self.RE_TRY_COUNT:  # Is this last try
                    resp_value = self.parse_response(
                        resp, self.FW_UP_MODULE_NAME, True, True
                    )  # Terminate on failure
                else:
                    resp_value = self.parse_response(
                        resp, self.FW_UP_MODULE_NAME, True, False
                    )  # Do not terminate here on failure

                # Break on success
                if resp_value == self.RESP_VALUES[0]:
                    break

        # Close bin file
        binary.close()

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
        self.com.readline()  # Read new line printed on ending the cmd

    def send_data(self, string):
        """ Send raw data """
        time.sleep(self.WR_FW_INITIAL_DELAY)  # Initial Delay
        for data in string:  # Read Byte from String
            data = data.encode("charmap")  # Encode Byte
            self.com.write(data)  # Send Data Byte
            self.com.flushOutput()  # Flush Data

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


def valid_file(file_path):
    """ Function to validate input files """
    file_name = os.path.basename(file_path)

    base, ext = os.path.splitext(file_path)
    if ext.lower() not in (".bin",):
        raise argparse.ArgumentTypeError(
            "Invalid file extension. Only files with .bin extension are supported"
        )
    if not os.path.isfile(file_path):
        raise argparse.ArgumentTypeError("File {} does not exist".format(file_path))
    if re.match(
        r"^((lbb_mcu)(_bootloader|_factory)?)(_[0-9]{4,6})?(\.bin)$", file_name
    ):
        ver = re.search(r"\d+", file_name)
        if ver and int(ver.group()) < int("4005"):
            raise argparse.ArgumentTypeError("File {} not recognized".format(file_path))
    else:
        raise argparse.ArgumentTypeError("File {} not recognized".format(file_path))

    return file_path


if __name__ == "__main__":

    # Argument parser
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "OP",
        default=EveFwUpdate.OP_FW_UPDATE,
        nargs="?",
        metavar="OP",
        choices=[EveFwUpdate.OP_FW_UPDATE, EveFwUpdate.OP_SMT_SIMULATE],
        help="Operation to be performed. {} - For SMT simulate."
        " {} - For firmware update(default)".format(
            EveFwUpdate.OP_SMT_SIMULATE, EveFwUpdate.OP_FW_UPDATE
        ),
    )

    reqArgs = ap.add_argument_group("required arguments")
    reqArgs.add_argument(
        "-p", "--port", required=True, metavar="", help="COM port (Ex: COM10)"
    )

    fwUpArgs = ap.add_argument_group("firmware update arguments")
    fwUpArgs.add_argument(
        "-m",
        "--mode",
        choices=EveFwUpdate.EVE_MODES,
        metavar="",
        required="SMT_SIMULATE" not in sys.argv,
        help="Current mode of EVE {}".format(EveFwUpdate.EVE_MODES),
    )
    fwUpArgs.add_argument(
        "-f",
        "--file",
        required="SMT_SIMULATE" not in sys.argv,
        metavar="",
        type=valid_file,
        nargs=argparse.ONE_OR_MORE,
        help="Firmware binary file/s. (Max 2 files application and "
        "boot-loader binary files if required to update both)",
    )

    smtSimArgs = ap.add_argument_group("smt simulate arguments")
    smtSimArgs.add_argument(
        "-b",
        "--bin",
        required="SMT_SIMULATE" in sys.argv,
        type=valid_file,
        nargs=2,
        metavar="",
        help="Factory and TG application firmware binary files",
    )
    smtSimArgs.add_argument(
        "-c",
        "--checksum",
        type=lambda x: int(x, 16),
        nargs=2,
        required="SMT_SIMULATE" in sys.argv,
        metavar="",
        help="Checksum(In hex) of factory and TG application firmware "
        "binary files in exact order of -b/--bin arguments",
    )

    args = vars(ap.parse_args())

    if args["OP"] == EveFwUpdate.OP_FW_UPDATE:
        bin_files = args["file"]
    else:
        bin_files = args["bin"]

    # If more than 2 files are found
    if len(bin_files) > 2:
        print("\nERROR: Maximum 2 files expected, found {}".format(len(bin_files)))
        sys.exit()

    update = EveFwUpdate(args["mode"], args["OP"])

    # Extract info from given bin files
    if update.extract_bin_info(bin_files, args["checksum"]):
        # Connect to EVE
        update.connect(args["port"], 115200)

        update.process_request()

    # Disconnect from EVE
    update.disconnect()

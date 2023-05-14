""" This script is a tool for uploading a DFU package to the MCU then transfering to BLE sensor devices.
    Pre-requisites:
        * Python3
        * AG-55 running factory CLI
        * AG-55 serial port connected to the computer running this script
    Command Line Syntax:
        * Run `python ZYXSensor_fw_update.py --help`
"""

import sys
import signal
import argparse
import os
from time import time, sleep

import utils
import modules

import json
import zipfile
import shutil

import binascii
import serial

MANIFEST_FILE = "manifest.json"
CHUNK_SIZE = 4 * 1024  # 4KB

APP_INIT_PKT_OFFSET = 2936832  # 0x2CD000
APP_BINARY_OFFSET = 2937856  # 0x2CD400
APP_BINARY_MAX_SIZE = 864 * 1024  # max size is 864KB

BLE_DFU_EXMEM_RAW_ID = 65281  # 0xFF01

QSPI_SEC_SIZE = 4096

QSPI_OTA_SEC_START = 2785280  # 0x2A8000, sectors [680:1032]
QSPI_OTA_SEC_COUNT = 352  # sector size is 4096B

QSPI_SENSOR_OTA_SEC_START = 2162688  # 0x210000, sectors [528:657]
QSPI_SENSOR_OTA_SEC_COUNT = 129  # info sector + binary image data

SENSOR_APP_INIT_OFFSET = 2162688  # 0x210000 initial sector is image info
SENSOR_APP_BINARY_OFFSET = 2166784  # 0x211000 app image begins at next sector
SENSOR_APP_BINARY_MAX_SIZE = 512 * 1024  # max size is 512KB

RETRY_COUNT = 10  # Retry count
com = None
qspi = None


def signal_handler(sig, frame):
    com.disconnect()
    print("Exiting Script")
    sys.exit(0)


class DfuPackage(modules.module_class):
    target_path = None
    zip_file_path = None
    zip_pkg = None
    manifest_file = None
    application_info_file = None
    application_bin_file = None

    RESP_KEY = "RESULT"
    RESP_VALUES = ["PASS", "FAIL", "TIMEOUT", "INVALID"]

    def __init__(self, arg, zip_file):
        """
        Check the zip is present and get the target path
        :param arg:
        :param zip_file:
        """
        modules.module_class.__init__(self, arg)
        if not os.path.isfile(zip_file):
            print("FILE NOT FOUND : Specified zip package does not exist")
            sys.exit(0)
        self.zip_pkg = zip_file
        self.zip_file_path = os.path.dirname(os.path.realpath(zip_file))
        self.target_path = os.path.join(self.zip_file_path, "temp")

    def dfu_exit(self):
        """
        Disconnect com and exit script
        """
        self.remove_temp()
        com.disconnect()
        sys.exit(0)

    def unpack_pkg(self):
        """
        Unpack the zip file
        """
        zfile = zipfile.ZipFile(self.zip_pkg)
        if zfile.extractall(self.target_path):
            print("Failed to Unzip file")
            sys.exit(0)
        self.manifest_file = os.path.join(self.target_path, MANIFEST_FILE)
        print(self.manifest_file)
        if not os.path.isfile(self.manifest_file):
            print("ERROR : Invalid zip package")
            self.dfu_exit()

    def prep_qspi(self):
        """
        Erase QSPI sectors to write firmware
        """
        sec_addr = QSPI_SENSOR_OTA_SEC_START
        for i in range(1, QSPI_SENSOR_OTA_SEC_COUNT + 1, 1):
            print("Erasing Sec addr " + hex(sec_addr)[2:])
            resp = self.qspiSEC_ER(1, hex(sec_addr)[2:])
            resp = self.parse_response(resp, "QSPI", True)
            # Check for failure
            if resp != self.RESP_VALUES[0]:
                self.dfu_exit()
            sec_addr = sec_addr + 4096

    def remove_temp(self):
        """
        Delete temporary folder
        """
        try:
            shutil.rmtree(self.target_path)
        except:
            return

    def cal_crc(self, file):
        """
        calculate Crc
        :return: checksum
        """
        # Open Binary file
        binary = open(file, "rb")
        checksum = 0
        while True:  # Calculate CheckSum
            binary_data = binary.read(CHUNK_SIZE)  # Try reading 'CHUNK_SIZE' bytes
            if not binary_data:  # Break if nothing is read
                break
            binary_data = binary_data.decode("charmap")

            checksum += sum(map(ord, binary_data))  # Update CheckSum

        # Close bin file
        binary.close()
        return checksum

    def send_file(self, file_name, offset):
        """
        Send image to EVE
        """
        binary = open(file_name, "rb")
        print("Sending " + file_name)
        # Send chunk size of data
        while True:
            binary_data = binary.read(CHUNK_SIZE)  # Try reading 'CHUNK_SIZE' bytes
            if not binary_data:  # Break if nothing is read
                break
            # Calculate checksum of the chunk
            binary_data = binary_data.decode("charmap")
            checksum = sum(map(ord, binary_data))
            # ADAM-1662 : retry was not reaching the max value "RETRY_COUNT" in case of failure
            # Hence script kept sending next chunk of data even when last chunk failed
            # Now script will stop immediately if any data chunk fails for "RETRY_COUNT" times
            for retry in range(1, RETRY_COUNT + 1, 1):
                # send binary
                resp = self.fw_update_WR_FW(
                    hex(checksum), hex(offset), binary_data, len(binary_data)
                )

                # Parse response
                resp_value = self.parse_response(
                    resp, "FW_UPDATE", True
                )  # Terminate on failure

                # Break on success
                if resp_value == self.RESP_VALUES[0]:
                    break
                else:
                    if retry >= RETRY_COUNT:
                        print("Failed to transmit binary data")
                        binary.close()
                        self.dfu_exit()
                    else:
                        print("Retrying...")
            # increment offset
            offset += len(binary_data)
        # Close file
        binary.close()

    def parse_response(self, response, module, display):
        """ Parse the Response and on error terminates program if terminate flag is Set """
        try:
            result = json.loads(response)
            return result[module]["RESULT"]
        except:
            return "INVALID"

    def send_application(self):
        """
        Send application package
        """

        self.application_init_file = self.manifest_file
        with open(self.application_init_file, "r") as file_list:
            data_list = json.load(file_list)

        try:
            self.application_bin_file = os.path.join(
                self.target_path, data_list["files"][0]["file"]
            )
        except:
            print("No application package to send\r\n")
            return

        print("\nManifest file contents:")
        print(data_list)
        print()

        type = data_list["files"][0]["type"]
        app_bin_file_size = data_list["files"][0]["size"]

        # get file info
        app_bin_file_info = os.stat(self.application_bin_file)
        app_init_file_info = os.stat(self.application_init_file)

        if app_bin_file_size > SENSOR_APP_BINARY_MAX_SIZE:
            print("Invalid File : Application Image size too big")
            self.dfu_exit()

        if app_bin_file_info.st_size != app_bin_file_size:
            print("Invalid File : Application Image size does not match file stat size")
            self.dfu_exit()

        if type != "application":
            print("incorrect image type: " + type)
            return

        if app_bin_file_size > SENSOR_APP_BINARY_MAX_SIZE:
            print("app image is too large, must be <= " + {SENSOR_APP_BINARY_MAX_SIZE})
            return

        # Calculate CRC
        app_bin_crc = self.cal_crc(self.application_bin_file)
        app_init_crc = self.cal_crc(self.application_init_file)

        # Print Application Manifest file info
        print("\t\tApplication Manifest : " + self.application_init_file)
        print("\t\t\tSize   : " + str(app_init_file_info.st_size))
        print("\t\t\tCRC    : " + hex(app_init_crc))
        print("\t\t\tRegion : " + hex(BLE_DFU_EXMEM_RAW_ID))
        print("\t\t\tOffset : " + hex(SENSOR_APP_INIT_OFFSET))
        # Print Application FW info
        print("\t\tApplication Image : " + self.application_bin_file)
        print("\t\t\tSize   : " + str(app_bin_file_info.st_size))
        print("\t\t\tCRC    : " + hex(app_bin_crc))
        print("\t\t\tRegion : " + hex(BLE_DFU_EXMEM_RAW_ID))
        print("\t\t\tOffset : " + hex(SENSOR_APP_BINARY_OFFSET))

        # Send init info + binary info
        resp = self.fw_updateWR_BLE_DFU_INFO(
            "APP",
            app_init_file_info.st_size,
            hex(app_init_crc),
            hex(BLE_DFU_EXMEM_RAW_ID),
            hex(SENSOR_APP_INIT_OFFSET),
            app_bin_file_info.st_size,
            hex(app_bin_crc),
            hex(BLE_DFU_EXMEM_RAW_ID),
            hex(SENSOR_APP_BINARY_OFFSET),
        )

        resp_value = self.parse_response(resp, "FW_UPDATE", True)
        if resp_value != self.RESP_VALUES[0]:
            self.dfu_exit()

        # Send info File
        self.send_file(self.application_init_file, SENSOR_APP_INIT_OFFSET)

        # Send binary image
        self.send_file(self.application_bin_file, SENSOR_APP_BINARY_OFFSET)

    def send_fw_to_eve(self):
        """
        Send app package and manifest to eve
        """
        self.send_application()

    def update_sensor(self):
        resp = self.fw_updateXFER_SENSOR()
        result = self.parse_response(resp)
        print("SENSOR UPDATE : " + result)


if __name__ == "__main__":
    """
    main
    """
    # Signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Argument parser
    ap = argparse.ArgumentParser()
    ap.add_argument("-b", "--baud", required=False, metavar="", help="Baudrate")

    reqArgs = ap.add_argument_group("required arguments")
    reqArgs.add_argument(
        "-p", "--port", required=True, metavar="", help="COM port (example: COM10)"
    )

    reqArgs = ap.add_argument_group("required arguments")
    reqArgs.add_argument(
        "-pkg", "--package", required=True, metavar="", help="Zip package not Found"
    )

    args = vars(ap.parse_args())

    # Connect to EVE
    com = utils.com_class()
    # create object for dfu class
    dfu = DfuPackage(com, args["package"])
    if args["baud"]:
        com.connect(args["port"], args["baud"], 1)
    else:
        com.connect(args["port"], 115200, 1)

    # unpack the zip file
    dfu.unpack_pkg()

    # Erase qspi sectors
    dfu.prep_qspi()

    # Send update package to eve
    dfu.send_fw_to_eve()

    # Issue command to transfer image to flash on the nRF52840
    #    dfu.update_SENSOR()

    # Exit the script
    dfu.dfu_exit()


# $ python2 lbb_sdk/mcu/Scripts/test/sensor_fw_update.py -p /dev/ttyUSB0 -pkg lbb_sdk/mcu/Scripts/test/dfu_application.zip

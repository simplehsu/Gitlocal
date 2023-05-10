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

MANIFEST_FILE = "manifest.json"
CHUNK_SIZE = 4 * 1024

INIT_PKT_SIZE_MAX = 512  # init packet max size is 512

BL_INIT_PKT_OFFSET = 2752512  # bootloader init pakcet offset
BL_BINARY_OFFSET = 2753536
BL_BINARY_SIZE_MAX = 24 * 1024  # max size is 24kb as per document

SD_INIT_PKT_OFFSET = 2781184
SD_BINARY_OFFSET = 2782208
SD_BINARY_SIZE_MAX = 148 * 1024  # max size is 148KB

APP_INIT_PKT_OFFSET = 2936832
APP_BINARY_OFFSET = 2937856
APP_BINARY_MAX_SIZE = 864 * 1024  # max size is 864KB

BLE_DFU_EXMEM_RAW_ID = 65281

QSPI_BLE_SEC_START = 2785280
QSPI_BLE_SEC_COUNT = 352

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
    bootloader_init_file = None
    bootloader_bin_file = None
    softdevice_init_file = None
    softdevice_bin_file = None
    application_init_file = None
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

    def set_pkg(self, zip_file):
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
        if not os.path.isfile(self.manifest_file):
            print("ERROR : Invalid zip package")
            self.dfu_exit()

    def prep_qspi(self):
        """
        Erase QSPI sectors to write firmware
        """
        sec_addr = QSPI_BLE_SEC_START
        for i in range(1, QSPI_BLE_SEC_COUNT + 1, 1):
            resp = self.qspiSEC_ER(1, hex(sec_addr)[2:])
            resp = self.parse_response(resp, "QSPI", True)
            if resp != self.RESP_VALUES[0]:
                self.dfu_exit()
            # Check for failure
            sec_addr = sec_addr + 4096
            print("Erasing Sec addr " + hex(sec_addr)[2:])

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

    def send_bootloader(self, data_list):
        """
        Send bootloader package if present
        """
        try:
            self.bootloader_init_file = os.path.join(
                self.target_path, data_list["manifest"]["bootloader"]["dat_file"]
            )
            self.bootloader_bin_file = os.path.join(
                self.target_path, data_list["manifest"]["bootloader"]["bin_file"]
            )
        except:
            print("No Bootloader package to send\r\n")
            return
        # get file info
        bl_init_file_info = os.stat(self.bootloader_init_file)
        bl_bin_file_info = os.stat(self.bootloader_bin_file)

        if bl_init_file_info.st_size > INIT_PKT_SIZE_MAX:
            print("Invalid File : Bootloader Init packet size too big\t\n")
            self.dfu_exit()
        if bl_bin_file_info.st_size > SD_BINARY_SIZE_MAX:
            print("Invalid File : Bootloader Image size too big\r\n")
            self.dfu_exit()

        # Calculate CRC
        bl_init_crc = self.cal_crc(self.bootloader_init_file)
        bl_bin_crc = self.cal_crc(self.bootloader_bin_file)

        # Print Bootloader init packet info
        print("\t\tBootloader Init Packet : " + self.bootloader_init_file)
        print("\t\t\tSize   : " + str(bl_init_file_info.st_size))
        print("\t\t\tCRC    : " + hex(bl_init_crc))
        print("\t\t\tRegion : " + hex(BLE_DFU_EXMEM_RAW_ID))
        print("\t\t\tOffset : " + hex(BL_INIT_PKT_OFFSET))
        # Print Bootlaoder FW info
        print("\t\tBootloader Image : " + self.bootloader_bin_file)
        print("\t\t\tSize   : " + str(bl_bin_file_info.st_size))
        print("\t\t\tCRC    : " + hex(bl_bin_crc))
        print("\t\t\tRegion : " + hex(BLE_DFU_EXMEM_RAW_ID))
        print("\t\t\tOffset : " + hex(BL_BINARY_OFFSET))
        # Send FW_info init_packet + binary  info
        resp = self.fw_updateWR_BLE_DFU_INFO(
            "BL",
            bl_init_file_info.st_size,
            hex(bl_init_crc),
            hex(BLE_DFU_EXMEM_RAW_ID),
            hex(BL_INIT_PKT_OFFSET),
            bl_bin_file_info.st_size,
            hex(bl_bin_crc),
            hex(BLE_DFU_EXMEM_RAW_ID),
            hex(BL_BINARY_OFFSET),
        )

        resp_value = self.parse_response(resp, "FW_UPDATE", True)
        if resp_value != self.RESP_VALUES[0]:
            self.dfu_exit()

        # Send Init packet
        self.send_file(self.bootloader_init_file, BL_INIT_PKT_OFFSET)
        # Send binary image
        self.send_file(self.bootloader_bin_file, BL_BINARY_OFFSET)

    def send_softdevice(self, data_list):
        """
        Send softdevice package if present
        """
        try:
            self.softdevice_init_file = os.path.join(
                self.target_path, data_list["manifest"]["softdevice"]["dat_file"]
            )
            self.softdevice_bin_file = os.path.join(
                self.target_path, data_list["manifest"]["softdevice"]["bin_file"]
            )
        except:
            print("No Softdevice package to send\r\n")
            return
        # get file info
        sd_init_file_info = os.stat(self.softdevice_init_file)
        sd_bin_file_info = os.stat(self.softdevice_bin_file)

        if sd_init_file_info.st_size > INIT_PKT_SIZE_MAX:
            print("Invalid File : Softdevice Init packet size too big")
            self.dfu_exit()
        if sd_bin_file_info.st_size > APP_BINARY_MAX_SIZE:
            print("Invalid File : Softdevice Image size too big")
            self.dfu_exit()

        # Calculate CRC
        sd_init_crc = self.cal_crc(self.softdevice_init_file)
        sd_bin_crc = self.cal_crc(self.softdevice_bin_file)

        # Print Softdevice init packet info
        print("\t\tSoftdevice Init Packet : " + self.softdevice_init_file)
        print("\t\t\tSize   : " + str(sd_init_file_info.st_size))
        print("\t\t\tCRC    : " + hex(sd_init_crc))
        print("\t\t\tRegion : " + hex(BLE_DFU_EXMEM_RAW_ID))
        print("\t\t\tOffset : " + hex(SD_INIT_PKT_OFFSET))
        # Print Softdevice FW info
        print("\t\tSoftdevice Image : " + self.softdevice_bin_file)
        print("\t\t\tSize   : " + str(sd_bin_file_info.st_size))
        print("\t\t\tCRC    : " + hex(sd_bin_crc))
        print("\t\t\tRegion : " + hex(BLE_DFU_EXMEM_RAW_ID))
        print("\t\t\tOffset : " + hex(SD_BINARY_OFFSET))
        # Send FW_info init_packet + binary  info
        resp = self.fw_updateWR_BLE_DFU_INFO(
            "SD",
            sd_init_file_info.st_size,
            hex(sd_init_crc),
            hex(BLE_DFU_EXMEM_RAW_ID),
            hex(SD_INIT_PKT_OFFSET),
            sd_bin_file_info.st_size,
            hex(sd_bin_crc),
            hex(BLE_DFU_EXMEM_RAW_ID),
            hex(SD_BINARY_OFFSET),
        )

        resp_value = self.parse_response(resp, "FW_UPDATE", True)
        if resp_value != self.RESP_VALUES[0]:
            self.dfu_exit()

        # Send Init packet
        self.send_file(self.softdevice_init_file, SD_INIT_PKT_OFFSET)
        # Send binary image
        self.send_file(self.softdevice_bin_file, SD_BINARY_OFFSET)

    def send_application(self, data_list):
        """
        Send application package
        """
        try:
            self.application_init_file = os.path.join(
                self.target_path, data_list["manifest"]["application"]["dat_file"]
            )
            self.application_bin_file = os.path.join(
                self.target_path, data_list["manifest"]["application"]["bin_file"]
            )
        except:
            print("No application package to send\r\n")
            return

        # get file info
        app_init_file_info = os.stat(self.application_init_file)
        app_bin_file_info = os.stat(self.application_bin_file)

        if app_init_file_info.st_size > INIT_PKT_SIZE_MAX:
            print("Invalid File : Application Init packet size too big")
            self.dfu_exit()
        if app_bin_file_info.st_size > APP_BINARY_MAX_SIZE:
            print("Invalid File : Application Image size too big")
            self.dfu_exit()

        # Calculate CRC
        app_init_crc = self.cal_crc(self.application_init_file)
        app_bin_crc = self.cal_crc(self.application_bin_file)
        # Print Application init packet info
        print("\t\tApplication Init Packet : " + self.application_init_file)
        print("\t\t\tSize   : " + str(app_init_file_info.st_size))
        print("\t\t\tCRC    : " + hex(app_init_crc))
        print("\t\t\tRegion : " + hex(BLE_DFU_EXMEM_RAW_ID))
        print("\t\t\tOffset : " + hex(SD_INIT_PKT_OFFSET))
        # Print Application FW info
        print("\t\tApplication Image : " + self.application_bin_file)
        print("\t\t\tSize   : " + str(app_bin_file_info.st_size))
        print("\t\t\tCRC    : " + hex(app_bin_crc))
        print("\t\t\tRegion : " + hex(BLE_DFU_EXMEM_RAW_ID))
        print("\t\t\tOffset : " + hex(APP_INIT_PKT_OFFSET))
        # Send FW_info init_packet + binary  info
        resp = self.fw_updateWR_BLE_DFU_INFO(
            "APP",
            app_init_file_info.st_size,
            hex(app_init_crc),
            hex(BLE_DFU_EXMEM_RAW_ID),
            hex(APP_INIT_PKT_OFFSET),
            app_bin_file_info.st_size,
            hex(app_bin_crc),
            hex(BLE_DFU_EXMEM_RAW_ID),
            hex(APP_BINARY_OFFSET),
        )

        resp_value = self.parse_response(resp, "FW_UPDATE", True)
        if resp_value != self.RESP_VALUES[0]:
            self.dfu_exit()

        # Send Init packet
        self.send_file(self.application_init_file, APP_INIT_PKT_OFFSET)

        # Send binary image
        self.send_file(self.application_bin_file, APP_BINARY_OFFSET)

    def send_fw_to_eve(self):
        """
        Send all packages to eve
        parse manifest file and decide what package to send
        :return:
        """
        with open(self.manifest_file, "r") as file_list:
            datastore = json.load(file_list)
        self.send_bootloader(datastore)
        self.send_softdevice(datastore)
        self.send_application(datastore)

    def update_ble(self):
        """

        :return:
        """
        resp = self.fw_updateBLE_DFU()
        result = self.parse_response(resp)
        print("BLE UPDATE : " + result)


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

    ap.add_argument(
        "-r",
        "--repeat",
        required=False,
        metavar="",
        type=int,
        default=0,
        help="Repeat count (must specify -pkg2 if -r > 0",
    )

    ap.add_argument(
        "-pkg2",
        "--package2",
        required=False,
        metavar="",
        help="Second package for alternating repetition",
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

    reps = args["repeat"]

    if reps > 0:
        if not args["package2"]:
            print("\nERROR: if -r is > 0, you must specify -pkg2")
            sys.exit(1)

    print("reps = %s" % reps)

    # Get the sw version
    dfu.bleGetSwVer()

    for i in range(reps + 1):

        start_time = time()

        # reset the package
        if i % 2 == 0:
            dfu.set_pkg(args["package"])
        else:
            dfu.set_pkg(args["package2"])

        # unpack the zip file
        dfu.unpack_pkg()

        # Erase qspi sectors
        dfu.prep_qspi()

        # Send update package to eve
        dfu.send_fw_to_eve()

        # Issue update command
        dfu.fw_updateBLE_DFU()

        # Get the new sw version
        sleep(15)
        dfu.bleGetSwVer()

        print("iter %d took %.0f seconds" % (i, time() - start_time))

    # Exit the script
    dfu.dfu_exit()

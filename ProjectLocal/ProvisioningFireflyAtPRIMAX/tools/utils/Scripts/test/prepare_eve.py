# System imports

import sys
import signal
import argparse
from colorama import init, Style

# Local imports
import utils
import modules

com = None


def signal_handler(sig, frame):
    com.disconnect()
    print("Exiting Script")
    sys.exit(0)


class eepromPrepare(modules.module_class):
    """ Eerpom class """

    # Eeprom specific parameters
    EEPROM_SIZE = 16384  # size of EEPROM 16kB
    EEPROM_WRITE_SIZE = 512  # write size is restricted to 512B
    ERASE_LOOP_COUNT = EEPROM_SIZE / EEPROM_WRITE_SIZE
    EEPROM_DATA = "\xff" * EEPROM_WRITE_SIZE
    # EEPROM_DATA = EEPROM_DATA.decode('charmap')

    def __init__(self, arg):
        self.__com = arg
        modules.module_class.__init__(self, arg)

    def eepromWr(self):
        """Write data to eeprom"""
        LOOP_COUNT = 0
        ADDRESS = 0x00
        while LOOP_COUNT < self.ERASE_LOOP_COUNT:
            MEMORY_ADDRESS = format(ADDRESS, "02X")
            self.eepromWrite(MEMORY_ADDRESS, self.EEPROM_DATA)
            LOOP_COUNT = LOOP_COUNT + 1
            ADDRESS = ADDRESS + self.EEPROM_WRITE_SIZE

    def reboot(self):
        """reboot Device"""
        self.sysReboot(True)


if __name__ == "__main__":

    # Register Signal handler for graceful exit
    signal.signal(signal.SIGINT, signal_handler)

    # Init Colorama
    init()

    # Argument parser
    ap = argparse.ArgumentParser()
    ap.add_argument("-b", "--baud", required=False, metavar="", help="Baudrate")

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

    # Eeprom operation
    eepObj = eepromPrepare(com)
    eepObj.eepromWr()

    eepObj.reboot()

    com.disconnect()
    print("Script completed Successfully\r\n")

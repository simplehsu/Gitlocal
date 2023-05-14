import time
import argparse
import datetime
from colorama import init

import utils
import modules


class TestClass(modules.module_class):
    def __init__(self, arg):
        modules.module_class.__init__(self, arg)

    def config(self):
        utils.formatPrint.bright(" Configuring I2C module(s)")

        # Init all the I2C peripherals

        self.tempEn()
        self.tempLP_Exit()

    def exec_test(self, loop_n):
        loop_count = 0
        while loop_count != loop_n:
            loop_count += 1
            utils.formatPrint.cyan("\r\n\r\nIteration: %d" % loop_count)
            self.tempGetVal()
            self.eepromRead(0, 5)
            self.battGetID()
            self.atcaGetSerial()
            time.sleep(2)


if __name__ == "__main__":

    # use Colorama to make Termcolor work on Windows too
    init()

    # Argument parser
    ap = argparse.ArgumentParser()
    ap.add_argument("-b", "--baud", required=False, metavar="", help="Baudrate")
    ap.add_argument("-i", "--itr", required=False, help="Iteration count")

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

    # Capture iteration count
    if args["itr"] is None:
        itrCnt = -1
    else:
        itrCnt = int(args["itr"])

    # Create an instance and start execution
    sTest = TestClass(com)
    sTest.config()

    # Run tests
    sTest.exec_test(itrCnt)

    # Done testing, Disconnect and exit
    time.sleep(3)
    com.disconnect()

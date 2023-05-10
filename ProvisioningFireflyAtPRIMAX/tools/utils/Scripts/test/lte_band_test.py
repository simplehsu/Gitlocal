# System imports
import json
import time
import sys
import signal
import argparse
from colorama import init

# Local imports
import utils
import modules


class lte_band_test_class(modules.module_class):

    # Private variables
    __com = None

    def __init__(self, arg):
        self.__com = arg
        modules.module_class.__init__(self, arg)


if __name__ == "__main__":

    # for below constants please refer
    # u-blox.com/sites/default/files/SARA-R4-SARA-N4_ATCommands_%28UBX-17003787%29.pdf

    BAND_2_CH_START = 118600  # in MHz
    BAND_2_CH_END = 119199  # in MHz

    BAND_4_CH_START = 119950  # in MHz
    BAND_4_CH_END = 120399  # in MHz

    BAND_5_CH_START = 120400  # in MHz
    BAND_5_CH_END = 120649  # in MHz

    BAND_12_CH_START = 123010  # in MHz
    BAND_12_CH_END = 123179  # in MHz

    CHANNEL_BANDWIDTH = 5  # 5MHZ bandwidth for FDD

    BURST_DURATION_MS = 1000  # 1 seconds

    TX_POWER = 24  # dBm

    TX_TEST_MODE = "+UTEST=3,"  # Tx Test Mode.

    # Init Colorama
    init()

    # Argument parser
    ap = argparse.ArgumentParser()
    ap.add_argument("-b", "--baud", required=False, metavar="", help="Baudrate")

    reqArgs = ap.add_argument_group("required arguments")
    reqArgs.add_argument(
        "-p", "--port", required=True, metavar="", help="COM port (example: COM10)"
    )
    reqArgs.add_argument(
        "-i",
        "--iteration",
        required=True,
        metavar="",
        help="iteration count: 0 sets to infinite loops",
    )

    args = vars(ap.parse_args())

    f = open("lte_band_test_logs.txt", "w+")

    # Connect to EVE
    com = utils.com_class()
    if args["baud"]:
        com.connect(args["port"], args["baud"], 1)
    else:
        com.connect(args["port"], 115200, 1)

    # Run tests
    lteTest = lte_band_test_class(com)

    # check lte init
    Info = lteTest.lteAt("")
    if Info.find("OK") != -1:
        print("LTE module is up")
    else:
        utils.formatPrint.red("Please turn ON LTE before starting the test")
        com.disconnect()
        exit(1)

    LoopCount = int(args["iteration"])

    # No continous mode for now
    if LoopCount > 0:
        utils.formatPrint.cyan("Starting the LTE band test")
    else:
        utils.formatPrint.red("Err: Inval args")
        com.disconnect()
        exit(1)

    while LoopCount > 0:
        Iteration = 1
        print("LTE Band test: Iteration Count: ", Iteration)

        # start the test
        lteInfo = lteTest.lteAt("+UTEST=1")

        ############### Test band 2 - All channels ###############
        # construct the command
        utils.formatPrint.green("LTE Band 2 test in progress. Please wait ...")
        TestChannel = BAND_2_CH_START
        while TestChannel < BAND_2_CH_END:
            Command = (
                TX_TEST_MODE
                + str(TestChannel)
                + ","
                + str(TX_POWER)
                + ","
                + ","
                + ","
                + str(BURST_DURATION_MS)
            )
            # print ("Command ",Command)
            lteInfo = lteTest.lteAt(Command)
            f.write(lteInfo)
            if lteInfo.find("OK") == -1:
                print("Tested failed with command:", Command)
                break
            TestChannel = TestChannel + CHANNEL_BANDWIDTH  # next test channel
        utils.formatPrint.green("LTE Band 2 test Complete !!")

        ############### Test band 4 - All channels ###############
        utils.formatPrint.green("LTE Band 4 test in progress. Please wait ...")
        TestChannel = BAND_4_CH_START
        while TestChannel < BAND_4_CH_END:
            Command = (
                TX_TEST_MODE
                + str(TestChannel)
                + ","
                + str(TX_POWER)
                + ","
                + ","
                + ","
                + str(BURST_DURATION_MS)
            )
            # print ("Command ",Command)
            lteInfo = lteTest.lteAt(Command)
            f.write(lteInfo)
            if lteInfo.find("OK") == -1:
                print("Tested failed with command:", Command)
                break
            TestChannel = TestChannel + CHANNEL_BANDWIDTH  # next test channel
        utils.formatPrint.green("LTE Band 4 test Complete !!")

        ############### Test band 5 - All channels ###############
        utils.formatPrint.green("LTE Band 5 test in progress. Please wait ...")
        TestChannel = BAND_5_CH_START
        while TestChannel < BAND_5_CH_END:
            Command = (
                TX_TEST_MODE
                + str(TestChannel)
                + ","
                + str(TX_POWER)
                + ","
                + ","
                + ","
                + str(BURST_DURATION_MS)
            )
            # print ("Command ",Command)
            lteInfo = lteTest.lteAt(Command)
            f.write(lteInfo)
            if lteInfo.find("OK") == -1:
                print("Tested failed with command:", Command)
                break
            TestChannel = TestChannel + CHANNEL_BANDWIDTH  # next test channel
        utils.formatPrint.green("LTE Band 5 test Complete !!")

        ############### Test band 12 - All channels ###############
        utils.formatPrint.green("LTE Band 12 test in progress. Please wait ...")
        TestChannel = BAND_12_CH_START
        while TestChannel < BAND_12_CH_END:
            Command = (
                TX_TEST_MODE
                + str(TestChannel)
                + ","
                + str(TX_POWER)
                + ","
                + ","
                + ","
                + str(BURST_DURATION_MS)
            )
            # print ("Command ",Command)
            lteInfo = lteTest.lteAt(Command)
            f.write(lteInfo)
            if lteInfo.find("OK") == -1:
                print("Tested failed with command:", Command)
                break
            TestChannel = TestChannel + CHANNEL_BANDWIDTH  # next test channel
        utils.formatPrint.green("LTE Band 12 test Complete !!")

        # Note: All bands spectrum are not really multiple of BANDWIDTH(5MHZ), we may run this test on border of the allocated band
        # that may partially use other channel bands. To be fixed soon

        LoopCount = LoopCount - 1
        Iteration = Iteration + 1

        # Stop the Test
        lteInfo = lteTest.lteAt("+UTEST=0")

    # Clean-up and exit
    f.close()
    com.disconnect()

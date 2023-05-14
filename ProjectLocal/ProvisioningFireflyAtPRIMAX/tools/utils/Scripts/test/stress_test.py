import time
import argparse
import datetime
from colorama import init

import utils
import modules


class test_class(modules.module_class):
    def __init__(self, arg):
        modules.module_class.__init__(self, arg)

    def config(self):
        """ Configures all modules to max performance state """
        utils.formatPrint.bright("Configuring modules to their best performance..")
        # Configuring temperature
        self.tempEn()
        self.tempLP_Exit()

        # Configuring AGM
        self.agmEn()
        self.agmLP_Exit()
        self.agmODR_CONFIG(10)

        # Configuring GPS
        self.gpsEn()

        # Configuring BLE
        self.bleEn()

        # Configuring CAN
        self.canWakeUp()
        self.canStart()

        # Configuring LTE
        """ LTE will be turned on during board boot up, toggling the pin
            again, would disable it (although it says enable). Due to this
            we would not re-enable the module and it is assumed that LTE is
            enabled before the execution of this script """
        # self.lteEn()

        # Configuring RTC
        self.rtcEn()
        self.rtcSetCalendar(datetime.datetime.now().replace(microsecond=0).isoformat())

        # Configuring LED
        self.ledRed("ON")
        time.sleep(2)
        self.ledGreen("ON")
        time.sleep(2)
        self.ledBlue("ON")

    def execReadData(self):
        """ Sequential read all the modules """
        utils.formatPrint.bright("Reading peripheral data...")
        # Read Temperature
        self.tempGetVal()

        # Read Accelerometer and Gyroscope data
        self.agmRD_ACC()
        self.agmRD_GY()

        # Read GPS data
        self.gpsGetSat()

        # Read Navigation data
        self.gpsGetNav()

        # Read BLE data
        self.bleGetMac()  # TODO Scan for BLE devices might be a better call here

        # Read CAN data
        self.canGetFrame()

        # Read LTE data
        self.lteInfo()

        # Read RTC data
        self.rtcGetCalendar()

        # Read Battery Voltage
        self.battGetVolt()

        # Read Capacity Voltage
        self.battGetCapacity()

        # Read Status Voltage
        self.battGetStatus()

    def execTest(self, loop_n):
        loop_count = 0
        while loop_count != loop_n:
            loop_count += 1
            utils.formatPrint.cyan("\r\nIteration: %d" % loop_count)
            self.sysHogStart(10)  # Perform memcpy 10 times every cycle
            if (loop_count % 10) == 0:
                self.execReadData()


if __name__ == "__main__":

    # use Colorama to make Termcolor work on Windows too
    init()

    # Argument parser
    ap = argparse.ArgumentParser()
    ap.add_argument("-b", "--baud", required=False, metavar="", help="Baudrate")
    ap.add_argument(
        "-i", "--itr", required=False, help="Iteration count. -1 for infinite"
    )

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

    # Execute the test case
    if args["itr"] is None:
        itrCnt = -1
    else:
        itrCnt = int(args["itr"])

    # Create an instance and start execution
    sTest = test_class(com)
    sTest.config()

    # Run tests
    sTest.execTest(itrCnt)

    # Done testing, Disconnect and exit
    time.sleep(3)
    com.disconnect()

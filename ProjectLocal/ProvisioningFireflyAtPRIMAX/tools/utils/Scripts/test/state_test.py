# System imports
import datetime
import random
import string
import sys
import signal
import argparse
from colorama import init, Style
import time

# Local imports
import modules
import utils

modes = ["Parked", "Parked_Tx", "Moving", "Moving_Tx", "Shipment", "OTA"]

rtcWakeTimeout = 18 * 60 * 60

# Wake up source values
VIN = 1
VSOLAR = 2
BLE_AGM_INT = 4


class mode_class(modules.module_class):
    def __init__(self, arg):
        modules.module_class.__init__(self, arg)
        self.socket = -1

    def execParked(self):
        print(Style.BRIGHT + "Test began at {}".format(str(time.ctime())))
        # self.bleDis() #TODO
        # self.flashDis() #TODO
        self.lteDis()
        self.agmLP_Enter()
        # self.solarEn() #TODO
        self.tempDis()
        self.rs485Shutdown()
        self.canStop()
        self.gpsDis()
        self.rtcWakeEn(rtcWakeTimeout, 0)
        # self.eepromDis()   #TODO
        self.ledRed("OFF")
        self.ledGreen("OFF")
        self.ledBlue("OFF")
        self.battChargeEn()
        self.j1708Shutdown()
        self.tpmsDis()
        self.pmStopHighZ(str(BLE_AGM_INT))  # Vehicle motion based wakeup

        while True:
            sta = input(
                Style.BRIGHT
                + "\r\nIs DBG_LED (Debug LED) turned OFF? [Y/N]: "
                + Style.RESET_ALL
            )
            if sta == "Y":
                utils.formatPrint.green("Successfully entered {} mode".format(modes[0]))
                break
            elif sta == "N":
                utils.formatPrint.red("Failed to enter {} mode".format(modes[0]))
                break
            else:
                utils.formatPrint.cyan("Invalid input. Please provide [Y/N]")

    def execParked_Tx(self):
        start_time = time.time()
        print(Style.BRIGHT + "Test began at {}".format(str(time.ctime())))
        # self.gpsEn()   #Should be 'Enter LP'
        # self.lteEn()
        self.lteAt("")
        self.lteAt("E0")
        self.lte_signal_info()
        if not self.lte_network_reg():
            utils.formatPrint.red("Network Registration Failed.")
            utils.formatPrint.red("Check Antenna")
            exit(1)
        socket = int(self.lte_socket_init())
        if socket == -1:
            utils.formatPrint.red("Socket Init Failed")
            exit(1)
        self.lte_signal_info()
        socket_open, data = self.lte_socket_open(socket, 5008, "71.186.231.168")
        if not socket_open:
            utils.formatPrint.red("Socket Open Failed. Check the Server")
            self.lte_socket_close(socket)
            exit(1)
        # self.agmEn()
        self.agmLP_Enter()
        # self.tempEn()
        self.rs485ReadOnly()
        self.canStart()
        # self.rtcEn()
        self.ledRed("ON")
        self.ledGreen("ON")
        self.ledBlue("ON")
        self.battChargeEn()
        self.j1708ReadOnly()
        self.tpmsEn()

        chars = string.ascii_uppercase + string.ascii_lowercase
        data_send = "".join(random.choice(chars) for _ in range(300))
        tx_data = self.lte_socket_tx(socket, 1000, data_send)
        if not tx_data:
            utils.formatPrint.red("TX failed. Check the Server")
            exit(1)
        self.lte_socket_close(socket)
        utils.formatPrint.green("Socket is closed at {}".format(str(time.ctime())))

        # go back to stationed state
        print(
            Style.BRIGHT
            + "Going back to the Stationary state after {}".format(
                str(time.time() - start_time)
            )
        )
        self.pmStopHighZ(str(BLE_AGM_INT))  # Vehicle motion based wakeup

    def execMoving(self):
        # LTE AND GPS MUST BE ON
        self.lteDis()
        time.sleep(2)
        self.lteEn()
        time.sleep(5)
        self.lteAt("E0")
        time.sleep(5)
        self.lteAt("")
        if not self.lte_network_reg():
            utils.formatPrint.red("Network Registration Failed.")
            utils.formatPrint.red("Check Antenna")
            exit(1)
        socket = int(self.lte_socket_init())
        if socket == -1:
            utils.formatPrint.red("Socket Init Failed")
            exit(1)
        socket_open, data = self.lte_socket_open(socket, 5008, "71.186.231.168")
        if not socket_open:
            utils.formatPrint.red("Socket open Failed")
            self.lte_socket_close(socket)
            exit(1)
        self.gpsDis()
        self.agmDis()
        self.tempLP_Enter()
        self.rs485Shutdown()
        self.canStop()
        self.rtcEn()
        # self.ledRed('ON')
        # self.ledGreen('ON')
        # self.ledBlue('ON')
        # self.battChargeEn()
        self.j1708Shutdown()
        self.tpmsDis()
        self.rtcWakeEn(180, 0)
        self.pmStop()
        print(
            Style.BRIGHT
            + "\r\nConfigurations for {} mode are done for 30 sec".format(modes[2])
            + Style.RESET_ALL
        )
        return socket

    def execMoving_Tx(self, socket):
        # self.lteEn() - MUST BE ON
        start_time = time.time()
        print(Style.BRIGHT + "Test began at {}".format(str(time.ctime())))

        # self.agmEn()
        # self.tempEn()
        # self.rs485ReadOnly()
        # self.canStart()
        self.tpmsEn()
        chars = string.ascii_uppercase + string.ascii_lowercase
        data_send = "".join(random.choice(chars) for _ in range(300))
        tx_data = self.lte_socket_tx(socket, 1000, data_send)
        if not tx_data:
            utils.formatPrint.red("TX failed. Check the Server")
            exit(1)
        print(Style.BRIGHT + "Data is sent at {}".format(str(time.ctime())))
        self.pmStop()
        print(
            Style.BRIGHT
            + "\r\nDevice in Moving State after {}".format(
                str(time.time() - start_time)
            )
        )
        print(
            Style.BRIGHT
            + "\r\nConfigurations for {} mode are done".format(modes[3])
            + Style.RESET_ALL
        )

    def execShipment(self):
        self.lteDis()
        self.bleSysOff()
        self.agmDis()
        self.tempDis()
        self.rs485Shutdown()
        self.canSleep()
        self.gpsDis()
        self.rtcDis()
        self.ledRed("OFF")
        self.ledGreen("OFF")
        self.ledBlue("OFF")
        self.battChargeDis()
        self.j1708Shutdown()
        self.tpmsDis()
        self.pmStopHighZ(str(VIN | VSOLAR))  # Vin/Vsolar based wakeup
        while True:
            sta = input(
                Style.BRIGHT
                + "\r\nIs DBG_LED (Debug LED) turned OFF? [Y/N]: "
                + Style.RESET_ALL
            )
            if sta == "Y":
                utils.formatPrint.green("Successfully entered {} mode".format(modes[4]))
                break
            elif sta == "N":
                utils.formatPrint.red("Failed to enter {} mode".format(modes[4]))
                break
            else:
                utils.formatPrint.cyan("Invalid input. Please provide [Y/N]")

    def execOta(self):
        self.lteEn()
        self.agmDis()
        self.tempDis()
        self.rs485ReadOnly()
        self.canStop()
        self.gpsDis()
        self.rtcEn()
        self.ledRed("ON")
        self.ledGreen("ON")
        self.ledBlue("ON")
        self.battChargeEn()
        self.j1708Shutdown()
        print(
            Style.BRIGHT
            + "\r\nConfigurations for {} mode are done".format(modes[5])
            + Style.RESET_ALL
        )


def signal_handler(sig, frame):
    com.disconnect()
    print("Exiting test")
    sys.exit(0)


if __name__ == "__main__":

    # Init Colorama
    init()

    # Register Signal handler for graceful exit
    signal.signal(signal.SIGINT, signal_handler)

    # Argument parser
    ap = argparse.ArgumentParser()
    ap.add_argument("-b", "--baud", required=False, metavar="", help="Baudrate")

    reqArgs = ap.add_argument_group("required arguments")
    reqArgs.add_argument(
        "-p", "--port", required=True, metavar="", help="COM port (example: COM10)"
    )
    reqArgs.add_argument(
        "-m",
        "--mode",
        required=True,
        choices=modes,
        metavar="",
        help="Mode of operation. Allowed values are " + ", ".join(modes),
    )

    args = vars(ap.parse_args())

    # Connect to EVE
    com = utils.com_class()
    if args["baud"]:
        com.connect(args["port"], args["baud"], 1)
    else:
        com.connect(args["port"], 115200, 1)

    # Run tests
    modeObj = mode_class(com)
    # Parked
    if args["mode"] == modes[0]:
        utils.formatPrint.bright("Configuring for mode {}".format(modes[0]))
        modeObj.execParked()

    elif args["mode"] == modes[1]:
        utils.formatPrint.bright("Configuring for mode {}".format(modes[1]))
        modeObj.execParked_Tx()

    elif args["mode"] == modes[2]:
        utils.formatPrint.bright("Configuring for mode {}".format(modes[2]))
        modeObj.execMoving()

    elif args["mode"] == modes[3]:
        utils.formatPrint.bright("Configuring for mode {} before TX".format(modes[2]))
        sock = modeObj.execMoving()
        time.sleep(40)
        utils.formatPrint.bright("Configuring for mode {}".format(modes[3]))
        modeObj.execMoving_Tx(sock)

    elif args["mode"] == modes[4]:
        utils.formatPrint.bright("Configuring for mode {}".format(modes[4]))
        modeObj.execShipment()

    elif args["mode"] == modes[5]:
        utils.formatPrint.bright("Configuring for mode {}".format(modes[5]))
        modeObj.execOta()

    com.disconnect()

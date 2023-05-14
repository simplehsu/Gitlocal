# System imports
import time
import os
import sys
import signal
import argparse
from colorama import init

# Local imports
import modules
import utils

boot_time = 2 * 60  # 2 mins

# MCU low power modes
modes = ["STAND-BY", "STOP", "SLEEP"]

# Wake-up sources
wakeupSources = {"VIN": "1 0 0", "SOLAR": "0 1 0", "AGM": "0 0 1"}

colours = ["C", "G", "R"]


class LowPwrStressTest(modules.module_class):
    """ Class to stress test low power modes """

    def __init__(self, ser, intvl, log_file):
        modules.module_class.__init__(self, ser)
        self.__cmdCom = ser
        self.interval = intvl
        if log_file:
            self.log = open(log_file, "w+")
        else:
            self.log = None

    def __del__(self):
        if self.log:
            self.log.close()

    def disable_modules(self, wakeUp):
        """ Disable all the modules """

        self.print_message("\nDisabling all modules", colours[0])

        self.lteDis()
        self.tempDis()
        self.rs485Shutdown()
        self.canSleep()
        self.gpsDis()
        self.j1708Shutdown()
        self.tpmsDis()
        self.bleDis()

        if wakeUp != "AGM":
            self.agmDis()
            self.print_message("\nDisabled all modules", colours[1])
        else:
            self.print_message("\nDisabled all modules, except AGM", colours[1])

    def enable_modules(self):
        """ Enable all the modules """

        self.print_message("\nEnabling all modules", colours[0])

        self.lteEn()
        self.tempEn()
        self.rs485ReadOnly()
        self.canWakeUp()
        self.gpsEn()
        self.j1708ReadOnly()
        self.tpmsEn()
        self.agmEn()
        self.bleEn()

        self.print_message("\nEnabled all modules", colours[1])

    def mcu_mode(self, mode, wakeUp):
        """ Configure MCU in requested low power mode """

        self.print_message("\nConfiguring MCU in {} mode".format(mode), colours[0])

        wakeUpArg = "0 0 0"
        if wakeUp in wakeupSources:
            wakeUpArg = wakeupSources[wakeUp]
            self.print_message(
                "With {} as additional wake-up source".format(wakeUp), colours[0]
            )

        # Non-blocking RTC wake-up
        self.rtcWakeEn(self.interval, 0)

        if mode == modes[0]:
            self.pmStandby(wakeUpArg)  # Enter STAND-BY
        elif mode == modes[1]:
            self.pmStop()  # Enter STOP
        elif mode == modes[2]:
            self.pmSleep()  # Enter SLEEP

        self.print_message(
            "\nConfigured MCU in {} mode. LED should go OFF if "
            "configuration is successful".format(mode),
            colours[1],
        )

    def check_stand_by_exit(self, timeout):
        """ Look for start boot-up logs to check whether device exited STAND-BY mode """
        log = self.__cmdCom.raw_read(timeout, ":")
        if "CONSOLE" in log:
            return True
        return False

    def check_boot_up_cmplt(self, timeout):
        """ Look for boot-up logs to check whether boot-up process is complete or not """
        log = self.__cmdCom.raw_read(timeout, "$")
        if "Welcome" in log:
            return True
        return False

    def check_sleep_stop_exit(self, timeout):
        """ Look for response to check whether device exited SLEEP/STOP mode """
        log = self.__cmdCom.raw_read(timeout, "$")
        if "$" in log:
            return True
        return False

    def print_message(self, message, colour):
        if colour == colours[0]:
            utils.formatPrint.cyan(message)
        elif colour == colours[1]:
            utils.formatPrint.green(message)
        else:
            utils.formatPrint.red(message)

        if self.log:
            if message[0] == "\n":
                message = message[1:]
            self.log.write("[{}]: {}\n".format(time.ctime(), message))


def signal_handler(sig, frame):
    """ Keyboard interrupt handler """
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
    ap.add_argument(
        "-b", "--baud", required=False, metavar="", default=115200, help="Baudrate"
    )
    ap.add_argument(
        "-t",
        "--time_interval",
        required=False,
        metavar="",
        type=int,
        default=5,
        help="Enter and exit low power mode time interval in mins "
        "(In decimal) (Default: 5 mins)",
    )
    ap.add_argument(
        "-w",
        "--wakeup",
        required=False,
        metavar="",
        choices=wakeupSources.keys(),
        help="Configure STAND-BY wake-up source {} if required ".format(
            wakeupSources.keys()
        ),
    )
    ap.add_argument(
        "-l",
        "--log_file",
        required=False,
        metavar="",
        help="Specify absolute path of file in which test logs has to be stored",
    )

    reqArgs = ap.add_argument_group("required arguments")
    reqArgs.add_argument(
        "-p", "--port", required=True, metavar="", help="COM port (example: COM10)"
    )
    reqArgs.add_argument(
        "-i",
        "--iterations",
        required=True,
        metavar="",
        type=int,
        help="Number of times to enter and exit low power mode (In decimal)",
    )
    reqArgs.add_argument(
        "-m",
        "--mode",
        required=True,
        choices=modes,
        metavar="",
        help="MCU low power mode {}".format(modes),
    )

    args = vars(ap.parse_args())

    if args["wakeup"] and args["mode"] != modes[0]:
        print("Usage error: argument -w/--wakeup: Supported only with STAND-BY mode")
        sys.exit()

    # Connect to EVE
    com = utils.com_class()
    com.connect(args["port"], args["baud"], 1)

    TestObj = LowPwrStressTest(com, args["time_interval"] * 60, args["log_file"])
    utils.formatPrint.green("Test Started: {}".format(time.ctime()))

    for count in range(1, args["iterations"] + 1):

        # Print iteration number
        TestObj.print_message(
            "\n******************** Iteration {} **********" "**********".format(count),
            colours[0],
        )

        # Disable all modules
        TestObj.disable_modules(args["wakeup"])

        # Configure MCU in requested low power mode
        TestObj.mcu_mode(args["mode"], args["wakeup"])

        # Display time remaining to exit low power mode
        TestObj.print_message(
            "\nMCU will exit {} mode after {} min/s".format(
                args["mode"], args["time_interval"]
            ),
            colours[0],
        )

        exitSuccessful = False

        if args["mode"] == modes[0]:
            if args["wakeup"] in wakeupSources:
                TestObj.print_message(
                    "If not woken up by {}".format(args["wakeup"]), colours[0]
                )

            if TestObj.check_stand_by_exit(args["time_interval"] * 60):
                TestObj.print_message(
                    "\nMCU exited {} mode and is booting".format(modes[0]), colours[1]
                )
                # Stand-by exit is similar to warm boot
                if TestObj.check_boot_up_cmplt(boot_time):
                    TestObj.print_message(
                        "All modules are enabled as part of boot-up. "
                        "GREEN LED should be ON",
                        colours[1],
                    )
                    exitSuccessful = True
        else:
            if TestObj.check_sleep_stop_exit(args["time_interval"] * 60):
                TestObj.print_message(
                    "\nMCU exited {} mode. GREEN LED should "
                    "be ON".format(args["mode"]),
                    colours[1],
                )
                exitSuccessful = True

                # Enable all modules back
                TestObj.enable_modules()

        if not exitSuccessful:
            TestObj.print_message(
                "\nMCU failed to exit {} mode".format(modes[0]), colours[2]
            )
            com.disconnect()
            sys.exit()

        # If not last iteration
        if count < args["iterations"]:
            # Display time remaining to enter low power mode again
            TestObj.print_message(
                "\nDevice will enter Low Power mode after {} "
                "min/s".format(args["time_interval"]),
                colours[0],
            )

            time.sleep(args["time_interval"] * 60)

    TestObj.print_message("\nTest completed", colours[1])
    com.disconnect()

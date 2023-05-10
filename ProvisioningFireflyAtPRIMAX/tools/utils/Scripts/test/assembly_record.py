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


class factLog_class(modules.module_class):

    # Private variables
    __FileHandle = None
    __com = None

    def __init__(self, arg):
        self.__com = arg
        modules.module_class.__init__(self, arg)

    def createFileHandle(self, path):
        utils.formatPrint.bright("\r\nOpening file...")
        pathString = ""
        csnVal = self.rdCSN()
        if csnVal == None:
            utils.formatPrint.red(
                "Unable to read value. Ensure it is set before reading"
            )
            sys.exit(1)
        else:
            try:
                json_obj = json.loads(csnVal)
                csnVal = str(json_obj[self.sn_module_name]["MSG"]["INFO"])
                pathString = path + csnVal + "_prod.log"

                # create file handle
                # TODO: handle fopen exceptions here
                self.__FileHandle = open(pathString, "w+")
                print("File successfully opened at <%s>" % pathString)
            except:
                utils.formatPrint.red("Unable to open the file, exiting...")
                self.__com.disconnect()
                sys.exit(1)

    def logSNdata(self):
        utils.formatPrint.bright("\r\nStoring Serial numbers...")
        csnVal = self.rdCSN()
        if csnVal == None:
            utils.formatPrint.red(
                "Unable to read value. Ensure it is set before reading"
            )
        else:
            self.__FileHandle.write(csnVal)

        qsnVal = self.rdQSN()
        if qsnVal == None:
            utils.formatPrint.red(
                "Unable to read value. Ensure it is set before reading"
            )
        else:
            self.__FileHandle.write(qsnVal)

        mbsnVal = self.rdMBSN()
        if mbsnVal == None:
            utils.formatPrint.red(
                "Unable to read value. Ensure it is set before reading"
            )
        else:
            self.__FileHandle.write(mbsnVal)

        mdlVal = self.rdMDL()
        if mdlVal == None:
            utils.formatPrint.red(
                "Unable to read value. Ensure it is set before reading"
            )
        else:
            self.__FileHandle.write(mdlVal)

        hwVal = self.sysHwVer()
        if hwVal == None:
            utils.formatPrint.red(
                "Unable to read value. Ensure Command availablity and successful initialization"
            )
        else:
            self.__FileHandle.write(hwVal)

        fwVal = self.sysFwVer()
        if fwVal == None:
            utils.formatPrint.red(
                "Unable to read value. Ensure Command availablity and successful initialization"
            )
        else:
            self.__FileHandle.write(fwVal)

        bleMac = self.bleGetMac()
        if bleMac == None:
            utils.formatPrint.red(
                "Unable to read value. Ensure Command availablity and successful initialization"
            )
        else:
            self.__FileHandle.write(bleMac)

        lteInfo = self.lteInfo()
        if lteInfo == None:
            utils.formatPrint.red(
                "Unable to read value. Ensure Command availablity and successful initialization"
            )
        else:
            self.__FileHandle.write(lteInfo)

        atcaSerial = self.atcaGetSerial()
        if atcaSerial == None:
            utils.formatPrint.red(
                "Unable to read value. Ensure Command availablity and successful initialization"
            )
        else:
            self.__FileHandle.write(atcaSerial)

        atcaCertSerial = self.atcaGetCertserial()
        if atcaCertSerial == None:
            utils.formatPrint.red(
                "Unable to read value. Ensure Command availablity and successful initialization"
            )
        else:
            self.__FileHandle.write(atcaCertSerial)

        self.__FileHandle.close()


if __name__ == "__main__":

    # Init Colorama
    init()

    # Argument parser
    ap = argparse.ArgumentParser()
    ap.add_argument("-b", "--baud", required=False, metavar="", help="Baudrate")
    ap.add_argument(
        "-d", "--dest", required=False, metavar="", help="absolute path for log file"
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

    # Run tests
    logger = factLog_class(com)

    # Setup log path
    pathToFile = "./"
    if args["dest"]:
        pathToFile = args["dest"]
    logger.createFileHandle(pathToFile)

    # Get SN data
    logger.logSNdata()

    # Clean-up and exit
    com.disconnect()

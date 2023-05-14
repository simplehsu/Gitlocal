import json
import time


class gps_class(object):
    gps_module_name = "GPS"

    def __init__(self, arg):
        self.__cmdComm = arg

    def gpsEn(self):
        self.__write("EN")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print("Enabling module..." + str(json_obj[self.gps_module_name]["RESULT"]))
        except:
            print("Ensure module is successfully configured\r\n")
            return

    def gpsDis(self):
        self.__write("DIS")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "Disabling GPS module..."
                + str(json_obj[self.gps_module_name]["RESULT"])
            )
        except:
            print("Ensure module is successfully configured\r\n")
            return

    def gpsCnfBaud(self, baud):
        cmd = "CNF_BAUD" + " " + str(baud)
        self.__write(cmd)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print("Setup baudrate..." + str(json_obj[self.gps_module_name]["RESULT"]))
        except:
            print("Ensure module is successfully configured\r\n")
            return

    def gpsGetSat(self):
        self.__write("SAT")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "Reading satellite info..."
                + str(json_obj[self.gps_module_name]["RESULT"])
            )
            print(json.dumps(json_obj[self.gps_module_name]["MSG"]))

        except:
            print("Ensure module is successfully configured\r\n")
            return

    def gpsGetNav(self):
        self.__write("NAV")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "Reading Navigation info..."
                + str(json_obj[self.gps_module_name]["RESULT"])
            )
            print(
                str(json.dumps(json_obj[self.gps_module_name]["MSG"])).replace(
                    ",", "\n"
                )
            )

        except:
            print("Ensure module is successfully configured\r\n")
            return

    # Private variables and methods
    __timeout_sec = 5
    __cmdComm = None

    def __write(self, func):
        command = str(self.gps_module_name) + " " + func + "\r\n"
        print("\r\nsending...%s" % command.rstrip())
        self.__cmdComm.send_str(command)

    def __read(self):
        return self.__cmdComm.read_response(self.__cmdComm.DEFAULT_RD_TIMEOUT)

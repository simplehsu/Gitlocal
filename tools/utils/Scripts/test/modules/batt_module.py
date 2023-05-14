import json


class batt_class(object):
    batt_module_name = "BATT"

    def __init__(self, arg):
        self.__cmdComm = arg

    def battGetID(self):
        self.__write("GETID")
        resp = self.__read()

        try:
            json_obj = json.loads(resp)
            print("Getting BATT ID..." + str(json_obj[self.batt_module_name]["RESULT"]))
        except:
            print("Ensure module is successfully configured")
            return

    # DEPRECATED
    def battChargeEn(self):
        # Enable charging
        self.__write("CHG_EN")
        resp = self.__read()

        try:
            json_obj = json.loads(resp)
            print(
                "Enabling charging..." + str(json_obj[self.batt_module_name]["RESULT"])
            )
        except:
            print("Ensure module is successfully configured")
            return

    def battChargeDis(self):
        # Disable charging
        self.__write("CHG_DIS")
        resp = self.__read()

        try:
            json_obj = json.loads(resp)
            print(
                "Disabling charging..." + str(json_obj[self.batt_module_name]["RESULT"])
            )
        except:
            print("Ensure module is successfully configured")
            return

    def battGetVolt(self):
        # Read Voltage
        self.__write("VOLT")
        resp = self.__read()

        try:
            json_obj = json.loads(resp)
            print(
                "Reading BATT Voltage..."
                + str(json_obj[self.batt_module_name]["RESULT"])
            )
            print(json.dumps(json_obj[self.batt_module_name]["MSG"]))
        except:
            print("Ensure module is successfully configured")
            return

    def battGetCapacity(self):
        # Read Capacity
        self.__write("CAPACITY")
        resp = self.__read()

        try:
            json_obj = json.loads(resp)
            print(
                "Reading BATT Capacity..."
                + str(json_obj[self.batt_module_name]["RESULT"])
            )
            print(
                str(json.dumps(json_obj[self.batt_module_name]["MSG"])).replace(
                    ",", "\n"
                )
            )
        except:
            print("Ensure module is successfully configured")
            return

    def battGetStatus(self):
        # Read Status
        self.__write("STAT")
        resp = self.__read()

        try:
            json_obj = json.loads(resp)
            print(
                "Reading BATT Status..."
                + str(json_obj[self.batt_module_name]["RESULT"])
            )
            print(
                str(json.dumps(json_obj[self.batt_module_name]["MSG"])).replace(
                    ",", "\n"
                )
            )
        except:
            print("Ensure module is successfully configured")
            return

    # Private variables and methods
    __cmdComm = None

    def __write(self, func):
        command = str(self.batt_module_name) + " " + func + "\r\n"
        print("\r\nsending...%s" % command.rstrip())
        self.__cmdComm.send_str(command)

    def __read(self):
        return self.__cmdComm.read_response(self.__cmdComm.DEFAULT_RD_TIMEOUT)

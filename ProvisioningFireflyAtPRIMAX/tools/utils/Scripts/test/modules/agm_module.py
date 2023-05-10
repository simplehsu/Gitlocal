import sys
import json


class agm_class(object):
    agm_module_name = "AGM"

    def __init__(self, arg):
        self.__cmdComm = arg

    def agmEn(self):
        # Enable Module
        self.__write("EN")
        resp = self.__read()

        try:
            json_obj = json.loads(resp)
            print("Enabling module..." + str(json_obj[self.agm_module_name]["RESULT"]))
        except:
            print("Ensure module is successfully configured")
            return

    def agmDis(self):
        # Disable Module
        self.__write("DIS")
        resp = self.__read()

        try:
            json_obj = json.loads(resp)
            print("Enabling module..." + str(json_obj[self.agm_module_name]["RESULT"]))
        except:
            print("Ensure module is successfully configured")
            return

    def agmLP_Enter(self):
        # Enter low power
        self.__write("ENTER_LP")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print("Enter low power..." + str(json_obj[self.agm_module_name]["RESULT"]))

        except:
            print("Ensure module is successfully configured")
            return

    def agmLP_Exit(self):
        # Exit low power
        self.__write("EXIT_LP")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "Exiting low power..." + str(json_obj[self.agm_module_name]["RESULT"])
            )

        except:
            print("Ensure module is successfully configured")
            return

    def agmODR_CONFIG(self, odr):
        # Configure ODR
        cmd = "SET_ODR" + " " + str(odr)
        self.__write(cmd)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print("Configuring ODR..." + str(json_obj[self.agm_module_name]["RESULT"]))

        except:
            print("Ensure you are using firmware greater than v2.3")
            return

    def agmRD_GY(self):
        # Read Gyro
        self.__write("RD_GY")
        resp = self.__read()

        try:
            json_obj = json.loads(resp)
            print(
                "Reading Gyro Data..." + str(json_obj[self.agm_module_name]["RESULT"])
            )
            print(str(json_obj[self.agm_module_name]["MSG"]).replace("u", ""))

        except:
            print("Ensure module is successfully configured\r\n")
            return

    def agmRD_ACC(self):
        # Read Acc
        self.__write("RD_ACC")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "Reading Accelero Data..."
                + str(json_obj[self.agm_module_name]["RESULT"])
            )
            print(str(json_obj[self.agm_module_name]["MSG"]).replace("u", ""))

        except:
            print("Ensure module is successfully configured\r\n")
            return

    # Private variables and methods
    __cmdComm = None

    def __write(self, func):
        command = str(self.agm_module_name) + " " + func + "\r\n"
        print("\r\nsending...%s" % command.rstrip())
        self.__cmdComm.send_str(command)

    def __read(self):
        return self.__cmdComm.read_response(self.__cmdComm.DEFAULT_RD_TIMEOUT)

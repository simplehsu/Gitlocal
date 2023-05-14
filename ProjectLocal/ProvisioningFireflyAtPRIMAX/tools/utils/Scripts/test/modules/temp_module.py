import json


class temp_class(object):
    temp_module_name = "TEMP"

    def __init__(self, arg):
        self.__cmdComm = arg

    def tempEn(self):
        # Enable Module
        self.__write("EN_DEV")
        resp = self.__read()

        try:
            json_obj = json.loads(resp)
            print("Enabling module..." + str(json_obj[self.temp_module_name]["RESULT"]))
        except:
            print("Ensure module is successfully configured")
            return

    def tempLP_Enter(self):
        # Enter Low power
        self.__write("ENTR_LPWR")
        resp = self.__read()

        try:
            json_obj = json.loads(resp)
            print(
                "Entering Lowpower..." + str(json_obj[self.temp_module_name]["RESULT"])
            )
        except:
            print("Ensure module is successfully configured")
            return

    def tempLP_Exit(self):
        # Exit Low power
        self.__write("EXT_LPWR")
        resp = self.__read()

        try:
            json_obj = json.loads(resp)
            print(
                "Exiting Low power mode..."
                + str(json_obj[self.temp_module_name]["RESULT"])
            )
        except:
            print("Ensure module is successfully configured")
            return

    def tempDis(self):
        # Disable Module
        self.__write("DIS_DEV")
        resp = self.__read()

        try:
            json_obj = json.loads(resp)
            print(
                "Disabling module..." + str(json_obj[self.temp_module_name]["RESULT"])
            )
        except:
            print("Ensure module is successfully configured")
            return

    def tempGetVal(self):
        self.__write("GET_TEMP")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "Reading Temperature..."
                + str(json_obj[self.temp_module_name]["RESULT"])
            )
            print("Value %s\r\n" % str(json_obj[self.temp_module_name]["MSG"]["VAL"]))

        except:
            print("Ensure module is successfully configured")
            return

    # Private variables and methods
    __cmdComm = None

    def __write(self, func):
        command = str(self.temp_module_name) + " " + func + "\r\n"
        print("\r\nsending...%s" % command.rstrip())
        self.__cmdComm.send_str(command)

    def __read(self):
        return self.__cmdComm.read_response(self.__cmdComm.DEFAULT_RD_TIMEOUT)

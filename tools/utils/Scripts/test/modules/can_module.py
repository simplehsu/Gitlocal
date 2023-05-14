import sys
import json


class can_class(object):
    can_module_name = "CAN"
    cmdComm = None

    def __init__(self, arg):
        self.__cmdComm = arg

    def canWakeUp(self):
        # Wakeup Module
        self.__write("WAKE_UP")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print("Wake-up module..." + str(json_obj[self.can_module_name]["RESULT"]))
        except:
            print("Ensure module is successfully configured")
            return

    def canStart(self):
        # Enable Module
        self.__write("START")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print("Start module..." + str(json_obj[self.can_module_name]["RESULT"]))
        except:
            print("Ensure module is successfully configured")
            return

    def canStop(self):
        # Disable Module
        self.__write("STOP")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print("Stop module..." + str(json_obj[self.can_module_name]["RESULT"]))
        except:
            print("Ensure module is successfully configured")
            return

    def canSleep(self):
        # Module sleep
        self.__write("SLEEP")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "CAN entering sleep..." + str(json_obj[self.can_module_name]["RESULT"])
            )
        except:
            print("Ensure module is successfully configured")
            return

    def canGetFrame(self):
        self.__write("GET_FRAME")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print("Reading CAN bus..." + str(json_obj[self.can_module_name]["RESULT"]))
            print(
                "CAN FRAME: %s\r\n"
                % str(json_obj[self.can_module_name]["MSG"]["CAN FRAME"])
            )

        except:
            print("Ensure module is successfully configured\r\n")
            return

    # Private variables and methods
    __cmdComm = None

    def __write(self, func):
        command = str(self.can_module_name) + " " + func + "\r\n"
        print("\r\nsending...%s" % command.rstrip())
        self.__cmdComm.send_str(command)

    def __read(self):
        return self.__cmdComm.read_response(self.__cmdComm.DEFAULT_RD_TIMEOUT)

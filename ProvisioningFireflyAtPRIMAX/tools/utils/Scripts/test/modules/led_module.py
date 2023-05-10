import sys
import json


class led_class(object):
    led_module_name = "LED"

    def __init__(self, arg):
        self.__cmdComm = arg

    def ledRed(self, status):
        cmd = "RED" + " " + status
        self.__write(cmd)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "Turn %s RED LED..." % status
                + str(json_obj[self.led_module_name]["RESULT"])
            )
        except:
            print("Ensure module is successfully configured")
            return

    def ledGreen(self, status):
        cmd = "GREEN" + " " + status
        self.__write(cmd)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "Turn %s GREEN LED..." % status
                + str(json_obj[self.led_module_name]["RESULT"])
            )
        except:
            print("Ensure module is successfully configured")
            return

    def ledBlue(self, status):
        cmd = "BLUE" + " " + status
        self.__write(cmd)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "Turn %s BLUE LED..." % status
                + str(json_obj[self.led_module_name]["RESULT"])
            )
        except:
            print("Ensure module is successfully configured")
            return

    def ledDebug(self, status):
        cmd = "DEBUG" + " " + status
        self.__write(cmd)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "Turn %s DEBUG LED..." % status
                + str(json_obj[self.led_module_name]["RESULT"])
            )
        except:
            print("Ensure module is successfully configured")
            return

    # Private variables and methods
    __cmdComm = None

    def __write(self, func):
        command = str(self.led_module_name) + " " + func + "\r\n"
        print("\r\nsending...%s" % command.rstrip())
        self.__cmdComm.send_str(command)

    def __read(self):
        return self.__cmdComm.read_response(self.__cmdComm.DEFAULT_RD_TIMEOUT)

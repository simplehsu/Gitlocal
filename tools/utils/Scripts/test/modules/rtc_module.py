import sys
import json
import datetime


class rtc_class(object):
    rtc_module_name = "RTC"

    def __init__(self, arg):
        self.__cmdComm = arg

    def rtcEn(self):
        # Enable Module
        self.__write("EN")
        resp = self.__read()

        try:
            json_obj = json.loads(resp)
            print("Enabling module..." + str(json_obj[self.rtc_module_name]["RESULT"]))
        except:
            print("Ensure module is successfully configured")
            return

    def rtcDis(self):
        # Disable Module
        self.__write("DIS")
        resp = self.__read()

        try:
            json_obj = json.loads(resp)
            print("Disabling module..." + str(json_obj[self.rtc_module_name]["RESULT"]))
        except:
            print("Ensure module is successfully configured")
            return

    def rtcWakeDis(self):
        # Disable wake-up interrupt
        self.__write("WAKE_DIS")
        resp = self.__read()

        try:
            json_obj = json.loads(resp)
            print(
                "Disabling wake-up interrupt..."
                + str(json_obj[self.rtc_module_name]["RESULT"])
            )
        except:
            print("Ensure module is successfully configured")
            return

    def rtcWakeEn(self, timeSecs, isBlock):
        # Enable Wake-up interrupt
        cmd = "WAKE_EN" + " " + str(timeSecs) + " " + str(isBlock)
        self.__write(cmd)
        resp = self.__read()

        try:
            json_obj = json.loads(resp)
            print(
                "Enabling wake-up interrupt..."
                + str(json_obj[self.rtc_module_name]["RESULT"])
            )
        except:
            print("Ensure module is successfully configured")
            return

    def rtcSetCalendar(self, isoDateTime):
        cmd = "SET_CALENDAR" + " " + isoDateTime
        self.__write(cmd)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print("Result..." + str(json_obj[self.rtc_module_name]["RESULT"]))
        except:
            # TODO: print in red
            print("Failed to get response!")
            return

    def rtcGetCalendar(self):
        self.__write("GET_CALENDAR")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print("Result..." + str(json_obj[self.rtc_module_name]["RESULT"]))
            print(json.dumps(json_obj[self.rtc_module_name]["MSG"]))
            return str(json_obj[self.rtc_module_name]["MSG"]["VAL"])
        except:
            # TODO: print in red
            print("Failed to get response!")
            return

    # Private variables and methods
    __cmdComm = None

    def __write(self, func):
        command = str(self.rtc_module_name) + " " + func + "\r\n"
        print("\r\nsending...%s" % command.rstrip())
        self.__cmdComm.send_str(command)

    def __read(self):
        return self.__cmdComm.read_response(self.__cmdComm.DEFAULT_RD_TIMEOUT)

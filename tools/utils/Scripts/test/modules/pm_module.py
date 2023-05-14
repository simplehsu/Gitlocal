import json


class pm_class(object):
    pm_module_name = "PM"

    def __init__(self, arg):
        self.__cmdComm = arg

    def pmStop(self):
        self.__write("STOP")

    def pmStopHighZ(self, wakeSrc):
        cmd = "STOP 1" + " " + wakeSrc
        self.__write(cmd)

    def pmSleep(self):
        self.__write("SLEEP")

    def pmStandby(self, args):
        cmd = "STANDBY" + " " + args
        self.__write(cmd)

    # Private variables and methods
    __cmdComm = None

    def __write(self, func):
        command = str(self.pm_module_name) + " " + func + "\r\n"
        print("\r\nsending...%s" % command.rstrip())
        self.__cmdComm.send_str(command)

    # Read may be redundant for this module
    # def __read(self):
    #   return self.__cmdComm.read_response(self.__cmdComm.DEFAULT_RD_TIMEOUT)

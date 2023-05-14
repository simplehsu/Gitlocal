import sys
import json


class sn_class(object):
    sn_module_name = "SN"

    def __init__(self, arg):
        self.__cmdComm = arg

    def rdMBSN(self):
        cmd = "RD_MBSN"
        self.__write(cmd)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "Read Main Board Serial Number(MBSN)..."
                + str(json_obj[self.sn_module_name]["RESULT"])
            )
            return resp
        except:
            print("Ensure module is successfully configured")
            return None

    def rdQSN(self):
        cmd = "RD_QSN"
        self.__write(cmd)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "Read Quanta Serial Number(QSN)..."
                + str(json_obj[self.sn_module_name]["RESULT"])
            )
            return resp
        except:
            print("Ensure module is successfully configured")
            return None

    def rdCSN(self):
        cmd = "RD_CSN"
        self.__write(cmd)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "Read Customer Serial Number(CSN)..."
                + str(json_obj[self.sn_module_name]["RESULT"])
            )
            return resp
        except:
            print("Ensure module is successfully configured")
            return None

    def rdMDL(self):
        cmd = "RD_MDL"
        self.__write(cmd)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "Read Model Information..."
                + str(json_obj[self.sn_module_name]["RESULT"])
            )
            return resp
        except:
            print("Ensure module is successfully configured")
            return None

    # Private variables and methods
    __cmdComm = None

    def __write(self, func):
        command = str(self.sn_module_name) + " " + func + "\r\n"
        print("\r\nsending...%s" % command.rstrip())
        self.__cmdComm.send_str(command)

    def __read(self):
        return self.__cmdComm.read_response(self.__cmdComm.DEFAULT_RD_TIMEOUT)

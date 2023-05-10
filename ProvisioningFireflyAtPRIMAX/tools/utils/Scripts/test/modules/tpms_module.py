import json


class tpms_class(object):
    tpms_module_name = "TPMS"

    def __init__(self, arg):
        self.__cmdComm = arg

    def tpmsEn(self):
        # Enable Module
        self.__write("ENABLE")
        resp = self.__read()

        try:
            json_obj = json.loads(resp)
            print("Enabling module..." + str(json_obj[self.tpms_module_name]["RESULT"]))
        except:
            print("Ensure module is successfully configured")
            return

    def tpmsDis(self):
        # Disable Module
        self.__write("DISABLE")
        resp = self.__read()

        try:
            json_obj = json.loads(resp)
            print(
                "Disabling module..." + str(json_obj[self.tpms_module_name]["RESULT"])
            )
        except:
            print("Ensure module is successfully configured")
            return

    def __write(self, func):
        command = str(self.tpms_module_name) + " " + func + "\r\n"
        print("\r\nsending...%s" % command.rstrip())
        self.__cmdComm.send_str(command)

    def __read(self):
        return self.__cmdComm.read_response(self.__cmdComm.DEFAULT_RD_TIMEOUT)

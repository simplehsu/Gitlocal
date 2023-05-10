import json


class atca_class(object):
    atca_module_name = "ATCA"

    def __init__(self, arg):
        self.__cmdComm = arg

    def atcaGetSerial(self):
        self.__write("SERIAL")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "Getting ATCA serial..."
                + str(json_obj[self.atca_module_name]["RESULT"])
            )
            return resp
        except:
            print("Ensure module is successfully configured")
            return None

    def atcaGetCertserial(self):
        self.__write("CERTSERIAL")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "Getting ATCA cert serial..."
                + str(json_obj[self.atca_module_name]["RESULT"])
            )
            return resp
        except:
            print("Ensure module is successfully configured")
            return None

    # Private variables and methods
    __cmdComm = None

    def __write(self, func):
        command = str(self.atca_module_name) + " " + func + "\r\n"
        print("\r\nsending...%s" % command.rstrip())
        self.__cmdComm.send_str(command)

    def __read(self):
        return self.__cmdComm.read_response(self.__cmdComm.DEFAULT_RD_TIMEOUT)

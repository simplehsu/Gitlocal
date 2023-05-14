import json


class qspi_class(object):
    qspi_module_name = "QSPI"

    def __init__(self, arg):
        self.__cmdComm = arg

    def __write(self, func):
        command = str(self.qspi_module_name) + " " + func + "\n"
        print("\r\nsending...%s" % command.rstrip())
        self.__cmdComm.send_str(command)

    def __read(self):
        return self.__cmdComm.read_response(self.__cmdComm.DEFAULT_RD_TIMEOUT)

    def qspiGET_INFO(self):
        self.__write("GET_INFO")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print("QSPI GET_INFO..." + str(json_obj[self.qspi_module_name]["RESULT"]))
            return resp
        except:
            print("Ensure module is successfully configured")
            return None

    def qspiSEC_ER(self, sec_size, sec_addr):
        cmd = "SEC_ER" + " " + str(sec_size) + " " + str(sec_addr)
        print(cmd)
        self.__write(cmd)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print("QSPI SEC_ER..." + str(json_obj[self.qspi_module_name]["RESULT"]))
            return resp
        except:
            print("Ensure module is successfully configured")
            return None

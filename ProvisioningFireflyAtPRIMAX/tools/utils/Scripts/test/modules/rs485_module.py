import json


class rs485_class(object):
    rs485_module_name = "RS485"

    def __init__(self, arg):
        self.__cmdComm = arg

    def rs485Shutdown(self):
        # RS485 shutdown
        self.__write("SHUTDOWN")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "Shutting down RS485..."
                + str(json_obj[self.rs485_module_name]["RESULT"])
            )

        except:
            print("Ensure module is successfully configured")
            return

    def rs485ReadOnly(self):
        # RS485 Read only mode
        self.__write("EN_RD_ONLY")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "Entering RS485 Read only mode ..."
                + str(json_obj[self.rs485_module_name]["RESULT"])
            )

        except:
            print("Ensure module is successfully configured")
            return

    # Private variables and methods
    __cmdComm = None

    def __write(self, func):
        command = str(self.rs485_module_name) + " " + func + "\r\n"
        print("\r\nsending...%s" % command.rstrip())
        self.__cmdComm.send_str(command)

    def __read(self):
        return self.__cmdComm.read_response(self.__cmdComm.DEFAULT_RD_TIMEOUT)

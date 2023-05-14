import json


class j1708_class(object):
    j1708_module_name = "J1708"

    def __init__(self, arg):
        self.__cmdComm = arg

    def j1708Shutdown(self):
        # j1708 shutdown
        self.__write("SHUTDOWN")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "Shutting down j1708..."
                + str(json_obj[self.j1708_module_name]["RESULT"])
            )

        except:
            print("Ensure module is successfully configured")
            return

    def j1708ReadOnly(self):
        # j1708 Read only mode
        self.__write("EN_RD_ONLY")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "Entering j1708 Read only mode ..."
                + str(json_obj[self.j1708_module_name]["RESULT"])
            )

        except:
            print("Ensure module is successfully configured")
            return

    # Private variables and methods
    __cmdComm = None

    def __write(self, func):
        command = str(self.j1708_module_name) + " " + func + "\r\n"
        print("\r\nsending...%s" % command.rstrip())
        self.__cmdComm.send_str(command)

    def __read(self):
        return self.__cmdComm.read_response(self.__cmdComm.DEFAULT_RD_TIMEOUT)

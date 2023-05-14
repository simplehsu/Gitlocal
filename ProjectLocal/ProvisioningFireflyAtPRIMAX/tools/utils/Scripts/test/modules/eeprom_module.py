import json


class eeprom_class(object):
    eeprom_module_name = "EEPROM"

    def __init__(self, arg):
        self.__cmdComm = arg

    def eepromRead(self, address, len):
        cmd = "READ" + " " + str(address) + " " + str(len)
        self.__write(cmd)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "EEPROM READ successful..."
                + str(json_obj[self.eeprom_module_name]["RESULT"])
            )
        except:
            print("EERPOM READ opeartion failed\r\n")
            return

    def eepromWrite(self, address, data):
        cmd = "WRITE" + " " + str(address) + " " + data
        self.__write(cmd)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "EEPRM WRITE successful..."
                + str(json_obj[self.eeprom_module_name]["RESULT"])
            )
        except:
            print("EEPRM WRITE failed\r\n")
            return

    # Private variables and methods
    __timeout_sec = 5
    __cmdComm = None

    def __write(self, func):
        command = str(self.eeprom_module_name) + " " + func + "\r\n"
        print("\r\nsending...%s" % command.rstrip())
        self.__cmdComm.send_str(command)

    def __read(self):
        return self.__cmdComm.read_response(self.__cmdComm.DEFAULT_RD_TIMEOUT)

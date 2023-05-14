import json


class sys_class(object):
    sys_module_name = "SYS"

    def __init__(self, arg):
        self.__cmdComm = arg

    def check_boot_up_cmplt(self, timeout):
        """ Look for boot-up logs to check whether boot-up process is complete or not """
        log = self.__cmdComm.raw_read(timeout, b"$")
        if "Welcome" in log:
            return True
        return False

    def sysHwVer(self):
        self.__write("HW_REV")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "Hardware Revision..." + str(json_obj[self.sys_module_name]["RESULT"])
            )
            return resp
        except:
            print("Ensure module is successfully configured")
            return None

    def sysFwVer(self):
        self.__write("FW_VER")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "Firmware Revision..." + str(json_obj[self.sys_module_name]["RESULT"])
            )
            return resp
        except:
            print("Ensure module is successfully configured")
            return None

    def sysHogStart(self, itr):
        cmd = "HOG_START" + " " + str(itr)
        self.__write(cmd)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print("MEMORY operation..." + str(json_obj[self.sys_module_name]["RESULT"]))
        except:
            print("Ensure module is successfully configured")
            return

    def sysReboot(self, check_status):
        self.__write("REBOOT")
        if check_status:
            if self.check_boot_up_cmplt(self.__cmdComm.DEFAULT_RD_TIMEOUT):
                print("Device is successfully Rebooted")
            else:
                print("Failed to Reboot Device")

    # Private variables and methods
    __cmdComm = None

    def __write(self, func):
        command = str(self.sys_module_name) + " " + func + "\r\n"
        print("\r\nsending...%s" % command.rstrip())
        self.__cmdComm.send_str(command)

    def __read(self):
        return self.__cmdComm.read_response(self.__cmdComm.DEFAULT_RD_TIMEOUT)

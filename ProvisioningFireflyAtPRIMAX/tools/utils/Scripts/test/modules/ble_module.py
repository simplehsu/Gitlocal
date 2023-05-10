import json
import re


class ble_class(object):
    ble_module_name = "BLE"

    def __init__(self, arg):
        self.__cmdComm = arg

    def bleGetMac(self):
        self.__write("GET_MAC")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print("Getting BLE MAC..." + str(json_obj[self.ble_module_name]["RESULT"]))
            return resp
        except:
            print("Ensure module is successfully configured")
            return None

    def bleGetSwVer(self):
        self.__write("GET_SW_VER")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "Getting SW VERSION..." + str(json_obj[self.ble_module_name]["RESULT"])
            )
            if json_obj[self.ble_module_name]["RESULT"] == "PASS":
                print(
                    "SW VERSION: "
                    + str(json_obj[self.ble_module_name]["MSG"]["FW_VER"])
                )
            return json_obj[self.ble_module_name]
        except:
            print("Ensure module is successfully configured")
            return None

    def bleChipReset(self):
        self.__write("CHIP_RESET")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print("BLE CHIP_RESET..." + str(json_obj[self.ble_module_name]["RESULT"]))
            return json_obj[self.ble_module_name]
        except:
            print("Ensure module is successfully configured")
            return None

    def bleEn(self):
        self.__write("ENABLE")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print("Enabling BLE..." + str(json_obj[self.ble_module_name]["RESULT"]))
            return resp
        except:
            print("Ensure module is successfully configured")
            return None

    def bleDis(self):
        self.__write("DISABLE")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print("Disabling BLE..." + str(json_obj[self.ble_module_name]["RESULT"]))
            return resp
        except:
            print("Ensure module is successfully configured")
            return None

    def bleSysOff(self):
        self.__write("SYS_OFF")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "Entering BLE Low power..."
                + str(json_obj[self.ble_module_name]["RESULT"])
            )
            return resp
        except:
            print("Ensure module is successfully configured")
            return None

    def bleScan(self, on=True):
        self.__write("AT scan %s" % ("on" if on else "off"))
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "Turning BLE scanning %s: %s"
                % ("on" if on else "off", str(json_obj[self.ble_module_name]["RESULT"]))
            )
            return resp
        except:
            print("Ensure module is successfully configured")
            return None

    def bleConnect(self, mac):
        self.__write("AT connect %s" % mac)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print("Connect... ", str(json_obj[self.ble_module_name]["RESULT"]))
            return resp
        except:
            print("Ensure module is successfully configured")
            return None

    def bleDisconnect(self, mac):
        self.__write("AT disconnect %s" % mac)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print("Disconnect... ", str(json_obj[self.ble_module_name]["RESULT"]))
            return resp
        except:
            print("Ensure module is successfully configured")
            return None

    def bleEsDevices(self):
        self.__write("AT es_devices")
        resp = self.__read()
        env_sensors = {}
        try:
            r = re.compile(r"(-?\d+) ([0-9A-F:]*) (ES-2 \d{6})")
            json_obj = json.loads(resp)
            lines = json_obj[self.ble_module_name]["MSG"]["RESPONSE"].values()
            for line in filter(lambda l: l, lines):
                result = r.search(line)
                if result:
                    # make a dict of dicts keyed by the mac address
                    env_sensors[result.group(2)] = {
                        "rssi": int(result.group(1)),
                        "mac": result.group(2),
                        "name": result.group(3),
                    }
            return env_sensors

        except:
            print("Ensure module is successfully configured")
            return env_sensors

    def bleConnectedDevices(self):
        self.__write("AT connected_devices")
        resp = self.__read()
        connected_sensors = {}
        try:
            r = re.compile(r"(\d+)\.\s*([0-9A-F:]*)\s*Security level:\s*(\d?)")
            json_obj = json.loads(resp)
            lines = json_obj[self.ble_module_name]["MSG"]["RESPONSE"].values()
            for line in filter(lambda l: l, lines):
                result = r.search(line)
                if result:
                    # make a dict of dicts keyed by the mac address
                    connected_sensors[result.group(2)] = {
                        "idx": int(result.group(1)),
                        "mac": result.group(2),
                        "security_level": result.group(3),
                    }
            return connected_sensors

        except:
            print("Ensure module is successfully configured")
            return connected_sensors

    def bleDumpDb(self):
        self.__write("AT dump_db")
        resp = self.__read()
        lines = []

        try:
            json_obj = json.loads(resp)
            lines = json_obj[self.ble_module_name]["MSG"]["RESPONSE"].values()
            return lines

        except:
            print("Ensure module is successfully configured")
            return lines

    def bleSetSensorList(self, list=None):
        devices = " ".join(list) if list else ""
        cmd = "AT set_sensor_list %s" % devices
        self.__write(cmd)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(cmd + "...", str(json_obj[self.ble_module_name]["RESULT"]))
            return resp
        except:
            print("Ensure module is successfully configured")
            return None

    # Private variables and methods
    __cmdComm = None

    def __write(self, func):
        command = str(self.ble_module_name) + " " + func + "\r\n"
        # print("\r\nsending...%s" % command.rstrip())
        self.__cmdComm.send_str(command)

    def __read(self):
        return self.__cmdComm.read_response(self.__cmdComm.DEFAULT_RD_TIMEOUT)

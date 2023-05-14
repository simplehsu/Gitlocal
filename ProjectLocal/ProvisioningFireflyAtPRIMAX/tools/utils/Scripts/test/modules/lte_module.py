import time
import json

timeout_sec = 2


class lte_class(object):
    lte_module_name = "LTE"

    def __init__(self, arg):
        self.__cmdComm = arg

    def lteInfo(self):
        self.__write("GET_INFO")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print("Get Info..." + str(json_obj[self.lte_module_name]["RESULT"]))
            return resp
        except:
            print("Ensure module is successfully configured")
            return None

    def lteEn(self):
        # Enable Module
        self.__write("EN")
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print("Enabling module..." + str(json_obj[self.lte_module_name]["RESULT"]))
        except:
            print("Ensure module is successfully configured")
            return

    def lteDis(self):
        # Disable Module
        self.__write("DIS")
        time.sleep(timeout_sec)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print("Disabling module..." + str(json_obj[self.lte_module_name]["RESULT"]))
        except:
            print("Ensure module is successfully configured")
            return

    def lteAt(self, ATCmd):
        cmd = "SEND AT" + ATCmd
        self.__write(cmd)
        time.sleep(timeout_sec)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print("Command send..." + str(json_obj[self.lte_module_name]["RESULT"]))
            print(
                "Response..." + str(json_obj[self.lte_module_name]["MSG"]["RESPONSE"])
            )
            return str(json_obj[self.lte_module_name]["MSG"]["RESPONSE"])
        except:
            print("Failed to get response!")
            return

    def lte_network_reg(self):
        time_start = time.time()
        result = False
        cmd = "NW_REG"
        self.__write(cmd)
        # time.sleep(timeout_sec)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            if json_obj[self.lte_module_name]["RESULT"] == "PASS":
                result = True
            print("Command send..." + str(json_obj[self.lte_module_name]["RESULT"]))
            print(
                "Command send...{} after {}".format(
                    str(json_obj[self.lte_module_name]["RESULT"]),
                    str(time.time() - time_start),
                )
            )

            return result
        except:
            print("Failed to get response!")
            return False

    def lte_socket_init(self):
        time_start = time.time()
        cmd = "SOCK_INIT TCP"
        self.__write(cmd)
        # time.sleep(timeout_sec)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "Command send...{} after {}".format(
                    str(json_obj[self.lte_module_name]["RESULT"]),
                    str(time.time() - time_start),
                )
            )
            if str(json_obj[self.lte_module_name]["RESULT"]) == "FAIL":
                return -1
            print(
                "Socket ID..." + str(json_obj[self.lte_module_name]["MSG"]["Socket ID"])
            )
            return json_obj[self.lte_module_name]["MSG"]["Socket ID"]
        except:
            print("Failed to get response!")
            return -1

    def lte_socket_open(self, socket, port, ip):
        time_start = time.time()
        result = False
        command = "SOCK_OPEN {} {} {}".format(socket, port, ip)
        self.__write(command)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            if json_obj[self.lte_module_name]["RESULT"] == "PASS":
                result = True
            data_to_read = int(json_obj[self.lte_module_name]["MSG"]["Data to be read"])
            print(
                "Command send...{} after {}".format(
                    str(result), str(time.time() - time_start)
                )
            )
            print("Data to read..." + str(data_to_read))
            return result, data_to_read
        except:
            print("Failed to get response!")
            return False, -1

    def lte_socket_tx(self, socket, size, data):
        time_start = time.time()
        result_tx = False
        command = "SOCK_WR {} {} {}".format(socket, size, data)
        self.__write(command)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            if json_obj[self.lte_module_name]["RESULT"] == "PASS":
                result_tx = True
            print(
                "Command send...{} after {}".format(
                    str(result_tx), str(time.time() - time_start)
                )
            )
            return result_tx
        except:
            print("Failed to get response!")
            return False, -1

    def lte_socket_close(self, socket):
        time_start = time.time()
        result = False
        command = "SOCK_CL {}".format(socket)
        self.__write(command)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            if json_obj[self.lte_module_name]["RESULT"] == "PASS":
                result = True
            print(
                "Command send...{} after {}".format(
                    str(result), str(time.time() - time_start)
                )
            )
            return result
        except:
            print("Failed to get response!")
            return False, -1

    def lte_signal_info(self):
        command = "GET_SIG_INFO"
        self.__write(command)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            power = json_obj[self.lte_module_name]["MSG"]["Power"]
            print("Power {}".format(str(power)))
        except:
            print("Failed to get response!")
            return False, -1

    def lte_check_network(self):
        time_start = time.time()
        command = "+CREG?"
        response = self.lteAt(command)
        network_status = response.split()[1].split(",")[1]
        print(
            "Network Status...{} after {}".format(
                str(network_status), str(time.time() - time_start)
            )
        )
        if int(network_status) == 1:
            return True
        return False

    # Private variables and methods
    __cmdComm = None

    def __write(self, func):
        command = str(self.lte_module_name) + " " + func + "\r\n"
        print("\r\nsending...%s" % command.rstrip())
        self.__cmdComm.send_str(command)

    def __read(self):
        return self.__cmdComm.read_response(self.__cmdComm.DEFAULT_RD_TIMEOUT)

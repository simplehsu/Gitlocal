import json
import time


class fw_update_class(object):
    fw_update_module_name = "FW_UPDATE"

    def __init__(self, arg):
        self.__cmdComm = arg

    def fw_update_WR_MCU_FW_INFO(
        self, img_size, checksum, rawmsg_id, exmem_offset, int_flash_region
    ):
        """

        :param size: Size of fw image
        :param checksum: checksum
        :param rawmsg_id: exmem raw region id
        :param exmem_offset: exmem offset to store fw
        :param int_flash_region: internal flash region
        """
        cmd = (
            "WR_MCU_FW_INFO"
            + " "
            + str(img_size)
            + " "
            + str(checksum)
            + " "
            + str(rawmsg_id)
            + " "
            + str(exmem_offset)
            + " "
            + str(int_flash_region)
        )
        self.__wrte(cmd)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "WR_MCU_FW_INFO READ successful..."
                + str(json_obj[self.fw_update_module_name]["RESULT"])
            )
            return resp
        except:
            print("WR_MCU_FW_INFO READ operation failed\r\n")
            return None

    def fw_update_WR_FW(self, checksum, offset, data, size):
        cmd = "WR_FW" + " " + str(checksum) + " " + str(offset) + " " + str(size)
        self.__write(cmd)

        # ADAM-1662 : Additional checks has been added in Application while writing binary
        # Slow down the data rate
        time.sleep(0.1)
        # Send image
        self.__write_binary(data)
        # Send binary here
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "WR_FW successful..."
                + str(json_obj[self.fw_update_module_name]["RESULT"])
            )
            return resp
        except:
            print("WR_FW READ operation failed\r\n")
            return None

    def fw_updateWR_BLE_DFU_INFO(
        self,
        img_type,
        init_sz,
        init_crc,
        init_exmem_id,
        init_offset,
        fw_sz,
        fw_crc,
        fw_exmem,
        fw_offset,
    ):
        cmd = (
            "WR_BLE_DFU_INFO"
            + " "
            + img_type
            + " "
            + str(init_sz)
            + " "
            + str(init_crc)
            + " "
            + str(init_exmem_id)
            + " "
            + str(init_offset)
            + " "
            + str(fw_sz)
            + " "
            + str(fw_crc)
            + " "
            + str(fw_exmem)
            + " "
            + str(fw_offset)
        )
        print(cmd)
        self.__write(cmd)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "WR_BLE_DFU_INFO successful..."
                + str(json_obj[self.fw_update_module_name]["RESULT"])
            )
            return resp
        except:
            print("WR_BLE_DFU_INFO operation failed\r\n")
            return None

    def fw_updateBLE_DFU(self):
        cmd = "BLE_DFU"
        self.__write(cmd)
        # wait for target reboot
        time.sleep(15)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "BLE_DFU READ successful..."
                + str(json_obj[self.fw_update_module_name]["RESULT"])
            )
            return resp
        except:
            print("BLE_DFU READ operation failed\r\n")
            return None

    def fw_updateXFER_SENSOR(self):
        cmd = "XFER_SENSOR"
        self.__write(cmd)
        resp = self.__read()
        try:
            json_obj = json.loads(resp)
            print(
                "XFER_SENSOR READ successful..."
                + str(json_obj[self.fw_update_module_name]["RESULT"])
            )
            return resp
        except:
            print("XFER_SENSOR READ operation failed\r\n")
            return None

    def __write(self, func):
        command = str(self.fw_update_module_name) + " " + func + "\n"
        print("\r\nsending...%s" % command.rstrip())
        self.__cmdComm.send_str(command)

    def __read(self):
        return self.__cmdComm.read_response(self.__cmdComm.DEFAULT_RD_TIMEOUT)

    def __write_binary(self, data):
        # en_data = data.encode('charmap')
        self.__cmdComm.send_binary(data)

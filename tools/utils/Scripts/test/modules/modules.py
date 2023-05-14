"""Helper class to help with inheritance """
from . import agm_module
from . import ble_module
from . import can_module
from . import gps_module
from . import led_module
from . import lte_module
from . import pm_module
from . import rtc_module
from . import sys_module
from . import temp_module
from . import rs485_module
from . import j1708_module
from . import batt_module
from . import sn_module
from . import atca_module
from . import eeprom_module
from . import tpms_module
from . import qspi_module
from . import fw_update_module


class module_class(
    agm_module.agm_class,
    ble_module.ble_class,
    can_module.can_class,
    gps_module.gps_class,
    led_module.led_class,
    pm_module.pm_class,
    rtc_module.rtc_class,
    sys_module.sys_class,
    temp_module.temp_class,
    lte_module.lte_class,
    rs485_module.rs485_class,
    j1708_module.j1708_class,
    batt_module.batt_class,
    sn_module.sn_class,
    atca_module.atca_class,
    eeprom_module.eeprom_class,
    tpms_module.tpms_class,
    qspi_module.qspi_class,
    fw_update_module.fw_update_class,
):
    def __init__(self, arg):
        agm_module.agm_class.__init__(self, arg)
        lte_module.lte_class.__init__(self, arg)
        ble_module.ble_class.__init__(self, arg)
        can_module.can_class.__init__(self, arg)
        gps_module.gps_class.__init__(self, arg)
        led_module.led_class.__init__(self, arg)
        pm_module.pm_class.__init__(self, arg)
        rtc_module.rtc_class.__init__(self, arg)
        sys_module.sys_class.__init__(self, arg)
        temp_module.temp_class.__init__(self, arg)
        rs485_module.rs485_class.__init__(self, arg)
        j1708_module.j1708_class.__init__(self, arg)
        batt_module.batt_class.__init__(self, arg)
        sn_module.sn_class.__init__(self, arg)
        atca_module.atca_class.__init__(self, arg)
        eeprom_module.eeprom_class.__init__(self, arg)
        tpms_module.tpms_class.__init__(self, arg)
        qspi_module.qspi_class.__init__(self, arg)
        fw_update_module.fw_update_class.__init__(self, arg)

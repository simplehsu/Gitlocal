import time
import serial

devs_to_try = [
    "/dev/ttyACM0",
    "/dev/ttyACM1",
    "/dev/ttyACM2",
    "/dev/ttyACM3",
    "/dev/ttyUSB0",
    "/dev/ttyUSB1",
    "/dev/ttyUSB2",
    "/dev/ttyUSB3",
    "/dev/ttyS0",
    "/dev/ttyS1",
    "/dev/ttyS2",
    "/dev/ttyS3",
]

if __name__ == "__main__":
    """Find and print the device name of serial port connect to an AG-55 running factory_cli"""

    for dev in devs_to_try:
        try:
            ser = serial.Serial(port=dev, baudrate=115200, timeout=0.5)

            # Send the bare FW_UPDATE command and see what shakes out.
            for c in "FW_UPDATE\r\n":
                ser.write(c)
                time.sleep(0.005)  # AG UART can't take the heat at 115K baud

            if ser.read(2024).find("BLE_DFU") >= 0:
                print(dev)
                ser.close()
                break

        except:
            continue

        ser.close()

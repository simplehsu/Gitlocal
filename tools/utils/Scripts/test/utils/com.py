import time
import serial
import sys


class com_class:
    """ Communication class """

    # TimeOuts
    INTER_BYTE_TIMEOUT = 0.001
    DEFAULT_RD_TIMEOUT = 30000

    def __init__(self):
        self.ser = None

    def connect(self, *args):
        """ To establish connection between EVE and the PC """

        # Connect to serial COM port with specified configuration
        try:
            self.ser = serial.Serial(
                port=str(args[0]), baudrate=args[1], timeout=float(args[2])
            )

            # Print Connection Info to user
            print("Connected to EVE")
            print(self.ser)

            # Clear serial port
            self.ser.flushInput()
            self.ser.flushOutput()

        # Ensure EVE console is not busy
        # self.send_str('HELP\r\n')
        # res = self.read_response(com.DEFAULT_RD_TIMEOUT)

        except:
            print("Failed to establish connection with EVE")
            sys.exit()

    def disconnect(self):
        """ Disconnects the connection between EVE and the PC """
        self.ser.close()
        print("Disconnected")

    def send_str(self, string):
        """ Send String """
        # Wait for sometime to flush unread data
        time.sleep(0.1)
        self.ser.flushInput()  # Flush input buffer

        for data in string:  # Read Byte from String
            data = data.encode("charmap")  # Encode Byte
            self.ser.write(data)  # Send Byte
            time.sleep(self.INTER_BYTE_TIMEOUT)  # Wait for Timeout

    def read_response(self, timeout):
        """ Read Response """
        #        time.sleep(0.1)
        self.ser.timeout = timeout  # Configure Serial timeout
        localEcho = self.ser.readline()  # To omit local echo, read a line here

        # Read entire data
        line = self.ser.read_until(b"\n$")

        # Debug output of printERRORs  TODO: Add logging
        # if line.startswith("[E 20"):
        #    print(line)

        line = line.decode("charmap")
        if "$" in line:
            line = line[:-1].strip()  # Remove '$'
        location = line.find("{")
        line = line[location:]
        return line

        # while True:
        #     line += self.ser.read()
        #     if '$' in line:
        #         line=line[:-1]                      # Remove '$'
        #         #print(line)
        #         return line

    def raw_read(self, timeout, read_until):
        """ Raw Read console """

        self.ser.timeout = timeout  # Configure Serial timeout
        data = []
        data.append(self.ser.read_until(read_until))
        return b"".join(data).decode("utf8")

    def send_binary(self, binary):
        """ Send binary image """
        for data in binary:  # Read Byte from String
            # print '%x' % ord(data)
            data = data.encode("charmap")
            self.ser.write(data)
            self.ser.flushOutput()

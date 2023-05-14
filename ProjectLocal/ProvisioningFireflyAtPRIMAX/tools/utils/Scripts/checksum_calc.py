# -*- coding: UTF-8 -*-
"""
/**===========================================================================
 * @file   checksum_calc.py
 * @date   05-April-2019
 * @author nishal.r@pathpartnertech.com
 *
 * @brief  Python script to find checksum for a given file
 *
 *============================================================================
 *
 * Copyright � 2019, KeepTruckin, Inc.
 * All rights reserved.
 *
 * All information contained herein is the property of KeepTruckin Inc. The
 * intellectual and technical concepts contained herein are proprietary to
 * KeepTruckin. Dissemination of this information or reproduction of this
 * material is strictly forbidden unless prior written permission is obtained
 * from KeepTruckin.
 *
 *===========================================================================
 */
"""

import sys

# Number of bytes to send in one shot
CHUNK_SIZE = 1024  # 1 KB


def calculate_checksum(bin_file):
    """ Calculate simple checksum to validate a binary file """

    # Open Binary file
    binary = open(bin_file, "rb")
    checksum = 0
    size = 0
    while True:  # Calculate CheckSum and Size
        binary_data = binary.read(CHUNK_SIZE)  # Try reading 'CHUNK_SIZE' bytes
        if not binary_data:  # Break if nothing is read
            break
        binary_data = binary_data.decode("charmap")

        checksum += sum(map(ord, binary_data))  # Update CheckSum
        size += len(binary_data)  # Update Size

    # Close bin file
    binary.close()
    print("File                 : " + bin_file)
    print("Checksum [Decimal]   : " + str(checksum))
    print("Checksum [HEX]       : " + hex(checksum))
    print("File Size [Decimal]  : " + str(size))
    print("File Size [HEX]      : " + hex(size))

    print("Done")


if __name__ == "__main__":

    # Check for Arguments
    if len(sys.argv) < 2:
        # Print Error Message
        print("\nError: Insufficient Arguments")
        # Print Usage Information
        print("Expected  Firmware binary filename as arguments")
        sys.exit()

    # calculate checksum
    calculate_checksum(sys.argv[1])

#!/usr/bin/env python3

"""
FPGA register access demonstration.
Copyright (c) 2022 Pascal Stang
This program comes with ABSOLUTELY NO WARRANTY.
"""

import fpgacomm
import logging

PORT = '/dev/ttyUSB0'

def main():
  # Create instance.
  # Set a high logging level so we can see our operations.
  fc = fpgacomm.fpgacomm( serialport=PORT,
                          baudrate=115200,
                          addrchars=8,
                          datachars=8,
                          loglevel=logging.DEBUG)
  # Open the channel to the FPGA.
  fc.open()
  # Do some operations.
  data = fc.regRead(0x40000000)
  data = fc.regRead(0x40000001)
  data = fc.regRead(0x40000002)
  data = fc.regRead(0x40000003)
  fc.regWrite(0x40000024, 0xF5)
  fc.regWrite(0x40000024, 0xD5)
  fc.regWrite(0x40000024, 0xC5)
  fc.regWrite(0x40000024, 0x05)
  # Close the channel.
  fc.close()

if __name__ == '__main__':
  main()

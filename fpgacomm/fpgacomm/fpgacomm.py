#!/usr/bin/env python3

"""
FPGA register access module via UART.
Copyright (c) 2018-2021 Pascal Stang
This program comes with ABSOLUTELY NO WARRANTY.

This module provides read/write methods for FPGA register access over UART.
The module can also be run as a console tool, invoke with no arguments for
usage help.

TODO: Convert argument processing to argparse, no excuse for not using it.

Example Usage:

  import fpgacomm
  import logging

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
  # Close the serial channel.
  fc.close()
"""

import logging
import serial
import sys
import time

class fpgacomm:
  def __init__(self, serialport, baudrate=115200, addrchars=8, datachars=8, loglevel=logging.ERROR):
    self._ser = serial.Serial()
    self._ser.port = serialport
    self._ser.baudrate = baudrate
    self._ser.timeout = 0.1
    self._addrchars = addrchars
    self._datachars = datachars
    logging.basicConfig(format = '%(levelname)s:%(name)s:%(message)s', level=loglevel)
    self._log = logging.getLogger(__name__)

  def open(self):
    """Open the communication port."""
    self._ser.open()

  def close(self):
    """Close the communication port."""
    self._ser.close()

  def serialWrite(self, string):
    """Write string to serial device."""
    # Send characters with 10ms delay between each.
    # This time allowance not required after implementing FPGA fix.
    self._log.debug("Serial Tx: \'{:s}\'".format(string))
    for c in string:
      self._ser.write(c.encode())
      time.sleep(0.01)
    return

  def serialRead(self, maxchars):
    """Read string from serial device."""
    string = self._ser.read(maxchars).decode('utf-8')
    self._log.debug("Serial Rx: \'{:s}\'".format(string))
    return string

  def regWrite(self, addr, data):
    """Write FPGA register at <addr> to value <data>, returns <data> or None."""
    # Compose and send the operation, read the reply.
    # Example: wAAAADDDDDDDD
    wrstr = "w{addr:0{addrchars}X}{data:0{datachars}X}".format(
      addr=addr, addrchars=self._addrchars,
      data=data, datachars=self._datachars)
    self.serialWrite(wrstr)
    rdstr = self.serialRead(1+self._addrchars+self._datachars+2+1)
    # Verify that the command was echoed, otherwise the operation failed.
    if wrstr in rdstr:
      wrdata = data
    else:
      wrdata = None;
    # Do debug.
    self._log.info("Addr 0x{:08X} write value 0x{:08X} => {:s}".format(
        addr, data, ['FAILED', 'OK'][wrdata == data]))
    return wrdata

  def regRead(self, addr):
    """Read FPGA register at <addr>, returns <data> or None."""
    # Compose and send the operation, read the reply.
    # Example: rAAAADDDDDDDD
    wrstr = "r{addr:0{addrchars}X}".format(
      addr=addr, addrchars=self._addrchars)
    self.serialWrite(wrstr)
    rdlen = 1+self._addrchars+self._datachars+2+1;
    rdstr = self.serialRead(rdlen)
    # Verify that the command was echoed, otherwise the operation failed.
    # Also parse the reply.
    data = None
    if ((len(rdstr) >= rdlen) and (rdstr[0] == 'r')):
      if (int(rdstr[1:1+self._addrchars], 16) == addr):
        data = int(rdstr[1+self._addrchars:1+self._addrchars+self._datachars], 16)
    # Do debug.
    if data is not None:
      self._log.info("Addr 0x{:08X} read  value 0x{:08X} => {:s}".format(
        addr, data, 'OK'))
    else:
      self._log.info("Addr 0x{:08X} read => {:s}".format(
        addr, 'FAILED'))
    return data

def mainHelp():
  print('  Usage: fpgacomm [serport] [regaddr] {write value}')
  print(' Examples:')
  print('   read: fpgacomm /dev/ttyUSB0 0x40000000')
  print('  write: fpgacomm /dev/ttyUSB0 0x40000000 0xFF')

def main():
  # Parse the arguments.
  if(len(sys.argv) <= 1):
    mainHelp()
    exit()

  # Create fpgacomm instance.
  fc = fpgacomm(serialport=sys.argv[1],
                baudrate=115200,
                addrchars=8,
                datachars=8,
                loglevel=logging.DEBUG)

  # Open the port.
  fc.open()

  # Perform the operation.
  if (len(sys.argv) == 3):
    arg_addr = int(sys.argv[2], 0)
    data = fc.regRead(arg_addr)
    if (data != None):
      print("Addr 0x{:08X} read  value 0x{:08X} => OK".format(arg_addr, data))
    else:
      print("Addr 0x{:08X} read => FAILED".format(arg_addr))
  elif (len(sys.argv) == 4):
    arg_addr = int(sys.argv[2], 0)
    arg_data = int(sys.argv[3], 0)
    data = fc.regWrite(arg_addr, arg_data)
    print("Addr 0x{:08X} write value 0x{:08X} => {:s}".format(
      arg_addr, arg_data, ['FAILED', 'OK'][data == arg_data]))
  else:
    print('No operation specified.')
    mainHelp()

  # Close the port.
  fc.close()

if __name__ == '__main__':
  main()


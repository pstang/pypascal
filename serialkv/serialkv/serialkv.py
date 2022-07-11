#!/usr/bin/env python3

"""
Serial Key-Value reader.
Copyright (c) 2020-2022 Pascal Stang
This program comes with ABSOLUTELY NO WARRANTY.

The module can also be run as a console tool, invoke with no arguments for
usage help.

Example Usage:

  import serialkv

  PORT = '/dev/ttyUSB0'

  # Create instance.
  skv = serialkv.serialkv(serialport=PORT,
                          baudrate=115200)
  # Open communication.
  skv.open()

  # Do a read.
  kvdict = skv.read()

  # Close communication.
  skv.close()
"""

# system
import argparse
import logging
import serial
import sys
import time

class serialkv:
  def __init__(self, serialport, baudrate=9600, timeout=2, line_terminator=b'\r', loglevel=logging.ERROR):
    self._ser = serial.Serial()
    self._ser.port = serialport
    self._ser.baudrate = baudrate
    self._ser.timeout = timeout
    self._ser.line_terminator = line_terminator
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
    self._log.debug("Serial Tx: \'{:s}\'".format(string))
    self._ser.write(string.encode())
    return

  def serialRead(self, maxchars):
    """Read string from serial device."""
    #string = self._ser.read(maxchars).decode('utf-8')
    string = self._ser.read_until(self._ser.line_terminator)
    string = string.decode('utf-8')
    self._log.debug("Serial Rx: \'{:s}\'".format(string))
    return string

  def read(self):
    """
    Read key-value string from the serial port and return dict.
    :return dict of keys-values, or None if unsuccessful
    :rtype: dict
    """
    # Read serial port.
    rxstring = self.serialRead(1024)
    kvdict = self.parse(rxstring)
    return kvdict

  def parse(self, kvstring):
    # Example 'PD0:123 PD1:456 PD2:222 PD3:333'
    kvdict = {}
    # Strip off any <CR><LF> or extra whitespace.
    kvstring = str(kvstring).strip()
    # Then split the space-separated fields.
    kvstrarray = kvstring.split(' ')
    # Try to convert each field to int, or float, or leave as string
    for k in kvstrarray:
      try:
        (key,value) = k.split(':')
      except ValueError:
        return None
      try:
        kvdict[key] = int(value)
      except ValueError:
        try:
          kvdict[key] = float(value)
        except ValueError:
          kvdict[key] = value
          pass
    # Print parsed data.
    self._log.debug("Parse {:}".format(kvdict))
    return kvdict

def test():
  kvdict = skv.parse('PD0:123 PD1:456 PD2:222 PD3:333\r\n')
  print(kvdict)
  kvdict = skv.parse(':123 PD1:456 PD2:222 PD3:333\r\n')
  print(kvdict)
  kvdict = skv.parse('123 PD1:456 PD2:222 PD3:333\r\n')
  print(kvdict)

def main():
  # Parse the arguments.
  parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='Serial Key-Value Read Utility.',
    epilog= 'Examples:\n' +
            '  serialkv /dev/ttyUSB0\n'
            '  serialkv /dev/ttyUSB0 --log DEBUG\n')
  parser.add_argument('device', metavar='device', type=str,
                      help='serial port of the PTU')
  parser.add_argument('--debug', dest='loglevel', action='store_const',
                      const='DEBUG', default=None,
                      help='produce debugging output (like --log DEBUG)')
  parser.add_argument('--log', dest='loglevel', type=str, default=None,
                      help='set log level',
                      choices=['DEBUG','INFO','ERROR'])
  args = parser.parse_args()

  # Create instance and run operation.
  skv = serialkv(args.device, baudrate=115200, loglevel=args.loglevel)
  skv.open()
  kvdict = skv.read()
  skv.close()
  print(kvdict)

if __name__ == '__main__':
  main()

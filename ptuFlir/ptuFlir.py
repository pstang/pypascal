#!/usr/bin/env python3

"""
FLIR PTU E-series control library.
Copyright (c) 2020-2021 Pascal Stang
This program comes with ABSOLUTELY NO WARRANTY.

This module provides simple control of FLIR E-series Pan-Tilt Units (PTUs).
Supported devices include:
  - PTU-E46
  - PTU-D48 E-series
  - PTU-D100 E-series
  - PTU-D300 E-series

The module can also be run as a console tool, invoke with no arguments for
usage help.

TODO(pstang): Expand to also support network TCP access.

Example Usage:

  import ptuFlir

  PORT = '/dev/ttyUSB0'

  # Create instance.
  ptu = ptuFlir.ptu(serialport=PORT,
                    baudrate=115200)
  # Open communication to the PTU.
  ptu.open()

  # Do some operations.
  ptu.command(cmd='RE')
  ptu.setPanTiltNative(1000,200)
  print(ptu.getPanTiltNative())
  ptu.setPanTiltNative(-1000,-200)
  print(ptu.getPanTiltNative())
  ptu.setPanTiltNative(0,0)
  print(ptu.getPanTiltNative())

  # Close communication to the PTU.
  ptu.close()
"""

# system
import argparse
import logging
import parse
import serial
import socket
import sys
import time

class ptu:
  def __init__(self, serialport, baudrate=9600, timeout=5, loglevel=logging.ERROR):
    self._ser = serial.Serial()
    self._ser.port = serialport
    self._ser.baudrate = baudrate
    self._ser.timeout = timeout
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
    string = self._ser.read_until(b'\n')
    string = string.decode('utf-8')
    self._log.debug("Serial Rx: \'{:s}\'".format(string))
    return string

  def operation(self, operation):
    """
    Perform an operation on the PTU.
    :param str operation: the operation string
    :return (success, reply) where
      success bool: whether the command was successful
      reply str: the reply string from the PTU
    :rtype: tuple
    """
    # Send operation.
    self._log.debug("Sending operation: \'{:s}\'".format(operation))
    txstring = operation + ' '
    self.serialWrite(txstring)
    # Use brief delay to allow device to respond.
    #time.sleep(0.05)
    # Capture the recevied data from session.
    rxstring = self.serialRead(1024)
    # Strip off <CR><LF>
    rxstring = str(rxstring).strip()
    # Verify that the operation was echoed, otherwise the operation failed.
    success = False
    reply = None
    if rxstring.startswith(txstring):
      # Strip off echoed command to get reply.
      #reply = rxstring.rstrip(txstring)
      reply = rxstring.replace(txstring, '')
      #print("REPLY: " + reply)
      if reply[0] is '*':
        success = True
    # Print data received.
    self._log.debug("Received reply: \'{:s}\' => {:s}".format(reply, ['FAILED', 'OK'][success]))
    return (success, reply)

  def command(self, cmd, args=[]):
    """
    Perform a command on the PTU.
    :param str cmd: the command string, e.g. 'PP'
    :param list args: the argument list, e.g. [5000]
    :return: whether the command was successful
    :rtype: bool
    """
    opstr = "{:s}".format(cmd)
    for arg in args:
      opstr = opstr + "{:d}".format(arg)
    (success, reply) = self.operation(opstr)
    self._log.info("command: {:s} => {}".format(opstr, ['FAILED', 'OK'][success]))
    return success

  def queryParse(query_string):
    query_result = None
    # There is no regular guaranteed query result format.
    # Could also do this parsing with parse() or re.
    if query_string.startswith('* Current Pan position is '):
      query_string = query_string.replace('* Current Pan position is ', '')
      query_result = (int(query_string))
    elif query_string.startswith('* Current Tilt position is '):
      query_string = query_string.replace('* Current Tilt position is ', '')
      query_result = (int(query_string))
    return query_result

  def query(self, cmd):
    """
    Perform a query on the PTU.
    :param str cmd: the command string, e.g. 'PP'
    :return: query result as a list
    :rtype: tulpe
    """
    opstr = "{:s}".format(cmd)
    (success, reply) = self.operation(opstr)
    query_result = None
    if success is True:
      # Parse query result
      query_result = ptu.queryParse(reply)
    self._log.info("query: {:s} => {}".format(cmd, query_result))
    return query_result

  def setPanTiltNative(self, pan, tilt):
    """Point PTU to requested pan and tilt (native units)."""
    # Compose and send the operation.
    success = self.command(cmd='S')
    success = self.command(cmd='PP', args=[pan])
    success = self.command(cmd='TP', args=[tilt])
    success = self.command(cmd='A')
    self._log.info("setPanTiltNative: pan={:d} tilt={:d} => {:s}".format(pan, tilt, ['FAILED', 'OK'][success]))
    return success

  def getPanTiltNative(self):
    """Get current PTU pan and tilt position (native units)."""
    # Compose and send the operation.
    pan = self.query(cmd='PP')
    tilt = self.query(cmd='TP')
    self._log.info("getPanTiltNative: pan={:d} tilt={:d}".format(pan, tilt))
    return (pan, tilt)

  def setPanTilt(self, pan, tilt):
    """Point PTU to requested pan and tilt (radians)."""
    # Compose and send the operation.
    success = self.pointPanTilt(pan, tilt)
    self._log.info("pointPanTilt: pan={:f} tilt={:f} => {:s}".format(pan, tilt, ['FAILED', 'OK'][success]))
    return success

  def setAzEl(self, azimuth, elevation):
    """Point PTU to requested Azimuth and Elevation (radians)."""
    # Compose and send the operation.
    success = self.pointPanTilt(azimuth, elevation)
    self._log.info("pointAzEl: az={:f} el={:f} => {:s}".format(azimuth, elevation, ['FAILED', 'OK'][success]))
    return success

def main():
  # Parse the arguments.
  parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='FLIR PTU E-series Control Utility.',
    epilog= 'Examples:\n' +
            '  ptuFlir /dev/ttyUSB0 PP 1000\n' +
            '  ptuFlir /dev/ttyUSB0 TP -200\n')
  parser.add_argument('device', metavar='device', type=str,
                      help='serial port of the PTU')
  parser.add_argument('cmd', metavar='command', type=str,
                      help='command/query to issue')
  parser.add_argument('args', metavar='args', nargs='?', type=int,
                      default=None,
                      help='command argument')
  parser.add_argument('--debug', dest='loglevel', action='store_const',
                      const='DEBUG', default=None,
                      help='produce debugging output (like --log DEBUG)')
  parser.add_argument('--log', dest='loglevel', type=str, default=None,
                      help='set log level',
                      choices=['DEBUG','INFO','ERROR'])
  args = parser.parse_args()

  # Create PDU and run operation.
  ptuInst = ptu(args.device, baudrate=115200, loglevel=args.loglevel)
  ptuInst.open()
  if args.args is None:
    ptuInst.query(cmd=args.cmd)
  else:
    ptuInst.command(cmd=args.cmd, args=[args.args])
  ptuInst.close()

if __name__ == '__main__':
  main()

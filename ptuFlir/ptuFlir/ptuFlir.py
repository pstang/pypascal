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
import math
import logging
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
    self.deviceInit()

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

  def deviceInit(self):
    """Initialize PTU for operations."""
    # Query information about the PTU.
    self._ptu_version = self.query('VV')
    self._ptu_model = self.query('VM')
    self._ptu_serialnumber = self.query('VS')
    # Set PTU to terse feedback mode.
    self.command('FT')
    # Get parameters.
    self.getLimitsNative()
    self.getResolution()

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
    # Example '* 24.9,91,84,84'
    query_result = None
    # With verbose feedback, there is no regular guaranteed query result format.
    # At open time, we set the feedback to terse.
    # This permits parsing fields with split.
    # First drop the '* '.
    query_string = query_string.replace('* ', '')
    # Then split CSV fields.
    query_result = query_string.split(',')
    # Try to convert each field to int, or float, or leave as string
    for n, v in enumerate(query_result):
      try:
        query_result[n] = int(query_result[n])
      except ValueError:
        try:
          query_result[n] = float(query_result[n])
        except ValueError:
          pass
    # TODO(pstang): Could probably do the above in a more pythonic way with map
    # and a type converter.
    #query_result = list(map(int, query_result))
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

  def setPositionNative(self, pan, tilt):
    """Point PTU to requested pan and tilt (native units)."""
    # Compose and send the operation.
    success = self.command(cmd='S')
    success = self.command(cmd='PP', args=[pan])
    success = self.command(cmd='TP', args=[tilt])
    success = self.command(cmd='A')
    self._log.info("setPositionNative: pan={:d} tilt={:d} => {:s}".format(pan, tilt, ['FAILED', 'OK'][success]))
    return success

  def getPositionNative(self):
    """Get current PTU pan and tilt position (native units)."""
    # Compose and send the operation.
    pan = self.query(cmd='PP')[0]
    tilt = self.query(cmd='TP')[0]
    self._log.info("getPositionNative: pan={:d} tilt={:d}".format(pan, tilt))
    return (pan, tilt)

  def getLimitsNative(self):
    """Get PTU pan and tilt limits (native units)."""
    # Compose and send the operation.
    self._ptu_pan_limit = (self.query('PN')[0], self.query('PX')[0])
    self._ptu_tilt_limit = (self.query('TN')[0], self.query('TX')[0])
    self._log.info("getLimitsNative: pan={:} tilt={:}".format(
      self._ptu_pan_limit, self._ptu_tilt_limit))
    return (self._ptu_pan_limit, self._ptu_tilt_limit)

  def getResolution(self):
    """Get current PTU pan and tilt resolution (radians/native unit)."""
    # Compose and send the operation.
    # Query returns arc-seconds per step. 1arc-sec * pi/(180 * 3600)
    self._ptu_pan_resolution = self.query(cmd='PR')[0] * math.pi / (180 * 3600)
    self._ptu_tilt_resolution = self.query(cmd='TR')[0] * math.pi / (180 * 3600)
    self._log.info("getResolution: pan={:f} tilt={:f}".format(self._ptu_pan_resolution, self._ptu_tilt_resolution))
    return (self._ptu_pan_resolution, self._ptu_tilt_resolution)

  def setPositionRadians(self, pan, tilt):
    """Point PTU to requested pan and tilt (radians)."""
    # Compose and send the operation.
    pan_native = int(pan / self._ptu_pan_resolution)
    tilt_native = int(tilt / self._ptu_tilt_resolution)
    success = self.setPositionNative(pan_native, tilt_native)
    self._log.info("setPositionRadians: pan={:f} tilt={:f} => {:s}".format(pan, tilt, ['FAILED', 'OK'][success]))
    return success

  def setPositionDegrees(self, pan, tilt):
    """Point PTU to requested pan and tilt (degrees)."""
    # Compose and send the operation.
    pan_radians = (pan * math.pi / 180)
    tilt_radians = (tilt * math.pi / 180)
    success = self.setPositionRadians(pan_radians, tilt_radians)
    self._log.info("setPositionDegrees: pan={:f} tilt={:f} => {:s}".format(pan, tilt, ['FAILED', 'OK'][success]))
    return success

  def setPositionAzEl(self, azimuth, elevation):
    """Point PTU to requested Azimuth and Elevation (radians)."""
    # Compose and send the operation.
    success = self.setPositionRadians(azimuth, elevation)
    self._log.info("setPositionAzEl: az={:f} el={:f} => {:s}".format(azimuth, elevation, ['FAILED', 'OK'][success]))
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

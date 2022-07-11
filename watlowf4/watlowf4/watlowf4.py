#!/usr/bin/env python3

"""
Watlow F4 Temperature Controller driver library.
Copyright (c) 2015-2022 Pascal Stang
This program comes with ABSOLUTELY NO WARRANTY.

This module provides simple synchronous access to Watlow F4/F4T Temperature
Controllers, including reading/writing setpoint and querying current
temperature.

The Watlow F4/F4T is a digital controller commonly used on thermal
chambers, ovens, and other closed-loop thermal control applications.
Communication between the Watlow F4 and a host machine can be over serial port
or ethernet, with both interfaces complying to the ModBus standard.

The library currently only supports serial port interface.

This module can also be run as a console tool, invoke with no arguments for
usage help.

Example Usage:

  import watlowf4

  SERIAL = '/dev/ttyUSB0'

  # Create library instance for the device.
  wf4 = watlowf4.watlowf4(device=SERIAL)
  # Open communications.
  wf4.open()
  # Do operations.
  targetC = 25.0
  print("Setting Temp Setpoint to {:} C".format(targetC))
  wf4.setTemperatureSetpoint(targetC)
  print("Temp Setpoint = {:} C".format(wf4.getTemperatureSetpoint()))
  print("Current Temp  = {:} C".format(wf4.getTemperature()))
  # Close communications.
  wf4.close()
"""

# system
import argparse
import logging
import serial
import socket
import sys
import time
# package
#from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.client.sync import ModbusSerialClient as ModbusClient


class watlowf4:
  def __init__(self, device, baudrate=9600, loglevel=logging.ERROR):
    self._device = device
    self._baudrate = baudrate
    logging.basicConfig(format = '%(levelname)s:%(name)s:%(message)s', level=loglevel)
    self._log = logging.getLogger(__name__)

  def open(self):
    """
    Open communications with the controller.
    """
    self._client = ModbusClient(method='rtu',
                                port='/dev/ttyUSB0',
                                baudrate=self._baudrate,
                                parity='N',
                                stopbits=2,
                                timeout=1)
    v = self._client.connect()
    self._log.debug('Open client: ' + str(v))
    self._client.debug_enabled()

  def close():
    """
    Close communications with the controller.
    """
    v = self._client.disconnect()
    self._log.debug('Close client: ' + str(v))

  def tempCtoRegister(tempC):
    """
    Convert temperature in Celcius to Watlow register value.
    """
    # WatlowF4 uses integer deci-degrees.
    regvalue = int(tempC * 10.0) & 0xFFFF
    return regvalue

  def registerToTempC(regvalue):
    """
    Convert Watlow register value to temperature in Celcius.
    """
    # If regvlaue has sign bit set, convert to negative number.
    if regvalue & 0x8000:
      regvalue = regvalue - 0x10000
    # Convert from deci-degrees
    tempC = regvalue / 10.0
    return tempC

  def getTemperature(self):
    """
    Get the current temperature measurement (in degC).
    """
    response = self._client.read_holding_registers(
      address=100, count=1, unit=1)
    tempC = watlowf4.registerToTempC(response.registers[0])
    self._log.debug("getTemperature: {:0.1f} C".format(tempC))
    return T

  def getTemperatureSetpoint(self):
    """
    Get the temperature controller setpoint (in degC).
    """
    response = self._client.read_holding_registers(
      address=300, count=1, unit=1)
    tempC = watlowf4.registerToTempC(response.registers[0])
    self._log.debug("getTemperatureSetpoint: {:0.1f} C".format(tempC))
    return tempC

  def setTemperatureSetpoint(self, tempC):
    """
    Set the temperature controller setpoint (in degC).
    """
    self._log.debug("setTemperatureSetpoint: {:0.1f} C".format(tempC))
    regvalue = watlowf4.tempCtoRegister(tempC)
    response = self._client.write_register(
      address=300, value=regvalue, unit=1)
    return tempC

class StoreNameValuePair(argparse.Action):
  def __call__(self, parser, namespace, values, option_string=None):
    if values is not None:
      try:
        name, value = values.split('=', 1)
        setattr(namespace, name, value)
      except ValueError:
        print("Argument '{:s}' must be of form key=value".format(values))

def main():
  # Parse the arguments.
  parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='watlowF4 Control Utility.',
    epilog= 'Examples:\n' +
            '  watlowf4 /dev/ttyUSB0 setpoint=50\n' +
            '  watlowf4 /dev/ttyUSB0 setpoint=?\n' +
            '  watlowf4 /dev/ttyUSB0 temperature=?\n')
  parser.add_argument('device', metavar='device', type=str,
                      help='tty/serial device connected to Watlow controller')
  parser.add_argument('baudrate', metavar='baudrate', type=str, nargs='?',
                      default=9600, action=StoreNameValuePair,
                      help='serial port baud rate (in bps)')
  parser.add_argument('setpoint', metavar='setpoint', type=str, nargs='?',
                      action=StoreNameValuePair,
                      help='get/set the temperature setpoint')
  parser.add_argument('temperature', metavar='temperature', type=str, nargs='?',
                      action=StoreNameValuePair,
                      help='get the current temperature')
  parser.add_argument('--debug', dest='loglevel', action='store_const',
                      const='DEBUG', default=None,
                      help='produce debugging output (like --log DEBUG)')
  parser.add_argument('--log', dest='loglevel', type=str, default=None,
                      help='set log level',
                      choices=['DEBUG','INFO','ERROR'])
  args = parser.parse_args()

  # Create instance and run operation.
  wf4 = watlowf4(args.device, loglevel=args.loglevel)
  wf4.open()
  if args.setpoint in ['?']:
    print('getTemperatureSetpoint() = {:}'.format(wf4.getTemperatureSetpoint()))
  elif args.setpoint is not None:
    print('setTemperatureSetpoint({:f})'.format(float(args.setpoint)) )
    wf4.setTemperatureSetpoint(float(args.setpoint))

  if args.temperature in ['?']:
    print('getTemperature() = {:}'.format(wf4.getTemperature()))
  wf4.close()

if __name__ == '__main__':
  main()

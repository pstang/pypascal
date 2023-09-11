#!/usr/bin/env python3

"""
RF Switch control library for MiniCircuits RC/USB Series.
Copyright (c) 2017-2023 Pascal Stang
This program comes with ABSOLUTELY NO WARRANTY.

This module provides simple control of RF switches.
Supported devices include:
  - MiniCircuits RC-Series switches
  - MiniCircuits USB-Series switches

Supported interfaces include:
  - Ethernet (Telnet)
  - USB (USB HID class)

NOTE: USB access may require udev rule updates for device permissions.
  For example, in /etc/udev/rules.d/50-myusb.rules:
    # MiniCircuits USB Controller
    SUBSYSTEMS=="usb", ATTRS{idVendor}=="20ce", ATTRS{idProduct}=="0022" GROUP="users", MODE="0666"

NOTE: This library uses SCPI commands to talk to the switch. Old firmwares
  that do not support SCPI will not work with this libary. It is surprisingly
  challenging to easily suppport a wide variety of MiniCircuits switches and
  firmwares because early switches used only a USB binary protocol, followed
  by switches that supported string-based SCPI commands over Telnet but not
  over USB interface on the same device, and then finally SCPI over both USB
  and Telnet.

TODO(pstang): Support multiple USB devices via 'usb:[serial]'

The module can also be run as a console tool, invoke with no arguments for
usage help.

Example Usage:

  import rfswitchMcl

  DEVICE = '192.168.1.100'
    or
  DEVICE = 'usb'

  # Create instance.
  rfsw = rfswitchMcl.rfswitch(device=DEVICE),
  # Open communications.
  rfsw.open()

  # Do some operations.
  # You can use letter or number arguments for switch.
  rfsw.set(switch='A', state=1)
  rfsw.set(switch='B', state=1)
  time.sleep(1)
  rfsw.set(switch=0, state=0)
  rfsw.set(switch=1, state=0)

  # Get state.
  print(rfsw.get(switch='A'))
  print(rfsw.get(switch=1))

  # Close communication.
  rfsw.close()
"""

# system
import argparse
import logging
import parse
import socket
import sys
import time
import usb.core
import usb.util


class rfswitch:
  NET_OPERATION_TERMINATOR = '\r\n'
  NET_REPLY_TERMINATOR = '\n\r'
  USB_ENDPOINT_WRITE = 0x01
  USB_ENDPOINT_READ = 0x81

  def __init__(self, device, switch=None, loglevel=logging.ERROR):
    self._device = device
    self._port = 23
    self._switch = switch
    logging.basicConfig(format = '%(levelname)s:%(name)s:%(message)s', level=loglevel)
    self._log = logging.getLogger(__name__)

  def open(self):
    """Open the communication port."""
    # Prepare the USB device access.
    # (Ethernet does not require any initialization.)
    if self._device.startswith('usb'):
      # USB connection approach taken from MiniCircuits examples.
      self._devUsb = usb.core.find(idVendor=0x20CE, idProduct=0x0022)
      if self._devUsb is None:
        raise ValueError('USB device not found')
      for configuration in self._devUsb:
        for interface in configuration:
          ifnum = interface.bInterfaceNumber
          if not self._devUsb.is_kernel_driver_active(ifnum):
            continue
          try:
            self._devUsb.detach_kernel_driver(ifnum)
          except (usb.core.USBError):
            pass
      # Set the active configuration.
      # No args selects the first config.
      self._devUsb.set_configuration()
    # Query and initialize the RF switch.
    self.deviceInit()

  def close(self):
    """Close the communication port."""
    pass

  def deviceInit(self):
    """Initialize the RF switch operations."""
    # Query information about the device.
    self.model = self.query('MN')[1]
    self.serialnumber = self.query('SN')[1]
    # Extract characteristics of the device from model numnber.
    # TODO(pstang): This is works over limited cases, needs improvement.
    # Examples:
    #   RC-2SP6T-A12
    #   USB-8SPDT-A18
    #   USB-1SP8T-852H
    if self.model.startswith("RC"):
      fields = parse.parse("RC-{switches:d}{poles:l}P{states:d}T-{type}", self.model)
    elif self.model.startswith("USB"):
      fields = parse.parse("USB-{switches:d}{poles:l}P{states:d}T-{type}", self.model)
    else:
      raise ValueError('Unsupported HW model')
    self.switches = fields['switches']
    self.poles = fields['poles']
    self.states = fields['states']
    self._log.info("RF Switch \'{:s}\' has: {} switches, {} poles, {} states".format(
      self.model, self.switches, self.poles, self.states))

  def operationNet(self, operation):
    # Examples:
    #  'MN?\r\n'           => '\r\nMN=RC-2SP6T-A12\n\r'
    #  'SN?\r\n'           => '\r\nSN=11710240017\n\r'
    #  'SP6TA:STATE:1\r\n' => '\r\n1\n\r'
    # Open TCP socket to device.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
      sock.connect((str(self._device), int(self._port)))
    except:
      self._log.error("Connection to {:s} FAILED".format(str(self._device)))
      return (False, "")
    # Send operation.
    txstring = operation + self.NET_OPERATION_TERMINATOR
    self._log.debug("SendingStr: \'{:}\'".format(txstring))
    sock.send(txstring.encode('utf-8'))
    # Send logout command to gracefully close socket connection.
    #sock.send('logout\r'.encode('utf-8'))
    # Use brief delay to allow device to respond.
    time.sleep(0.05)
    # Capture the recevied data from session.
    rxstring = sock.recv(1024)
    rxstring = rxstring.decode()
    sock.close()
    self._log.debug("ReceivedStr: \'{:}\'".format(rxstring))
    # Verify that the operation is framed, otherwise the operation failed.
    success = False
    reply = None
    if rxstring.startswith(self.NET_OPERATION_TERMINATOR):
      if rxstring.endswith(self.NET_REPLY_TERMINATOR):
        # Strip off <CR><LF>
        rxstring = rxstring.strip()
        # Some replies already include CMD=REPLY.
        if '=' in rxstring:
          reply = rxstring
        else:
          reply = operation + '=' + rxstring
        success = True
    return (success, reply)

  def operationUsb(self, operation):
    # Examples:
    #  '*:MN?'          => '*USB-1SP8T-852H'
    #  '*:SN?'          => '*12308130012'
    #  '*:SP8T:STATE:0' => '*0' (failed)
    #  '*:SP8T:STATE:1' => '*1' (success)
    #  '*:SP8T:STATE:2' => '*2' (success)
    txstring = "*:" + operation
    self._log.debug("SendingStr: \'{:}\'".format(txstring))
    self._devUsb.write(self.USB_ENDPOINT_WRITE, txstring)
    rxdata = self._devUsb.read(self.USB_ENDPOINT_READ, 64)
    rxstring = ""
    for byte in rxdata:
      if (byte > 0 and byte < 255):
        rxstring = rxstring + chr(byte)
      else:
        break
    self._log.debug("ReceivedStr: \'{:}\'".format(rxstring))
    # Verify that the operation is framed, otherwise the operation failed.
    success = False
    reply = None
    if rxstring.startswith(txstring[0]):
      rxstring = rxstring[1:]
      reply = operation + '=' + rxstring
      success = True
    return (success, reply)

  def operationUsbBinary(self, operation):
    # This function is an attempt to support older firmware with binary-only
    # commands.
    # Examples:
    #  '(' => 'RC-2SP6T-A12'
    #  ')' => '11710240017'
    if operation == 'MN?':
      txstring = '('
    elif operation == 'SN?':
      txstring = ')'
    else:
      txstring = "*:" + operation
    self._log.debug("SendingStr: \'{:}\'".format(txstring))
    self._devUsb.write(self.USB_ENDPOINT_WRITE, txstring)
    rxdata = self._devUsb.read(self.USB_ENDPOINT_READ, 64)
    rxstring = ""
    for byte in rxdata:
      if (byte > 0 and byte < 255):
        rxstring = rxstring + chr(byte)
      else:
        break
    self._log.debug("ReceivedStr: \'{:}\'".format(rxstring))
    # Verify that the operation is framed, otherwise the operation failed.
    success = False
    reply = None
    if rxstring.startswith(txstring[0]):
      rxstring = rxstring[1:]
      reply = operation + '=' + rxstring
      success = True
    return (success, reply)

  def operation(self, operation):
    """
    Perform an operation on the device.
    :param str operation: the operation string
    :return (success, reply) where
      success bool: whether the command was successful
      reply str: the reply string
    :rtype: tuple
    """
    # Send operation.
    self._log.debug("Sending operation: \'{:s}\'".format(operation))
    if self._device.startswith('usb'):
      (success, reply) = self.operationUsb(operation)
    else:
      (success, reply) = self.operationNet(operation)
    # Print data received.
    self._log.debug("Received reply: \'{:}\' => {:s}".format(reply, ['FAILED', 'OK'][success]))
    return (success, reply)

  def commandComposeScpi(self, state, switch=None):
    """
    Return the SCPI string for a switch command.
    :param int state: the desired switch state
    :param str/int switch: the switch to control, e.g. 0 or 'A'
    :return: the SCPI command
    :rtype: str
    """
    # Handle switch argument.
    if switch is None:
      switch = self._switch
    if isinstance(switch, int):
      switch = chr(switch + 65)
    # If there is only one switch, omit the argument.
    if self.switches == 1:
      switch = ''
    # Handle composition based on states.
    if self.states in [2, 'D']:
      # Example commands:
      #   Read : SETA
      #   Write: SETA=3
      if state == None:
        cmd = "SET{:}".format(switch)
      else:
        cmd = "SET{:}={:d}".format(switch, int(state))
    elif self.states in range(4, 17):
      # Example commands:
      #   Read : SP8T:STATE
      #   Write: SP8T:STATE:3
      if state == None:
        cmd = "SP{:}T{:}:STATE".format(self.states, switch)
      else:
        cmd = "SP{:}T{:}:STATE:{:d}".format(self.states, switch, int(state))
    else:
      raise ValueError('Unsupported states/throws')
    return cmd

  def replyParse(reply_string):
    reply_result = None
    # Split on '='.
    reply_result = reply_string.split('=')
    # Try to convert each field to int, or float, or leave as string
    for n, v in enumerate(reply_result):
      try:
        reply_result[n] = int(reply_result[n])
      except ValueError:
        try:
          reply_result[n] = float(reply_result[n])
        except ValueError:
          pass
    return reply_result

  def command(self, cmd, args=[]):
    """
    Perform a command on the device.
    :param str cmd: the command string, e.g. 'SETA='
    :param list args: the argument list, e.g. [1]
    :return: whether the command was successful
    :rtype: bool
    """
    opstr = "{:s}".format(cmd)
    for arg in args:
      opstr = opstr + "{:d}".format(arg)
    (success, reply) = self.operation(opstr)
    if success is True:
      # Parse query results
      cmd_result = rfswitch.replyParse(reply)
      # Check for reply of '1' to indicate command success.
      if cmd_result[1] != 1:
        success = False
    self._log.info("Command: {:s} => {}".format(opstr, ['FAILED', 'OK'][success]))
    return success

  def query(self, cmd):
    """
    Perform a query on the device.
    :param str cmd: the command string without the ?, e.g. 'MN'
    :return: query result as a list
    :rtype: tuple
    """
    opstr = "{:s}?".format(cmd)
    (success, reply) = self.operation(opstr)
    query_result = None
    if success is True:
      # Parse query results
      query_result = rfswitch.replyParse(reply)
    self._log.info("Query: {:s} => {}".format(cmd, query_result))
    return query_result

  def set(self, state, switch=None):
    """
    Set RF switch to requested state.
    You can use letter or number arguments for switch.
    :param int state: the desired switch state
    :param str/int switch: the switch to control, e.g. 0 or 'A'
    :return: True if the command was successful
    :rtype: bool
    """
    # Compose and send the operation.
    cmd = self.commandComposeScpi(state, switch)
    success = self.command(cmd)
    self._log.info("Set Sw{:}={:d} => {:s}".format(switch, state, ['FAILED', 'OK'][success]))
    return success

  def get(self, switch=None):
    """
    Get RF switch current state.
    You can use letter or number arguments for switch.
    :param str/int switch: the switch to control, e.g. 0 or 'A'
    :return: current state of the switch
    :rtype: int
    """
    # Compose and send the operation.
    cmd = self.commandComposeScpi(None, switch)
    state = self.query(cmd)
    # Extract data from reply.
    if state is None:
      self._log.error("Get Sw{:} => FAILED".format(switch))
    else:
      state = state[1]
      self._log.info("Get Sw{:}={:d}".format(switch, state))
    return state

def main():
  # Parse the arguments.
  parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='RF Switch Control Utility for MiniCircuits RC Series.',
    epilog= 'Examples:\n' +
            '  rfswitchMcl usb MN?\n' +
            '  rfswitchMcl usb SP8T:STATE:1\n' +
            '  rfswitchMcl 192.168.1.100 MN?\n' +
            '  rfswitchMcl 192.168.1.100 SP6TA:STATE?\n' +
            '  rfswitchMcl 192.168.1.100 SP6TA:STATE:1\n')
  parser.add_argument('device', metavar='device', type=str,
                      help='URI/IP address of the RF switch, or \'usb\' for USB access')
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

  # Create instance and run operation.
  rfswInst = rfswitch(args.device, loglevel=args.loglevel)
  rfswInst.open()
  if args.cmd.endswith('?'):
    args.cmd = args.cmd.rstrip('?')
    print(rfswInst.query(cmd=args.cmd))
  elif args.args is None:
    print(rfswInst.command(cmd=args.cmd))
  else:
    print(rfswInst.command(cmd=args.cmd, args=[args.args]))
  rfswInst.close()

if __name__ == '__main__':
  main()

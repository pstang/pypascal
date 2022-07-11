#!/usr/bin/env python3

"""
RF Switch control library for MiniCircuits RC Series.
Copyright (c) 2017-2021 Pascal Stang
This program comes with ABSOLUTELY NO WARRANTY.

This module provides simple control of RF switches.
Supported devices include:
  - MiniCircuits RC-Series switches

The module can also be run as a console tool, invoke with no arguments for
usage help.

TODO(pstang): Expand to also support USB access.

Example Usage:

  import rfswitchMcl

  DEVICE = '192.168.1.100'

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

class rfswitch:
  OPERATION_TERMINATOR = '\r\n'
  REPLY_TERMINATOR = '\n\r'

  def __init__(self, device, switch=None, loglevel=logging.ERROR):
    self._device = device
    self._port = 23
    self._switch = switch
    logging.basicConfig(format = '%(levelname)s:%(name)s:%(message)s', level=loglevel)
    self._log = logging.getLogger(__name__)

  def open(self):
    """Open the communication port."""
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
    fields = parse.parse("RC-{:d}{:l}P{:d}T-A{:d}", self.model)
    self.switches = fields[0]
    self.poles = fields[1]
    self.states = fields[2]

  def operation(self, operation):
    """
    Perform an operation on the device.
    :param str operation: the operation string
    :return (success, reply) where
      success bool: whether the command was successful
      reply str: the reply string
    :rtype: tuple
    """
    # Open TCP socket to device.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
      sock.connect((str(self._device), int(self._port)))
    except:
      self._log.error("Connection to {:s} FAILED".format(str(self._device)))
      return (False, "")
    # Send operation.
    self._log.debug("Sending operation: \'{:s}\'".format(operation))
    txstring = operation + rfswitch.OPERATION_TERMINATOR
    sock.send(txstring.encode('utf-8'))
    # Send logout command to gracefully close socket connection.
    #sock.send('logout\r'.encode('utf-8'))
    # Use brief delay to allow device to respond.
    time.sleep(0.05)
    # Capture the recevied data from session.
    rxstring = sock.recv(1024)
    sock.close()
    self._log.debug("Received: \'{:}\'".format(rxstring))
    # Verify that the operation is framed, otherwise the operation failed.
    rxstring = rxstring.decode()
    success = False
    reply = None
    if rxstring.startswith(rfswitch.OPERATION_TERMINATOR):
      if rxstring.endswith(rfswitch.REPLY_TERMINATOR):
        # Strip off <CR><LF>
        rxstring = rxstring.strip()
        reply = rxstring
        success = True
    # Print data received.
    self._log.debug("Received reply: \'{:}\' => {:s}".format(reply, ['FAILED', 'OK'][success]))
    return (success, reply)

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
    # Check for reply of '1' to indicate command success.
    if reply is not '1':
      success = False
    self._log.info("command: {:s} => {}".format(opstr, ['FAILED', 'OK'][success]))
    return success

  def queryParse(query_string):
    query_result = None
    # Split on '='.
    query_result = query_string.split('=')
    # Try to convert each field to int, or float, or leave as string
    for n, v in enumerate(query_result):
      try:
        query_result[n] = int(query_result[n])
      except ValueError:
        try:
          query_result[n] = float(query_result[n])
        except ValueError:
          pass
    return query_result

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
      # Parse query result
      query_result = rfswitch.queryParse(reply)
    self._log.info("query: {:s} => {}".format(cmd, query_result))
    return query_result

  def set(self, state, switch=None):
    """
    Set RF switch to requested state.
    You can use letter or number arguments for switch.
    :param int state: the desired switch state
    :param str/int switch: the switch to control, e.g. 0 or 'A'
    :return: whether the command was successful
    :rtype: bool
    """
    # Process switch argument.
    if switch is None:
      switch = self._switch
    if isinstance(switch, int):
      switch = chr(switch + 65)
    # Compose and send the operation.
    state = int(state)
    print(self.states)
    if self.states in [2, 'D']:
      cmd = "SET{:}={:d}".format(switch, state)
    elif self.states in [4, 6]:
      cmd = "SP{:}T{:}:STATE:{:d}".format(self.states, switch, state)
    else:
      return False
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
    # Process switch argument.
    if switch is None:
      switch = self._switch
    if isinstance(switch, int):
      switch = chr(switch + 65)
    # Compose and send the operation.
    if self.states in [2, 'D']:
      cmd = "SET{:}".format(switch)
    elif self.states in [4, 6]:
      cmd = "SP{:}T{:}:STATE".format(self.states, switch)
    else:
      return None
    cmd = "SP6T{:}:STATE".format(switch)
    state = self.query(cmd)
    # Extract data from reply.
    if state is None:
      self._log.error("Get Sw{:} => FAILED".format(switch))
    else:
      state = state[0]
      self._log.info("Get Sw{:}={:d}".format(switch, state))
    return state

def main():
  # Parse the arguments.
  parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='RF Switch Control Utility for MiniCircuits RC Series.',
    epilog= 'Examples:\n' +
            '  rfswitchMcl 192.168.1.100 MN?\n' +
            '  rfswitchMcl 192.168.1.100 SP6TA:STATE?\n' +
            '  rfswitchMcl 192.168.1.100 SP6TA:STATE:1\n')
  parser.add_argument('device', metavar='device', type=str,
                      help='URI/IP address of the RF switch')
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

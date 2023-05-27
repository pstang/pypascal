#!/usr/bin/env python3

"""
SynAccess PDU control library.
Copyright (c) 2021 Pascal Stang
This program comes with ABSOLUTELY NO WARRANTY.

This module provides simple library access to SynAccess switched PDUs.
The module can also be run as a console tool, invoke with no arguments for
usage help.

TODO(pstang): Expand to also support serial port access.

Example Usage:

  import pduSynaccess

  HOST = '192.168.1.100'

  # Create PDU without channel specified (arbitrary access).
  pdu = pduSynaccess.pdu(uri=HOST)
  pdu.on(ch=2)
  time.sleep(1)
  pdu.off(ch=2)
  pdu.set(ch=1, state=False)
  pdu.set(ch=2, state=False)
  pdu.set(ch=3, state=False)
  print("Channel state = " + str(pdu.get()))

  # Create PDU with channel specified (tied to channel).
  pduCh = pduSynaccess.pdu(uri=HOST, ch=3)
  pduCh.on()
  time.sleep(1)
  pduCh.off()
"""

# system
import argparse
import logging
import serial
import socket
import sys
import time

class pdu:
  def __init__(self, uri, ch=None, loglevel=logging.ERROR):
    self._uri = uri
    self._port = 23
    self._ch = ch
    logging.basicConfig(format = '%(levelname)s:%(name)s:%(message)s', level=loglevel)
    self._log = logging.getLogger(__name__)

  def operation(self, operation):
    # Open TCP socket to device.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(4)
    try:
      sock.connect((str(self._uri), int(self._port)))
    except:
      self._log.error("Connection to {:s} FAILED".format(str(self._uri)))
      return (False, "")
    # Send operation.
    self._log.debug("Sending operation: " + operation)
    opstring = '\r' + operation + '\r'
    sock.send(opstring.encode('utf-8'))
    # Send logout command to gracefully close socket connection.
    sock.send('logout\r'.encode('utf-8'))
    # Use brief delay to allow device to respond.
    # Delay was increased to 300ms to work properly with slower 8ch Synaccess PDUs.
    # TODO(pstang): Change this implementation to a continuous read looking for
    # command echo response, up to a timeout value.
    time.sleep(0.3)
    # Capture the recevied data from session.
    rxstring = sock.recv(4096)
    sock.close()
    # Print data received.
    self._log.debug("Received reply: " + str(rxstring))
    # Verify that the operation was echoed, otherwise the operation failed.
    if (str(operation) in str(rxstring)):
      success = True
    else:
      success = False
    return (success, rxstring)

  def command(self, cmd):
    reply = self.operation(cmd)
    success = reply[0]
    return success

  def set(self, ch, state):
    """Set PDU channel to requested state."""
    # Compose and send the operation.
    offon = int(bool(state));
    cmd = "pset {:d} {:d}".format(ch, offon)
    success = self.command(cmd)
    self._log.info("Set Ch{:d}={:s} => {:s}".format(ch, ['OFF', 'ON'][offon], ['FAILED', 'OK'][success]))
    return success

  def get(self, ch=None):
    """Get PDU channel state."""
    if ch is None:
      ch = self._ch
    # Compose and send the operation.
    cmd = 'sysshow'
    reply = self.operation(cmd)
    if reply[0] is False:
      self._log.error("Get Ch => FAILED")
      return None
    # Extract data from string reply.
    replystring = str(reply[1])
    replystring = replystring.partition("Outlet Status")[2].partition("\\r")[0]
    replystring = replystring.partition(":")[2]
    replystring = replystring.strip()
    chstate = replystring.split(" ")
    chstate = [int(x) for x in chstate]
    # Reduce data to one channel if specified.
    if ch is not None:
      chstate = chstate[ch-1]
      self._log.info("Get Ch{:d}={:s}".format(ch, ['OFF', 'ON'][chstate]))
    else:
      self._log.info("Get Ch= " + str(chstate))
    return chstate

  def on(self, ch=None):
    """Set PDU channel ON."""
    if ch is None:
      ch = self._ch
    return self.set(ch, True)

  def off(self, ch=None):
    """Set PDU channel OFF."""
    if ch is None:
      ch = self._ch
    return self.set(ch, False)

def strBool(v):
  if isinstance(v, bool):
    return v
  elif v.lower() in ('0', 'off', 'false', 'no'):
    return False
  elif v.lower() in ('1', 'on', 'true', 'yes'):
    return True
  else:
    raise argparse.ArgumentTypeError('Boolean value expected.')

def main():
  # Parse the arguments.
  parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='Synaccess PDU Control Utility.',
    epilog= 'Examples:\n' +
            '  pduSynaccess 192.168.1.100 1 on\n' +
            '  pduSynaccess 192.168.1.100 3 off\n')
  parser.add_argument('host', metavar='host', type=str,
                      help='host/ip address of the PDU')
  parser.add_argument('ch', metavar='channel', type=int,
                      help='channel to access [1-N]')
  parser.add_argument('state', metavar='state', type=strBool,
                      help='power state to set [0/1, on/off, true/false, yes/no]')
  parser.add_argument('--debug', dest='loglevel', action='store_const',
                      const='DEBUG', default=None,
                      help='produce debugging output (like --log DEBUG)')
  parser.add_argument('--log', dest='loglevel', type=str, default=None,
                      help='set log level',
                      choices=['DEBUG','INFO','ERROR'])
  args = parser.parse_args()

  # Create PDU and run operation.
  pduInst = pdu(args.host, loglevel=args.loglevel)
  pduInst.set(ch=args.ch, state=args.state)

if __name__ == '__main__':
  main()

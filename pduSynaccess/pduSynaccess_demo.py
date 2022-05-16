#!/usr/bin/env python3

"""
SynAccess PDU control library demonstration.
Copyright (c) 2022 Pascal Stang
This program comes with ABSOLUTELY NO WARRANTY.
"""

# system
import logging
import sys
import time
# package
import pduSynaccess

HOST = '192.168.1.100'

DELAY = 0.0

def pduCycle():
  # Create PDU without channel specified (arbitrary access).
  pdu = pduSynaccess.pdu(uri=HOST, debuglevel=logging.INFO)
  # Sequence all channels
  print("Channel state = {:s}".format(str(pdu.get())))
  for ch in range(1,6):
    print("Turning on ch{:d}".format(ch))
    pdu.set(ch=ch, state=True)
    time.sleep(DELAY)
  print("Channel state = {:s}".format(str(pdu.get())))
  for ch in range(1,6):
    print("Turning off ch{:d}".format(ch))
    pdu.set(ch=ch, state=False)
    time.sleep(DELAY)
  print("Channel state = {:s}".format(str(pdu.get())))

def pduChannel():
  # Create PDU with channel specified (tied to channel).
  pduCh = pduSynaccess.pdu(uri=HOST, ch=3, debuglevel=logging.INFO)
  print("Turning on channel")
  pduCh.on()
  print("Channel state = {:s}".format(str(pduCh.get())))
  time.sleep(DELAY)
  print("Turning off channel")
  pduCh.off()
  print("Channel state = {:s}".format(str(pduCh.get())))

def main():
  pduCycle()
  pduChannel()

if __name__ == '__main__':
  main()

#!/usr/bin/env python3

"""
RF Switch control library demonstration.
Copyright (c) 2017-2021 Pascal Stang
This program comes with ABSOLUTELY NO WARRANTY.

Demo tested on a MiniCircuits USB-1SP8T-852H.
"""

# system
import logging
import sys
import time
# package
import rfswitchMcl

DEVICE = 'usb'

def rfswitchCharacteristics(rfsw):
  print("Model: " + rfsw.model)
  print("Serial: " + str(rfsw.serialnumber))
  print(" Switches: " + str(rfsw.switches))
  print(" Poles: " + str(rfsw.poles))
  print(" States/Throws: " + str(rfsw.states))

def rfswitchRoundRobin(rfsw):
  for n in range(1,rfsw.states+1,1):
    print('rfsw#{} set({}) => {}'.format(0, n, rfsw.set(switch=0, state=n)))
    print('rfsw#{} get() => {}'.format(0, rfsw.get(switch=0)))
    time.sleep(0.5)
  print('rfsw#{} set({}) => {}'.format(0, 0, rfsw.set(switch=0, state=0)))
  print('rfsw#{} get() => {}'.format(0, rfsw.get(switch=0)))

def rfswitchError(rfsw):
  print('rfsw#{} set({}) => {}'.format(0, 0, rfsw.set(switch=0, state=0)))
  print('rfsw#{} get() => {}'.format(0, rfsw.get(switch=0)))
  time.sleep(0.5)
  print('rfsw#{} set({}) => {}'.format(0, 1, rfsw.set(switch=0, state=1)))
  print('rfsw#{} get() => {}'.format(0, rfsw.get(switch=0)))

def main():
  # Create instance.
  # Set a high logging level so we can see our operations.
  rfsw = rfswitchMcl.rfswitch(device=DEVICE,
                              loglevel=logging.INFO)
  # Open the channel to the RF switch.
  rfsw.open()

  rfswitchCharacteristics(rfsw)

  # Do some operations.
  rfswitchRoundRobin(rfsw)
  rfswitchError(rfsw)

  # Close the channel.
  rfsw.close()

if __name__ == '__main__':
  main()

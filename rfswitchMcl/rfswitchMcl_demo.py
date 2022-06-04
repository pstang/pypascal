#!/usr/bin/env python3

"""
RF Switch control library demonstration.
Copyright (c) 2017-2021 Pascal Stang
This program comes with ABSOLUTELY NO WARRANTY.

Demo tested on a MiniCircuits RC-2SP6T-A12.
"""

# system
import logging
import sys
import time
# package
import rfswitchMcl

DEVICE = '192.168.1.100'

def rfswitchCharacteristics(rfsw):
  print("Model: " + rfsw.model)
  print("Serial: " + str(rfsw.serialnumber))
  print(" Switches: " + str(rfsw.switches))
  print(" Poles: " + str(rfsw.poles))
  print(" States/Throws: " + str(rfsw.states))

def rfswitchDirectCommandQuery(rfsw):
  print(rfsw.query('MN'))
  print(rfsw.query('SP6TA:STATE'))
  print(rfsw.query('SP6TB:STATE'))

  print(rfsw.command(cmd='SP6TA:STATE:', args=[1]))
  print(rfsw.command(cmd='SP6TB:STATE:', args=[1]))
  time.sleep(1)
  print(rfsw.command(cmd='SP6TA:STATE:', args=[0]))
  print(rfsw.command(cmd='SP6TB:STATE:', args=[0]))
  time.sleep(1)

def rfswitchBasicOperation(rfsw):
  # You can use letter or number arguments for switch.
  rfsw.set(switch='A', state=1)
  rfsw.set(switch='B', state=1)
  rfsw.set(switch=0, state=1)
  rfsw.set(switch=1, state=1)
  time.sleep(1)
  rfsw.set(switch='A', state=0)
  rfsw.set(switch='B', state=0)
  rfsw.set(switch=0, state=0)
  rfsw.set(switch=1, state=0)
  time.sleep(1)
  print(rfsw.get(switch='A'))
  print(rfsw.get(switch='B'))
  print(rfsw.get(switch=0))
  print(rfsw.get(switch=1))

def rfswitchRoundRobin(rfsw):
  for n in range(1,rfsw.states+1,1):
    rfsw.set(switch='A', state=n)
    rfsw.set(switch='B', state=n)
    time.sleep(0.5)
  rfsw.set(switch='A', state=0)
  rfsw.set(switch='B', state=0)
  print(rfsw.get(switch='A'))
  print(rfsw.get(switch='B'))

def rfswitchDedicatedSwitch():
  # Create instance to specific switch in array.
  # Set a high logging level so we can see our operations.
  rfswA = rfswitchMcl.rfswitch(device=DEVICE,
                              switch='A',
                              loglevel=logging.INFO)
  # Open the channel to the RF switch.
  rfswA.open()
  rfswitchCharacteristics(rfswA)
  # Do some operations.
  rfswA.set(1)
  time.sleep(1)
  rfswA.set(2)
  time.sleep(1)
  rfswA.set(0)
  print(rfswA.get())
  # Close the channel.
  rfswA.close()

def main():
  # Create instance.
  # Set a high logging level so we can see our operations.
  rfsw = rfswitchMcl.rfswitch(device=DEVICE,
                              loglevel=logging.INFO)
  # Open the channel to the RF switch.
  rfsw.open()

  rfswitchCharacteristics(rfsw)

  # Do some operations.
  rfswitchDirectCommandQuery(rfsw)
  rfswitchBasicOperation(rfsw)
  rfswitchRoundRobin(rfsw)

  # Close the channel.
  rfsw.close()

  # Dedicated channel demonstration.
  rfswitchDedicatedSwitch()

if __name__ == '__main__':
  main()

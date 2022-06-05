#!/usr/bin/env python3

"""
Watlow F4 Temperature Controller driver library.
Copyright (c) 2015-2022 Pascal Stang
This program comes with ABSOLUTELY NO WARRANTY.
"""

# system
import logging
import sys
import time
# package
import watlowf4

SERIAL = '/dev/ttyUSB0'

def main():
  # Create library instance for the device.
  wf4 = watlowf4.watlowf4(device=SERIAL)
  # Open communications.
  wf4.open()

  # Do operations.
  print("Temp Setpoint = {:} C".format(wf4.getTemperatureSetpoint()))
  print("Current Temp  = {:} C".format(wf4.getTemperature()))

  time.sleep(1)

  targetC = 25.0
  print("Setting Temp Setpoint to {:} C".format(targetC))
  wf4.setTemperatureSetpoint(targetC)
  print("Temp Setpoint = {:} C".format(wf4.getTemperatureSetpoint()))
  print("Current Temp  = {:} C".format(wf4.getTemperature()))

  # Close communications.
  wf4.close()

if __name__ == '__main__':
  main()
